import json
import logging
from typing import Any, Dict, List, Optional

from backend.services.llm.llm_provider import generate_json
from backend.services.reporting.chart_validator import validate_charts

logger = logging.getLogger(__name__)

MAX_SCHEMA_COLUMNS = 120
MAX_PROFILE_CHARS = 12000
MAX_SUMMARY_CHARS = 8000


SYSTEM_CSV_REPORT = """
You are an expert data analyst.

You receive structured metadata from a CSV file:
1. CSV schema
2. CSV profile
3. CSV summary

Create a useful business-style report.

Rules:
- Output JSON only.
- Use ONLY the provided CSV metadata.
- Do not invent facts, labels, columns, units or numbers.
- If the metadata is not enough for a deep interpretation, say that clearly.
- Focus on what the dataset contains, visible structure, important columns, data quality, possible analysis value and limitations.
- Do not mention internal implementation details like Parquet, DuckDB, SQL, embeddings, chunks or RAG.
- Write the entire report in the requested language.

Return JSON schema:
{
  "title": string,
  "summary": string,
  "sections": [
    {
      "heading": string,
      "content": string,
      "sources": []
    }
  ],
  "key_figures": [
    {
      "name": string,
      "value": string,
      "unit": string,
      "context": string
    }
  ],
  "main_findings": [
    {
      "title": string,
      "description": string,
      "importance": "low" | "medium" | "high"
    }
  ],
  "risks": [
    {
      "title": string,
      "description": string,
      "severity": "low" | "medium" | "high"
    }
  ],
  "recommendations": [
    {
      "title": string,
      "description": string,
      "priority": "low" | "medium" | "high"
    }
  ],
  "charts": [
    {
      "title": string,
      "type": "bar" | "line" | "pie",
      "data": [
        {
          "label": string,
          "value": number
        }
      ]
    }
  ],
  "timeline": [],
  "conclusion": string
}
""".strip()


def _compact_json(data: Any, max_chars: int) -> str:
    """
    Convert data to readable JSON and truncate it if it becomes too large.
    """
    text = json.dumps(data, ensure_ascii=False, indent=2, default=str)

    if len(text) <= max_chars:
        return text

    return text[:max_chars] + "\n...TRUNCATED..."


def _normalize_level(value: Any, default: str = "medium") -> str:
    """
    Normalize LLM-generated priority/severity/importance values.
    """
    normalized = str(value or "").strip().lower()

    mapping = {
        "low": "low",
        "niedrig": "low",
        "gering": "low",
        "medium": "medium",
        "mittel": "medium",
        "hoch": "high",
        "high": "high",
    }

    return mapping.get(normalized, default)


def _list_or_empty(value: Any) -> List[Any]:
    """
    Return the value if it is a list, otherwise return an empty list.
    """
    return value if isinstance(value, list) else []


def _normalize_sections(sections: Any) -> List[Dict[str, Any]]:
    """
    Normalize report sections into the structure expected by ReportModel.
    """
    normalized = []

    for section in _list_or_empty(sections):
        if not isinstance(section, dict):
            continue

        normalized.append(
            {
                "heading": str(section.get("heading", "") or "Untitled"),
                "content": str(section.get("content", "") or ""),
                "sources": section.get("sources", [])
                if isinstance(section.get("sources"), list)
                else [],
            }
        )

    return normalized


def _normalize_key_figures(items: Any) -> List[Dict[str, str]]:
    """
    Normalize key figure objects for the report schema.
    """
    normalized = []

    for item in _list_or_empty(items):
        if not isinstance(item, dict):
            continue

        normalized.append(
            {
                "name": str(item.get("name", "") or ""),
                "value": str(item.get("value", "") or ""),
                "unit": str(item.get("unit", "") or ""),
                "context": str(item.get("context", "") or ""),
            }
        )

    return normalized


def _normalize_findings(items: Any) -> List[Dict[str, str]]:
    """
    Normalize main findings.
    """
    normalized = []

    for item in _list_or_empty(items):
        if not isinstance(item, dict):
            continue

        normalized.append(
            {
                "title": str(item.get("title", "") or ""),
                "description": str(item.get("description", "") or ""),
                "importance": _normalize_level(item.get("importance")),
            }
        )

    return normalized


def _normalize_risks(items: Any) -> List[Dict[str, str]]:
    """
    Normalize risk items.
    """
    normalized = []

    for item in _list_or_empty(items):
        if not isinstance(item, dict):
            continue

        normalized.append(
            {
                "title": str(item.get("title", "") or ""),
                "description": str(item.get("description", "") or ""),
                "severity": _normalize_level(item.get("severity")),
            }
        )

    return normalized


def _normalize_recommendations(items: Any) -> List[Dict[str, str]]:
    """
    Normalize recommendation items.
    """
    normalized = []

    for item in _list_or_empty(items):
        if not isinstance(item, dict):
            continue

        normalized.append(
            {
                "title": str(item.get("title", "") or ""),
                "description": str(item.get("description", "") or ""),
                "priority": _normalize_level(item.get("priority")),
            }
        )

    return normalized


def _fallback_csv_report() -> Dict[str, Any]:
    """
    Create a minimal fallback report if CSV report generation fails.
    """
    return {
        "title": "CSV Report",
        "summary": "Automatic report generation failed for this CSV dataset.",
        "sections": [
            {
                "heading": "Report Generation Failed",
                "content": (
                    "InsightAI could not automatically generate a structured "
                    "report for this CSV file. "
                    "You can still explore the dataset using the CSV chat."
                ),
                "sources": [],
            }
        ],
        "key_figures": [],
        "main_findings": [],
        "risks": [],
        "recommendations": [],
        "charts": [],
        "timeline": [],
        "conclusion": (
            "The CSV file was uploaded successfully, but report generation failed."
        ),
    }


def generate_csv_report(
    *,
    filename: Optional[str],
    csv_schema: List[Dict[str, Any]],
    csv_profile: Dict[str, Any],
    csv_summary: Dict[str, Any],
    language: str = "de",
    base_meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Generate a report-ready payload from structured CSV metadata.

    This service is only for CSV files. It does not affect the existing
    PDF, DOCX or TXT report flow.
    """
    try:
        payload = generate_json(
            model="gpt-4o-mini",
            system_prompt=SYSTEM_CSV_REPORT,
            user_prompt=f"""
Requested report language: {language}

Filename:
{filename}

CSV schema:
{_compact_json(csv_schema[:MAX_SCHEMA_COLUMNS], max_chars=12000)}

CSV profile:
{_compact_json(csv_profile, max_chars=MAX_PROFILE_CHARS)}

CSV summary:
{_compact_json(csv_summary, max_chars=MAX_SUMMARY_CHARS)}
""".strip(),
            temperature=0.2,
            max_tokens=5000,
            trace_meta={**(base_meta or {}), "csv_stage": "csv_report"},
            trace_input={"task": "csv_report_generation"},
        )

    except Exception as exc:
        logger.warning(f"CSV report generation failed, using fallback report: {exc}")
        payload = {}

    if not isinstance(payload, dict):
        payload = {}

    if not payload:
        payload = _fallback_csv_report()

    return {
        "title": str(payload.get("title", "") or "CSV Report"),
        "summary": str(payload.get("summary", "") or ""),
        "sections": _normalize_sections(payload.get("sections")),
        "key_figures": _normalize_key_figures(payload.get("key_figures")),
        "main_findings": _normalize_findings(payload.get("main_findings")),
        "risks": _normalize_risks(payload.get("risks")),
        "recommendations": _normalize_recommendations(payload.get("recommendations")),
        "charts": validate_charts(payload.get("charts", [])),
        "timeline": payload.get("timeline", []) if isinstance(payload.get("timeline"), list) else [],
        "conclusion": str(payload.get("conclusion", "") or ""),
    }
