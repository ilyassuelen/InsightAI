from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from backend.database.database import SessionLocal
from backend.services.report_service import generate_report_for_document
from backend.models.report import Report

router = APIRouter()

@router.get("/")
def get_reports():
    """
    Retrieve a list of all reports.
    """
    db: Session = SessionLocal()
    try:
        reports = db.query(Report).all()
        return JSONResponse(
            content = [{
                "id": report.id,
                "document_id": report.document_id,
                "content": report.content
            }
            for report in reports
            ],
            media_type="application/json"
        )
    finally:
        db.close()

@router.post("/{document_id}")
def create_report(document_id: int):
    """
    Generating a structured report for a given document.
    """
    db: Session = SessionLocal()
    try:
        # Generate Report
        report_data = generate_report_for_document(db, document_id)

        # Save to DB
        report = Report(
            document_id=document_id,
            content=report_data
        )

        db.add(report)
        db.commit()
        db.refresh(report)

        return JSONResponse(
            content=report_data,
            media_type="application/json"
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@router.get("/{id}")
def get_report(id: int):
    """
    Retrieve a single report by its ID.
    """
    db: Session = SessionLocal()
    try:
        report = db.query(Report).filter(Report.id == id).first()
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        return JSONResponse(
            content={
                    "id": report.id,
                    "document_id": report.document_id,
                    "content": report.content
            },
            media_type="application/json"
        )
    finally:
        db.close()

@router.patch("/{id}")
def update_report(id: int):
    """
    Update report details for a given ID.
    """
    return {"message": f"Update report {id}"}

@router.delete("/{id}")
def delete_report(id: int):
    """
    Delete a report by its ID.
    """
    db = SessionLocal()
    try:
        report = db.query(Report).filter(Report.id == id).first()
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")

        db.delete(report)
        db.commit()

        return {"message": f"Report with ID: {id} deleted successfully"}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete report: {str(e)}")
    finally:
        db.close()
