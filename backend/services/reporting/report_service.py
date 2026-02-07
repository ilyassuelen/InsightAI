import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from backend.services.llm.llm_provider import generate_json
from backend.models.document import Document
from backend.models.document_block import DocumentBlock
from backend.services.vector.vector_store import query_similar_chunks
from backend.services.reporting.report_schema import ReportModel, ReportSection, KeyFigure
from backend.services.observability.langfuse_client import langfuse
from backend.services.observability.langfuse_helpers import (
    langfuse_span,
    hash_text,
)

logger = logging.getLogger(__name__)

# -------- HELPER FUNCTION FOR LANGUAGE --------
def language_instruction(lang: str) -> str:
    lang = (lang or "de").strip()
    low = lang.lower()
    if low in ("de", "german", "deutsch"):
        return (
            "Output language: German (de). "
            "IMPORTANT: Write the entire output strictly in German. "
            "Do not use English words for headings or labels."
        )
    if low in ("en", "english"):
        return (
            "Output language: English (en). "
            "IMPORTANT: Write the entire output strictly in English."
        )
    return (
        f"Output language: {lang}. "
        f"IMPORTANT: Write the entire output strictly in {lang}. "
        "Do not mix languages."
    )

REPORT_SECTIONS = [
    ("Executive Summary", "High-level overview of the document and its purpose."),
    ("Key Findings", "Most important insights, takeaways, patterns or decisions."),
    ("Key Figures", "Extract explicit numerical values, totals, KPIs stated in the document."),
    ("Risks & Issues", "Risks, inconsistencies, missing data, warnings, concerns."),
    ("Conclusion", "Concluding statement based strictly on the document."),
]

SYSTEM_SECTION = """
You are an expert business analyst.

Rules:
- Use ONLY the evidence.
- Do not invent facts or numbers.
- Output JSON only.

Return JSON schema:
{
  "heading": string,
  "content": string,
  "sources": [
    {"chunk_id": string, "page_start": integer|null, "page_end": integer|null, "section_title": string|null}
  ]
}
""".strip()

SYSTEM_KEYFIGURES = """
You extract key figures (KPIs / numbers) from evidence.

Rules:
- Use ONLY evidence. Do not use external knowledge.
- Do NOT calculate or infer missing values.
- Return AT MOST 12 key figures (pick the most important ones).
- Each value MUST include its unit or scale if explicitly present in evidence (e.g. €, EUR, USD, %, million €, bn €, k€).
- If the evidence does not clearly state the unit/scale, set unit to "unknown" and keep the raw value as written.

Output MUST be valid JSON only.

Return JSON schema:
{
  "key_figures": [
    {
      "name": string,
      "value": string,
      "unit": string,
      "context": string
    }
  ],
  "sources": [
    {"chunk_id": string, "page_start": integer|null, "page_end": integer|null, "section_title": string|null}
  ]
}

Field notes:
- "name": short clear KPI name (e.g. "Total revenue 2023/24")
- "value": the number exactly as shown (e.g. "3.2", "51.2", "1,027")
- "unit": must be explicit ("EUR", "€", "%", "million €", "unknown", etc.)
- "context": short hint like year/club/metric reference
""".strip()

SYSTEM_FINAL = """
You create the final report wrapper based ONLY on the drafted sections.
Output JSON only.

Return JSON schema:
{ "title": string, "summary": string, "conclusion": string }
""".strip()


# -------------------- HELPERS FOR NORMALIZATION --------------------
def parse_number_de(value: str) -> Optional[float]:
    """
    Parses German-style numbers:
    - "1.875.394" -> 1875394
    - "1,23" -> 1.23
    """
    if not value:
        return None
    s = value.strip().replace(" ", "")
    s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def detect_currency(unit: str) -> str:
    u = (unit or "").lower()
    if ("€" in u) or ("eur" in u) or ("euro" in u):
        return "EUR"
    if ("$" in u) or ("usd" in u) or ("dollar" in u):
        return "USD"
    return "UNKNOWN"


def currency_symbol(currency: str) -> str:
    return "€" if currency == "EUR" else "$" if currency == "USD" else ""


def format_compact_money(amount: float, currency: str) -> str:
    sym = currency_symbol(currency)

    if amount >= 1_000_000_000:
        return (f"{amount / 1_000_000_000:.2f}".replace(".", ",") + f" Mrd. {sym}").strip()
    if amount >= 1_000_000:
        return (f"{amount / 1_000_000:.2f}".replace(".", ",") + f" Mio. {sym}").strip()
    return (f"{int(round(amount)):,}".replace(",", ".") + f" {sym}").strip()


def is_thousand_unit(unit: str) -> bool:
    u = (unit or "").lower().replace(".", "").strip()
    return ("tausend" in u) or ("tsd" in u) or ("thousand" in u) or ("k€" in u) or ("keur" in u) or ("kusd" in u)


def normalize_key_figure(kf: KeyFigure) -> KeyFigure:
    unit = (kf.unit or "").strip()
    currency = detect_currency(unit)

    # Only normalize for known currencies (EUR/USD)
    if currency == "UNKNOWN":
        return kf

    num = parse_number_de(kf.value)
    if num is None:
        return kf

    # Thousand scaling
    if is_thousand_unit(unit):
        amount = num * 1000.0
        kf.value = format_compact_money(amount, currency)
        kf.unit = ""  # value already includes symbol
        return kf

    # Plain currency: compact only if large
    if unit in ["€", "EUR", "$", "USD"] and num >= 1_000_000:
        kf.value = format_compact_money(num, currency)
        kf.unit = ""
        return kf

    return kf


# -------------------- MAIN --------------------
def generate_report_for_document(db: Session, document_id: int) -> Dict[str, Any]:
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise ValueError(f"Document {document_id} not found")

    lang = document.language or "de"
    lang_rule = language_instruction(lang)

    system_section = f"{SYSTEM_SECTION}\n\n{lang_rule}"
    system_keyfig = f"{SYSTEM_KEYFIGURES}\n\n{lang_rule}"
    system_final = f"{SYSTEM_FINAL}\n\n{lang_rule}"

    logger.info(f"Generating report (section-by-section) for document {document_id} (lang={lang})")

    base_meta = {
        "document_id": document_id,
        "workspace_id": getattr(document, "workspace_id", None),
        "language": lang,
        "filename": getattr(document, "filename", None)
    }

    sections: List[ReportSection] = []
    key_figures: List[KeyFigure] = []

    with langfuse_span(
        langfuse,
        name="report.generate",
        input={"document_id": document_id},
        metadata={**base_meta, "sections_total": len(REPORT_SECTIONS)}
    ):
        for heading, instruction in REPORT_SECTIONS:
            with langfuse_span(
                langfuse,
                name="report.section",
                input={"heading": heading},
                metadata={**base_meta, "section_heading": heading}
            ):
                hits = query_similar_chunks(document_id=document_id, query=f"{heading}. {instruction}", k=8)

                if not hits:
                    blocks = (
                        db.query(DocumentBlock)
                        .filter(DocumentBlock.document_id == document_id)
                        .order_by(DocumentBlock.block_index)
                        .limit(12)
                        .all()
                    )
                    hits = [
                        {
                            "id": f"block_{b.id}",
                            "text": b.content,
                            "metadata": {
                                "page_start": None,
                                "page_end": None,
                                "section_title": b.title or b.semantic_label,
                            },
                        }
                        for b in blocks
                    ]

                # 3) Build Evidence-Text
                evidence_parts = []
                for h in hits:
                    md = h.get("metadata") or {}
                    evidence_parts.append(
                        f"[{h.get('id')}] (p{md.get('page_start')}–{md.get('page_end')}, section={md.get('section_title')})\n"
                        f"{(h.get('text') or '').strip()}"
                    )
                evidence_text = "\n\n---\n\n".join(evidence_parts)[:14000]  # safety cap
                evidence_chars = len(evidence_text)
                evidence_hash = hash_text(evidence_text)

                # 4) Sources fallback
                sources_fallback: List[Dict[str, Any]] = []
                for h in hits:
                    md = h.get("metadata") or {}
                    sources_fallback.append({
                        "chunk_id": h.get("id"),
                        "page_start": md.get("page_start"),
                        "page_end": md.get("page_end"),
                        "section_title": md.get("section_title"),
                    })

                user_prompt = f"""
Section: {heading}
Instruction: {instruction}

Evidence (use only this):
{evidence_text}
""".strip()

                trace_meta = {
                    **base_meta,
                    "report_section": heading,
                    "evidence_chars": evidence_chars,
                    "evidence_hash": evidence_hash,
                    "hits_count": len(hits),
                    "sources_count": len(sources_fallback)
                }
                trace_input = {
                    "task": "report_section",
                    "heading": heading
                }

                # 5) LLM Call: OpenAI primary, Gemini fallback
                if heading == "Key Figures":
                    data = generate_json(
                        model="gpt-4o-mini",
                        system_prompt=system_keyfig,
                        user_prompt=user_prompt,
                        temperature=0.2,
                        trace_meta=trace_meta,
                        trace_input=trace_input
                    )

                    extracted = data.get("key_figures", [])
                    validated: List[KeyFigure] = []

                    if isinstance(extracted, list):
                        for item in extracted[:12]:
                            try:
                                validated.append(KeyFigure(**item))
                            except Exception:
                                continue

                    key_figures = [normalize_key_figure(kf) for kf in validated]

                    # Build a readable, user-friendly text (no raw JSON)
                    lines = []
                    for kf in key_figures:
                        unit = "" if (kf.unit in ["", "unknown"]) else f" {kf.unit}"
                        context = f" ({kf.context})" if kf.context else ""
                        lines.append(f"- {kf.name}: {kf.value}{unit}{context}")
                    pretty_content = "\n".join(lines) if lines else "No key figures could be extracted from the evidence."

                    section_dict = {
                        "heading": heading,
                        "content": pretty_content,
                        "sources": data.get("sources", sources_fallback) if isinstance(data.get("sources"),
                                                                                       list) else sources_fallback,
                    }

                else:
                    section_dict = generate_json(
                        model="gpt-4o-mini",
                        system_prompt=system_section,
                        user_prompt=user_prompt,
                        temperature=0.2,
                        trace_meta=trace_meta,
                        trace_input=trace_input
                    )

                    if not isinstance(section_dict, dict):
                        section_dict = {}
                    if not section_dict.get("heading"):
                        section_dict["heading"] = heading
                    if section_dict.get("content") is None:
                        section_dict["content"] = ""
                    if not isinstance(section_dict.get("sources"), list):
                        section_dict["sources"] = sources_fallback

                section_obj = ReportSection(**section_dict)
                sections.append(section_obj)

        # 6) Final wrapper call
        assembled = "\n\n".join([f"{s.heading}\n{s.content}" for s in sections])

        # Trace Meta for final wrapper call
        final_meta = {
            **base_meta,
            "report_stage": "final_wrapper",
            "assembled_chars": len(assembled),
            "assembled_hash": hash_text(assembled)
        }

        final_json = generate_json(
            model="gpt-4o-mini",
            system_prompt=system_final,
            user_prompt=f"Drafted sections:\n\n{assembled}",
            temperature=0.2,
            trace_meta=final_meta,
            trace_input={"task": "report_final_wrapper"}
        )

        report = ReportModel(
            title=final_json.get("title", f"Report for {document.filename}"),
            summary=final_json.get("summary", ""),
            sections=sections,
            key_figures=key_figures,
            conclusion=final_json.get("conclusion", ""),
        )

        return report.model_dump()
