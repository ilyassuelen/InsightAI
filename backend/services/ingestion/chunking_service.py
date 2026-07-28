import re
from typing import Iterator, List, Optional, Tuple

from backend.database.database import SessionLocal
from backend.models.document_chunk import DocumentChunk
from backend.parsers.pdf_parser import parse_document

import tiktoken
from docling.chunking import HybridChunker
from docling_core.transforms.chunker.tokenizer.openai import OpenAITokenizer

ENCODING = tiktoken.encoding_for_model("gpt-4o-mini")
MAX_TOKENS = 800
CHUNK_OVERLAP_TOKENS = 80

MARKDOWN_ATX_HEADING = re.compile(
    r"^[ \t]{0,3}(#{1,6})(?:[ \t]+|$)(.*?)(?:\r?\n)?$"
)
MARKDOWN_SETEXT_HEADING = re.compile(
    r"^[ \t]{0,3}(=+|-+)[ \t]*(?:\r?\n)?$"
)
MARKDOWN_FENCE = re.compile(r"^[ \t]{0,3}(`{3,}|~{3,})")

# Initialize PDF chunker once
TOKENIZER = OpenAITokenizer(tokenizer=ENCODING, max_tokens=MAX_TOKENS)
PDF_CHUNKER = HybridChunker(tokenizer=TOKENIZER)


# ------------- TEXT CHUNKING -------------
def _markdown_lines_outside_fences(lines: List[str]) -> List[bool]:
    """
    Mark Markdown lines that are not contained in fenced code blocks.
    """
    outside_fence = []
    fence_character = None
    fence_length = 0

    for line in lines:
        fence_match = MARKDOWN_FENCE.match(line)

        if fence_character is None:
            if fence_match:
                fence = fence_match.group(1)
                fence_character = fence[0]
                fence_length = len(fence)
                outside_fence.append(False)
            else:
                outside_fence.append(True)
            continue

        outside_fence.append(False)
        if not fence_match:
            continue

        fence = fence_match.group(1)
        remainder = line[fence_match.end():].strip()
        if (
            fence[0] == fence_character
            and len(fence) >= fence_length
            and not remainder
        ):
            fence_character = None
            fence_length = 0

    return outside_fence


def _split_markdown_sections(
        text: str
) -> List[Tuple[Optional[str], Optional[int], str]]:
    """
    Split Markdown before ATX and Setext headings while preserving all text.
    """
    lines = text.splitlines(keepends=True)
    if not lines:
        return [(None, None, text)]

    outside_fence = _markdown_lines_outside_fences(lines)
    headings = {}

    for index, line in enumerate(lines):
        if not outside_fence[index]:
            continue

        atx_match = MARKDOWN_ATX_HEADING.match(line)
        if atx_match:
            raw_title = atx_match.group(2)
            title = re.sub(r"[ \t]+#+[ \t]*$", "", raw_title).strip()
            headings[index] = (title or None, len(atx_match.group(1)))
            continue

        if (
            line.strip()
            and index + 1 < len(lines)
            and outside_fence[index + 1]
        ):
            setext_match = MARKDOWN_SETEXT_HEADING.match(lines[index + 1])
            if setext_match:
                level = 1 if setext_match.group(1).startswith("=") else 2
                headings[index] = (line.strip() or None, level)

    if not headings:
        return [(None, None, text)]

    sections = []
    section_starts = sorted(headings)

    if section_starts[0] > 0:
        sections.append((None, None, "".join(lines[:section_starts[0]])))

    for position, start in enumerate(section_starts):
        end = (
            section_starts[position + 1]
            if position + 1 < len(section_starts)
            else len(lines)
        )
        title, level = headings[start]
        sections.append((title, level, "".join(lines[start:end])))

    return sections


def _split_tokens(
        tokens: List[int],
        max_tokens: int,
        overlap_tokens: int
) -> Iterator[List[int]]:
    """
    Split tokens into overlapping windows without breaking Unicode characters.
    """
    if max_tokens <= 0:
        raise ValueError("max_tokens must be greater than zero")

    if overlap_tokens < 0 or overlap_tokens >= max_tokens:
        raise ValueError("overlap_tokens must be between zero and max_tokens")

    if not tokens:
        return

    _, text_offsets = ENCODING.decode_with_offsets(tokens)
    total_tokens = len(tokens)
    start = 0

    while start < total_tokens:
        end = min(start + max_tokens, total_tokens)

        while (
            end > start
            and end < total_tokens
            and text_offsets[end] == text_offsets[end - 1]
        ):
            end -= 1

        if end == start:
            end = min(start + max_tokens, total_tokens)
            while (
                end < total_tokens
                and text_offsets[end] == text_offsets[end - 1]
            ):
                end += 1

        yield tokens[start:end]

        if end >= total_tokens:
            break

        next_start = max(start + 1, end - overlap_tokens)
        while (
            next_start < end
            and text_offsets[next_start] == text_offsets[next_start - 1]
        ):
            next_start += 1

        start = next_start


def chunk_text_from_text(
        db,
        document_id: int,
        parse_id: Optional[int],
        text: str,
        max_tokens: int = MAX_TOKENS,
        overlap_tokens: int = CHUNK_OVERLAP_TOKENS,
        section_title: Optional[str] = None,
        section_level: Optional[int] = None,
        page_start: Optional[int] = None,
        page_end: Optional[int] = None,
        start_index: int = 0,
        split_markdown_headings: bool = False
) -> Tuple[int, int]:
    """
    Split text into overlapping token chunks and store them in DocumentChunk.
    """

    if not text or not text.strip():
        return 0, start_index

    created = 0
    sections = [(section_title, section_level, text)]

    if split_markdown_headings:
        sections = _split_markdown_sections(text)

    for current_title, current_level, section_text in sections:
        if not section_text or not section_text.strip():
            continue

        tokens = ENCODING.encode(section_text)

        for token_chunk in _split_tokens(tokens, max_tokens, overlap_tokens):
            db_chunk = DocumentChunk(
                document_id=document_id,
                parse_id=parse_id,
                chunk_index=start_index + created,
                token_count=len(token_chunk),
                text=ENCODING.decode(token_chunk),
                section_title=current_title,
                section_level=current_level,
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
def chunk_pdf(
        document_id: int,
        pdf_path: str,
        max_tokens: int = MAX_TOKENS,
        overlap_tokens: int = CHUNK_OVERLAP_TOKENS
) -> Tuple[Optional[int], int]:
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
                overlap_tokens=overlap_tokens,
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
