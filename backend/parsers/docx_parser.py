import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Optional

from docx import Document
from docx.oxml.ns import qn
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import Table
from docx.text.paragraph import Paragraph


@dataclass(frozen=True)
class _DocxBlock:
    kind: str
    text: str


def _iter_document_content(document) -> Iterator[Paragraph | Table]:
    """
    Yield top-level paragraphs and tables in their original document order.
    """
    if hasattr(document, "iter_inner_content"):
        yield from document.iter_inner_content()
        return

    for child in document.element.body.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, document._body)
        elif isinstance(child, CT_Tbl):
            yield Table(child, document._body)


def _paragraph_property(paragraph: Paragraph, property_name: str):
    """
    Resolve a paragraph property from the paragraph or its assigned style.
    """
    paragraph_properties = paragraph._p.pPr
    if paragraph_properties is not None:
        value = getattr(paragraph_properties, property_name, None)
        if value is not None:
            return value

    style = paragraph.style
    while style is not None:
        style_properties = style.element.pPr
        if style_properties is not None:
            value = getattr(style_properties, property_name, None)
            if value is not None:
                return value
        style = style.base_style

    return None


def _heading_level(paragraph: Paragraph) -> Optional[int]:
    """
    Return the semantic heading level defined by a built-in or outline style.
    """
    style_id = paragraph.style.style_id if paragraph.style else ""
    style_match = re.fullmatch(r"Heading([1-9])", style_id, flags=re.IGNORECASE)
    if style_match:
        return min(int(style_match.group(1)), 6)

    outline_level = _paragraph_property(paragraph, "outlineLvl")
    if outline_level is None:
        return None

    level = int(outline_level.val) + 1
    return level if 1 <= level <= 6 else None


def _number_format(paragraph: Paragraph, num_id: int, level: int) -> Optional[str]:
    """
    Resolve the Word numbering format for a list paragraph.
    """
    numbering = paragraph.part.numbering_part.element
    numberings = numbering.xpath(f'./w:num[@w:numId="{num_id}"]')
    if not numberings:
        return None

    abstract_reference = numberings[0].find(qn("w:abstractNumId"))
    if abstract_reference is None:
        return None

    abstract_id = abstract_reference.get(qn("w:val"))
    abstract_numberings = numbering.xpath(
        f'./w:abstractNum[@w:abstractNumId="{abstract_id}"]'
    )
    if not abstract_numberings:
        return None

    levels = abstract_numberings[0].findall(qn("w:lvl"))
    selected_level = next(
        (
            item
            for item in levels
            if int(item.get(qn("w:ilvl"), "0")) == level
        ),
        levels[0] if levels else None,
    )
    if selected_level is None:
        return None

    number_format = selected_level.find(qn("w:numFmt"))
    return number_format.get(qn("w:val")) if number_format is not None else None


def _list_properties(paragraph: Paragraph) -> Optional[tuple[bool, int]]:
    """
    Return whether a paragraph is ordered and its zero-based nesting level.
    """
    num_properties = _paragraph_property(paragraph, "numPr")
    if num_properties is None or num_properties.numId is None:
        return None

    num_id = int(num_properties.numId.val)
    level = (
        int(num_properties.ilvl.val)
        if num_properties.ilvl is not None
        else 0
    )

    style_id = paragraph.style.style_id if paragraph.style else ""
    style_level = re.search(r"(?:ListBullet|ListNumber)([2-9])$", style_id)
    if num_properties.ilvl is None and style_level:
        level = int(style_level.group(1)) - 1

    number_format = _number_format(paragraph, num_id, level)
    is_ordered = number_format != "bullet"
    return is_ordered, max(level, 0)


def _render_paragraph(paragraph: Paragraph) -> Optional[_DocxBlock]:
    text = paragraph.text.strip()
    if not text:
        return None

    heading_level = _heading_level(paragraph)
    if heading_level is not None:
        heading = " ".join(text.split())
        return _DocxBlock("heading", f"{'#' * heading_level} {heading}")

    list_properties = _list_properties(paragraph)
    if list_properties is not None:
        is_ordered, level = list_properties
        marker = "1." if is_ordered else "-"
        indentation = "    " * level
        continuation = f"\n{indentation}    "
        item_text = continuation.join(line.strip() for line in text.splitlines())
        return _DocxBlock("list", f"{indentation}{marker} {item_text}")

    return _DocxBlock("paragraph", text)


def _escape_table_cell(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    normalized = "<br>".join(lines)
    return normalized.replace("\\", "\\\\").replace("|", "\\|")


def _render_table(table: Table) -> Optional[_DocxBlock]:
    rows = [
        [_escape_table_cell(cell.text) for cell in row.cells]
        for row in table.rows
    ]
    if not rows:
        return None

    column_count = max(len(row) for row in rows)
    if column_count == 0:
        return None

    normalized_rows = [
        row + [""] * (column_count - len(row))
        for row in rows
    ]

    def render_row(row: list[str]) -> str:
        return f"| {' | '.join(row)} |"

    table_lines = [
        render_row(normalized_rows[0]),
        render_row(["---"] * column_count),
        *(render_row(row) for row in normalized_rows[1:]),
    ]
    return _DocxBlock("table", "\n".join(table_lines))


def _join_blocks(blocks: list[_DocxBlock]) -> str:
    parts = []

    for block in blocks:
        if parts and block.kind == "list" and parts[-1].kind == "list":
            previous = parts[-1]
            parts[-1] = _DocxBlock("list", f"{previous.text}\n{block.text}")
        else:
            parts.append(block)

    return "\n\n".join(block.text for block in parts)


def parse_docx(file_path: str) -> str:
    """
    Extract DOCX content as structure-preserving Markdown-like text.

    Headings retain their hierarchy, consecutive list items remain grouped,
    and tables preserve their rows and columns in the original document order.
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"DOCX file not found: {file_path}")

    document = Document(path)
    blocks = []

    for content in _iter_document_content(document):
        if isinstance(content, Paragraph):
            block = _render_paragraph(content)
        else:
            block = _render_table(content)

        if block is not None:
            blocks.append(block)

    return _join_blocks(blocks)
