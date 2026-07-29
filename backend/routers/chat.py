import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.database.database import SessionLocal
from backend.models.chat_conversation import ChatConversation
from backend.models.chat_message import ChatMessage
from backend.models.document import Document
from backend.models.user import User
from backend.models.workspace_member import WorkspaceMember
from backend.services.auth.deps import get_current_user
from backend.services.chat.chat_service import generate_chat_response

router = APIRouter()
HISTORY_DB_MESSAGE_LIMIT = 20
CONVERSATION_LIST_LIMIT = 50


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    workspace_id: int
    document_id: int | None = None
    conversation_id: int | None = None


class ChatResponse(BaseModel):
    answer: str
    conversation_id: int


class ChatMessageResponse(BaseModel):
    id: int
    role: str
    content: str
    sequence_index: int
    created_at: datetime.datetime


class ChatConversationSummary(BaseModel):
    id: int
    title: str
    workspace_id: int
    document_id: int | None
    created_at: datetime.datetime
    updated_at: datetime.datetime


class ChatConversationDetail(ChatConversationSummary):
    messages: List[ChatMessageResponse]


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


def require_workspace_access(db: Session, user_id: int, workspace_id: int) -> None:
    if not user_has_access_to_workspace(db, user_id, workspace_id):
        raise HTTPException(status_code=403, detail="Forbidden")


def require_document_context(db: Session, document_id: Optional[int], workspace_id: int) -> Optional[Document]:
    if document_id is None:
        return None

    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    if document.workspace_id != workspace_id:
        raise HTTPException(
            status_code=400,
            detail="Document does not belong to this workspace",
        )
    return document


def require_owned_conversation(
        db: Session,
        conversation_id: int,
        current_user: User
) -> ChatConversation:
    conversation = (
        db.query(ChatConversation)
        .filter(
            ChatConversation.id == conversation_id,
            ChatConversation.created_by_user_id == current_user.id,
        )
        .first()
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    require_workspace_access(
        db,
        current_user.id,
        conversation.workspace_id,
    )
    return conversation


def conversation_summary(conversation: ChatConversation) -> ChatConversationSummary:
    return ChatConversationSummary(
        id=conversation.id,
        title=conversation.title,
        workspace_id=conversation.workspace_id,
        document_id=conversation.document_id,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
    )


def next_message_index(db: Session, conversation_id: int) -> int:
    current = (
        db.query(func.max(ChatMessage.sequence_index))
        .filter(ChatMessage.conversation_id == conversation_id)
        .scalar()
    )
    return (current if current is not None else -1) + 1


def conversation_title(message: str) -> str:
    normalized = " ".join(message.split())
    return normalized[:80] or "New conversation"


@router.get("/conversations", response_model=List[ChatConversationSummary])
def list_conversations(
        workspace_id: int,
        document_id: int | None = Query(default=None),
        current_user: User = Depends(get_current_user),
):
    """
    List the current user's conversations for one exact chat context.
    """
    db = SessionLocal()
    try:
        require_workspace_access(db, current_user.id, workspace_id)
        require_document_context(db, document_id, workspace_id)

        query = db.query(ChatConversation).filter(
            ChatConversation.workspace_id == workspace_id,
            ChatConversation.created_by_user_id == current_user.id,
        )
        if document_id is None:
            query = query.filter(ChatConversation.document_id.is_(None))
        else:
            query = query.filter(ChatConversation.document_id == document_id)

        conversations = (
            query.order_by(ChatConversation.updated_at.desc())
            .limit(CONVERSATION_LIST_LIMIT)
            .all()
        )
        return [conversation_summary(item) for item in conversations]
    finally:
        db.close()


@router.get("/conversations/{conversation_id}", response_model=ChatConversationDetail)
def get_conversation(conversation_id: int, current_user: User = Depends(get_current_user)):
    """
    Return a private conversation and all persisted messages.
    """
    db = SessionLocal()
    try:
        conversation = require_owned_conversation(
            db,
            conversation_id,
            current_user,
        )
        messages = (
            db.query(ChatMessage)
            .filter(ChatMessage.conversation_id == conversation.id)
            .order_by(ChatMessage.sequence_index)
            .all()
        )
        summary = conversation_summary(conversation)
        return ChatConversationDetail(
            **summary.model_dump(),
            messages=[
                ChatMessageResponse(
                    id=message.id,
                    role=message.role,
                    content=message.content,
                    sequence_index=message.sequence_index,
                    created_at=message.created_at,
                )
                for message in messages
            ],
        )
    finally:
        db.close()


@router.delete("/conversations/{conversation_id}")
def delete_conversation(conversation_id: int, current_user: User = Depends(get_current_user)):
    """
    Delete one private conversation and its messages.
    """
    db = SessionLocal()
    try:
        conversation = require_owned_conversation(
            db,
            conversation_id,
            current_user,
        )
        db.delete(conversation)
        db.commit()
        return {"message": "Conversation deleted"}
    except HTTPException:
        raise
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to delete conversation",
        )
    finally:
        db.close()


@router.post("/", response_model=ChatResponse)
async def create_chat(request: ChatRequest, current_user: User = Depends(get_current_user)):
    """
    Persist a user message, generate a grounded answer, and persist the answer.
    """
    message = request.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    db = SessionLocal()

    try:
        require_workspace_access(db, current_user.id, request.workspace_id)
        require_document_context(
            db,
            request.document_id,
            request.workspace_id,
        )

        if request.conversation_id is None:
            conversation = ChatConversation(
                workspace_id=request.workspace_id,
                document_id=request.document_id,
                created_by_user_id=current_user.id,
                title=conversation_title(message),
            )
            db.add(conversation)
            db.flush()
        else:
            conversation = require_owned_conversation(
                db,
                request.conversation_id,
                current_user,
            )
            if (
                conversation.workspace_id != request.workspace_id
                or conversation.document_id != request.document_id
            ):
                raise HTTPException(
                    status_code=400,
                    detail="Conversation context does not match the request",
                )

        recent_messages = (
            db.query(ChatMessage)
            .filter(ChatMessage.conversation_id == conversation.id)
            .order_by(ChatMessage.sequence_index.desc())
            .limit(HISTORY_DB_MESSAGE_LIMIT)
            .all()
        )
        history = [
            {"role": item.role, "content": item.content}
            for item in reversed(recent_messages)
        ]

        user_sequence = next_message_index(db, conversation.id)
        db.add(
            ChatMessage(
                conversation_id=conversation.id,
                role="user",
                content=message,
                sequence_index=user_sequence,
            )
        )
        conversation.updated_at = datetime.datetime.utcnow()
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

        answer = await generate_chat_response(
            document_id=request.document_id,
            message=message,
            user_id=current_user.id,
            workspace_id=request.workspace_id,
            history=history,
        )

        db.add(
            ChatMessage(
                conversation_id=conversation.id,
                role="assistant",
                content=answer,
                sequence_index=user_sequence + 1,
            )
        )
        conversation.updated_at = datetime.datetime.utcnow()
        db.add(conversation)
        db.commit()

        return ChatResponse(
            answer=answer,
            conversation_id=conversation.id,
        )

    except HTTPException:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to generate chat response",
        )

    finally:
        db.close()
