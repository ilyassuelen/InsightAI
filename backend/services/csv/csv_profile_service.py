import json
import logging
import os
import tempfile
from typing import Any, Dict, List, Optional

import duckdb

logger = logging.getLogger(__name__)

MAX_SCHEMA_COLUMNS = 300
MAX_PREVIEW_ROWS = 10
MAX_NUMERIC_COLUMNS = 80
MAX_CATEGORY_COLUMNS = 40
MAX_TOP_VALUES = 8


def _safe_identifier(name: str) -> str:
    return '"' + str(name).replace('"', '""') + '"'


def _safe_value(value: Any) -> Any:
    if value is None:
        return None

    if isinstance(value, (str, int, float, bool)):
        return value

    try:
        if hasattr(value, "item"):
            return value.item()
    except Exception:
        pass

    return str(value)


def _rows_to_dicts(columns: List[str], rows: List[tuple]) -> List[Dict[str, Any]]:
    return [
        {columns[index]: _safe_value(value) for index, value in enumerate(row)}
        for row in rows
    ]


def _is_numeric_type(column_type: str) -> bool:
    normalized = column_type.upper()

    numeric_types = [
        "TINYINT",
        "SMALLINT",
        "INTEGER",
        "BIGINT",
        "HUGEINT",
        "UTINYINT",
        "USMALLINT",
        "UINTEGER",
        "UBIGINT",
        "FLOAT",
        "DOUBLE",
        "DECIMAL",
        "REAL",
    ]

    return any(normalized.startswith(item) for item in numeric_types)


def _is_text_type(column_type: str) -> bool:
    normalized = column_type.upper()
    return normalized.startswith("VARCHAR") or normalized.startswith("TEXT")


def _is_date_type(column_type: str) -> bool:
    normalized = column_type.upper()
    return (
        normalized.startswith("DATE")
        or normalized.startswith("TIMESTAMP")
        or normalized.startswith("TIME")
    )


def _open_csv_with_duckdb(csv_file_path: str) -> duckdb.DuckDBPyConnection:
    if not os.path.exists(csv_file_path):
        raise FileNotFoundError(f"CSV file not found: {csv_file_path}")

    conn = duckdb.connect(database=":memory:")

    conn.execute(
        """
        CREATE TABLE data AS
        SELECT *
        FROM read_csv_auto(
            ?,
            header = true,
            ignore_errors = true
        )
        """,
        [csv_file_path],
    )

    return conn


def _get_schema(conn: duckdb.DuckDBPyConnection) -> List[Dict[str, Any]]:
    rows = conn.execute("DESCRIBE data").fetchall()

    schema = []

    for index, row in enumerate(rows):
        column_name = str(row[0])
        column_type = str(row[1])

        schema.append(
            {
                "index": index,
                "name": column_name,
                "type": column_type,
                "is_numeric": _is_numeric_type(column_type),
                "is_text": _is_text_type(column_type),
                "is_date": _is_date_type(column_type),
            }
        )

    return schema[:MAX_SCHEMA_COLUMNS]


def _get_row_count(conn: duckdb.DuckDBPyConnection) -> int:
    return int(conn.execute("SELECT COUNT(*) FROM data").fetchone()[0])


def _get_preview_rows(conn: duckdb.DuckDBPyConnection) -> List[Dict[str, Any]]:
    result = conn.execute(f"SELECT * FROM data LIMIT {MAX_PREVIEW_ROWS}")
    columns = [desc[0] for desc in result.description]
    rows = result.fetchall()

    return _rows_to_dicts(columns, rows)


def _get_column_quality(
    conn: duckdb.DuckDBPyConnection,
    schema: List[Dict[str, Any]],
    row_count: int,
) -> List[Dict[str, Any]]:
    quality = []

    for column in schema:
        column_name = column["name"]
        quoted = _safe_identifier(column_name)

        try:
            null_count = conn.execute(
                f"SELECT COUNT(*) - COUNT({quoted}) FROM data"
            ).fetchone()[0]

            empty_count = 0

            if column.get("is_text"):
                empty_count = conn.execute(
                    f"""
                    SELECT COUNT(*)
                    FROM data
                    WHERE {quoted} IS NOT NULL
                    AND TRIM(CAST({quoted} AS VARCHAR)) = ''
                    """
                ).fetchone()[0]

            non_empty_count = row_count - int(null_count) - int(empty_count)

            quality.append(
                {
                    "name": column_name,
                    "type": column["type"],
                    "null_count": int(null_count),
                    "empty_count": int(empty_count),
                    "non_empty_count": int(non_empty_count),
                    "completeness_ratio": round(
                        non_empty_count / row_count, 4
                    )
                    if row_count > 0
                    else 0,
                }
            )

        except Exception as exc:
            logger.warning(f"Could not profile quality for column {column_name}: {exc}")

    return quality


def _get_numeric_profile(
    conn: duckdb.DuckDBPyConnection,
    schema: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    numeric_columns = [column for column in schema if column.get("is_numeric")]
    profile = []

    for column in numeric_columns[:MAX_NUMERIC_COLUMNS]:
        column_name = column["name"]
        quoted = _safe_identifier(column_name)

        try:
            row = conn.execute(
                f"""
                SELECT
                    COUNT({quoted}) AS non_null_count,
                    MIN({quoted}) AS min_value,
                    MAX({quoted}) AS max_value,
                    AVG({quoted}) AS avg_value,
                    STDDEV({quoted}) AS stddev_value
                FROM data
                """
            ).fetchone()

            profile.append(
                {
                    "name": column_name,
                    "type": column["type"],
                    "non_null_count": _safe_value(row[0]),
                    "min": _safe_value(row[1]),
                    "max": _safe_value(row[2]),
                    "avg": _safe_value(row[3]),
                    "stddev": _safe_value(row[4]),
                }
            )

        except Exception as exc:
            logger.warning(f"Could not profile numeric column {column_name}: {exc}")

    return profile


def _get_category_profile(
    conn: duckdb.DuckDBPyConnection,
    schema: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    text_columns = [column for column in schema if column.get("is_text")]
    profile = []

    for column in text_columns[:MAX_CATEGORY_COLUMNS]:
        column_name = column["name"]
        quoted = _safe_identifier(column_name)

        try:
            distinct_count = conn.execute(
                f"SELECT COUNT(DISTINCT {quoted}) FROM data"
            ).fetchone()[0]

            result = conn.execute(
                f"""
                SELECT CAST({quoted} AS VARCHAR) AS value, COUNT(*) AS count
                FROM data
                WHERE {quoted} IS NOT NULL
                AND TRIM(CAST({quoted} AS VARCHAR)) != ''
                GROUP BY {quoted}
                ORDER BY count DESC
                LIMIT {MAX_TOP_VALUES}
                """
            )

            rows = result.fetchall()

            profile.append(
                {
                    "name": column_name,
                    "type": column["type"],
                    "distinct_count": int(distinct_count),
                    "top_values": [
                        {
                            "value": _safe_value(row[0]),
                            "count": int(row[1]),
                        }
                        for row in rows
                    ],
                }
            )

        except Exception as exc:
            logger.warning(f"Could not profile category column {column_name}: {exc}")

    return profile


def _classify_table(
    schema: List[Dict[str, Any]],
    row_count: int,
    numeric_profile: List[Dict[str, Any]],
    category_profile: List[Dict[str, Any]],
) -> str:
    column_count = len(schema)
    numeric_count = len([column for column in schema if column.get("is_numeric")])
    text_count = len([column for column in schema if column.get("is_text")])
    date_count = len([column for column in schema if column.get("is_date")])

    if row_count == 0 or column_count == 0:
        return "empty_table"

    if column_count >= 50 and numeric_count / max(column_count, 1) >= 0.5:
        return "wide_numeric_table"

    if date_count > 0 and numeric_count > 0:
        return "time_series_like_table"

    if text_count > 0 and numeric_count > 0:
        return "mixed_business_table"

    if numeric_count == column_count:
        return "numeric_table"

    if text_count == column_count:
        return "categorical_table"

    return "general_table"


def _build_summary(
    *,
    filename: Optional[str],
    row_count: int,
    schema: List[Dict[str, Any]],
    table_type: str,
    numeric_profile: List[Dict[str, Any]],
    category_profile: List[Dict[str, Any]],
) -> Dict[str, Any]:
    numeric_columns = [column["name"] for column in schema if column.get("is_numeric")]
    text_columns = [column["name"] for column in schema if column.get("is_text")]
    date_columns = [column["name"] for column in schema if column.get("is_date")]

    return {
        "filename": filename,
        "row_count": row_count,
        "column_count": len(schema),
        "table_type": table_type,
        "numeric_column_count": len(numeric_columns),
        "text_column_count": len(text_columns),
        "date_column_count": len(date_columns),
        "numeric_columns": numeric_columns[:50],
        "text_columns": text_columns[:50],
        "date_columns": date_columns[:20],
        "strong_numeric_signals": numeric_profile[:10],
        "strong_category_signals": category_profile[:10],
        "processing_note": (
            "CSV has been profiled as structured data. "
            "Reports and questions should use structured analysis instead of raw row-based RAG."
        ),
    }


def build_csv_profile_from_file(
    csv_file_path: str,
    *,
    filename: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Build structured CSV metadata.

    Returns:
        {
            "schema": [...],
            "profile": {...},
            "summary": {...}
        }
    """
    conn: Optional[duckdb.DuckDBPyConnection] = None

    try:
        conn = _open_csv_with_duckdb(csv_file_path)

        schema = _get_schema(conn)
        row_count = _get_row_count(conn)
        preview_rows = _get_preview_rows(conn)

        column_quality = _get_column_quality(conn, schema, row_count)
        numeric_profile = _get_numeric_profile(conn, schema)
        category_profile = _get_category_profile(conn, schema)

        table_type = _classify_table(
            schema=schema,
            row_count=row_count,
            numeric_profile=numeric_profile,
            category_profile=category_profile,
        )

        profile = {
            "row_count": row_count,
            "column_count": len(schema),
            "table_type": table_type,
            "preview_rows": preview_rows,
            "column_quality": column_quality,
            "numeric_profile": numeric_profile,
            "category_profile": category_profile,
        }

        summary = _build_summary(
            filename=filename,
            row_count=row_count,
            schema=schema,
            table_type=table_type,
            numeric_profile=numeric_profile,
            category_profile=category_profile,
        )

        return {
            "schema": schema,
            "profile": profile,
            "summary": summary,
        }

    finally:
        if conn is not None:
            conn.close()


def build_csv_profile_from_text(
    csv_text: str,
    *,
    filename: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Build structured CSV metadata from CSV text.
    """
    if not csv_text or not csv_text.strip():
        raise ValueError("CSV text is empty")

    temp = tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".csv",
        encoding="utf-8",
        newline="",
        delete=False,
    )

    temp_path = temp.name

    try:
        temp.write(csv_text)
        temp.close()

        return build_csv_profile_from_file(temp_path, filename=filename)

    finally:
        try:
            os.remove(temp_path)
        except Exception:
            pass


def to_json_debug(data: Dict[str, Any]) -> str:
    """
    Helper for local debugging only.
    """
    return json.dumps(data, ensure_ascii=False, indent=2, default=str)
