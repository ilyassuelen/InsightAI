from backend.database.database import engine, Base
from backend.models.document import Document

Base.metadata.create_all(engine)