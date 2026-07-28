from __future__ import annotations

import tests as _test_bootstrap  # noqa: F401  # configure isolated services first
import math
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import tiktoken

# The production tokenizer downloads its vocabulary on first use.  Tests use a
# deterministic byte-level tiktoken Encoding so the suite stays fully offline.
TEST_ENCODING = tiktoken.Encoding(
    name="insightai_test_bytes",
    pat_str=r"(?s).",
    mergeable_ranks={bytes([value]): value for value in range(256)},
    special_tokens={},
)

with patch("tiktoken.encoding_for_model", return_value=TEST_ENCODING):
    from backend.services.ingestion.chunking_service import (
        CHUNK_OVERLAP_TOKENS,
        ENCODING,
        MAX_TOKENS,
        chunk_pdf,
        chunk_text_from_text,
    )

from backend.database.database import SessionLocal
from backend.models.document_block import DocumentBlock
from backend.models.document_chunk import DocumentChunk
from backend.services.ingestion.document_block_service import create_blocks_from_chunks
from tests.support import create_document, create_user_workspace, reset_database


class TextChunkingTests(unittest.TestCase):
    def setUp(self) -> None:
        reset_database()
        self.user, self.workspace = create_user_workspace()
        self.document = create_document(self.workspace.id, self.user.id)

    def test_empty_text_creates_no_chunks(self) -> None:
        db = SessionLocal()
        try:
            created, next_index = chunk_text_from_text(db, self.document.id, None, "   ", start_index=7)
            db.flush()
            self.assertEqual((created, next_index), (0, 7))
            self.assertEqual(db.query(DocumentChunk).count(), 0)
        finally:
            db.close()

    def test_text_is_split_by_token_limit_with_metadata(self) -> None:
        text = "alpha " * 2200
        token_count = len(ENCODING.encode(text))
        max_tokens = 100
        overlap_tokens = 10

        db = SessionLocal()
        try:
            created, next_index = chunk_text_from_text(
                db,
                self.document.id,
                None,
                text,
                max_tokens=max_tokens,
                overlap_tokens=overlap_tokens,
                section_title="Overview",
                page_start=2,
                page_end=3,
                start_index=4,
            )
            db.commit()
            rows = db.query(DocumentChunk).order_by(DocumentChunk.chunk_index).all()

            expected_chunks = 1 + math.ceil(
                (token_count - max_tokens) / (max_tokens - overlap_tokens)
            )
            self.assertEqual(created, expected_chunks)
            self.assertEqual(next_index, 4 + created)
            self.assertEqual(rows[0].chunk_index, 4)
            self.assertEqual(rows[-1].chunk_index, next_index - 1)
            self.assertTrue(all(row.token_count <= max_tokens for row in rows))
            self.assertTrue(all(row.section_title == "Overview" for row in rows))
            self.assertTrue(all(row.page_start == 2 and row.page_end == 3 for row in rows))

            reconstructed = rows[0].text
            for previous, current in zip(rows, rows[1:]):
                previous_tokens = ENCODING.encode(previous.text)
                current_tokens = ENCODING.encode(current.text)
                self.assertEqual(
                    previous_tokens[-overlap_tokens:],
                    current_tokens[:overlap_tokens],
                )
                reconstructed += current.text[overlap_tokens:]

            self.assertEqual(reconstructed, text)
        finally:
            db.close()

    def test_unicode_survives_a_chunk_boundary_inside_multibyte_token(self) -> None:
        db = SessionLocal()
        try:
            chunk_text_from_text(
                db,
                self.document.id,
                None,
                "ä",
                max_tokens=1,
                overlap_tokens=0,
            )
            db.commit()
            reconstructed = "".join(
                row.text for row in db.query(DocumentChunk).order_by(DocumentChunk.chunk_index).all()
            )
        finally:
            db.close()
        self.assertEqual(reconstructed, "ä")

    def test_default_chunking_uses_800_tokens_with_80_token_overlap(self) -> None:
        text = "a" * 1700
        db = SessionLocal()
        try:
            created, _ = chunk_text_from_text(
                db,
                self.document.id,
                None,
                text,
            )
            db.commit()
            rows = db.query(DocumentChunk).order_by(DocumentChunk.chunk_index).all()
        finally:
            db.close()

        self.assertEqual(MAX_TOKENS, 800)
        self.assertEqual(CHUNK_OVERLAP_TOKENS, 80)
        self.assertEqual(created, 3)
        self.assertEqual([row.token_count for row in rows], [800, 800, 260])
        self.assertEqual(rows[0].text[-80:], rows[1].text[:80])
        self.assertEqual(rows[1].text[-80:], rows[2].text[:80])

    def test_invalid_overlap_is_rejected(self) -> None:
        db = SessionLocal()
        try:
            for overlap_tokens in (-1, 100):
                with self.subTest(overlap_tokens=overlap_tokens), self.assertRaises(ValueError):
                    chunk_text_from_text(
                        db,
                        self.document.id,
                        None,
                        "text",
                        max_tokens=100,
                        overlap_tokens=overlap_tokens,
                    )
        finally:
            db.close()

    def test_markdown_headings_create_section_boundaries_and_metadata(self) -> None:
        markdown = (
            "Introduction\n\n"
            "# Overview\n"
            "Overview content.\n\n"
            "## Details ##\n"
            "Detailed content.\n"
        )
        db = SessionLocal()
        try:
            created, _ = chunk_text_from_text(
                db,
                self.document.id,
                None,
                markdown,
                split_markdown_headings=True,
            )
            db.commit()
            rows = db.query(DocumentChunk).order_by(DocumentChunk.chunk_index).all()
        finally:
            db.close()

        self.assertEqual(created, 3)
        self.assertEqual(
            [row.section_title for row in rows],
            [None, "Overview", "Details"],
        )
        self.assertEqual([row.section_level for row in rows], [None, 1, 2])
        self.assertEqual("".join(row.text for row in rows), markdown)

    def test_markdown_overlap_stays_inside_heading_section(self) -> None:
        markdown = "# First\n" + ("a" * 900) + "\n## Second\nShort section."
        db = SessionLocal()
        try:
            created, _ = chunk_text_from_text(
                db,
                self.document.id,
                None,
                markdown,
                split_markdown_headings=True,
            )
            db.commit()
            rows = db.query(DocumentChunk).order_by(DocumentChunk.chunk_index).all()
        finally:
            db.close()

        self.assertEqual(created, 3)
        self.assertEqual(
            [row.section_title for row in rows],
            ["First", "First", "Second"],
        )
        self.assertEqual(rows[0].text[-80:], rows[1].text[:80])
        self.assertTrue(rows[2].text.startswith("## Second"))
        self.assertNotIn("a" * 80, rows[2].text)

    def test_markdown_setext_headings_ignore_fenced_code(self) -> None:
        markdown = (
            "# Real\n"
            "```markdown\n"
            "# Not a heading\n"
            "```not-a-closing-fence\n"
            "## Still not a heading\n"
            "```\n"
            "Setext title\n"
            "============\n"
            "Body\n"
        )
        db = SessionLocal()
        try:
            chunk_text_from_text(
                db,
                self.document.id,
                None,
                markdown,
                split_markdown_headings=True,
            )
            db.commit()
            rows = db.query(DocumentChunk).order_by(DocumentChunk.chunk_index).all()
        finally:
            db.close()

        self.assertEqual(
            [row.section_title for row in rows],
            ["Real", "Setext title"],
        )
        self.assertEqual([row.section_level for row in rows], [1, 1])
        self.assertIn("# Not a heading", rows[0].text)
        self.assertIn("## Still not a heading", rows[0].text)


class PdfChunkingOrchestrationTests(unittest.TestCase):
    def test_pdf_chunks_keep_heading_and_page_context(self) -> None:
        heading = SimpleNamespace(title="Chapter")
        meta = SimpleNamespace(heading_context=[heading], page_start=4, page_end=5)
        fake_chunk = SimpleNamespace(meta=meta)
        fake_chunker = MagicMock()
        fake_chunker.chunk.return_value = [fake_chunk]
        fake_chunker.contextualize.return_value = "Chapter\nEvidence"
        fake_db = MagicMock()

        with (
            patch("backend.services.ingestion.chunking_service.SessionLocal", return_value=fake_db),
            patch(
                "backend.services.ingestion.chunking_service.parse_document",
                return_value=(SimpleNamespace(id=91), object()),
            ),
            patch("backend.services.ingestion.chunking_service.PDF_CHUNKER", fake_chunker),
            patch(
                "backend.services.ingestion.chunking_service.chunk_text_from_text",
                return_value=(1, 1),
            ) as chunk_text,
        ):
            parse_id, total = chunk_pdf(
                17,
                "document.pdf",
                max_tokens=800,
                overlap_tokens=80,
            )

        self.assertEqual((parse_id, total), (91, 1))
        chunk_text.assert_called_once()
        kwargs = chunk_text.call_args.kwargs
        self.assertEqual(kwargs["text"], "Chapter\nEvidence")
        self.assertEqual(kwargs["max_tokens"], 800)
        self.assertEqual(kwargs["overlap_tokens"], 80)
        self.assertEqual(kwargs["section_title"], "Chapter")
        self.assertEqual(kwargs["page_start"], 4)
        self.assertEqual(kwargs["page_end"], 5)
        fake_db.commit.assert_called_once()
        fake_db.close.assert_called_once()

    @unittest.expectedFailure
    def test_pdf_chunks_support_current_docling_headings_metadata_shape(self) -> None:
        provenance = SimpleNamespace(page_no=6)
        doc_item = SimpleNamespace(prov=[provenance])
        meta = SimpleNamespace(headings=["Current Heading"], doc_items=[doc_item])
        fake_chunk = SimpleNamespace(meta=meta)
        fake_chunker = MagicMock()
        fake_chunker.chunk.return_value = [fake_chunk]
        fake_chunker.contextualize.return_value = "Current Heading\nEvidence"
        fake_db = MagicMock()
        with (
            patch("backend.services.ingestion.chunking_service.SessionLocal", return_value=fake_db),
            patch(
                "backend.services.ingestion.chunking_service.parse_document",
                return_value=(SimpleNamespace(id=1), object()),
            ),
            patch("backend.services.ingestion.chunking_service.PDF_CHUNKER", fake_chunker),
            patch(
                "backend.services.ingestion.chunking_service.chunk_text_from_text",
                return_value=(1, 1),
            ) as chunk_text,
        ):
            chunk_pdf(1, "document.pdf")
        kwargs = chunk_text.call_args.kwargs
        self.assertEqual(kwargs["section_title"], "Current Heading")
        self.assertEqual(kwargs["page_start"], 6)


class DocumentBlockTests(unittest.TestCase):
    def setUp(self) -> None:
        reset_database()
        self.user, self.workspace = create_user_workspace()
        self.document = create_document(self.workspace.id, self.user.id)

    def test_five_chunks_per_block_and_remainder(self) -> None:
        db = SessionLocal()
        try:
            for index in range(12):
                db.add(
                    DocumentChunk(
                        document_id=self.document.id,
                        parse_id=None,
                        chunk_index=index,
                        token_count=2,
                        text=f"chunk-{index}",
                    )
                )
            db.commit()
        finally:
            db.close()

        created = create_blocks_from_chunks(self.document.id, None)
        self.assertEqual(created, 3)

        db = SessionLocal()
        try:
            blocks = db.query(DocumentBlock).order_by(DocumentBlock.block_index).all()
            self.assertEqual(len(blocks), 3)
            self.assertEqual(blocks[0].content, "\n\n".join(f"chunk-{i}" for i in range(5)))
            self.assertEqual(blocks[2].content, "chunk-10\n\nchunk-11")
            self.assertEqual(blocks[0].block_type, "section")
            self.assertLessEqual(len(blocks[0].summary), 500)
        finally:
            db.close()

    def test_no_chunks_returns_zero(self) -> None:
        self.assertEqual(create_blocks_from_chunks(self.document.id, None), 0)


if __name__ == "__main__":
    unittest.main()
