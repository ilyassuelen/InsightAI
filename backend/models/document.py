from backend.database.database import Base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
import datetime

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True)
    filename = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    storage_path = Column(String, nullable=False)
    file_status = Column(String, nullable=False)

    # Report & Chat Language
    language = Column(String, nullable=False, default="de")

    # Documents belong to a workspace (personal or team)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)
    # Who uploaded File
    uploaded_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    # Relationships
    workspace = relationship("Workspace")
    uploaded_by = relationship("User")

    parses = relationship("DocumentParse", back_populates="document", cascade="all, delete-orphan")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    blocks = relationship("DocumentBlock", back_populates="document", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="document", cascade="all, delete-orphan")
