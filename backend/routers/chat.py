from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.services.chat.chat_service import generate_chat_response

router = APIRouter()

class ChatRequest(BaseModel):
    document_id: int
    message: str

class ChatResponse(BaseModel):
    answer: str

@router.get("/")
def get_chats():
    """
    Retrieve a list of all chat messages.
    """
    return {"message": "List all chats"}

@router.post("/", response_model=ChatResponse)
async def create_chat(request: ChatRequest):
    """
    Send a new chat message and get a response.
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    try:
        answer = await generate_chat_response(request.document_id, request.message)
        return ChatResponse(answer=answer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate chat response: {e}")

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