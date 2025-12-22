from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def get_reports():
    """
    Retrieve a list of all reports.
    """
    return {"message": "List all reports"}

@router.post("/")
def create_report():
    """
    Generating a new report.
    """
    return {"message": "Create a new report"}

@router.get("/{id}")
def get_report(id: int):
    """
    Retrieve a single report by its ID.
    """
    return {"message": f"Get report {id}"}

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
    return {"message": f"Delete report {id}"}