from backend.database.database import engine, Base
from backend.models.document import Document
from backend.models.user import User
from backend.models.workspace import Workspace
from backend.models.workspace_member import WorkspaceMember
from backend.models.document_parse import DocumentParse
from backend.models.document_block import DocumentBlock
from backend.models.document_chunk import DocumentChunk
from backend.models.report import Report

Base.metadata.create_all(engine)