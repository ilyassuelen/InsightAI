from typing import List, Optional, Tuple
from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.models.user import User
from backend.models.workspace import Workspace
from backend.models.workspace_member import WorkspaceMember

class WorkspaceService:
    @staticmethod
    def get_personal_workspace(db: Session, user_id: int) -> Workspace:
        ws = (
            db.query(Workspace)
            .filter(Workspace.type == "personal", Workspace.owner_user_id == user_id)
            .first()
        )
        if ws:
            return ws

        ws = Workspace(
            name="My Personal Workspace",
            type="personal",
            owner_user_id=user_id,
        )
        db.add(ws)
        db.commit()
        db.refresh(ws)

        # Ensure membership owner
        member = WorkspaceMember(
            workspace_id=ws.id,
            user_id=user_id,
            role="owner",
        )
        db.add(member)
        db.commit()
        return ws

    @staticmethod
    def list_user_workspaces(db: Session, user_id: int) -> List[Workspace]:
        return (
            db.query(Workspace)
            .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
            .filter(WorkspaceMember.user_id == user_id)
            .order_by(Workspace.created_at.asc())
            .all()
        )

    @staticmethod
    def get_workspace(db: Session, workspace_id: int) -> Workspace:
        ws = db.query(Workspace).filter(Workspace.id == workspace_id).first()
        if not ws:
            raise HTTPException(status_code=404, detail="Workspace not found")
        return ws

    @staticmethod
    def get_membership(db: Session, workspace_id: int, user_id: int) -> Optional[WorkspaceMember]:
        return (
            db.query(WorkspaceMember)
            .filter(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.user_id == user_id,
            )
            .first()
        )

    @staticmethod
    def require_member(db: Session, workspace_id: int, user_id: int) -> WorkspaceMember:
        membership = WorkspaceService.get_membership(db, workspace_id, user_id)
        if not membership:
            raise HTTPException(status_code=403, detail="Not a member of this workspace")
        return membership

    @staticmethod
    def require_owner(db: Session, workspace_id: int, user_id: int) -> WorkspaceMember:
        membership = WorkspaceService.require_member(db, workspace_id, user_id)
        if membership.role != "owner":
            raise HTTPException(status_code=403, detail="Owner permission required")
        return membership

    # ---------------- Team workspace CRUD ----------------

    @staticmethod
    def create_team_workspace(db: Session, owner_user: User, name: str) -> Workspace:
        name = (name or "").strip()
        if len(name) < 2:
            raise HTTPException(status_code=400, detail="Workspace name must be at least 2 characters")

        ws = Workspace(
            name=name,
            type="team",
            owner_user_id=owner_user.id,
        )
        db.add(ws)
        db.commit()
        db.refresh(ws)

        # owner membership
        member = WorkspaceMember(
            workspace_id=ws.id,
            user_id=owner_user.id,
            role="owner",
        )
        db.add(member)
        db.commit()

        return ws

    @staticmethod
    def rename_workspace(db: Session, workspace_id: int, user_id: int, new_name: str) -> Workspace:
        WorkspaceService.require_owner(db, workspace_id, user_id)
        ws = WorkspaceService.get_workspace(db, workspace_id)

        new_name = (new_name or "").strip()
        if len(new_name) < 2:
            raise HTTPException(status_code=400, detail="Workspace name must be at least 2 characters")

        ws.name = new_name
        db.add(ws)
        db.commit()
        db.refresh(ws)
        return ws

    @staticmethod
    def delete_workspace(db: Session, workspace_id: int, user_id: int) -> None:
        WorkspaceService.require_owner(db, workspace_id, user_id)
        ws = WorkspaceService.get_workspace(db, workspace_id)

        if ws.type == "personal":
            raise HTTPException(status_code=400, detail="Personal workspace cannot be deleted")

        db.delete(ws)
        db.commit()

    # ---------------- Member management ----------------

    @staticmethod
    def list_members(db: Session, workspace_id: int, user_id: int) -> List[Tuple[WorkspaceMember, User]]:
        WorkspaceService.require_member(db, workspace_id, user_id)

        rows = (
            db.query(WorkspaceMember, User)
            .join(User, User.id == WorkspaceMember.user_id)
            .filter(WorkspaceMember.workspace_id == workspace_id)
            .all()
        )
        return rows

    @staticmethod
    def add_member_by_email(db: Session, workspace_id: int, owner_user_id: int, email: str, role: str = "member") -> None:
        WorkspaceService.require_owner(db, workspace_id, owner_user_id)

        ws = WorkspaceService.get_workspace(db, workspace_id)
        if ws.type == "personal":
            raise HTTPException(status_code=400, detail="Cannot add members to personal workspace")

        email = (email or "").strip().lower()
        if not email:
            raise HTTPException(status_code=400, detail="Email is required")

        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User with this email not found")

        existing = WorkspaceService.get_membership(db, workspace_id, user.id)
        if existing:
            raise HTTPException(status_code=409, detail="User is already a member of this workspace")

        if role not in ("owner", "member"):
            raise HTTPException(status_code=400, detail="Invalid role")

        member = WorkspaceMember(
            workspace_id=workspace_id,
            user_id=user.id,
            role=role,
        )
        db.add(member)
        db.commit()

    @staticmethod
    def remove_member(db: Session, workspace_id: int, owner_user_id: int, remove_user_id: int) -> None:
        WorkspaceService.require_owner(db, workspace_id, owner_user_id)

        ws = WorkspaceService.get_workspace(db, workspace_id)
        if ws.type == "personal":
            raise HTTPException(status_code=400, detail="Cannot remove members from personal workspace")

        if remove_user_id == owner_user_id:
            raise HTTPException(status_code=400, detail="Owner cannot remove themselves")

        membership = WorkspaceService.get_membership(db, workspace_id, remove_user_id)
        if not membership:
            raise HTTPException(status_code=404, detail="Member not found")

        db.delete(membership)
        db.commit()
