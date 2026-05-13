import logging
import asyncio
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from backend.database.database import SessionLocal
from backend.services.llm.llm_provider import generate_json
from backend.models.document import Document
from backend.models.document_block import DocumentBlock
from backend.services.vector.vector_store import query_similar_chunks
from backend.services.reporting.report_schema import ReportModel, ReportSection, KeyFigure
from backend.services.reporting.timeline_extractor import generate_timeline
from backend.services.reporting.insight_extractor import generate_report_insights
from backend.services.reporting.chart_validator import validate_charts
from backend.services.observability.langfuse_client import langfuse
from backend.services.observability.langfuse_helpers import (
    langfuse_span,
    hash_text,
)

logger = logging.getLogger(__name__)

REPORT_LLM_CONCURRENCY = 2
report_semaphore = asyncio.Semaphore(REPORT_LLM_CONCURRENCY)

# -------- HELPER FUNCTION FOR LANGUAGE --------
def language_instruction(lang: str) -> str:
    """
    Generate a language instruction for the LLM.
    Ensures that the LLM produces output entirely in the specified
    language and does not mix languages within headings or labels.
    """
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

SECTION_QUERY_VARIANTS = {
    "Executive Summary": [
        "executive summary",
        "document overview",
        "main purpose of the document",
        "overall business summary",
    ],

    "Key Findings": [
        "important findings",
        "main insights",
        "key developments",
        "important decisions",
    ],

    "Key Figures": [
        "financial metrics",
        "important numbers",
        "KPIs revenue profit growth",
        "financial performance",
    ],

    "Risks & Issues": [
        "risks warnings concerns",
        "issues inconsistencies",
        "potential problems",
        "compliance risk",
    ],

    "Conclusion": [
        "final conclusion",
        "overall assessment",
        "future outlook",
        "summary outcome",
    ],
}

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
    """Detect the currency type from a unit string."""
    u = (unit or "").lower()
    if ("€" in u) or ("eur" in u) or ("euro" in u):
        return "EUR"
    if ("$" in u) or ("usd" in u) or ("dollar" in u):
        return "USD"
    return "UNKNOWN"


def currency_symbol(currency: str) -> str:
    """
    Convert a currency code into its symbol.

    Returns:
        Currency symbol ("€", "$") or empty string if unknown.
    """
    return "€" if currency == "EUR" else "$" if currency == "USD" else ""


def format_compact_money(amount: float, currency: str) -> str:
    """
    Format a numeric amount into a compact human-readable string.
    Examples:
        1200000 -> 1,20 Mio. €
        2300000000 -> 2,30 Mrd. €
    """
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
    """Normalize and standardize a key figure value."""

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


# -------------------- SECTION GENERATION --------------------
async def generate_section(
    heading: str,
    instruction: str,
    document_id: int,
    system_section: str,
    system_keyfig: str,
    base_meta: Dict[str, Any]
):
    """
    Generate a single report section using LLM analysis.

    The function retrieves relevant document chunks using semantic
    vector search and constructs an evidence prompt. The evidence
    is then passed to the LLM to generate a structured section.

    For the "Key Figures" section, the LLM extracts structured
    KPI objects which are returned separately.

    Returns:
        Tuple containing:
            - ReportSection object
            - List of extracted KeyFigure objects
    """
    async with report_semaphore:
        db = SessionLocal()

        try:
            queries = SECTION_QUERY_VARIANTS.get(
                heading,
                [f"{heading}. {instruction}"]
            )

            all_hits = []

            for q in queries:
                hits = query_similar_chunks(
                    document_id=document_id,
                    query=q,
                    k=15,
                )

                all_hits.extend(hits)

            # -------- DEDUPLICATION + DIVERSITY --------

            seen_texts = set()
            page_counts = {}

            filtered_hits = []

            all_hits.sort(
                key=lambda x: x.get("score", 0),
                reverse=True
            )

            for h in all_hits:
                text = " ".join(
                    (h.get("text") or "").split()
                ).strip()

                if not text:
                    continue

                if text in seen_texts:
                    continue

                metadata = h.get("metadata") or {}

                page = metadata.get("page_start")

                # Avoid too many chunks from same page
                if page is not None:
                    count = page_counts.get(page, 0)

                    if count >= 2:
                        continue

                    page_counts[page] = count + 1

                filtered_hits.append(h)
                seen_texts.add(text)

                if len(filtered_hits) >= 15:
                    break

            hits = filtered_hits

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

            evidence_parts = []
            for h in hits:
                md = h.get("metadata") or {}
                evidence_parts.append(
                    f"[{h.get('id')}] (p{md.get('page_start')}–{md.get('page_end')}, section={md.get('section_title')})\n"
                    f"{(h.get('text') or '').strip()}"
                )

            evidence_text = "\n\n---\n\n".join(evidence_parts)[:12000]

            sources_fallback = []
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

            if heading == "Key Figures":
                data = await asyncio.to_thread(
                    lambda: generate_json(
                        model="gpt-4o-mini",
                        system_prompt=system_keyfig,
                        user_prompt=user_prompt,
                        temperature=0.2,
                        trace_meta={**base_meta, "report_section": heading},
                        trace_input={"task": "report_section", "heading": heading},
                    )
                )

                figures = data.get("key_figures", []) if isinstance(data, dict) else []

                lines = []
                key_figure_objects = []

                for f in figures[:12]:
                    if not isinstance(f, dict):
                        continue

                    name = f.get("name", "")
                    value = f.get("value", "")
                    unit = f.get("unit", "")
                    context = f.get("context", "")

                    lines.append(f"- {name}: {value} {unit} ({context})")

                    key_figure_objects.append(
                        KeyFigure(
                            name=name,
                            value=value,
                            unit=unit,
                            context=context
                        )
                    )

                return (
                    ReportSection(
                        heading=heading,
                        content="\n".join(lines),
                        sources=(
                            data.get("sources", sources_fallback)
                            if isinstance(data, dict) and isinstance(data.get("sources"), list)
                            else sources_fallback
                        ),
                    ),
                    key_figure_objects
                )

            data = await asyncio.to_thread(
                lambda: generate_json(
                    model="gpt-4o-mini",
                    system_prompt=system_section,
                    user_prompt=user_prompt,
                    temperature=0.3,
                    trace_meta={**base_meta, "report_section": heading},
                    trace_input={"task": "report_section", "heading": heading},
                )
            )

            if not isinstance(data, dict):
                data = {}

            sources = data.get("sources", sources_fallback)
            if not isinstance(sources, list):
                sources = sources_fallback

            return (
                ReportSection(
                    heading=data.get("heading", heading),
                    content=data.get("content", "") or "",
                    sources=sources,
                ),
                []
            )

        finally:
            db.close()


# -------------------- MAIN --------------------
async def generate_report_for_document(db: Session, document_id: int) -> Dict[str, Any]:
    """
    Generate a full structured report for a document.

    The report is created in multiple parallel LLM calls, each generating a specific section.
    Extracted key figures are aggregated separately.

    The pipeline performs the following steps:
        1. Retrieve document metadata
        2. Generate report sections in parallel
        3. Aggregate key figures
        4. Create a final report wrapper (title, summary, conclusion)

    Returns:
        Dictionary representation of the generated report.
    """
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

    with langfuse_span(
        langfuse,
        name="report.generate",
        input={"document_id": document_id},
        metadata={**base_meta, "sections_total": len(REPORT_SECTIONS)}
    ):
        tasks = [
            generate_section(
                heading,
                instruction,
                document_id,
                system_section,
                system_keyfig,
                base_meta
            )
            for heading, instruction in REPORT_SECTIONS
        ]

        results = await asyncio.gather(*tasks)

        sections: List[ReportSection] = []
        key_figures: List[KeyFigure] = []

        for section, kf in results:
            sections.append(section)
            key_figures.extend(kf)

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

        key_figure_dicts = [kf.model_dump() for kf in key_figures]

        insight_data = await generate_report_insights(
            assembled_report=assembled,
            key_figures=key_figure_dicts,
            lang_rule=lang_rule,
            base_meta=base_meta,
        )

        timeline = await generate_timeline(
            assembled_report=assembled,
            lang_rule=lang_rule,
            base_meta=base_meta,
        )

        charts = validate_charts(insight_data.get("charts", []))

        report = ReportModel(
            title=final_json.get("title", f"Report for {document.filename}"),
            summary=final_json.get("summary", ""),
            sections=sections,
            key_figures=key_figures,
            main_findings=insight_data.get("main_findings", []),
            risks=insight_data.get("risks", []),
            recommendations=insight_data.get("recommendations", []),
            charts=charts,
            timeline=timeline,
            conclusion=final_json.get("conclusion", ""),
        )

        return report.model_dump()
