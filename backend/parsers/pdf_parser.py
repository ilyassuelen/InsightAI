from backend.models.document_parse import DocumentParse
from backend.database.database import SessionLocal

from docling.document_converter import DocumentConverter
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import PdfFormatOption

from pathlib import Path
from fastapi import HTTPException

import fitz
import logging

logger = logging.getLogger(__name__)


def pdf_contains_text(pdf_path: str, pages_to_check: int = 3) -> bool:
    """
    Check if the PDF contains extractable text.
    Only checks the first few pages for performance.
    """

    try:
        with fitz.open(pdf_path) as doc:

            for page_index in range(min(pages_to_check, len(doc))):
                page = doc.load_page(page_index)
                text = page.get_text().strip()

                if text:
                    return True

        return False

    except Exception:
        # If detection fails OCR is needed
        return False


def create_converter(pdf_path: str) -> DocumentConverter:
    """Create a Docling converter with smart OCR detection."""

    pipeline_options = PdfPipelineOptions()

    if pdf_contains_text(pdf_path):
        pipeline_options.do_ocr = False
        logger.info("PDF contains text → OCR disabled")
    else:
        pipeline_options.do_ocr = True
        logger.info("Scanned PDF detected → OCR enabled")

    # performance optimizations
    pipeline_options.do_table_structure = False
    pipeline_options.do_picture_description = False

    return DocumentConverter(
        format_options={
            "pdf": PdfFormatOption(
                pipeline_options=pipeline_options
            )
        }
    )


def parse_document(document_id: int, file_path: str):
    """
    Parse a document using Docling and store the result in the database.
    Returns BOTH the DB parse entry and the DoclingDocument.
    """
    db = SessionLocal()
    try:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File {file_path} does not exist")

        converter = create_converter(file_path)

        result = converter.convert(file_path)
        docling_doc = result.document

        # Extract full text (Markdown for structure)
        full_text = docling_doc.export_to_markdown()
        page_count = len(docling_doc.pages)
        used_ocr = getattr(docling_doc, "ocr_used", False)
        warnings = getattr(docling_doc, "warnings", None)

        # Database entry
        doc_parse = DocumentParse(
            document_id=document_id,
            success=True,
            full_text=full_text,
            page_count=page_count,
            used_ocr=used_ocr,
            warnings=str(warnings) if warnings else None
        )

        db.add(doc_parse)
        db.commit()
        db.refresh(doc_parse)

        return doc_parse, docling_doc

    except FileNotFoundError as e:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Document parsing failed: {str(e)}")

    finally:
        db.close()
