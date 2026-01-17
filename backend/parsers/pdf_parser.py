from backend.models.document_parse import DocumentParse
from backend.database.database import SessionLocal
from docling.document_converter import DocumentConverter
from pathlib import Path
from fastapi import HTTPException

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

        converter = DocumentConverter()
        docling_doc = converter.convert(file_path).document

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
