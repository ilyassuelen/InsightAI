import json
from typing import Iterator, Dict, List, Optional, Tuple

from backend.database.database import SessionLocal
from backend.models.document_chunk import DocumentChunk
from backend.parsers.pdf_parser import parse_document

import tiktoken
from docling.chunking import HybridChunker
from docling_core.transforms.chunker.tokenizer.openai import OpenAITokenizer

ENCODING = tiktoken.encoding_for_model("gpt-4o-mini")
MAX_TOKENS = 1000

# Initialize PDF chunker once
TOKENIZER = OpenAITokenizer(tokenizer=ENCODING, max_tokens=MAX_TOKENS)
PDF_CHUNKER = HybridChunker(tokenizer=TOKENIZER)


# ------------- CSV HELPERS -------------
def row_to_json_line(row: dict) -> str:
    """Convert a CSV row to compact JSON."""
    return json.dumps(row, ensure_ascii=False, separators=(",", ":"))


# ------------- TEXT CHUNKING -------------
def chunk_text_from_text(
        db,
        document_id: int,
        parse_id: Optional[int],
        text: str,
        max_tokens: int = MAX_TOKENS,
        section_title: Optional[str] = None,
        page_start: Optional[int] = None,
        page_end: Optional[int] = None,
        start_index: int = 0
) -> Tuple[int, int]:
    """Splits plain text into token chunks and stores them in DocumentChunk."""

    if not text or not text.strip():
        return 0, start_index

    tokens = ENCODING.encode(text)

    created = 0

    for i in range(0, len(tokens), max_tokens):
        token_chunk = tokens[i:i + max_tokens]

        db_chunk = DocumentChunk(
                document_id=document_id,
                parse_id=parse_id,
                chunk_index=start_index + created,
                token_count=len(token_chunk),
                text=ENCODING.decode(token_chunk),
                section_title=section_title,
                page_start=page_start,
                page_end=page_end,
                summary=None,
                keywords=None,
                topics=None,
        )
        db.add(db_chunk)
        created += 1

    next_index = start_index + created
    return created, next_index


# ------------- PDF CHUNKING -------------
def chunk_pdf(document_id: int, pdf_path: str, max_tokens: int = MAX_TOKENS) -> Tuple[Optional[int], int]:
    """
    Parses a PDF using Docling and create chunks using HybridChunker.
    """
    db = SessionLocal()
    parse_id: Optional[int] = None

    try:
        doc_parse, docling_doc = parse_document(document_id, pdf_path)
        parse_id = doc_parse.id

        total_chunks = 0
        global_index = 0

        doc_chunks = PDF_CHUNKER.chunk(dl_doc=docling_doc)

        for chunk in doc_chunks:
            # Get text enriched with context from headings
            enriched_text = PDF_CHUNKER.contextualize(chunk)

            # Extract section metadata from heading context
            section_title = None
            if hasattr(chunk.meta, "heading_context") and chunk.meta.heading_context:
                section_title = " > ".join(
                    h.title for h in chunk.meta.heading_context
                    if getattr(h, "title", None)
                )

            # Page start/end if available
            page_start = getattr(chunk.meta, "page_start", None)
            page_end = getattr(chunk.meta, "page_end", None)

            created, global_index = chunk_text_from_text(
                db=db,
                document_id=document_id,
                parse_id=parse_id,
                text=enriched_text,
                max_tokens=max_tokens,
                section_title=section_title,
                page_start=page_start,
                page_end=page_end,
                start_index=global_index
            )

            total_chunks += created

        db.commit()
        return parse_id, total_chunks

    finally:
        db.close()


# ------------- CSV STREAM CHUNKING -------------
def chunk_csv_stream(
    document_id: int,
    rows_iter: Iterator[Dict],
    max_tokens: int = 1200,
    overlap_rows: int = 5,
    section_title: Optional[str] = "CSV",
) -> int:
    """Stream CSV rows and create token-safe DocumentChunks."""
    db = SessionLocal()

    try:
        created = 0
        buffer_rows: List[Dict] = []
        buffer_token_count = 0

        def token_len(s: str) -> int:
            return len(ENCODING.encode(s))

        def flush(rows: List[Dict]):
            nonlocal created
            if not rows:
                return

            lines = ["CSV Records (JSON):"]
            lines.extend(row_to_json_line(r) for r in rows)

            text = "\n".join(lines)
            token_count = token_len(text)

            db.add(
                DocumentChunk(
                    document_id=document_id,
                    parse_id=None,
                    chunk_index=created,
                    token_count=token_count,
                    text=text,
                    section_title=section_title,
                    page_start=None,
                    page_end=None,
                    summary=None,
                    keywords=None,
                    topics=None,
                )
            )
            created += 1

        for row in rows_iter:
            line = row_to_json_line(row)
            line_tokens = token_len(line)

            # If a single row is too large, shorten it significantly so that we can still embed it.
            if line_tokens > max_tokens:
                toks = ENCODING.encode(line)
                truncated = ENCODING.decode(toks[: max_tokens - 50])
                row = {"__truncated_row__": truncated}
                line = row_to_json_line(row)
                line_tokens = token_len(line)

            if buffer_rows and (buffer_token_count + line_tokens) > max_tokens:
                flush(buffer_rows)

                buffer_rows = buffer_rows[-overlap_rows:] if overlap_rows > 0 else []

                buffer_token_count = 0
                for r in buffer_rows:
                    buffer_token_count += token_len(row_to_json_line(r))

            buffer_rows.append(row)
            buffer_token_count += line_tokens

        flush(buffer_rows)

        db.commit()
        return created
    finally:
        db.close()


# ------------- OLD CSV (optional to keep) -------------
def chunk_csv_rows(
        document_id: int,
        rows: List[Dict],
        rows_per_chunk: int = 200,
        overlap_rows: int = 20,
        section_title: Optional[str] = "CSV",
) -> int:
    """
    Row-based CSV chunking (legacy method).
    Prefer chunk_csv_stream for large files.
    """
    db = SessionLocal()
    try:
        if not rows:
            return 0

        headers = list(rows[0].keys())
        created = 0
        start = 0

        while start < len(rows):
            end = min(start + rows_per_chunk, len(rows))
            chunk_rows = rows[start:end]

            lines = []
            lines.append("Columns: " + ", ".join(headers))
            lines.append("Rows:")
            for r in chunk_rows:
                lines.append(" | ".join(f"{h}={str(r.get(h, ''))}" for h in headers))

            text = "\n".join(lines)
            token_count = len(ENCODING.encode(text))

            db.add(
                DocumentChunk(
                    document_id=document_id,
                    parse_id=None,
                    chunk_index=created,
                    token_count=token_count,
                    text=text,
                    section_title=section_title,
                    page_start=None,
                    page_end=None,
                    summary=None,
                    keywords=None,
                    topics=None,
                )
            )

            created += 1

            if end == len(rows):
                break

            start = max(0, end - overlap_rows)

        db.commit()
        return created
    finally:
        db.close()
