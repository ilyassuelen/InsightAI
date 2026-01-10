from fastapi import APIRouter, UploadFile, HTTPException, Body
from pathlib import Path
from uuid import uuid4
import logging
from backend.database.database import SessionLocal
from backend.models.document import Document
from backend.parsers.pdf_parser import parse_document
from backend.services.chunking_service import chunk_text, MAX_TOKENS
from backend.services.document_block_service import create_blocks_from_chunks
from backend.services.structured_block_service import structure_blocks

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
async def upload_document(file: UploadFile):
    """
    Async upload and process a document:
    - store file
    - parse file (sync)
    - chunk text (sync)
    - create blocks (sync)
    - structure blocks with LLM (async and parallel)
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
            f.write(await file.read())

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

        # Parsing (sync)
        doc_parse = parse_document(document_id=document.id, file_path=str(filepath))
        document.file_status = "parsed"
        db.commit()

        if not doc_parse.full_text.strip():
            document.file_status = "parsed_empty"
            db.commit()
            return {
                "message": "Document parsed but contains no text",
                "document_id": document.id,
            }

        # Chunking (sync)
        num_chunks = chunk_text(
            document_id=document.id,
            parse_id=doc_parse.id,
            text=doc_parse.full_text,
            max_tokens=MAX_TOKENS,
        )

        document.file_status = "chunked"
        db.commit()
        logger.info(f"Created {num_chunks} chunks for document ID {document.id}")

        # Blocks
        num_blocks = create_blocks_from_chunks(
            document_id=document.id,
            parse_id=doc_parse.id,
        )
        logger.info(f"Created {num_blocks} blocks for document ID {document.id}")

        # LLM structuring (async and parallel)
        structured_blocks = await structure_blocks(
            document_id=document.id,
            parse_id=doc_parse.id,
        )

        document.file_status = "structured"
        db.commit()

        return {
            "message": "Document processed successfully",
            "document_id": document.id,
            "chunks_created": num_chunks,
            "blocks_created": num_blocks,
            "structured_blocks": structured_blocks,
        }

    except Exception as e:
        db.rollback()
        logger.exception(f"Upload failed: {e}")

        if filepath.exists():
            filepath.unlink()

        raise HTTPException(
            status_code=500,
            detail="Document upload failed",
        )

    finally:
        await file.close()
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