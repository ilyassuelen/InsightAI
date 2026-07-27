from __future__ import annotations

import tests as _test_bootstrap  # noqa: F401  # configure isolated services first
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from backend.database.database import SessionLocal
from backend.models.document_chunk import DocumentChunk
from backend.services.vector import retrieval_service
from tests.support import create_document, create_user_workspace, reset_database


class HybridRetrievalTests(unittest.TestCase):
    def setUp(self) -> None:
        reset_database()
        self.user, self.workspace = create_user_workspace()
        self.text_document = create_document(
            self.workspace.id,
            self.user.id,
            filename="report.txt",
            file_type="text/plain",
        )
        self.csv_document = create_document(
            self.workspace.id,
            self.user.id,
            filename="data.csv",
            file_type="text/csv",
        )
        db = SessionLocal()
        try:
            db.add_all(
                [
                    DocumentChunk(
                        document_id=self.text_document.id,
                        chunk_index=0,
                        token_count=5,
                        text="Revenue increased strongly in 2025.",
                        section_title="Revenue",
                        page_start=2,
                    ),
                    DocumentChunk(
                        document_id=self.csv_document.id,
                        chunk_index=0,
                        token_count=3,
                        text="CSV revenue row",
                    ),
                ]
            )
            db.commit()
        finally:
            db.close()

    def test_hybrid_search_filters_csv_and_deduplicates_text(self) -> None:
        csv_point = SimpleNamespace(
            score=0.99,
            payload={"document_id": self.csv_document.id, "_text": "CSV revenue row"},
        )
        text_point = SimpleNamespace(
            score=0.88,
            payload={
                "document_id": self.text_document.id,
                "_text": "Revenue increased strongly in 2025.",
                "page_start": 2,
                "section_title": "Revenue",
            },
        )
        fake_client = MagicMock()
        fake_client.query_points.return_value = SimpleNamespace(points=[csv_point, text_point])

        with (
            patch.object(retrieval_service, "client", fake_client),
            patch.object(retrieval_service, "embed_texts", return_value=[[0.1, 0.2]]),
        ):
            results = retrieval_service.search_chunks(
                "Revenue increased",
                workspace_id=self.workspace.id,
                limit=8,
            )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["document_id"], self.text_document.id)
        self.assertEqual(results[0]["source"], "vector")
        self.assertEqual(results[0]["page"], 2)
        self.assertNotIn("CSV revenue row", [item["text"] for item in results])

        kwargs = fake_client.query_points.call_args.kwargs
        self.assertEqual(kwargs["limit"], 24)
        workspace_condition = kwargs["query_filter"].must[0]
        self.assertEqual(workspace_condition.key, "workspace_id")
        self.assertEqual(workspace_condition.match.value, self.workspace.id)

    def test_document_filter_is_added_to_vector_and_keyword_search(self) -> None:
        fake_client = MagicMock()
        fake_client.query_points.return_value = SimpleNamespace(points=[])

        with (
            patch.object(retrieval_service, "client", fake_client),
            patch.object(retrieval_service, "embed_texts", return_value=[[0.1]]),
        ):
            results = retrieval_service.search_chunks(
                "Revenue",
                workspace_id=self.workspace.id,
                document_id=self.text_document.id,
                limit=3,
            )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["source"], "keyword")
        conditions = fake_client.query_points.call_args.kwargs["query_filter"].must
        self.assertEqual([condition.key for condition in conditions], ["workspace_id", "document_id"])
        self.assertEqual(conditions[1].match.value, self.text_document.id)

    def test_short_query_words_do_not_trigger_keyword_search(self) -> None:
        fake_client = MagicMock()
        fake_client.query_points.return_value = SimpleNamespace(points=[])
        with (
            patch.object(retrieval_service, "client", fake_client),
            patch.object(retrieval_service, "embed_texts", return_value=[[0.1]]),
        ):
            results = retrieval_service.search_chunks("a to of", self.workspace.id)
        self.assertEqual(results, [])

    @unittest.expectedFailure
    def test_qdrant_document_payload_is_rechecked_against_workspace_in_sql(self) -> None:
        other_user, other_workspace = create_user_workspace(email="other@example.test")
        other_document = create_document(other_workspace.id, other_user.id, filename="other.txt")
        spoofed = SimpleNamespace(
            score=0.99,
            payload={
                "workspace_id": self.workspace.id,
                "document_id": other_document.id,
                "_text": "Other tenant secret",
            },
        )
        fake_client = MagicMock()
        fake_client.query_points.return_value = SimpleNamespace(points=[spoofed])
        with (
            patch.object(retrieval_service, "client", fake_client),
            patch.object(retrieval_service, "embed_texts", return_value=[[0.1]]),
        ):
            results = retrieval_service.search_chunks("secret", self.workspace.id)
        self.assertEqual(results, [])


if __name__ == "__main__":
    unittest.main()
