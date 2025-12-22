from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def get_users():
    """
    Retrieve a list of all users.
    """
    return {"message": "List all users"}

@router.post("/")
def create_user():
    """
    Create a new user.
    """
    return {"message": "Create a new user"}

@router.get("/{id}")
def get_user(id: int):
    """
    Retrieve a single user by their ID.
    """
    return {"message": f"Get user {id}"}

@router.patch("/{id}")
def update_user(id: int):
    """
    Update user details for a given user ID.
    """
    return {"message": f"Update user {id}"}

@router.delete("/{id}")
def delete_user(id: int):
    """
    Delete a user by their ID.
    """
    return {"message": f"Delete user {id}"}