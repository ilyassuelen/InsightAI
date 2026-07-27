from __future__ import annotations

import tests as _test_bootstrap  # noqa: F401  # configure isolated services first
import asyncio
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from backend.database.database import SessionLocal
from backend.models.document import Document
from backend.models.report import Report
from backend.routers import document as document_router
from tests.support import create_document, create_user_workspace, reset_database


class DocumentProcessingTests(unittest.TestCase):
    def setUp(self) -> None:
        reset_database()
        self.user, self.workspace = create_user_workspace()

    def _temp_file(self, suffix: str, content: str) -> Path:
        handle = tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False, encoding="utf-8")
        handle.write(content)
        handle.close()
        return Path(handle.name)

    def _document_status(self, document_id: int) -> str:
        db = SessionLocal()
        try:
            return db.query(Document).filter(Document.id == document_id).one().file_status
        finally:
            db.close()

    def test_txt_pipeline_runs_all_stages_and_persists_report(self) -> None:
        document = create_document(
            self.workspace.id,
            self.user.id,
            filename="notes.txt",
            file_type="text/plain",
            status="uploaded",
        )
        local_file = self._temp_file(".txt", "Grounded document content")
        chunk_text = MagicMock(return_value=(1, 1))
        chunk_pdf = MagicMock()
        create_blocks = MagicMock(return_value=1)
        structure_blocks = AsyncMock(return_value=[])
        generate_report = AsyncMock(return_value={"title": "Test", "sections": [], "conclusion": "Done"})
        delete_vectors = MagicMock()

        with (
            patch.object(document_router, "download_to_temp_file", return_value=local_file),
            patch.object(document_router, "get_chunking_services", return_value=(chunk_text, chunk_pdf, 1000)),
            patch.object(document_router, "get_block_services", return_value=(create_blocks, structure_blocks)),
            patch.object(document_router, "get_report_service", return_value=generate_report),
            patch.object(document_router, "get_vector_services", return_value=(MagicMock(), delete_vectors)),
            patch.object(document_router, "upsert_chunks_to_vectorstore") as upsert,
        ):
            asyncio.run(document_router.process_document_logic(document.id))

        self.assertEqual(self._document_status(document.id), "completed")
        self.assertFalse(local_file.exists())
        chunk_text.assert_called_once()
        chunk_pdf.assert_not_called()
        upsert.assert_called_once()
        create_blocks.assert_called_once_with(document_id=document.id, parse_id=None)
        structure_blocks.assert_awaited_once_with(document_id=document.id, parse_id=None)
        generate_report.assert_awaited_once()
        delete_vectors.assert_called_once_with(document.id)

        db = SessionLocal()
        try:
            report = db.query(Report).filter(Report.document_id == document.id).one()
            self.assertEqual(report.content["title"], "Test")
        finally:
            db.close()

    def test_csv_pipeline_skips_embeddings_and_uses_structured_report(self) -> None:
        document = create_document(
            self.workspace.id,
            self.user.id,
            filename="sales.csv",
            file_type="text/csv",
            status="uploaded",
        )
        local_file = self._temp_file(".csv", "region,revenue\nNorth,100\n")
        csv_metadata = {
            "schema": [{"name": "revenue", "type": "INTEGER"}],
            "profile": {"row_count": 1},
            "summary": {"row_count": 1},
        }
        chunk_text = MagicMock()
        chunk_pdf = MagicMock()
        create_blocks = MagicMock()
        structure_blocks = AsyncMock()
        text_report = AsyncMock()

        with (
            patch.object(document_router, "download_to_temp_file", return_value=local_file),
            patch.object(document_router, "get_chunking_services", return_value=(chunk_text, chunk_pdf, 1000)),
            patch.object(document_router, "get_block_services", return_value=(create_blocks, structure_blocks)),
            patch.object(document_router, "get_report_service", return_value=text_report),
            patch.object(document_router, "get_vector_services", return_value=(MagicMock(), MagicMock())),
            patch.object(
                document_router,
                "create_and_upload_parquet_from_csv_file",
                return_value="documents/sales.parquet",
            ),
            patch.object(document_router, "build_csv_profile_from_file", return_value=csv_metadata),
            patch.object(
                document_router,
                "generate_csv_report",
                return_value={"title": "CSV Report", "sections": [], "conclusion": "Done"},
            ) as csv_report,
            patch.object(document_router, "upsert_chunks_to_vectorstore") as upsert,
        ):
            asyncio.run(document_router.process_document_logic(document.id))

        self.assertEqual(self._document_status(document.id), "completed")
        self.assertFalse(local_file.exists())
        chunk_text.assert_not_called()
        chunk_pdf.assert_not_called()
        create_blocks.assert_not_called()
        structure_blocks.assert_not_awaited()
        text_report.assert_not_awaited()
        upsert.assert_not_called()
        csv_report.assert_called_once()

        db = SessionLocal()
        try:
            stored = db.query(Document).filter(Document.id == document.id).one()
            self.assertEqual(stored.parquet_key, "documents/sales.parquet")
            self.assertEqual(stored.csv_summary, {"row_count": 1})
        finally:
            db.close()

    def test_failure_sets_failed_status_and_deletes_temp_file(self) -> None:
        document = create_document(
            self.workspace.id,
            self.user.id,
            filename="broken.txt",
            file_type="text/plain",
            status="uploaded",
        )
        local_file = self._temp_file(".txt", "broken")

        with (
            patch.object(document_router, "download_to_temp_file", return_value=local_file),
            patch.object(document_router, "parse_txt", side_effect=RuntimeError("parse failed")),
            patch.object(document_router, "get_chunking_services", return_value=(MagicMock(), MagicMock(), 1000)),
            patch.object(document_router, "get_block_services", return_value=(MagicMock(), AsyncMock())),
            patch.object(document_router, "get_report_service", return_value=AsyncMock()),
            patch.object(document_router, "get_vector_services", return_value=(MagicMock(), MagicMock())),
        ):
            asyncio.run(document_router.process_document_logic(document.id))

        self.assertEqual(self._document_status(document.id), "failed")
        self.assertFalse(local_file.exists())


if __name__ == "__main__":
    unittest.main()
