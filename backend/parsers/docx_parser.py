from docx import Document
from pathlib import Path


def parse_docx(file_path: str) -> str:
    """
    Reads a DOCX file and returns its full text content.
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"DOCX file not found: {file_path}")

    doc = Document(path)

    paragraphs = [
        para.text.strip()
        for para in doc.paragraphs
        if para.text and para.text.strip()
    ]

    return "\n\n".join(paragraphs)