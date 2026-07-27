from __future__ import annotations

import tests as _test_bootstrap  # noqa: F401  # configure isolated services first
import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from backend.services.reporting import insight_extractor, report_service
from backend.services.reporting.chart_validator import validate_charts
from backend.services.reporting.report_schema import ChartDataPoint, KeyFigure, ReportChart, ReportModel, ReportSection
from tests.support import create_document, create_user_workspace, reset_database


class ReportHelperTests(unittest.TestCase):
    def test_language_instruction(self) -> None:
        self.assertIn("German", report_service.language_instruction("de"))
        self.assertIn("English", report_service.language_instruction("en"))
        self.assertIn("French", report_service.language_instruction("French"))

    def test_key_figure_money_normalization(self) -> None:
        figure = KeyFigure(name="Revenue", value="1.200", unit="k€", context="2025")
        normalized = report_service.normalize_key_figure(figure)
        self.assertEqual(normalized.value, "1,20 Mio. €")
        self.assertEqual(normalized.unit, "")

        percentage = KeyFigure(name="Margin", value="12,5", unit="%")
        self.assertEqual(report_service.normalize_key_figure(percentage).value, "12,5")

    def test_priority_levels_are_normalized(self) -> None:
        self.assertEqual(insight_extractor.normalize_level("hoch"), "high")
        self.assertEqual(insight_extractor.normalize_level("gering"), "low")
        self.assertEqual(insight_extractor.normalize_level("unexpected"), "medium")

    def test_chart_validator_filters_and_limits_content(self) -> None:
        valid = ReportChart(
            title="A" * 140,
            type="bar",
            unit="EUR",
            data=[ChartDataPoint(label=f"Point {index}", value=index) for index in range(15)],
        )
        too_short = SimpleNamespace(title="Only one", type="bar", unit="", data=[SimpleNamespace(label="A", value=1)])
        charts = validate_charts([valid, too_short])
        self.assertEqual(len(charts), 1)
        self.assertEqual(len(charts[0].title), 120)
        self.assertEqual(len(charts[0].data), 12)

    def test_report_schema_requires_core_fields(self) -> None:
        report = ReportModel(
            title="Report",
            summary="Summary",
            sections=[ReportSection(heading="Overview", content="Content")],
            conclusion="Conclusion",
        )
        self.assertEqual(report.title, "Report")
        self.assertEqual(report.key_figures, [])


class ReportGenerationTests(unittest.TestCase):
    def setUp(self) -> None:
        reset_database()
        self.user, self.workspace = create_user_workspace()
        self.document = create_document(self.workspace.id, self.user.id, filename="report.pdf")

    def test_section_uses_fallback_sources_and_evidence_limit(self) -> None:
        hits = [
            {
                "id": f"chunk-{index}",
                "text": f"Evidence {index}",
                "metadata": {"page_start": index, "page_end": index, "section_title": "S"},
                "distance": 1.0 - index / 100,
            }
            for index in range(20)
        ]

        with (
            patch.object(report_service, "query_similar_chunks", return_value=hits),
            patch.object(
                report_service,
                "generate_json",
                return_value={"heading": "Executive Summary", "content": "Grounded"},
            ) as generate,
        ):
            section, figures = asyncio.run(
                report_service.generate_section(
                    "Executive Summary",
                    "Summarize",
                    self.document.id,
                    report_service.SYSTEM_SECTION,
                    report_service.SYSTEM_KEYFIGURES,
                    {},
                )
            )

        self.assertEqual(section.content, "Grounded")
        self.assertEqual(figures, [])
        self.assertLessEqual(len(section.sources), 15)
        self.assertLessEqual(len(generate.call_args.kwargs["user_prompt"]), 13000)

    @unittest.expectedFailure
    def test_model_cannot_return_sources_outside_retrieved_evidence(self) -> None:
        hits = [{"id": "real", "text": "Evidence", "metadata": {}, "distance": 0.9}]
        forged = [{"chunk_id": "fabricated", "page_start": None, "page_end": None, "section_title": None}]
        with (
            patch.object(report_service, "query_similar_chunks", return_value=hits),
            patch.object(
                report_service,
                "generate_json",
                return_value={"heading": "Executive Summary", "content": "Text", "sources": forged},
            ),
        ):
            section, _ = asyncio.run(
                report_service.generate_section(
                    "Executive Summary",
                    "Summarize",
                    self.document.id,
                    report_service.SYSTEM_SECTION,
                    report_service.SYSTEM_KEYFIGURES,
                    {},
                )
            )
        self.assertEqual([source["chunk_id"] for source in section.sources], ["real"])

    @unittest.expectedFailure
    def test_multi_query_results_are_sorted_by_qdrant_relevance(self) -> None:
        """Known defect: hits expose `distance`, while sorting reads `score`."""

        def query(*, query: str, **_: object):
            if query == "low":
                return [{"id": "low", "text": "LOW", "metadata": {}, "distance": 0.1}]
            return [{"id": "high", "text": "HIGH", "metadata": {}, "distance": 0.9}]

        captured: dict[str, str] = {}

        def generate_json(**kwargs):
            captured["prompt"] = kwargs["user_prompt"]
            return {"heading": "Executive Summary", "content": "ok"}

        variants = {**report_service.SECTION_QUERY_VARIANTS, "Executive Summary": ["low", "high"]}
        with (
            patch.object(report_service, "SECTION_QUERY_VARIANTS", variants),
            patch.object(report_service, "query_similar_chunks", side_effect=query),
            patch.object(report_service, "generate_json", side_effect=generate_json),
        ):
            asyncio.run(
                report_service.generate_section(
                    "Executive Summary",
                    "Summarize",
                    self.document.id,
                    report_service.SYSTEM_SECTION,
                    report_service.SYSTEM_KEYFIGURES,
                    {},
                )
            )

        self.assertLess(captured["prompt"].index("HIGH"), captured["prompt"].index("LOW"))


if __name__ == "__main__":
    unittest.main()
