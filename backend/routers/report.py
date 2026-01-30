from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from backend.database.database import SessionLocal
from backend.models.report import Report
from backend.models.document import Document
from backend.models.workspace_member import WorkspaceMember
from backend.models.user import User
from backend.services.auth.deps import get_current_user
from backend.services.reporting.report_service import generate_report_for_document

router = APIRouter()


def user_has_access_to_document(db: Session, user_id: int, document: Document) -> bool:
    return (
        db.query(WorkspaceMember)
        .filter(
            WorkspaceMember.user_id == user_id,
            WorkspaceMember.workspace_id == document.workspace_id,
        )
        .first()
        is not None
    )


@router.get("/")
def get_reports(current_user: User = Depends(get_current_user)):
    """
    Retrieve a list of reports accessible to the current user.
    """
    db: Session = SessionLocal()
    try:
        # Workspaces where user is member
        workspace_ids = [
            wid for (wid,) in db.query(WorkspaceMember.workspace_id)
            .filter(WorkspaceMember.user_id == current_user.id)
            .all()
        ]
        if not workspace_ids:
            return JSONResponse(content=[], media_type="application/json")

        # Join documents -> reports through document_id
        docs = db.query(Document.id).filter(Document.workspace_id.in_(workspace_ids)).all()
        doc_ids = [d[0] for d in docs]
        if not doc_ids:
            return JSONResponse(content=[], media_type="application/json")

        reports = db.query(Report).filter(Report.document_id.in_(doc_ids)).all()

        return JSONResponse(
            content=[{
                "id": report.id,
                "document_id": report.document_id,
                "content": report.content,
                "generated_at": report.created_at.isoformat()
            } for report in reports],
            media_type="application/json"
        )
    finally:
        db.close()


@router.post("/{document_id}")
def create_report(document_id: int, current_user: User = Depends(get_current_user)):
    """
    Generate a structured report for a given document (document_id).
    Protected + access-controlled.
    """
    db: Session = SessionLocal()
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        if not user_has_access_to_document(db, current_user.id, document):
            raise HTTPException(status_code=403, detail="Forbidden")

        report_data = generate_report_for_document(db, document_id)

        report = Report(
            document_id=document_id,
            content=report_data
        )

        db.add(report)
        db.commit()
        db.refresh(report)

        report_data["generated_at"] = report.created_at.isoformat()

        return JSONResponse(content=report_data, media_type="application/json")

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    finally:
        db.close()


@router.get("/{document_id}")
def get_report(document_id: int, current_user: User = Depends(get_current_user)):
    """
    Returns the latest report for that document.
    """
    db: Session = SessionLocal()
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        if not user_has_access_to_document(db, current_user.id, document):
            raise HTTPException(status_code=403, detail="Forbidden")

        report = (
            db.query(Report)
            .filter(Report.document_id == document_id)
            .order_by(Report.created_at.desc())
            .first()
        )

        if not report:
            raise HTTPException(status_code=404, detail="Report not found")

        report_data = report.content or {}
        report_data["generated_at"] = report.created_at.isoformat()
        return report_data

    finally:
        db.close()


@router.delete("/{report_id}")
def delete_report(report_id: int, current_user: User = Depends(get_current_user)):
    """
    Delete a report by report_id, but only if user has access to the underlying document.
    """
    db: Session = SessionLocal()
    try:
        report = db.query(Report).filter(Report.id == report_id).first()
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")

        document = db.query(Document).filter(Document.id == report.document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        if not user_has_access_to_document(db, current_user.id, document):
            raise HTTPException(status_code=403, detail="Forbidden")

        db.delete(report)
        db.commit()
        return {"message": f"Report with ID: {report_id} deleted successfully"}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete report: {str(e)}")

    finally:
        db.close()
