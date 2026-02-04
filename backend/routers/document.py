from fastapi import APIRouter, UploadFile, HTTPException, Body, BackgroundTasks, File, Form, Depends
from pathlib import Path
from uuid import uuid4
import logging

from backend.database.database import SessionLocal
from backend.models.document import Document
from backend.models.report import Report
from backend.models.document_chunk import DocumentChunk

from backend.parsers.csv_parser import iter_csv_rows
from backend.parsers.txt_parser import parse_txt
from backend.parsers.docx_parser import parse_docx

from backend.services.ingestion.chunking_service import (
    chunk_text_from_text,
    chunk_csv_stream,
    chunk_pdf,
    MAX_TOKENS
)
from backend.services.ingestion.document_block_service import create_blocks_from_chunks
from backend.services.ingestion.structured_block_service import structure_blocks
from backend.services.reporting.report_service import generate_report_for_document
from backend.services.ingestion.csv_block_service import create_blocks_from_csv_rows
from backend.services.vector.vector_store import upsert_document_chunks, delete_document_chunks

from backend.services.auth.deps import get_current_user
from backend.models.user import User
from backend.services.workspaces.workspace_service import WorkspaceService
from backend.models.workspace_member import WorkspaceMember

logger = logging.getLogger(__name__)
router = APIRouter()


# -------------------- ACCESS CONTROL --------------------
def user_has_access_to_document(db, user_id: int, document: Document) -> bool:
    membership = (
        db.query(WorkspaceMember)
        .filter(
            WorkspaceMember.user_id == user_id,
            WorkspaceMember.workspace_id == document.workspace_id,
        )
        .first()
    )
    return membership is not None


def user_workspace_ids(db, user_id: int) -> list[int]:
    rows = (
        db.query(WorkspaceMember.workspace_id)
        .filter(WorkspaceMember.user_id == user_id)
        .all()
    )
    return [wid for (wid,) in rows]


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

        # Clear existing chunks + vectorstore for this document
        db.query(DocumentChunk) \
            .filter(DocumentChunk.document_id == document.id) \
            .delete()
        db.commit()
        delete_document_chunks(document.id)

        document.file_status = "processing"
        db.commit()

        parse_id = None

        # ---------------- CSV ----------------
        if document.file_type in ("text/csv", "application/csv"):
            # Stream rows (memory safe)
            rows_iter = iter_csv_rows(document.storage_path)

            # Chunk stream into DocumentChunk (token safe)
            created_chunks = chunk_csv_stream(
                document_id=document.id,
                rows_iter=rows_iter,
                max_tokens=1200,
                overlap_rows=5,
                section_title="CSV",
            )

            if created_chunks == 0:
                document.file_status = "parsed_empty"
                db.commit()
                return

            # Upsert chunks to qdrant
            upsert_chunks_to_vectorstore(db, document.id)

            # Blocks
            rows_for_blocks = []
            for i, row in enumerate(iter_csv_rows(document.storage_path)):
                rows_for_blocks.append(row)
                if i >= 3000:  # safety cap for huge CSVs
                    break

            create_blocks_from_csv_rows(
                db=db,
                document_id=document.id,
                rows=rows_for_blocks,
            )

        # ---------------- TXT ----------------
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

            # Upsert chunks to qdrant
            upsert_chunks_to_vectorstore(db, document.id)

            # Blocks
            create_blocks_from_chunks(
                document_id=document.id,
                parse_id=None
            )
            logger.info(f"Block creation completed for document ID {document.id}")

        # ---------------- DOCX ----------------
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

            # Upsert chunks to qdrant
            upsert_chunks_to_vectorstore(db, document.id)

            # Blocks
            create_blocks_from_chunks(
                document_id=document.id,
                parse_id=None
            )
            logger.info(f"Block creation completed for document ID {document.id}")

        # ---------------- PDF ----------------
        else:
            # Chunk PDF with Docling + HybridChunker
            parse_id, total_chunks = chunk_pdf(
                document_id=document.id,
                pdf_path=document.storage_path,
            )

            # Upsert chunks to qdrant
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
def get_documents(workspace_id: int | None = None, current_user: User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        if workspace_id is None:
            ws = WorkspaceService.get_personal_workspace(db, current_user.id)
            workspace_id = ws.id
        else:
            WorkspaceService.require_member(db, workspace_id, current_user.id)

        documents = (
            db.query(Document)
            .filter(Document.workspace_id == workspace_id)
            .all()
        )

        return [
            {
                "id": document.id,
                "filename": document.filename,
                "file_type": document.file_type,
                "storage_path": document.storage_path,
                "file_status": document.file_status,
                "language": document.language,
                "created_at": document.created_at,
                "workspace_id": document.workspace_id
            }
            for document in documents
        ]

    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch documents")

    finally:
        db.close()


@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    language: str = Form("de"),
    workspace_id: int | None = Form(default=None),
    current_user: User = Depends(get_current_user),
):

    storage_dir = Path("backend/storage/documents")
    storage_dir.mkdir(parents=True, exist_ok=True)

    unique_filename = f"{uuid4()}_{file.filename}"
    filepath = storage_dir / unique_filename

    db = SessionLocal()
    try:
        with open(filepath, "wb") as f:
            f.write(await file.read())

        # Default: personal workspace
        if workspace_id is None:
            ws = WorkspaceService.get_personal_workspace(db, current_user.id)
            workspace_id = ws.id
        else:
            # Must be member of the selected workspace
            WorkspaceService.require_member(db, workspace_id, current_user.id)

        document = Document(
            filename=file.filename,
            file_type=file.content_type,
            storage_path=str(filepath),
            file_status="uploaded",
            language=(language or "de").strip(),
            workspace_id=workspace_id,
            uploaded_by_user_id=current_user.id,
        )

        db.add(document)
        db.commit()
        db.refresh(document)
        logger.info(f"Uploaded file '{file.filename}' as document ID {document.id}")

        background_tasks.add_task(process_document_logic, document.id)

        return {
            "message": "Document uploaded successfully and processing started",
            "document_id": document.id,
            "status": document.file_status,
            "language": document.language,
            "workspace_id": document.workspace_id
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
async def process_document_route(id: int, current_user: User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        document = db.query(Document).filter(Document.id == id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        if not user_has_access_to_document(db, current_user.id, document):
            raise HTTPException(status_code=403, detail="Forbidden")
    finally:
        db.close()

    await process_document_logic(id)
    return {"message": f"Processing started for document {id}"}


@router.get("/{id}")
def get_document(id: int, current_user: User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        document = db.query(Document).filter(Document.id == id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        if not user_has_access_to_document(db, current_user.id, document):
            raise HTTPException(status_code=403, detail="Forbidden")

        return {
            "id": document.id,
            "filename": document.filename,
            "file_type": document.file_type,
            "storage_path": document.storage_path,
            "file_status": document.file_status,
            "language": document.language,
            "created_at": document.created_at
        }
    finally:
        db.close()


@router.patch("/{id}")
def update_document(
        id: int, filename: str | None = Body(default=None),
        file_status: str | None = Body(default=None),
        current_user: User = Depends(get_current_user),
):
    db = SessionLocal()
    try:
        document = db.query(Document).filter(Document.id == id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        if not user_has_access_to_document(db, current_user.id, document):
            raise HTTPException(status_code=403, detail="Forbidden")

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
                "language": document.language,
                "created_at": document.created_at
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update document: {str(e)}")

    finally:
        db.close()


@router.delete("/{id}")
def delete_document(id: int, current_user: User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        document = db.query(Document).filter(Document.id == id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        if not user_has_access_to_document(db, current_user.id, document):
            raise HTTPException(status_code=403, detail="Forbidden")

        filepath = Path(document.storage_path)
        if filepath.exists():
            filepath.unlink()

        db.delete(document)
        db.commit()

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