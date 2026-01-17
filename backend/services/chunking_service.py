from backend.database.database import SessionLocal
from backend.models.document_chunk import DocumentChunk
from backend.parsers.pdf_parser import parse_document

import tiktoken
from typing import Optional, List, Dict
from docling.chunking import HybridChunker
from docling_core.transforms.chunker.tokenizer.openai import OpenAITokenizer

ENCODING = tiktoken.encoding_for_model("gpt-4o-mini")
MAX_TOKENS = 1000
OVERLAP = 300

def chunk_text_from_text(
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
    db = SessionLocal()

    try:
        if not text or not text.strip():
            return 0, start_index

        tokens = ENCODING.encode(text)
        chunks = [
            tokens[i:i + max_tokens]
            for i in range(0, len(tokens), max_tokens)
        ]

        for i, token_chunk in enumerate(chunks):
            chunk_text_str = ENCODING.decode(token_chunk)
            db_chunk = DocumentChunk(
                document_id=document_id,
                parse_id=parse_id,
                chunk_index=start_index + i,
                token_count=len(token_chunk),
                text=chunk_text_str,
                section_title=section_title,
                page_start=page_start,
                page_end=page_end,
                summary=None,
                keywords=None,
                topics=None,
            )
            db.add(db_chunk)

        db.commit()
        next_index = start_index + len(chunks)
        return len(chunks), next_index

    finally:
        db.close()


def chunk_pdf(document_id: int, pdf_path: str, max_tokens: int = MAX_TOKENS, overlap: int = OVERLAP) -> tuple[int, int]:
    """
    Parses a PDF using Docling and chunks it using HybridChunker.
    """
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

        # Tokenize text, chunking with overlap and save in DB
        tokens = ENCODING.encode(enriched_text)
        start = 0

        while start < len(tokens):
            end = min(start + max_tokens, len(tokens))
            token_chunk = tokens[start:end]
            chunk_text_str = ENCODING.decode(token_chunk)

            created, global_index = chunk_text_from_text(
                document_id=document_id,
                parse_id=parse_id,
                text=chunk_text_str,
                max_tokens=max_tokens,
                section_title=section_title,
                page_start=page_start,
                page_end=page_end,
                start_index=global_index
            )

            total_chunks += created

            if end == len(tokens):
                break
            start = end - overlap

    return parse_id, total_chunks


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
