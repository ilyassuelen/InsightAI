from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def get_documents():
    """
    Retrieve a list of all documents for a user.
    """
    return {"message": "List all documents"}

@router.post("/")
def create_document():
    """
    Upload a new document.
    """
    return {"message": "Create a new document"}

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