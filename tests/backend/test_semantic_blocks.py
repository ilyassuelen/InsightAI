from __future__ import annotations

import tests as _test_bootstrap  # noqa: F401  # configure isolated services first

import asyncio
import unittest
from unittest.mock import AsyncMock, patch

from backend.database.database import SessionLocal
from backend.models.document_block import DocumentBlock
from backend.services.ingestion import structured_block_service
from tests.support import create_document, create_user_workspace, reset_database


class SemanticBlockTests(unittest.TestCase):
    def setUp(self) -> None:
        reset_database()
        self.user, self.workspace = create_user_workspace()
        self.document = create_document(self.workspace.id, self.user.id)

    def _blocks(self, count: int) -> list[DocumentBlock]:
        return [
            DocumentBlock(
                id=index + 1,
                document_id=self.document.id,
                parse_id=None,
                block_index=index,
                block_type="section",
                content=f"Block content {index}",
                summary="initial",
            )
            for index in range(count)
        ]

    def test_batch_maps_valid_items_and_falls_back_for_missing_block(self) -> None:
        blocks = self._blocks(2)
        response = {
            "items": [
                {
                    "block_id": blocks[0].id,
                    "section_type": "paragraph",
                    "title": "Overview",
                    "summary": "A" * 600,
                }
            ]
        }
        with patch.object(structured_block_service, "generate_json", return_value=response) as generate:
            result = asyncio.run(structured_block_service.structure_block_batch(blocks))

        self.assertEqual(result[blocks[0].id]["section_type"], "paragraph")
        self.assertEqual(result[blocks[0].id]["title"], "Overview")
        self.assertEqual(len(result[blocks[0].id]["summary"]), 500)
        self.assertEqual(result[blocks[1].id]["section_type"], "other")
        self.assertIn("Block content 1", result[blocks[1].id]["summary"])
        self.assertEqual(generate.call_args.kwargs["temperature"], 0.0)

    def test_batch_provider_failure_returns_content_fallbacks(self) -> None:
        blocks = self._blocks(2)
        with patch.object(structured_block_service, "generate_json", side_effect=RuntimeError("offline")):
            result = asyncio.run(structured_block_service.structure_block_batch(blocks))
        self.assertEqual(set(result), {1, 2})
        self.assertTrue(all(item["section_type"] == "other" for item in result.values()))

    def test_structure_blocks_persists_semantic_metadata(self) -> None:
        db = SessionLocal()
        try:
            for block in self._blocks(3):
                block.id = None
                db.add(block)
            db.commit()
            stored = db.query(DocumentBlock).order_by(DocumentBlock.block_index).all()
            ids = [block.id for block in stored]
        finally:
            db.close()

        mapped = {
            block_id: {
                "section_type": "subsection",
                "title": f"Title {index}",
                "summary": f"Summary {index}",
            }
            for index, block_id in enumerate(ids)
        }
        with patch.object(structured_block_service, "structure_block_batch", new=AsyncMock(return_value=mapped)):
            result = asyncio.run(structured_block_service.structure_blocks(self.document.id, None))

        self.assertEqual(len(result), 3)
        db = SessionLocal()
        try:
            stored = db.query(DocumentBlock).order_by(DocumentBlock.block_index).all()
            self.assertTrue(all(block.semantic_label == "subsection" for block in stored))
            self.assertEqual(stored[0].title, "Title 0")
            self.assertEqual(stored[2].summary, "Summary 2")
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()

