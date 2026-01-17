from fastapi import APIRouter, UploadFile, HTTPException, Body, BackgroundTasks
from pathlib import Path
from uuid import uuid4
import logging

from backend.database.database import SessionLocal
from backend.models.document import Document
from backend.models.report import Report
from backend.parsers.csv_parser import parse_csv
from backend.parsers.txt_parser import parse_txt
from backend.parsers.docx_parser import parse_docx
from backend.services.chunking_service import chunk_text_from_text, chunk_csv_rows, chunk_pdf, MAX_TOKENS
from backend.services.document_block_service import create_blocks_from_chunks
from backend.services.structured_block_service import structure_blocks
from backend.services.report_service import generate_report_for_document
from backend.services.csv_block_service import create_blocks_from_csv_rows
from backend.models.document_chunk import DocumentChunk
from backend.services.vector_store import upsert_document_chunks, delete_document_chunks

logger = logging.getLogger(__name__)

router = APIRouter()


# -------------------- HELPER FUNCTION --------------------
def upsert_chunks_to_vectorstore(db, document_id: int):
    chunks = (
        db.query(DocumentChunk)
        .filter(DocumentChunk.document_id == document_id)
        .order_by(DocumentChunk.chunk_index)
        .all()
    )

    payload = []
    for chunk in chunks:
        payload.append({
            "id": chunk.id,
            "text": chunk.text,
            "metadata": {
                "chunk_index": chunk.chunk_index,
                "page_start": getattr(chunk, "page_start", None),
                "page_end": getattr(chunk, "page_end", None),
                "section_title": getattr(chunk, "section_title", None),
            },
            "keywords": (chunk.keywords or []) if hasattr(chunk, "keywords") else []
        })
    if payload:
        upsert_document_chunks(document_id=document_id, chunks=payload)


# -------------------- PROCESS LOGIC --------------------
async def process_document_logic(document_id: int):
    """
    Document processing logic:
    - parse
    - chunk
    - create blocks
    - structuring LLM
    """
    db = SessionLocal()
    document = None
    logger.info(f"Start processing document {document_id}")

    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            logger.error(f"Document {document_id} not found")
            return

        db.query(DocumentChunk) \
            .filter(DocumentChunk.document_id == document.id) \
            .delete()
        db.commit()
        delete_document_chunks(document.id)

        document.file_status = "processing"
        db.commit()

        # Parsing and block creation
        parse_id = None

        if document.file_type in ("text/csv", "application/csv"):
            rows = parse_csv(document.storage_path)

            if not rows:
                document.file_status = "parsed_empty"
                db.commit()
                return

            chunk_csv_rows(document_id=document.id, rows=rows)
            upsert_chunks_to_vectorstore(db, document.id)

            # Blocks
            create_blocks_from_csv_rows(
                db=db,
                document_id=document.id,
                rows=rows,
            )

        elif document.file_type in ("text/plain", "text/markdown"):
            full_text = parse_txt(document.storage_path)

            if not full_text.strip():
                document.file_status = "parsed_empty"
                db.commit()
                logger.info(f"Document {document_id} is empty")
                return

            # Chunking
            chunk_text_from_text(
                document_id=document.id,
                parse_id=None,
                text=full_text,
                max_tokens=MAX_TOKENS
            )
            logger.info(f"Chunking completed for document ID {document.id}")

            # Upsert chunks to Chroma
            upsert_chunks_to_vectorstore(db, document.id)

            # Blocks
            create_blocks_from_chunks(
                document_id=document.id,
                parse_id=None
            )
            logger.info(f"Block creation completed for document ID {document.id}")

        elif document.file_type in (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ):
            full_text = parse_docx(document.storage_path)

            if not full_text.strip():
                document.file_status = "parsed_empty"
                db.commit()
                logger.info(f"Document {document_id} is empty")
                return

            # Chunking
            chunk_text_from_text(
                document_id=document.id,
                parse_id=None,
                text=full_text,
                max_tokens=MAX_TOKENS
            )
            logger.info(f"Chunking completed for document ID {document.id}")

            # Upsert chunks to Chroma
            upsert_chunks_to_vectorstore(db, document.id)

            # Blocks
            create_blocks_from_chunks(
                document_id=document.id,
                parse_id=None
            )
            logger.info(f"Block creation completed for document ID {document.id}")

        else:
            # Chunk PDF with Docling + HybridChunker
            parse_id, total_chunks = chunk_pdf(
                document_id=document.id,
                pdf_path=document.storage_path,
            )

            # Upsert chunks to Chroma
            upsert_chunks_to_vectorstore(db, document.id)
            logger.info(f"Chunking completed for document ID {document.id} ({total_chunks} chunks)")

            create_blocks_from_chunks(
                document_id=document.id,
                parse_id=parse_id
            )
            logger.info(f"Block creation completed for document ID {document.id}")

        document.file_status = "reporting"
        db.commit()
        logger.info(f"Document {document.id} is now in reporting status")

        # LLM Structuring
        await structure_blocks(
            document_id=document.id,
            parse_id=parse_id
        )

        # Generate Report
        report_data = generate_report_for_document(db, document.id)
        report = Report(document_id=document.id, content=report_data)
        db.add(report)
        db.commit()
        db.refresh(report)
        logger.info(f"Report created for document {document.id}")

        document.file_status = "completed"
        db.commit()

    except Exception as e:
        db.rollback()
        if document:
            document.file_status = "report_failed"
            db.commit()
        logger.exception(f"Document {document_id} processing failed: {e}")
    finally:
        db.close()
        logger.info(f"Finished processing document {document_id}")


# -------------------- ROUTES --------------------
@router.get("/")
def get_documents():
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
async def upload_document(file: UploadFile, background_tasks: BackgroundTasks):
    storage_dir = Path("backend/storage/documents")
    storage_dir.mkdir(parents=True, exist_ok=True)

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

        background_tasks.add_task(process_document_logic, document.id)

        return {
            "message": "Document uploaded successfully and processing started",
            "document_id": document.id,
            "status": document.file_status
        }

    except Exception as e:
        db.rollback()
        logger.exception(f"Upload failed: {e}")
        if filepath.exists():
            filepath.unlink()
        raise HTTPException(status_code=500, detail="Document upload failed")
    finally:
        await file.close()
        db.close()


@router.post("/{id}/process")
async def process_document_route(id: int):
    await process_document_logic(id)
    return {"message": f"Processing started for document {id}"}


@router.get("/{id}")
def get_document(id: int):
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
    db = SessionLocal()
    try:
        document = db.query(Document).filter(Document.id == id).first()
        if not document:
            raise HTTPException(
                status_code=404,
                detail="Document not found"
            )

        filepath = Path(document.storage_path)
        if filepath.exists():
            filepath.unlink()

        db.delete(document)
        db.commit()

        # Delete from Chroma as well
        delete_document_chunks(id)

        return {"message": f"Document with ID: {id} deleted successfully"}

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete document: {str(e)}"
        )

    finally:
        db.close()