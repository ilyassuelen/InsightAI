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
    message: str
    workspace_id: int
    document_id: int | None = None


class ChatResponse(BaseModel):
    answer: str


def user_has_access_to_workspace(db: Session, user_id: int, workspace_id: int) -> bool:
    return (
        db.query(WorkspaceMember)
        .filter(
            WorkspaceMember.user_id == user_id,
            WorkspaceMember.workspace_id == workspace_id,
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
        if not user_has_access_to_workspace(db, current_user.id, request.workspace_id):
            raise HTTPException(status_code=403, detail="Forbidden")

        if request.document_id is not None:
            doc = db.query(Document).filter(Document.id == request.document_id).first()

            if not doc:
                raise HTTPException(status_code=404, detail="Document not found")

            if doc.workspace_id != request.workspace_id:
                raise HTTPException(
                    status_code=400,
                    detail="Document does not belong to this workspace",
                )

        answer = await generate_chat_response(
            document_id=request.document_id,
            message=request.message,
            user_id=current_user.id,
            workspace_id=request.workspace_id,
        )

        return ChatResponse(answer=answer)

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate chat response: {e}",
        )

    finally:
        db.close()
