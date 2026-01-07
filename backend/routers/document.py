from fastapi import APIRouter, UploadFile, HTTPException, Body
from pathlib import Path
from uuid import uuid4
from backend.database.database import SessionLocal
from backend.models.document import Document
from backend.parsers.pdf_parser import parse_document
from backend.services.chunking_service import chunk_text, MAX_TOKENS
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/")
def get_documents():
    """
    Retrieve a list of all documents in the database.
    """
    db = SessionLocal()
    try:
        documents = db.query(Document).all()
        return [
            {
                "id": document.id,
                "filename": document.filename,
                "file_type": document.file_type,
                "storage_path": document.storage_path,
                "file_status": document.file_status,
                "created_at": document.created_at
            }
            for document in documents
        ]

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch documents"
        )

    finally:
        db.close()

@router.post("/upload")
def upload_document(file: UploadFile):
    """
    Upload a new document, save it to the filesystem,
    create a database entry, parse it, and chunk the text.
    """
    # Create Location
    storage_dir = Path("backend/storage/documents")
    storage_dir.mkdir(parents=True, exist_ok=True)

    # Create unique file name
    unique_filename = f"{uuid4()}_{file.filename}"
    filepath = storage_dir / unique_filename

    db = SessionLocal()

    try:
        with open(filepath, "wb") as f:
            f.write(file.file.read())

        document = Document(
            filename=file.filename,
            file_type=file.content_type,
            storage_path=str(filepath),
            file_status="uploaded"
        )

        db.add(document)
        db.commit()
        db.refresh(document)
        logger.info(f"Uploaded file '{file.filename}' as document ID {document.id}")

        # Call parser
        try:
            doc_parse = parse_document(document_id=document.id, file_path=str(filepath))
            logger.info(f"Document ID {document.id} parsed successfully")
        except HTTPException as e:
            logger.warning(f"Parsing failed for document ID {document.id}: {e.detail}")
            return {
                "message": "Document uploaded, but parsing failed",
                "document_id": document.id,
                "parsing_error": e.detail
            }

        # Update status after parsing
        document.file_status = "parsed"
        db.commit()

        # Call chunking
        if not doc_parse.full_text.strip():
            logger.warning(f"Document ID {document.id} has empty text after parsing")
            num_chunks = 0
            document.file_status = "parsed_empty"
            db.commit()
        else:
            num_chunks = chunk_text(
                document_id=document.id,
                parse_id=doc_parse.id,
                text=doc_parse.full_text,
                max_tokens=MAX_TOKENS
            )
            document.file_status = "chunked"
            db.commit()
            logger.info(f"Created {num_chunks} chunks for document ID {document.id}")

        return {
            "message": "Document uploaded and parsed successfully",
            "document_id": document.id,
            "chunks_created": num_chunks
        }

    except Exception as e:
        db.rollback()

        if filepath.exists():
            filepath.unlink()

        logger.error(f"Failed to upload document '{file.filename}': {str(e)}")

        raise HTTPException(
            status_code=500,
            detail=f"Document upload failed: {str(e)}"
        )

    finally:
        file.file.close()
        db.close()

@router.get("/{id}")
def get_document(id: int):
    """
    Retrieve a document by its ID.
    """
    db = SessionLocal()
    try:
        document = db.query(Document).filter(Document.id == id).first()
        if not document:
            raise HTTPException(
                status_code=404,
                detail="Document not found"
            )

        return {
            "id": document.id,
            "filename": document.filename,
            "file_type": document.file_type,
            "storage_path": document.storage_path,
            "file_status": document.file_status,
            "created_at": document.created_at
        }

    finally:
        db.close()

@router.patch("/{id}")
def update_document(id: int, filename: str | None = Body(default=None), file_status: str | None = Body(default=None)):
    """
    Update document metadata (filename or file_status) for a given ID.
    """
    db = SessionLocal()
    try:
        document = db.query(Document).filter(Document.id == id).first()
        if not document:
            raise HTTPException(
                status_code=404,
                detail="Document not found"
            )

        if filename:
            document.filename = filename
        if file_status:
            document.file_status = file_status

        db.commit()
        db.refresh(document)

        return {
            "message": f"Document with ID: {id} updated successfully",
            "document": {
                "id": document.id,
                "filename": document.filename,
                "file_type": document.file_type,
                "storage_path": document.storage_path,
                "file_status": document.file_status,
                "created_at": document.created_at
            }
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update document: {str(e)}"
        )

    finally:
        db.close()

@router.delete("/{id}")
def delete_document(id: int):
    """
    Delete a document by its ID.
    """
    db = SessionLocal()
    try:
        document = db.query(Document).filter(Document.id == id).first()
        if not document:
            raise HTTPException(
                status_code=404,
                detail="Document not found"
            )

        # Delete file on file system, if it exists.
        filepath = Path(document.storage_path)
        if filepath.exists():
            filepath.unlink()

        # Delete Database entry
        db.delete(document)
        db.commit()

        return {"message": f"Document with ID: {id} deleted successfully"}

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete document: {str(e)}"
        )

    finally:
        db.close()