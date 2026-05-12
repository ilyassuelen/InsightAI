from typing import Optional, Tuple

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
