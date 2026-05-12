import json
import logging
import re
from typing import Any, Dict, List, Optional

from backend.services.csv.csv_query_service import run_sql_query
from backend.services.llm.llm_provider import generate_json

logger = logging.getLogger(__name__)

MAX_SCHEMA_COLUMNS = 120
MAX_SUMMARY_CHARS = 8000
MAX_RESULT_ROWS = 100
MAX_SAMPLE_ROWS = 5
MAX_SAMPLE_CHARS = 6000


SYSTEM_SQL_GENERATOR = """
You are a careful data analyst.

Your task is to create one safe SQL SELECT query for a CSV dataset.

Rules:
- Output JSON only.
- Use ONLY the provided schema, summary and sample rows.
- Do not invent columns.
- Table name is always: data
- Generate exactly one SELECT query.
- Do not use INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, COPY, ATTACH, DETACH, PRAGMA, INSTALL, LOAD.
- Always wrap column names in double quotes.
- Keep the query simple and robust.
- If the question cannot be answered with the available columns, return sql as null.
- Use the sample rows to understand how real values are stored, especially names, emails, phone numbers, dates and categories.

Return JSON schema:
{
  "sql": string|null,
  "reason": string
}
""".strip()


SYSTEM_ANSWER_GENERATOR = """
You are a helpful data analyst.

You receive:
1. The user's question
2. The executed SQL query
3. The query result

Answer the question based ONLY on the query result.

Rules:
- Do not invent facts or numbers.
- If the result is empty or insufficient, say that clearly.
- Do not mention implementation details.
- Write in the requested language.
- Output JSON only.

Return JSON schema:
{
  "answer": string,
  "confidence": "low" | "medium" | "high"
}
""".strip()


def _compact_json(data: Any, max_chars: int) -> str:
    """
    Convert data to readable JSON and truncate it if it gets too large.
    """
    text = json.dumps(data, ensure_ascii=False, indent=2, default=str)

    if len(text) <= max_chars:
        return text

    return text[:max_chars] + "\n...TRUNCATED..."


def _clean_sql(sql: Optional[str]) -> Optional[str]:
    """
    Clean an LLM-generated SQL string and remove markdown/code formatting.
    """
    if not sql:
        return None

    cleaned = sql.strip()

    cleaned = re.sub(r"```sql|```", "", cleaned, flags=re.IGNORECASE).strip()

    if cleaned.endswith(";"):
        cleaned = cleaned[:-1].strip()

    return cleaned or None


def build_csv_sql_prompt(
    *,
    user_question: str,
    csv_schema: List[Dict[str, Any]],
    csv_summary: Dict[str, Any],
    sample_rows: List[Dict[str, Any]],
    language: str,
) -> str:
    """
    Build the prompt used to generate a safe SQL query for a CSV question.
    """
    schema = csv_schema[:MAX_SCHEMA_COLUMNS]

    return f"""
Requested answer language: {language}

User question:
{user_question}

CSV schema:
{_compact_json(schema, max_chars=12000)}

CSV summary:
{_compact_json(csv_summary, max_chars=MAX_SUMMARY_CHARS)}

Sample rows:
{_compact_json(sample_rows, max_chars=MAX_SAMPLE_CHARS)}
""".strip()


def generate_sql_query(
    *,
    user_question: str,
    csv_schema: List[Dict[str, Any]],
    csv_summary: Dict[str, Any],
    sample_rows: List[Dict[str, Any]],
    language: str = "de",
    base_meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Ask the LLM to create one safe SELECT query based on the CSV metadata.
    """
    prompt = build_csv_sql_prompt(
        user_question=user_question,
        csv_schema=csv_schema,
        csv_summary=csv_summary,
        sample_rows=sample_rows,
        language=language,
    )

    data = generate_json(
        model="gpt-4o-mini",
        system_prompt=SYSTEM_SQL_GENERATOR,
        user_prompt=prompt,
        temperature=0.1,
        max_tokens=1200,
        trace_meta={**(base_meta or {}), "csv_stage": "sql_generation"},
        trace_input={"task": "csv_generate_sql"},
    )

    if not isinstance(data, dict):
        return {
            "sql": None,
            "reason": "The model did not return a valid SQL plan.",
        }

    return {
        "sql": _clean_sql(data.get("sql")),
        "reason": str(data.get("reason", "")),
    }


def generate_answer_from_sql_result(
    *,
    user_question: str,
    sql: str,
    sql_result: Dict[str, Any],
    language: str = "de",
    base_meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Ask the LLM to turn the SQL result into a user-friendly answer.
    """
    data = generate_json(
        model="gpt-4o-mini",
        system_prompt=SYSTEM_ANSWER_GENERATOR,
        user_prompt=f"""
Requested answer language: {language}

User question:
{user_question}

Executed SQL:
{sql}

Query result:
{_compact_json(sql_result, max_chars=12000)}
""".strip(),
        temperature=0.2,
        max_tokens=1600,
        trace_meta={**(base_meta or {}), "csv_stage": "answer_generation"},
        trace_input={"task": "csv_answer_from_sql_result"},
    )

    if not isinstance(data, dict):
        return {
            "answer": "",
            "confidence": "low",
        }

    return {
        "answer": str(data.get("answer", "")),
        "confidence": data.get("confidence", "medium"),
    }


def answer_csv_question(
    *,
    user_question: str,
    parquet_key: str,
    csv_schema: List[Dict[str, Any]],
    csv_summary: Dict[str, Any],
    language: str = "de",
    base_meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Answer a user question about a CSV document using SQL over Parquet.

    Flow:
    1. Load a few sample rows to help the LLM understand real values.
    2. Use schema, summary and sample rows to generate one safe SELECT query.
    3. Execute the query with DuckDB.
    4. Let the LLM explain the query result.
    """
    sample_rows = []

    try:
        preview_result = run_sql_query(
            parquet_key=parquet_key,
            sql=f"SELECT * FROM data LIMIT {MAX_SAMPLE_ROWS}",
            max_rows=MAX_SAMPLE_ROWS,
        )
        sample_rows = preview_result.get("rows", [])

    except Exception as exc:
        logger.warning(f"Could not load CSV sample rows for chat: {exc}")

    sql_plan = generate_sql_query(
        user_question=user_question,
        csv_schema=csv_schema,
        csv_summary=csv_summary,
        sample_rows=sample_rows,
        language=language,
        base_meta=base_meta,
    )

    sql = sql_plan.get("sql")

    if not sql:
        return {
            "answer": sql_plan.get(
                "reason",
                "The question could not be answered reliably with the available CSV columns.",
            ),
            "sql": None,
            "result": None,
            "confidence": "low",
        }

    sql_result = run_sql_query(
        parquet_key=parquet_key,
        sql=sql,
        max_rows=MAX_RESULT_ROWS,
    )

    answer_data = generate_answer_from_sql_result(
        user_question=user_question,
        sql=sql,
        sql_result=sql_result,
        language=language,
        base_meta=base_meta,
    )

    return {
        "answer": answer_data.get("answer", ""),
        "sql": sql,
        "result": sql_result,
        "confidence": answer_data.get("confidence", "medium"),
    }
