from backend.database.database import Base
from sqlalchemy import Column, Integer, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
import datetime

class DocumentParse(Base):
    __tablename__ = "document_parses"

    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    success = Column(Boolean, nullable=False)
    full_text = Column(Text, nullable=False)
    page_count = Column(Integer, nullable=False)
    used_ocr = Column(Boolean, nullable=False)
    warnings = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    document = relationship("Document", back_populates="parses")
    chunks = relationship("DocumentChunk", back_populates="parse", cascade="all, delete-orphan")
    blocks = relationship("DocumentBlock", back_populates="parse", cascade="all, delete-orphan")
