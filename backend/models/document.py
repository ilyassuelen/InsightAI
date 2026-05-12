from backend.database.database import Base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
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

    # CSV-specific structured processing fields
    parquet_key = Column(String, nullable=True)
    csv_schema = Column(JSON, nullable=True)
    csv_profile = Column(JSON, nullable=True)
    csv_summary = Column(JSON, nullable=True)

    # Documents belong to a workspace (personal or team)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)

    # Who uploaded File
    uploaded_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    # Relationships
    workspace = relationship("Workspace", back_populates="documents")
    uploaded_by = relationship("User", foreign_keys=[uploaded_by_user_id], back_populates="documents")

    parses = relationship("DocumentParse", back_populates="document", cascade="all, delete-orphan")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    blocks = relationship("DocumentBlock", back_populates="document", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="document", cascade="all, delete-orphan")
