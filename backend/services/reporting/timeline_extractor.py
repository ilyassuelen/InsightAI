import asyncio
from typing import Any, Dict, List

from backend.services.llm.llm_provider import generate_json
from backend.services.reporting.report_schema import TimelineEvent

SYSTEM_TIMELINE = """
You extract a simple timeline or development path from a drafted report.

Rules:
- Use only the provided report draft.
- Do not invent years, events or developments.
- Only return timeline events if the report contains clear dates, years, quarters, periods or sequential development.
- If no useful timeline exists, return an empty list.
- Do not mention technical processing details.
- Output JSON only.

Return JSON schema:
{
  "timeline": [
    {
      "label": string,
      "title": string,
      "description": string
    }
  ]
}
""".strip()


async def generate_timeline(
    assembled_report: str,
    lang_rule: str,
    base_meta: Dict[str, Any],
) -> List[TimelineEvent]:
    data = await asyncio.to_thread(
        lambda: generate_json(
            model="gpt-4o-mini",
            system_prompt=f"{SYSTEM_TIMELINE}\n\n{lang_rule}",
            user_prompt=f"Drafted report:\n\n{assembled_report}",
            temperature=0.2,
            trace_meta={**base_meta, "report_stage": "timeline_extraction"},
            trace_input={"task": "report_timeline_extraction"},
        )
    )

    if not isinstance(data, dict):
        return []

    return [
        TimelineEvent(**item)
        for item in data.get("timeline", [])
        if isinstance(item, dict)
    ][:8]
