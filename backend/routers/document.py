from fastapi import APIRouter, UploadFile, HTTPException, Body
from pathlib import Path
from uuid import uuid4
from backend.database.database import SessionLocal
from backend.models.document import Document
from backend.parsers.pdf_parser import parse_document

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
    create a database entry, and automatically parse it.
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

        # Call parser
        try:
            parse_document(document_id=document.id, file_path=str(filepath))
        except HTTPException as e:
            return {
                "message": "Document uploaded, but parsing failed",
                "document_id": document.id,
                "parsing_error": e.detail
            }

        return {
            "message": "Document uploaded and parsed successfully",
            "document_id": document.id
        }

    except Exception:
        db.rollback()

        if filepath.exists():
            filepath.unlink()

        raise HTTPException(
            status_code=500,
            detail="Document upload failed"
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