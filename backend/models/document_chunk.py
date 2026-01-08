from backend.database.database import Base
from sqlalchemy import Column, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    parse_id = Column(Integer, ForeignKey("document_parses.id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    token_count = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    document = relationship("Document", back_populates="chunks")
    parse = relationship("DocumentParse", back_populates="chunks")