from backend.database.database import SessionLocal
from backend.models.document_chunk import DocumentChunk
from backend.parsers.pdf_parser import parse_document

import tiktoken
from typing import Optional
from docling.chunking import HybridChunker
from docling.document_converter import DocumentConverter
from docling_core.transforms.chunker.tokenizer.openai import OpenAITokenizer

ENCODING = tiktoken.encoding_for_model("gpt-4o-mini")
MAX_TOKENS = 1000
OVERLAP = 300

def chunk_text_from_text(
        document_id: int,
        parse_id: int,
        text: str,
        max_tokens: int = MAX_TOKENS,
        section_title: Optional[str] = None,
        page_start: Optional[int] = None,
        page_end: Optional[int] = None,
) -> int:
    """
    Splits a plain text into token chunks and stores them in DocumentChunk.
    Keeps section metadata if provided.
    """
    db = SessionLocal()

    try:
        if not text or not text.strip():
            return 0

        tokens = ENCODING.encode(text)
        chunks = [
            tokens[i:i + max_tokens]
            for i in range(0, len(tokens), max_tokens)
        ]

        for index, token_chunk in enumerate(chunks):
            chunk_text_str = ENCODING.decode(token_chunk)
            db_chunk = DocumentChunk(
                document_id=document_id,
                parse_id=parse_id,
                chunk_index=index,
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
        return len(chunks)

    finally:
        db.close()


def chunk_pdf(document_id: int, pdf_path: str, max_tokens: int = MAX_TOKENS, overlap: int = OVERLAP) -> int:
    """
    Parses a PDF using Docling and HybridChunker, then splits it into token chunks with overlap.
    Stores chunks in DB with section metadata.
    """
    # Parse PDF with Docling and store parse info in DB
    doc_parse = parse_document(document_id, pdf_path)
    parse_id = doc_parse.id

    # Convert PDF to DoclingDocument
    converter = DocumentConverter()
    docling_doc = converter.convert(pdf_path).document

    # Initialize HybridChunker
    tokenizer = OpenAITokenizer(tokenizer=ENCODING, max_tokens=max_tokens)
    chunker = HybridChunker(tokenizer=tokenizer)

    total_chunks = 0
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
        chunk_index = 0

        while start < len(tokens):
            end = min(start + max_tokens, len(tokens))
            token_chunk = tokens[start:end]
            chunk_text_str = ENCODING.decode(token_chunk)

            total_chunks += chunk_text_from_text(
                document_id=document_id,
                parse_id=parse_id,
                text=chunk_text_str,
                max_tokens=max_tokens,
                section_title=section_title,
                page_start=page_start,
                page_end=page_end,
            )

            if end == len(tokens):
                break
            start = end - overlap
            chunk_index += 1

    return total_chunks
