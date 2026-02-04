from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Optional

from backend.database.database import SessionLocal
from backend.models.user import User
from backend.services.auth.deps import get_current_user
from backend.services.workspaces.workspace_service import WorkspaceService

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


class WorkspaceOut(BaseModel):
    id: int
    name: str
    type: str
    owner_user_id: int


class WorkspaceCreateIn(BaseModel):
    name: str


class WorkspaceRenameIn(BaseModel):
    name: str


class MemberOut(BaseModel):
    user_id: int
    email: str
    full_name: Optional[str] = None
    role: str


class AddMemberIn(BaseModel):
    email: str
    role: str = "member"


@router.get("/", response_model=List[WorkspaceOut])
def list_workspaces(current_user: User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        # Ensure personal exists
        WorkspaceService.get_personal_workspace(db, current_user.id)

        workspaces = WorkspaceService.list_user_workspaces(db, current_user.id)
        return [
            WorkspaceOut(
                id=w.id,
                name=w.name,
                type=w.type,
                owner_user_id=w.owner_user_id,
            )
            for w in workspaces
        ]
    finally:
        db.close()


@router.post("/", response_model=WorkspaceOut)
def create_workspace(payload: WorkspaceCreateIn, current_user: User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        ws = WorkspaceService.create_team_workspace(db, current_user, payload.name)
        return WorkspaceOut(id=ws.id, name=ws.name, type=ws.type, owner_user_id=ws.owner_user_id)
    finally:
        db.close()


@router.patch("/{workspace_id}", response_model=WorkspaceOut)
def rename_workspace(workspace_id: int, payload: WorkspaceRenameIn, current_user: User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        ws = WorkspaceService.rename_workspace(db, workspace_id, current_user.id, payload.name)
        return WorkspaceOut(id=ws.id, name=ws.name, type=ws.type, owner_user_id=ws.owner_user_id)
    finally:
        db.close()


@router.delete("/{workspace_id}")
def delete_workspace(workspace_id: int, current_user: User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        WorkspaceService.delete_workspace(db, workspace_id, current_user.id)
        return {"ok": True}
    finally:
        db.close()


@router.get("/{workspace_id}/members", response_model=List[MemberOut])
def list_members(workspace_id: int, current_user: User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        rows = WorkspaceService.list_members(db, workspace_id, current_user.id)
        out: List[MemberOut] = []
        for membership, user in rows:
            out.append(
                MemberOut(
                    user_id=user.id,
                    email=user.email,
                    full_name=user.full_name,
                    role=membership.role,
                )
            )
        return out
    finally:
        db.close()


@router.post("/{workspace_id}/members")
def add_member(workspace_id: int, payload: AddMemberIn, current_user: User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        WorkspaceService.add_member_by_email(
            db,
            workspace_id=workspace_id,
            owner_user_id=current_user.id,
            email=payload.email,
            role=payload.role,
        )
        return {"ok": True}
    finally:
        db.close()


@router.delete("/{workspace_id}/members/{user_id}")
def remove_member(workspace_id: int, user_id: int, current_user: User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        WorkspaceService.remove_member(
            db,
            workspace_id=workspace_id,
            owner_user_id=current_user.id,
            remove_user_id=user_id,
        )
        return {"ok": True}
    finally:
        db.close()
