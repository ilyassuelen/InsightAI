from backend.database.database import SessionLocal
from backend.models.document_chunk import DocumentChunk
import tiktoken

ENCODING = tiktoken.encoding_for_model("gpt-4o-mini")

MAX_TOKENS = 1000

def chunk_text(document_id: int, parse_id: int, text: str, max_tokens: int = 1000):
    db = SessionLocal()

    try:
        if not text or not text.strip():
            return 0

        tokens = ENCODING.encode(text)

        chunks = [
            tokens[i:i + max_tokens]
            for i in range(0, len(tokens), max_tokens)
        ]

        for index, token_chunk in enumerate(chunks):
            chunk_text_str = ENCODING.decode(token_chunk)
            db_chunk = DocumentChunk(
                document_id=document_id,
                parse_id=parse_id,
                chunk_index=index,
                token_count=len(token_chunk),
                text=chunk_text_str
            )
            db.add(db_chunk)

        db.commit()
        return len(chunks)

    finally:
        db.close()