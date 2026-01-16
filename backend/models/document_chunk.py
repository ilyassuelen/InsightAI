from datetime import datetime
from sqlalchemy import Column, Integer, Text, ForeignKey, String, DateTime
from sqlalchemy.orm import relationship
from backend.database.database import Base

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    parse_id = Column(Integer, ForeignKey("document_parses.id", ondelete="CASCADE"), nullable=True, index=True)
    chunk_index = Column(Integer, nullable=False)

    section_title = Column(String, nullable=True)
    section_level = Column(Integer, nullable=True)
    page_start = Column(Integer, nullable=True)
    page_end = Column(Integer, nullable=True)

    text = Column(Text, nullable=False)

    summary = Column(Text, nullable=True)
    keywords = Column(Text, nullable=True)
    topics = Column(Text, nullable=True)
    token_count = Column(Integer, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("Document", back_populates="chunks")
    parse = relationship("DocumentParse", back_populates="chunks")