from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any

from backend.database.database import Base, SessionLocal, engine
from backend.models.document import Document
from backend.models.document_block import DocumentBlock  # noqa: F401
from backend.models.document_chunk import DocumentChunk  # noqa: F401
from backend.models.document_parse import DocumentParse  # noqa: F401
from backend.models.report import Report  # noqa: F401
from backend.models.user import User
from backend.models.workspace import Workspace
from backend.models.workspace_member import WorkspaceMember


def reset_database() -> None:
    """Recreate the isolated SQLite schema used by tests."""

    expected_name = f"insightai_test_{__import__('os').getpid()}.db"
    if engine.url.get_backend_name() != "sqlite" or not str(engine.url.database).endswith(expected_name):
        raise RuntimeError(f"Refusing to reset non-test database: {engine.url}")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def create_user_workspace(
    *,
    email: str = "owner@example.test",
    workspace_name: str = "Personal",
    workspace_type: str = "personal",
    role: str = "owner",
) -> tuple[User, Workspace]:
    db = SessionLocal()
    try:
        user = User(email=email, password_hash="test-hash", full_name="Test User")
        db.add(user)
        db.flush()

        workspace = Workspace(
            name=workspace_name,
            type=workspace_type,
            owner_user_id=user.id,
        )
        db.add(workspace)
        db.flush()

        db.add(WorkspaceMember(workspace_id=workspace.id, user_id=user.id, role=role))
        db.commit()
        db.refresh(user)
        db.refresh(workspace)
        return user, workspace
    finally:
        db.close()


def create_document(
    workspace_id: int,
    user_id: int | None = None,
    *,
    filename: str = "sample.txt",
    file_type: str = "text/plain",
    status: str = "completed",
    storage_path: str = "documents/sample.txt",
    language: str = "de",
    parquet_key: str | None = None,
) -> Document:
    db = SessionLocal()
    try:
        document = Document(
            filename=filename,
            file_type=file_type,
            storage_path=storage_path,
            file_status=status,
            language=language,
            workspace_id=workspace_id,
            uploaded_by_user_id=user_id,
            parquet_key=parquet_key,
        )
        db.add(document)
        db.commit()
        db.refresh(document)
        db.expunge(document)
        return document
    finally:
        db.close()


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@dataclass
class FakeEmbeddingItem:
    embedding: list[float]


def embedding_response(vectors: list[list[float]]) -> Any:
    return SimpleNamespace(data=[FakeEmbeddingItem(vector) for vector in vectors])


def chat_response(content: str, *, prompt_tokens: int = 3, completion_tokens: int = 2) -> Any:
    usage = SimpleNamespace(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
    )
    message = SimpleNamespace(content=content)
    return SimpleNamespace(choices=[SimpleNamespace(message=message)], usage=usage)
