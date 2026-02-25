import json
from typing import Iterator, Dict, List, Optional

from backend.database.database import SessionLocal
from backend.models.document_chunk import DocumentChunk
from backend.parsers.pdf_parser import parse_document

import tiktoken
from docling.chunking import HybridChunker
from docling_core.transforms.chunker.tokenizer.openai import OpenAITokenizer

ENCODING = tiktoken.encoding_for_model("gpt-4o-mini")
MAX_TOKENS = 1000


# ------------- CSV HELPERS -------------
def row_to_json_line(row: dict) -> str:
    # Keep it compact but stable
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
) -> tuple[int, int]:
    """
    Splits a plain text into token chunks and stores them in DocumentChunk.
    Keeps section metadata if provided.
    """

    if not text or not text.strip():
        return 0, start_index

    tokens = ENCODING.encode(text)
    chunks = [
        tokens[i:i + max_tokens]
        for i in range(0, len(tokens), max_tokens)
    ]

    for i, token_chunk in enumerate(chunks):
        db.add(
            DocumentChunk(
                document_id=document_id,
                parse_id=parse_id,
                chunk_index=start_index + i,
                token_count=len(token_chunk),
                text=ENCODING.decode(token_chunk),
                section_title=section_title,
                page_start=page_start,
                page_end=page_end,
                summary=None,
                keywords=None,
                topics=None,
            )
        )

    next_index = start_index + len(chunks)
    return len(chunks), next_index


# ------------- PDF CHUNKING -------------
def chunk_pdf(document_id: int, pdf_path: str, max_tokens: int = MAX_TOKENS) -> tuple[int, int]:
    """
    Parses a PDF using Docling and chunks it using HybridChunker.
    """
    db = SessionLocal()

    try:
        doc_parse, docling_doc = parse_document(document_id, pdf_path)
        parse_id = doc_parse.id

        # Initialize HybridChunker
        tokenizer = OpenAITokenizer(tokenizer=ENCODING, max_tokens=max_tokens)
        chunker = HybridChunker(tokenizer=tokenizer)

        total_chunks = 0
        global_index = 0

        doc_chunks = chunker.chunk(dl_doc=docling_doc)

        for chunk in doc_chunks:
            # Get text enriched with context from headings
            enriched_text = chunker.contextualize(chunk)

            # Extract section metadata from heading context
            section_title = None
            if hasattr(chunk.meta, "heading_context") and chunk.meta.heading_context:
                section_title = " > ".join(
                    [h.title for h in chunk.meta.heading_context if getattr(h, "title", None)]
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
    max_tokens: int = 1200,           # safe for embeddings
    overlap_rows: int = 5,
    section_title: Optional[str] = "CSV",
) -> int:
    """
    Streams CSV rows and creates DocumentChunk entries with token-based chunking.
    - Memory safe (doesn't load full CSV)
    - Token safe (prevents embedding context overflow)
    """
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
            lines.extend([row_to_json_line(r) for r in rows])

            text = "\n".join(lines)
            tc = token_len(text)

            db.add(
                DocumentChunk(
                    document_id=document_id,
                    parse_id=None,
                    chunk_index=created,
                    token_count=tc,
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
                truncated = ENCODING.decode(toks[: max(0, max_tokens - 50)])
                row = {"__truncated_row__": truncated}
                line = row_to_json_line(row)
                line_tokens = token_len(line)

            # If adding this row would exceed token budget -> flush current buffer
            if buffer_rows and (buffer_token_count + line_tokens) > max_tokens:
                flush(buffer_rows)

                # overlap: keep last N rows
                if overlap_rows > 0:
                    buffer_rows = buffer_rows[-overlap_rows:]
                else:
                    buffer_rows = []

                # Recalculate buffer tokens
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
    Turns CSV rows into DocumentChunk entries so you can embed them.
    Chunking is row-based.
    For large CSVs, prefer chunk_csv_stream().
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

            chunk_text_str = "\n".join(lines)
            token_count = len(ENCODING.encode(chunk_text_str))

            db_chunk = DocumentChunk(
                document_id=document_id,
                parse_id=None,
                chunk_index=created,
                token_count=token_count,
                text=chunk_text_str,
                section_title=section_title,
                page_start=None,
                page_end=None,
                summary=None,
                keywords=None,
                topics=None,
            )
            db.add(db_chunk)
            created += 1

            if end == len(rows):
                break

            start = max(0, end - overlap_rows)

        db.commit()
        return created
    finally:
        db.close()
