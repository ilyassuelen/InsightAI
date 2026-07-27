from __future__ import annotations

import csv
import io
import os
import zipfile
from dataclasses import dataclass
from pathlib import Path

from fastapi import UploadFile


READ_CHUNK_SIZE = 64 * 1024
MAX_DOCX_UNCOMPRESSED_BYTES = 100 * 1024 * 1024
MAX_DOCX_COMPRESSION_RATIO = 200

SUPPORTED_CONTENT_TYPES = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".txt": "text/plain",
    ".csv": "text/csv",
}


def _load_max_upload_size_bytes() -> int:
    raw_value = os.getenv("MAX_UPLOAD_SIZE_MB", "25")
    try:
        size_mb = int(raw_value)
    except ValueError as exc:
        raise RuntimeError("MAX_UPLOAD_SIZE_MB must be a positive integer") from exc

    if size_mb <= 0:
        raise RuntimeError("MAX_UPLOAD_SIZE_MB must be a positive integer")

    return size_mb * 1024 * 1024


MAX_UPLOAD_SIZE_BYTES = _load_max_upload_size_bytes()


class UploadValidationError(ValueError):
    def __init__(self, detail: str, *, status_code: int = 400):
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


@dataclass(frozen=True)
class ValidatedUpload:
    filename: str
    content_type: str


async def read_upload_with_limit(
    upload: UploadFile,
    *,
    max_size_bytes: int | None = None,
) -> bytes:
    limit = MAX_UPLOAD_SIZE_BYTES if max_size_bytes is None else max_size_bytes
    chunks: list[bytes] = []
    total_size = 0

    while chunk := await upload.read(READ_CHUNK_SIZE):
        total_size += len(chunk)
        if total_size > limit:
            raise UploadValidationError(
                f"File exceeds the maximum upload size of {limit // (1024 * 1024)} MB",
                status_code=413,
            )
        chunks.append(chunk)

    if total_size == 0:
        raise UploadValidationError("File is empty")

    return b"".join(chunks)


def validate_upload(filename: str | None, file_bytes: bytes) -> ValidatedUpload:
    safe_filename = _normalize_filename(filename)
    extension = Path(safe_filename).suffix.lower()

    if extension not in SUPPORTED_CONTENT_TYPES:
        supported = ", ".join(SUPPORTED_CONTENT_TYPES)
        raise UploadValidationError(f"Unsupported file format. Allowed formats: {supported}")

    if extension == ".pdf":
        _validate_pdf(file_bytes)
    elif extension == ".docx":
        _validate_docx(file_bytes)
    elif extension == ".csv":
        _validate_csv(file_bytes)
    else:
        _decode_text(file_bytes)

    return ValidatedUpload(
        filename=safe_filename,
        content_type=SUPPORTED_CONTENT_TYPES[extension],
    )


def _normalize_filename(filename: str | None) -> str:
    raw_filename = (filename or "").strip()
    if not raw_filename or "\x00" in raw_filename:
        raise UploadValidationError("A valid filename is required")

    safe_filename = raw_filename.replace("\\", "/").rsplit("/", 1)[-1].strip()
    if not safe_filename or len(safe_filename) > 255 or not Path(safe_filename).stem:
        raise UploadValidationError("A valid filename is required")

    return safe_filename


def _validate_pdf(file_bytes: bytes) -> None:
    if b"%PDF-" not in file_bytes[:1024]:
        raise UploadValidationError("File content does not match the .pdf format")

    try:
        import fitz

        with fitz.open(stream=file_bytes, filetype="pdf") as document:
            if document.needs_pass:
                raise UploadValidationError("Password-protected PDF files are not supported")
            if document.page_count < 1:
                raise UploadValidationError("PDF must contain at least one page")
    except UploadValidationError:
        raise
    except Exception as exc:
        raise UploadValidationError("File content is not a valid PDF") from exc


def _validate_docx(file_bytes: bytes) -> None:
    try:
        with zipfile.ZipFile(io.BytesIO(file_bytes)) as archive:
            members = archive.infolist()
            names = {member.filename for member in members}
            required = {"[Content_Types].xml", "word/document.xml"}

            if not required.issubset(names):
                raise UploadValidationError("File content does not match the .docx format")
            if any(member.flag_bits & 0x1 for member in members):
                raise UploadValidationError("Encrypted DOCX files are not supported")

            total_uncompressed = sum(member.file_size for member in members)
            total_compressed = sum(member.compress_size for member in members)
            if total_uncompressed > MAX_DOCX_UNCOMPRESSED_BYTES:
                raise UploadValidationError("DOCX expands beyond the supported size")
            if total_uncompressed > max(total_compressed, 1) * MAX_DOCX_COMPRESSION_RATIO:
                raise UploadValidationError("DOCX compression ratio is unsafe")

            content_types = archive.getinfo("[Content_Types].xml")
            document_xml = archive.getinfo("word/document.xml")
            if content_types.file_size > 1024 * 1024 or document_xml.file_size == 0:
                raise UploadValidationError("File content is not a valid DOCX document")

            content_type_xml = archive.read("[Content_Types].xml")
            if b"wordprocessingml.document.main+xml" not in content_type_xml:
                raise UploadValidationError("File content is not a valid DOCX document")
    except UploadValidationError:
        raise
    except Exception as exc:
        raise UploadValidationError("File content is not a valid DOCX document") from exc


def _decode_text(file_bytes: bytes) -> str:
    if b"\x00" in file_bytes:
        raise UploadValidationError("Text file contains binary data")

    try:
        text = file_bytes.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise UploadValidationError("Text files must use UTF-8 encoding") from exc

    if not text.strip():
        raise UploadValidationError("Text file is empty")

    disallowed_controls = sum(
        1
        for character in text
        if ord(character) < 32 and character not in "\n\r\t\f"
    )
    if disallowed_controls / len(text) > 0.01:
        raise UploadValidationError("Text file contains binary control characters")

    return text


def _validate_csv(file_bytes: bytes) -> None:
    text = _decode_text(file_bytes)
    sample = text[:64 * 1024]

    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        reader = csv.reader(io.StringIO(text), dialect)
        non_empty_rows = [
            row
            for _, row in zip(range(101), reader)
            if any(cell.strip() for cell in row)
        ]
    except csv.Error as exc:
        raise UploadValidationError("File content is not a valid CSV table") from exc

    if len(non_empty_rows) < 2 or len(non_empty_rows[0]) < 2:
        raise UploadValidationError(
            "CSV must contain at least two columns and one data row"
        )

    expected_columns = len(non_empty_rows[0])
    if not any(len(row) == expected_columns for row in non_empty_rows[1:]):
        raise UploadValidationError("CSV rows do not match the header structure")
