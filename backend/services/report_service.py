import os
import json
import logging
from typing import Any, Dict, List

from sqlalchemy.orm import Session
from openai import OpenAI

from backend.models.document import Document
from backend.models.document_block import DocumentBlock
from backend.services.vector_store import query_similar_chunks
from backend.services.report_schema import ReportModel, ReportSection, KeyFigure

logger = logging.getLogger(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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


def generate_report_for_document(db: Session, document_id: int) -> Dict[str, Any]:
    # 1) Load document
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise ValueError(f"Document {document_id} not found")

    logger.info(f"Generating report (section-by-section) for document {document_id}")

    sections: List[ReportSection] = []
    key_figures: List[KeyFigure] = []

    # 2) Build each section
    for heading, instruction in REPORT_SECTIONS:
        # 2a) Retrieve evidence from Chroma
        hits = query_similar_chunks(document_id=document_id, query=f"{heading}. {instruction}", k=8)

        # 2b) Fallback: if Chroma is empty, use DB blocks
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

        # 2c) Format evidence text (compact)
        evidence_parts = []
        for h in hits:
            md = h.get("metadata") or {}
            evidence_parts.append(
                f"[{h.get('id')}] (p{md.get('page_start')}–{md.get('page_end')}, section={md.get('section_title')})\n"
                f"{(h.get('text') or '').strip()}"
            )
        evidence_text = "\n\n---\n\n".join(evidence_parts)[:14000]  # safety cap

        # 2d) Build fallback sources (always available)
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

        # 2e) Call LLM (JSON only)
        if heading == "Key Figures":
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": SYSTEM_KEYFIGURES},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
                response_format={"type": "json_object"},
            )
            data = json.loads((response.choices[0].message.content or "{}").strip())

            extracted = data.get("key_figures", [])
            validated_key_figures: List[KeyFigure] = []

            if isinstance(extracted, list):
                for item in extracted[:12]:
                    try:
                        validated_key_figures.append(KeyFigure(**item))
                    except Exception:
                        continue

            key_figures = validated_key_figures

            # Build a readable, user-friendly text (no raw JSON)
            lines = []
            for kf in key_figures:
                unit = "" if kf.unit == "unknown" else f" {kf.unit}"
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
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": SYSTEM_SECTION},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
                response_format={"type": "json_object"},
            )
            section_dict = json.loads((response.choices[0].message.content or "{}").strip())

            # Ensure required fields exist (simple guardrails)
            if not section_dict.get("heading"):
                section_dict["heading"] = heading
            if section_dict.get("content") is None:
                section_dict["content"] = ""
            if not isinstance(section_dict.get("sources"), list):
                section_dict["sources"] = sources_fallback

        # 2f) Validate section with Pydantic (guarantees structure)
        section_obj = ReportSection(**section_dict)
        sections.append(section_obj)

    # 3) Final wrapper (title/summary/conclusion) from drafted sections
    assembled = "\n\n".join([f"{s.heading}\n{s.content}" for s in sections])

    final_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_FINAL},
            {"role": "user", "content": f"Drafted sections:\n\n{assembled}"},
        ],
        temperature=0.2,
        response_format={"type": "json_object"},
    )
    final_json = json.loads((final_response.choices[0].message.content or "{}").strip())

    report = ReportModel(
        title=final_json.get("title", f"Report for {document.filename}"),
        summary=final_json.get("summary", ""),
        sections=sections,
        key_figures=key_figures,
        conclusion=final_json.get("conclusion", ""),
    )

    return report.model_dump()