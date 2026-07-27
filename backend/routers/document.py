from fastapi import APIRouter, UploadFile, HTTPException, Body, BackgroundTasks, File, Form, Depends
import logging
from pydantic import BaseModel

from backend.database.database import SessionLocal
from backend.models.document import Document
from backend.models.report import Report
from backend.models.document_chunk import DocumentChunk
from backend.models.document_parse import DocumentParse
from backend.models.document_block import DocumentBlock

from backend.parsers.txt_parser import parse_txt
from backend.parsers.docx_parser import parse_docx

from backend.services.csv.csv_storage_service import create_and_upload_parquet_from_csv_file
from backend.services.csv.csv_profile_service import build_csv_profile_from_file
from backend.services.csv.csv_report_service import generate_csv_report

from backend.services.storage.r2_storage import upload_file, download_to_temp_file, delete_file, copy_file
from backend.services.storage.upload_validation import (
    UploadValidationError,
    read_upload_with_limit,
    validate_upload,
)

from backend.services.auth.deps import get_current_user
from backend.models.user import User
from backend.services.workspaces.workspace_service import WorkspaceService
from backend.models.workspace_member import WorkspaceMember

logger = logging.getLogger(__name__)
router = APIRouter()


class DocumentTransferIn(BaseModel):
    target_workspace_id: int
    mode: str = "copy"  # "copy" or "move"


# -------------------- LAZY IMPORT HELPERS --------------------
def get_chunking_services():
    from backend.services.ingestion.chunking_service import (
        chunk_text_from_text,
        chunk_pdf,
        MAX_TOKENS,
    )
    return chunk_text_from_text, chunk_pdf, MAX_TOKENS


def get_block_services():
    from backend.services.ingestion.document_block_service import create_blocks_from_chunks
    from backend.services.ingestion.structured_block_service import structure_blocks
    return create_blocks_from_chunks, structure_blocks


def get_vector_services():
    from backend.services.vector.vector_store import upsert_document_chunks, delete_document_chunks
    return upsert_document_chunks, delete_document_chunks


def get_report_service():
    from backend.services.reporting.report_service import generate_report_for_document
    return generate_report_for_document


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


# -------------------- HELPER FUNCTIONS --------------------
def set_status(db, document, status: str):
    """Updates the processing status of a document and persists it to the database."""
    document.file_status = status
    db.add(document)
    db.commit()
    db.refresh(document)


def is_csv_file(document: Document) -> bool:
    """Checks whether the uploaded document is a CSV file."""
    return document.file_type in ("text/csv", "application/csv") or document.filename.lower().endswith(".csv")


def upsert_chunks_to_vectorstore(db, document):
    """
    Loads text-based document chunks from the database and inserts them into Qdrant.
    Used for PDF, TXT and DOCX files after chunking and embedding.
    CSV files use a separate structured processing flow.
    """
    upsert_document_chunks, _ = get_vector_services()

    chunks = (
        db.query(DocumentChunk)
        .filter(DocumentChunk.document_id == document.id)
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
            "keywords": (chunk.keywords or []) if hasattr(chunk, "keywords") else [],
        })

    if payload:
        upsert_document_chunks(document_id=document.id, workspace_id=document.workspace_id, chunks=payload)


# -------------------- PROCESS LOGIC --------------------
async def process_document_logic(document_id: int):
    """
    Main background processing pipeline for uploaded documents.

    PDF, TXT and DOCX files follow the text-based pipeline:
    1. Parse the document
    2. Split the content into chunks
    3. Generate embeddings and store chunks in Qdrant
    4. Create document blocks
    5. Structure blocks using an LLM
    6. Generate an AI report summarizing the document

    CSV files follow a separate data pipeline:
    1. Convert CSV to Parquet
    2. Build schema, profile and summary metadata
    3. Store the structured CSV metadata on the document
    4. Generate a CSV report from the structured metadata
    """

    chunk_text_from_text, chunk_pdf, MAX_TOKENS = get_chunking_services()
    create_blocks_from_chunks, structure_blocks = get_block_services()
    generate_report_for_document = get_report_service()
    upsert_document_chunks, delete_document_chunks = get_vector_services()

    db = SessionLocal()
    document = None
    local_file = None

    logger.info(f"Start processing document {document_id}")

    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            logger.error(f"Document {document_id} not found")
            return

        local_file = download_to_temp_file(document.storage_path)

        db.query(DocumentChunk).filter(DocumentChunk.document_id == document.id).delete()
        db.commit()

        delete_document_chunks(document.id)

        db.query(Report).filter(Report.document_id == document.id).delete()
        db.commit()

        set_status(db, document, "processing")

        parse_id = None

        if is_csv_file(document):
            set_status(db, document, "parsing")

            logger.info(f"Structured CSV processing started for document {document.id}")

            parquet_key = create_and_upload_parquet_from_csv_file(
                csv_file_path=str(local_file),
                original_filename=document.filename,
            )

            csv_metadata = build_csv_profile_from_file(
                csv_file_path=str(local_file),
                filename=document.filename,
            )

            document.parquet_key = parquet_key
            document.csv_schema = csv_metadata.get("schema")
            document.csv_profile = csv_metadata.get("profile")
            document.csv_summary = csv_metadata.get("summary")

            db.add(document)
            db.commit()
            db.refresh(document)

            set_status(db, document, "report_generating")

            csv_report_data = generate_csv_report(
                filename=document.filename,
                csv_schema=document.csv_schema or [],
                csv_profile=document.csv_profile or {},
                csv_summary=document.csv_summary or {},
                language=document.language or "de",
                base_meta={
                    "document_id": document.id,
                    "workspace_id": document.workspace_id,
                    "filename": document.filename,
                    "report_mode": "csv_structured",
                },
            )

            report = Report(document_id=document.id, content=csv_report_data)
            db.add(report)
            db.commit()
            db.refresh(report)

            set_status(db, document, "completed")

            logger.info(f"Structured CSV processing and report completed for document {document.id}")

            return

        elif document.file_type in ("text/plain", "text/markdown"):
            set_status(db, document, "parsing")

            full_text = parse_txt(local_file)

            if not full_text.strip():
                set_status(db, document, "parsed_empty")
                return

            set_status(db, document, "chunking")

            chunk_text_from_text(
                db=db,
                document_id=document.id,
                parse_id=None,
                text=full_text,
                max_tokens=MAX_TOKENS,
            )
            db.commit()

            set_status(db, document, "embedding")
            upsert_chunks_to_vectorstore(db, document)

            set_status(db, document, "blocking")

            create_blocks_from_chunks(
                document_id=document.id,
                parse_id=None,
            )

        elif document.file_type in (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ):
            set_status(db, document, "parsing")

            full_text = parse_docx(local_file)

            if not full_text.strip():
                set_status(db, document, "parsed_empty")
                return

            set_status(db, document, "chunking")

            chunk_text_from_text(
                db=db,
                document_id=document.id,
                parse_id=None,
                text=full_text,
                max_tokens=MAX_TOKENS,
            )
            db.commit()

            set_status(db, document, "embedding")
            upsert_chunks_to_vectorstore(db, document)

            set_status(db, document, "blocking")

            create_blocks_from_chunks(
                document_id=document.id,
                parse_id=None,
            )

        else:
            set_status(db, document, "parsing")

            parse_id, total_chunks = chunk_pdf(
                document_id=document.id,
                pdf_path=local_file,
            )

            set_status(db, document, "embedding")
            upsert_chunks_to_vectorstore(db, document)

            logger.info(f"Embedding completed for document ID {document.id} ({total_chunks} chunks)")

            set_status(db, document, "blocking")

            create_blocks_from_chunks(
                document_id=document.id,
                parse_id=parse_id,
            )

        set_status(db, document, "structuring")

        await structure_blocks(
            document_id=document.id,
            parse_id=parse_id,
        )

        set_status(db, document, "report_generating")

        report_data = await generate_report_for_document(db, document_id)

        report = Report(document_id=document.id, content=report_data)
        db.add(report)
        db.commit()
        db.refresh(report)

        set_status(db, document, "completed")

        logger.info(f"Report created for document {document.id}")

    except Exception as e:
        db.rollback()

        if document:
            set_status(db, document, "failed")

        logger.exception(f"Document {document_id} processing failed: {e}")

    finally:
        if local_file and local_file.exists():
            local_file.unlink()

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
                "file_status": document.file_status,
                "language": document.language,
                "created_at": document.created_at,
                "workspace_id": document.workspace_id,
            }
            for document in documents
        ]

    except HTTPException:
        raise
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
    db = SessionLocal()
    try:
        try:
            file_bytes = await read_upload_with_limit(file)
            validated_upload = validate_upload(file.filename, file_bytes)
        except UploadValidationError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

        storage_key = upload_file(file_bytes, validated_upload.filename)

        if workspace_id is None:
            ws = WorkspaceService.get_personal_workspace(db, current_user.id)
            workspace_id = ws.id
        else:
            WorkspaceService.require_member(db, workspace_id, current_user.id)

        document = Document(
            filename=validated_upload.filename,
            file_type=validated_upload.content_type,
            storage_path=storage_key,
            file_status="uploaded",
            language=(language or "de").strip(),
            workspace_id=workspace_id,
            uploaded_by_user_id=current_user.id,
        )

        db.add(document)
        db.commit()
        db.refresh(document)

        logger.info(
            f"Uploaded file '{validated_upload.filename}' as document ID {document.id}"
        )

        background_tasks.add_task(process_document_logic, document.id)

        return {
            "message": "Document uploaded successfully and processing started",
            "document_id": document.id,
            "status": document.file_status,
            "language": document.language,
            "workspace_id": document.workspace_id,
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.exception(f"Upload failed: {e}")
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
            "file_status": document.file_status,
            "language": document.language,
            "created_at": document.created_at,
            "workspace_id": document.workspace_id,
        }

    finally:
        db.close()


@router.patch("/{id}")
def update_document(
    id: int,
    filename: str | None = Body(default=None),
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
                "file_status": document.file_status,
                "language": document.language,
                "created_at": document.created_at,
                "workspace_id": document.workspace_id,
            },
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update document: {str(e)}")
    finally:
        db.close()


@router.post("/{id}/transfer")
def transfer_document(id: int, payload: DocumentTransferIn, current_user: User = Depends(get_current_user)):
    if payload.mode not in ("copy", "move"):
        raise HTTPException(status_code=400, detail="Mode must be 'copy' or 'move'")

    db = SessionLocal()

    try:
        source = db.query(Document).filter(Document.id == id).first()

        if not source:
            raise HTTPException(status_code=404, detail="Document not found")

        if not user_has_access_to_document(db, current_user.id, source):
            raise HTTPException(status_code=403, detail="Forbidden")

        WorkspaceService.require_member(db, payload.target_workspace_id, current_user.id)

        if source.workspace_id == payload.target_workspace_id:
            raise HTTPException(status_code=400, detail="Document is already in this workspace")

        _, delete_document_chunks = get_vector_services()

        if payload.mode == "move":
            delete_document_chunks(source.id)

            source.workspace_id = payload.target_workspace_id
            db.add(source)
            db.commit()
            db.refresh(source)

            if source.file_status == "completed":
                upsert_chunks_to_vectorstore(db, source)

            return {
                "message": "Document moved successfully",
                "document_id": source.id,
                "workspace_id": source.workspace_id,
                "mode": "move",
            }

        new_storage_path = copy_file(source.storage_path, source.filename)

        copied = Document(
            filename=source.filename,
            file_type=source.file_type,
            storage_path=new_storage_path,
            file_status=source.file_status,
            language=source.language,

            # CSV-specific structured processing fields
            parquet_key=source.parquet_key,
            csv_schema=source.csv_schema,
            csv_profile=source.csv_profile,
            csv_summary=source.csv_summary,

            workspace_id=payload.target_workspace_id,
            uploaded_by_user_id=current_user.id,
        )

        db.add(copied)
        db.flush()

        parse_id_map: dict[int, int] = {}

        source_parses = (
            db.query(DocumentParse)
            .filter(DocumentParse.document_id == source.id)
            .all()
        )

        for parse in source_parses:
            copied_parse = DocumentParse(
                document_id=copied.id,
                success=parse.success,
                full_text=parse.full_text,
                page_count=parse.page_count,
                used_ocr=parse.used_ocr,
                warnings=parse.warnings,
            )

            db.add(copied_parse)
            db.flush()

            parse_id_map[parse.id] = copied_parse.id

        source_chunks = (
            db.query(DocumentChunk)
            .filter(DocumentChunk.document_id == source.id)
            .all()
        )

        for chunk in source_chunks:
            copied_chunk = DocumentChunk(
                document_id=copied.id,
                parse_id=parse_id_map.get(chunk.parse_id) if chunk.parse_id else None,
                chunk_index=chunk.chunk_index,
                section_title=chunk.section_title,
                section_level=chunk.section_level,
                page_start=chunk.page_start,
                page_end=chunk.page_end,
                text=chunk.text,
                summary=chunk.summary,
                keywords=chunk.keywords,
                topics=chunk.topics,
                token_count=chunk.token_count,
            )

            db.add(copied_chunk)

        source_blocks = (
            db.query(DocumentBlock)
            .filter(DocumentBlock.document_id == source.id)
            .all()
        )

        for block in source_blocks:
            copied_block = DocumentBlock(
                document_id=copied.id,
                parse_id=parse_id_map.get(block.parse_id) if block.parse_id else None,
                block_index=block.block_index,
                block_type=block.block_type,
                semantic_label=block.semantic_label,
                title=block.title,
                content=block.content,
                summary=block.summary,
                confidence=block.confidence,
            )

            db.add(copied_block)

        source_reports = (
            db.query(Report)
            .filter(Report.document_id == source.id)
            .all()
        )

        for report in source_reports:
            copied_report = Report(document_id=copied.id, content=report.content)

            db.add(copied_report)

        db.commit()
        db.refresh(copied)

        if copied.file_status == "completed":
            upsert_chunks_to_vectorstore(db, copied)

        return {
            "message": "Document copied successfully",
            "document_id": copied.id,
            "workspace_id": copied.workspace_id,
            "mode": "copy",
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.exception(f"Document transfer failed: {e}")
        raise HTTPException(status_code=500, detail="Document transfer failed")
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

        _, delete_document_chunks = get_vector_services()

        delete_document_chunks(id)
        delete_file(document.storage_path)

        if document.parquet_key:
            delete_file(document.parquet_key)

        db.delete(document)
        db.commit()

        return {"message": f"Document with ID: {id} deleted successfully"}

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete document: {str(e)}"
        )

    finally:
        db.close()
