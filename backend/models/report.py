from sqlalchemy import Column, Integer, ForeignKey, JSON
from backend.database.database import Base
from sqlalchemy.orm import relationship

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    content = Column(JSON, nullable=False)

    document = relationship("Document", back_populates="reports")
