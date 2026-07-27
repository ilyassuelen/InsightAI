from __future__ import annotations

import tests as _test_bootstrap  # noqa: F401  # configure isolated services first
import asyncio
import unittest
from unittest.mock import AsyncMock, patch

from backend.services.chat import chat_service
from tests.support import chat_response, create_document, create_user_workspace, reset_database


class ChatServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        reset_database()
        self.user, self.workspace = create_user_workspace()
        self.document = create_document(
            self.workspace.id,
            self.user.id,
            filename="annual-report.pdf",
            file_type="application/pdf",
        )

    def test_missing_workspace_is_rejected_before_retrieval(self) -> None:
        with patch.object(chat_service, "search_chunks") as search:
            answer = asyncio.run(chat_service.generate_chat_response(None, "Question", workspace_id=None))
        self.assertEqual(answer, "No workspace selected.")
        search.assert_not_called()

    def test_no_retrieval_results_returns_clear_message(self) -> None:
        with patch.object(chat_service, "search_chunks", return_value=[]):
            answer = asyncio.run(
                chat_service.generate_chat_response(
                    self.document.id,
                    "Question",
                    user_id=self.user.id,
                    workspace_id=self.workspace.id,
                )
            )
        self.assertIn("could not find relevant information", answer)

    def test_text_chat_is_grounded_and_sources_are_appended(self) -> None:
        chunks = [
            {
                "text": "Revenue was EUR 10 million.",
                "document_id": self.document.id,
                "page": 4,
                "section": "Revenue",
                "score": 0.9,
                "source": "vector",
            },
            {
                "text": "Profit was EUR 2 million.",
                "document_id": self.document.id,
                "page": None,
                "section": "Profit",
                "score": 0.8,
                "source": "vector",
            },
        ]
        fake_call = AsyncMock(return_value=chat_response("The revenue was EUR 10 million."))

        with (
            patch.object(chat_service, "search_chunks", return_value=chunks) as search,
            patch.object(chat_service, "_openai_call", fake_call),
            patch.object(chat_service, "langfuse", None),
        ):
            answer = asyncio.run(
                chat_service.generate_chat_response(
                    self.document.id,
                    "How much revenue?",
                    user_id=self.user.id,
                    workspace_id=self.workspace.id,
                )
            )

        search.assert_called_once_with(
            query="How much revenue?",
            workspace_id=self.workspace.id,
            document_id=self.document.id,
        )
        system_prompt, user_prompt = fake_call.call_args.args
        self.assertIn("Use ONLY the provided document context", system_prompt)
        self.assertIn("Revenue was EUR 10 million", user_prompt)
        self.assertIn("How much revenue?", user_prompt)
        self.assertIn("Sources", answer)
        self.assertIn("annual-report.pdf – page 4", answer)

    def test_csv_document_uses_structured_sql_path(self) -> None:
        csv_document = create_document(
            self.workspace.id,
            self.user.id,
            filename="sales.csv",
            file_type="text/csv",
            parquet_key="documents/sales.parquet",
        )
        with (
            patch.object(
                chat_service,
                "answer_csv_question",
                return_value={"answer": "There are 25 rows."},
            ) as csv_answer,
            patch.object(chat_service, "search_chunks") as search,
        ):
            answer = asyncio.run(
                chat_service.generate_chat_response(
                    csv_document.id,
                    "How many rows?",
                    user_id=self.user.id,
                    workspace_id=self.workspace.id,
                )
            )

        self.assertEqual(answer, "There are 25 rows.")
        csv_answer.assert_called_once()
        search.assert_not_called()

    def test_unprocessed_csv_returns_status_message(self) -> None:
        csv_document = create_document(
            self.workspace.id,
            self.user.id,
            filename="sales.csv",
            file_type="text/csv",
            parquet_key=None,
        )
        answer = asyncio.run(
            chat_service.generate_chat_response(
                csv_document.id,
                "How many rows?",
                workspace_id=self.workspace.id,
            )
        )
        self.assertIn("not been fully processed", answer)


if __name__ == "__main__":
    unittest.main()
