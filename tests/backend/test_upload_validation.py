from __future__ import annotations

import tests as _test_bootstrap  # noqa: F401  # configure isolated services first
import asyncio
import io
import unittest

import fitz
from docx import Document as WordDocument
from fastapi import UploadFile

from backend.services.storage.upload_validation import (
    SUPPORTED_CONTENT_TYPES,
    UploadValidationError,
    read_upload_with_limit,
    validate_upload,
)


def valid_pdf_bytes() -> bytes:
    document = fitz.open()
    try:
        page = document.new_page()
        page.insert_text((72, 72), "InsightAI upload validation")
        return document.tobytes()
    finally:
        document.close()


def valid_docx_bytes() -> bytes:
    document = WordDocument()
    document.add_paragraph("InsightAI upload validation")
    output = io.BytesIO()
    document.save(output)
    return output.getvalue()


class UploadValidationTests(unittest.TestCase):
    def test_supported_format_allowlist_is_explicit(self) -> None:
        self.assertEqual(
            SUPPORTED_CONTENT_TYPES,
            {
                ".pdf": "application/pdf",
                ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                ".txt": "text/plain",
                ".md": "text/markdown",
                ".csv": "text/csv",
            },
        )

    def test_text_markdown_and_csv_are_validated_and_normalized(self) -> None:
        cases = [
            ("notes.txt", b"Valid UTF-8 text", "text/plain"),
            ("README.MD", "# Valid Markdown".encode(), "text/markdown"),
            ("sales.csv", b"region,revenue\nNorth,100\n", "text/csv"),
        ]

        for filename, content, expected_type in cases:
            with self.subTest(filename=filename):
                validated = validate_upload(filename, content)
                self.assertEqual(validated.content_type, expected_type)

    def test_pdf_and_docx_require_valid_internal_structures(self) -> None:
        self.assertEqual(
            validate_upload("report.pdf", valid_pdf_bytes()).content_type,
            "application/pdf",
        )
        self.assertEqual(
            validate_upload("report.docx", valid_docx_bytes()).content_type,
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

        for filename, content in [
            ("fake.pdf", b"%PDF-not-a-real-document"),
            ("fake.docx", b"PK-not-a-real-document"),
        ]:
            with self.subTest(filename=filename):
                with self.assertRaises(UploadValidationError):
                    validate_upload(filename, content)

    def test_unsupported_extension_is_rejected(self) -> None:
        for filename in ["malware.exe", "legacy.doc", "payload.json", "no-extension"]:
            with self.subTest(filename=filename):
                with self.assertRaises(UploadValidationError):
                    validate_upload(filename, b"content")

    def test_binary_and_non_utf8_text_are_rejected(self) -> None:
        for content in [b"text\x00binary", b"\xff\xfeinvalid"]:
            with self.subTest(content=content):
                with self.assertRaises(UploadValidationError):
                    validate_upload("notes.txt", content)

    def test_csv_requires_tabular_content_and_a_data_row(self) -> None:
        for content in [b"plain text only", b"column_a,column_b\n"]:
            with self.subTest(content=content):
                with self.assertRaises(UploadValidationError):
                    validate_upload("data.csv", content)

    def test_filename_is_reduced_to_safe_basename(self) -> None:
        validated = validate_upload("../../folder\\notes.txt", b"Valid text")
        self.assertEqual(validated.filename, "notes.txt")

    def test_streamed_reader_rejects_empty_and_oversized_uploads(self) -> None:
        empty = UploadFile(file=io.BytesIO(b""), filename="empty.txt")
        with self.assertRaises(UploadValidationError) as empty_error:
            asyncio.run(read_upload_with_limit(empty, max_size_bytes=5))
        self.assertEqual(empty_error.exception.status_code, 400)

        oversized = UploadFile(file=io.BytesIO(b"123456"), filename="large.txt")
        with self.assertRaises(UploadValidationError) as size_error:
            asyncio.run(read_upload_with_limit(oversized, max_size_bytes=5))
        self.assertEqual(size_error.exception.status_code, 413)


if __name__ == "__main__":
    unittest.main()
