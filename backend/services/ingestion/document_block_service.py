from backend.database.database import SessionLocal
from backend.models.document_chunk import DocumentChunk
from backend.models.document_block import DocumentBlock

CHUNKS_PER_BLOCK = 5

def create_blocks_from_chunks(document_id: int, parse_id: int):
    db = SessionLocal()

    try:
        chunks = (
            db.query(DocumentChunk)
            .filter(
                DocumentChunk.document_id == document_id,
                DocumentChunk.parse_id == parse_id
            )
            .order_by(DocumentChunk.chunk_index)
            .all()
        )

        if not chunks:
            return 0

        blocks_created = 0

        for i in range(0, len(chunks), CHUNKS_PER_BLOCK):
            group = chunks[i:i + CHUNKS_PER_BLOCK]

            combined_text = "\n\n".join(c.text for c in group)

            block = DocumentBlock(
                document_id=document_id,
                parse_id=parse_id,
                block_index=blocks_created,
                block_type="section",
                semantic_label=None,
                title=None,
                content=combined_text,
                summary=combined_text[:500],
                confidence=None
            )

            db.add(block)
            blocks_created += 1

        db.commit()
        return blocks_created

    finally:
        db.close()
