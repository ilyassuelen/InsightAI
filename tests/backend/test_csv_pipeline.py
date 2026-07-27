from __future__ import annotations

import tests as _test_bootstrap  # noqa: F401  # configure isolated services first
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pyarrow.parquet as pq

from backend.services.csv import csv_chat_service, csv_query_service, csv_storage_service
from backend.services.csv.csv_profile_service import build_csv_profile_from_file


class CsvStorageTests(unittest.TestCase):
    def test_parquet_filename_is_derived_from_original(self) -> None:
        self.assertEqual(csv_storage_service.build_parquet_filename("folder/sales.2025.csv"), "sales.2025.parquet")
        self.assertEqual(csv_storage_service.build_parquet_filename("data"), "data.parquet")

    def test_csv_is_converted_to_readable_parquet(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "data.csv"
            path.write_text("name,value\nA,10\nB,20\n", encoding="utf-8")

            parquet_bytes = csv_storage_service.convert_csv_file_to_parquet_bytes(str(path))
            table = pq.read_table(io.BytesIO(parquet_bytes))

        self.assertEqual(table.column_names, ["name", "value"])
        self.assertEqual(table.num_rows, 2)
        self.assertEqual(table.column("value").to_pylist(), [10, 20])

    def test_empty_csv_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "empty.csv"
            path.write_text("name,value\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                csv_storage_service.convert_csv_file_to_parquet_bytes(str(path))

    @unittest.expectedFailure
    def test_parquet_and_profile_agree_for_malformed_rows(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "malformed.csv"
            path.write_text("a,b,c\n1,2\n3,4,5\n", encoding="utf-8")
            parquet = pq.read_table(io.BytesIO(csv_storage_service.convert_csv_file_to_parquet_bytes(str(path))))
            profile = build_csv_profile_from_file(str(path))
        self.assertEqual(parquet.num_rows, profile["summary"]["row_count"])
        self.assertEqual(parquet.column_names, [column["name"] for column in profile["schema"]])


class CsvProfilingTests(unittest.TestCase):
    def test_profile_contains_schema_quality_numeric_and_category_signals(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sales.csv"
            path.write_text(
                "date,region,revenue,note\n"
                "2025-01-01,North,100,ok\n"
                "2025-01-02,South,200,\n"
                "2025-01-03,North,300,ok\n",
                encoding="utf-8",
            )
            result = build_csv_profile_from_file(str(path), filename="sales.csv")

        self.assertEqual(result["summary"]["row_count"], 3)
        self.assertEqual(result["summary"]["column_count"], 4)
        self.assertIn(result["summary"]["table_type"], {"time_series_like_table", "mixed_business_table"})
        schema_by_name = {column["name"]: column for column in result["schema"]}
        self.assertTrue(schema_by_name["revenue"]["is_numeric"])

        numeric = {item["name"]: item for item in result["profile"]["numeric_profile"]}
        self.assertEqual(numeric["revenue"]["min"], 100)
        self.assertEqual(numeric["revenue"]["max"], 300)
        self.assertEqual(numeric["revenue"]["avg"], 200.0)

        categories = {item["name"]: item for item in result["profile"]["category_profile"]}
        self.assertEqual(categories["region"]["distinct_count"], 2)
        self.assertEqual(categories["region"]["top_values"][0], {"value": "North", "count": 2})

        quality = {item["name"]: item for item in result["profile"]["column_quality"]}
        self.assertEqual(quality["note"]["null_count"] + quality["note"]["empty_count"], 1)


class CsvQuerySafetyTests(unittest.TestCase):
    def test_only_select_queries_are_allowed(self) -> None:
        self.assertTrue(csv_query_service._is_safe_select_query(" SELECT * FROM data "))
        for sql in (
            "DELETE FROM data",
            "UPDATE data SET x=1",
            "DROP TABLE data",
            "SELECT * FROM data; DROP TABLE data",
            "PRAGMA version",
            "ATTACH 'other.db' AS other",
        ):
            with self.subTest(sql=sql):
                self.assertFalse(csv_query_service._is_safe_select_query(sql))

    @unittest.expectedFailure
    def test_safe_column_names_are_not_rejected_by_substring_matching(self) -> None:
        """Known defect: `created_at` contains the forbidden substring `create`."""

        self.assertTrue(csv_query_service._is_safe_select_query('SELECT "created_at" FROM data'))

    @unittest.expectedFailure
    def test_multiple_select_statements_are_rejected(self) -> None:
        self.assertFalse(csv_query_service._is_safe_select_query("SELECT 1; SELECT 2"))

    @unittest.expectedFailure
    def test_external_reader_functions_are_rejected(self) -> None:
        self.assertFalse(csv_query_service._is_safe_select_query("SELECT * FROM read_csv_auto('/etc/passwd')"))

    def test_query_executes_against_parquet_and_limits_rows(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            original = Path(directory) / "source.parquet"
            pd.DataFrame({"name": ["A", "B", "C"], "value": [1, 2, 3]}).to_parquet(original)
            downloaded = Path(directory) / "downloaded.parquet"
            downloaded.write_bytes(original.read_bytes())

            with patch.object(csv_query_service, "download_to_temp_file", return_value=downloaded):
                result = csv_query_service.run_sql_query(
                    parquet_key="documents/source.parquet",
                    sql='SELECT "name", "value" FROM data ORDER BY "value"',
                    max_rows=2,
                )

            self.assertFalse(downloaded.exists())

        self.assertEqual(result["columns"], ["name", "value"])
        self.assertEqual(result["rows"], [{"name": "A", "value": 1}, {"name": "B", "value": 2}])
        self.assertEqual(result["row_count_returned"], 2)

    def test_unsafe_query_is_rejected_before_download(self) -> None:
        with patch.object(csv_query_service, "download_to_temp_file") as download:
            with self.assertRaises(ValueError):
                csv_query_service.run_sql_query(parquet_key="x", sql="DELETE FROM data")
        download.assert_not_called()


class CsvChatTests(unittest.TestCase):
    def test_sql_markdown_is_cleaned(self) -> None:
        self.assertEqual(
            csv_chat_service._clean_sql('```sql\nSELECT "revenue" FROM data;\n```'),
            'SELECT "revenue" FROM data',
        )
        self.assertIsNone(csv_chat_service._clean_sql(None))

    def test_sql_generation_uses_schema_and_low_temperature(self) -> None:
        with patch.object(
            csv_chat_service,
            "generate_json",
            return_value={"sql": 'SELECT SUM("revenue") FROM data;', "reason": "aggregate"},
        ) as generate:
            result = csv_chat_service.generate_sql_query(
                user_question="Total revenue?",
                csv_schema=[{"name": "revenue", "type": "INTEGER"}],
                csv_summary={"row_count": 3},
                sample_rows=[{"revenue": 10}],
                language="en",
            )

        self.assertEqual(result["sql"], 'SELECT SUM("revenue") FROM data')
        kwargs = generate.call_args.kwargs
        self.assertEqual(kwargs["temperature"], 0.1)
        self.assertIn("Total revenue?", kwargs["user_prompt"])
        self.assertIn("revenue", kwargs["user_prompt"])

    def test_answer_flow_executes_preview_plan_query_and_explanation(self) -> None:
        preview = {"rows": [{"revenue": 10}]}
        query_result = {"rows": [{"total": 30}], "columns": ["total"]}
        with (
            patch.object(csv_chat_service, "run_sql_query", side_effect=[preview, query_result]) as run,
            patch.object(
                csv_chat_service,
                "generate_sql_query",
                return_value={"sql": 'SELECT SUM("revenue") AS total FROM data', "reason": ""},
            ) as plan,
            patch.object(
                csv_chat_service,
                "generate_answer_from_sql_result",
                return_value={"answer": "Total revenue is 30.", "confidence": "high"},
            ) as explain,
        ):
            result = csv_chat_service.answer_csv_question(
                user_question="Total?",
                parquet_key="data.parquet",
                csv_schema=[{"name": "revenue"}],
                csv_summary={"row_count": 3},
                language="en",
            )

        self.assertEqual(run.call_count, 2)
        self.assertEqual(plan.call_args.kwargs["sample_rows"], [{"revenue": 10}])
        self.assertEqual(explain.call_args.kwargs["sql_result"], query_result)
        self.assertEqual(result["answer"], "Total revenue is 30.")
        self.assertEqual(result["confidence"], "high")

    def test_unanswerable_question_does_not_execute_analysis_query(self) -> None:
        with (
            patch.object(csv_chat_service, "run_sql_query", return_value={"rows": []}) as run,
            patch.object(
                csv_chat_service,
                "generate_sql_query",
                return_value={"sql": None, "reason": "Missing column"},
            ),
        ):
            result = csv_chat_service.answer_csv_question(
                user_question="Unknown?",
                parquet_key="data.parquet",
                csv_schema=[],
                csv_summary={},
            )

        self.assertEqual(run.call_count, 1)
        self.assertEqual(result["answer"], "Missing column")
        self.assertEqual(result["confidence"], "low")


class CsvReportTests(unittest.TestCase):
    @unittest.expectedFailure
    def test_non_empty_llm_chart_payload_is_normalized_without_crashing(self) -> None:
        from backend.services.csv import csv_report_service

        payload = {
            "title": "CSV Report",
            "summary": "Summary",
            "sections": [],
            "key_figures": [],
            "main_findings": [],
            "risks": [],
            "recommendations": [],
            "charts": [
                {
                    "title": "Revenue",
                    "type": "bar",
                    "unit": "EUR",
                    "data": [{"label": "A", "value": 1}, {"label": "B", "value": 2}],
                }
            ],
            "timeline": [],
            "conclusion": "Done",
        }
        with patch.object(csv_report_service, "generate_json", return_value=payload):
            report = csv_report_service.generate_csv_report(
                filename="sales.csv",
                csv_schema=[],
                csv_profile={},
                csv_summary={},
            )
        self.assertEqual(report["charts"][0]["title"], "Revenue")


if __name__ == "__main__":
    unittest.main()
