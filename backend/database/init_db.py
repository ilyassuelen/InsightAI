from backend.database.database import engine, Base
from backend.models.document import Document
from backend.models.document_parse import DocumentParse

Base.metadata.create_all(engine)