from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

from backend.database.database import SessionLocal
from backend.models.user import User
from backend.models.workspace import Workspace
from backend.models.workspace_member import WorkspaceMember
from backend.services.auth.passwords import hash_password, verify_password
from backend.services.auth.jwt import create_access_token
from backend.services.auth.deps import get_current_user

router = APIRouter()


# -------------------- Schemas --------------------
class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    email: str


class MeResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str] = None


# -------------------- HELPER FUNCTIONS --------------------
def create_personal_workspace(db, user: User) -> Workspace:
    workspace = Workspace(
        name=f"{user.email}'s Personal",
        type="personal",
        owner_user_id=user.id,
    )
    db.add(workspace)
    db.commit()
    db.refresh(workspace)

    member = WorkspaceMember(
        workspace_id=workspace.id,
        user_id=user.id,
        role="owner",
    )
    db.add(member)
    db.commit()

    return workspace


# -------------------- Routes --------------------
@router.post("/register", response_model=AuthResponse)
def register(payload: RegisterRequest):
    email = (payload.email or "").strip().lower()
    password = payload.password or ""

    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password are required")
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    if len(password) > 256:
        raise HTTPException(status_code=400, detail="Password must be at most 256 characters")

    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            raise HTTPException(status_code=409, detail="Email already registered")

        user = User(
            email=email,
            password_hash=hash_password(password),
            full_name=(payload.full_name or "").strip() or None,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Create personal workspace + Membership
        create_personal_workspace(db, user)

        token = create_access_token(subject=str(user.id))
        return AuthResponse(access_token=token, user_id=user.id, email=user.email)
    finally:
        db.close()


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest):
    email = (payload.email or "").strip().lower()
    password = payload.password or ""

    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password are required")

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid email or password")

        token = create_access_token(subject=str(user.id))
        return AuthResponse(access_token=token, user_id=user.id, email=user.email)
    finally:
        db.close()


@router.get("/me", response_model=MeResponse)
def me(current_user: User = Depends(get_current_user)):
    return MeResponse(id=current_user.id, email=current_user.email, full_name=current_user.full_name)
