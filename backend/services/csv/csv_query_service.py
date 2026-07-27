import json
import logging
import os
from typing import Any, Dict, Iterator, List, Optional

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


def _iter_ast_nodes(value: Any) -> Iterator[Dict[str, Any]]:
    """
    Yield every object contained in a serialized DuckDB SQL AST.
    """
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _iter_ast_nodes(child)
    elif isinstance(value, list):
        for child in value:
            yield from _iter_ast_nodes(child)


def _is_safe_select_query(sql: str) -> bool:
    """
    Allow one parsed SELECT statement that only reads from data or its CTEs.
    """
    if not isinstance(sql, str) or not sql.strip():
        return False

    conn: Optional[duckdb.DuckDBPyConnection] = None

    try:
        conn = duckdb.connect(database=":memory:")
        serialized = conn.execute(
            "SELECT json_serialize_sql(?)",
            [sql],
        ).fetchone()
        ast = json.loads(serialized[0])
        referenced_tables = {
            table_name.casefold()
            for table_name in conn.get_table_names(sql)
        }
    except Exception:
        return False
    finally:
        if conn is not None:
            conn.close()

    if ast.get("error"):
        return False

    statements = ast.get("statements")
    if not isinstance(statements, list) or len(statements) != 1:
        return False

    root_node = statements[0].get("node")
    if not isinstance(root_node, dict):
        return False

    if root_node.get("type") not in {"SELECT_NODE", "SET_OPERATION_NODE"}:
        return False

    if not referenced_tables.issubset({"data"}):
        return False

    nodes = list(_iter_ast_nodes(root_node))

    for node in nodes:
        node_type = node.get("type")

        if node_type == "TABLE_FUNCTION":
            return False

        if node_type != "BASE_TABLE":
            continue

        if node.get("catalog_name") or node.get("schema_name"):
            return False

    return True


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
