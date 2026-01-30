from sqlalchemy.orm import Session
from backend.models.workspace import Workspace

def get_personal_workspace(db: Session, user_id: int) -> Workspace:
    workspace = (
        db.query(Workspace)
        .filter(Workspace.type == "personal", Workspace.owner_user_id == user_id)
        .first()
    )
    if not workspace:
        raise ValueError("Personal workspace not found")
    return workspace