from fastapi import APIRouter, UploadFile, HTTPException
from pathlib import Path
from uuid import uuid4
from backend.database.database import SessionLocal
from backend.models.document import Document

router = APIRouter()

@router.get("/")
def get_documents():
    """
    Retrieve a list of all documents for a user.
    """
    return {"message": "List all documents"}

@router.post("/upload")
def upload_document(file: UploadFile):
    """
    Upload a new document, save it to the filesystem,
    and create a database entry.
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

        return {
            "message": "Document uploaded successfully",
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
    return {"message": f"Get document {id}"}

@router.patch("/{id}")
def update_document(id: int):
    """
    Update document metadata for a given ID.
    """
    return {"message": f"Update document {id}"}

@router.delete("/{id}")
def delete_document(id: int):
    """
    Delete a document by its ID.
    """
    return {"message": f"Delete document {id}"}