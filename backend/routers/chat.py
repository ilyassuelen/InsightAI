from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.services.chat.chat_service import generate_chat_response
from backend.services.auth.deps import get_current_user
from backend.database.database import SessionLocal
from backend.models.user import User
from backend.models.document import Document
from backend.models.workspace_member import WorkspaceMember

router = APIRouter()

class ChatRequest(BaseModel):
    document_id: int
    message: str

class ChatResponse(BaseModel):
    answer: str


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


@router.post("/", response_model=ChatResponse)
async def create_chat(request: ChatRequest, current_user: User = Depends(get_current_user)):
    """
    Send a new chat message and get a response.
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    db = SessionLocal()

    try:
        doc = db.query(Document).filter(Document.id == request.document_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        if not user_has_access_to_document(db, current_user.id, doc):
            raise HTTPException(status_code=403, detail="Forbidden")

        answer = await generate_chat_response(
            request.document_id,
            request.message,
            user_id=current_user.id,
            workspace_id=doc.workspace_id
        )
        return ChatResponse(answer=answer)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate Chat response: {e}")
    finally:
        db.close()
