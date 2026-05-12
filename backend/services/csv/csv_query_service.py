import logging
import os
from typing import Any, Dict, List, Optional

import duckdb

from backend.services.storage.r2_storage import download_to_temp_file

logger = logging.getLogger(__name__)

MAX_QUERY_ROWS = 100


def _safe_value(value: Any) -> Any:
    """
    Convert DuckDB values into JSON-friendly Python values.
    """
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
    """
    Convert SQL result rows into dictionaries.
    """
    return [
        {columns[index]: _safe_value(value) for index, value in enumerate(row)}
        for row in rows
    ]


def _is_safe_select_query(sql: str) -> bool:
    """
    Allow only SELECT queries for safety.
    """
    cleaned = (sql or "").strip().lower()

    if not cleaned.startswith("select"):
        return False

    forbidden_words = [
        "insert",
        "update",
        "delete",
        "drop",
        "alter",
        "create",
        "copy",
        "attach",
        "detach",
        "pragma",
        "install",
        "load",
    ]

    return not any(word in cleaned for word in forbidden_words)


def open_parquet_from_r2(parquet_key: str) -> tuple[duckdb.DuckDBPyConnection, str]:
    """
    Download a Parquet file from R2 and load it into DuckDB.

    Returns:
        DuckDB connection and local temp file path.
        The caller is responsible for closing the connection and deleting the temp file.
    """
    if not parquet_key:
        raise ValueError("parquet_key is required")

    local_file = download_to_temp_file(parquet_key)

    conn = duckdb.connect(database=":memory:")
    conn.execute(
        """
        CREATE TABLE data AS
        SELECT *
        FROM read_parquet(?)
        """,
        [str(local_file)],
    )

    return conn, str(local_file)


def run_sql_query(*, parquet_key: str, sql: str, max_rows: int = MAX_QUERY_ROWS) -> Dict[str, Any]:
    """
    Run a safe SELECT query against a Parquet-backed DuckDB table.

    The table name is always: data
    """
    if not _is_safe_select_query(sql):
        raise ValueError("Only safe SELECT queries are allowed")

    conn: Optional[duckdb.DuckDBPyConnection] = None
    local_file_path: Optional[str] = None

    try:
        conn, local_file_path = open_parquet_from_r2(parquet_key)

        result = conn.execute(sql)
        columns = [desc[0] for desc in result.description]
        rows = result.fetchmany(max_rows)

        return {
            "sql": sql,
            "columns": columns,
            "rows": _rows_to_dicts(columns, rows),
            "row_count_returned": len(rows),
            "max_rows": max_rows,
        }

    finally:
        if conn is not None:
            conn.close()

        if local_file_path and os.path.exists(local_file_path):
            try:
                os.remove(local_file_path)
            except Exception as exc:
                logger.warning(f"Could not delete temp parquet file: {exc}")


def get_table_preview(parquet_key: str, limit: int = 10) -> Dict[str, Any]:
    """
    Return the first rows of the CSV/Parquet table.
    """
    return run_sql_query(parquet_key=parquet_key, sql=f"SELECT * FROM data LIMIT {int(limit)}", max_rows=limit)


def get_table_row_count(parquet_key: str) -> Dict[str, Any]:
    """
    Return the total number of rows.
    """
    return run_sql_query(parquet_key=parquet_key, sql="SELECT COUNT(*) AS row_count FROM data", max_rows=1)
