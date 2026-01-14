from backend.database.database import Base
from sqlalchemy import Column, Integer, Text, String, Float, ForeignKey
from sqlalchemy.orm import relationship


class DocumentBlock(Base):
    __tablename__ = "document_blocks"

    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    parse_id = Column(Integer, ForeignKey("document_parses.id", ondelete="CASCADE"), nullable=True)
    block_index = Column(Integer, nullable=False)
    block_type = Column(String(50), nullable=False)
    semantic_label = Column(String(100), nullable=True)
    title = Column(Text, nullable=True)
    content = Column(Text, nullable=False)
    summary = Column(Text, nullable=False)
    confidence = Column(Float, nullable=True)
    document = relationship("Document", back_populates="blocks")
    parse = relationship("DocumentParse", back_populates="blocks")