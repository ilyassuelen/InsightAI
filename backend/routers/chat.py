from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def get_chats():
    """
    Retrieve a list of all chat messages.
    """
    return {"message": "List all chats"}

@router.post("/")
def create_chat():
    """
    Send a new chat message.
    """
    return {"message": "Create a new chat message"}

@router.get("/{id}")
def get_chat(id: int):
    """
    Retrieve a single chat message by its ID.
    """
    return {"message": f"Get chat message {id}"}

@router.patch("/{id}")
def update_chat(id: int):
    """
    Update chat message details for a given ID.
    """
    return {"message": f"Update chat message {id}"}

@router.delete("/{id}")
def delete_chat(id: int):
    """
    Delete a chat message by its ID.
    """
    return {"message": f"Delete chat message {id}"}