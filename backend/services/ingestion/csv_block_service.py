from sqlalchemy.orm import Session
from backend.models.document_block import DocumentBlock

ROWS_PER_BLOCK = 300

def create_blocks_from_csv_rows(
    db: Session,
    document_id: int,
    rows: list[dict],
):
    if not rows:
        return

    headers = list(rows[0].keys())

    blocks = []
    block_index = 0

    for i in range(0, len(rows), ROWS_PER_BLOCK):
        chunk = rows[i:i + ROWS_PER_BLOCK]

        text = "Columns:\n"
        text += ", ".join(headers) + "\n\nRows:\n"

        for row in chunk:
            text += " | ".join(str(row[h]) for h in headers) + "\n"

        block = DocumentBlock(
            document_id=document_id,
            block_index=block_index,
            block_type="table",
            content=text,
            semantic_label=None,
            title=None,
            summary=text[:500]
        )

        blocks.append(block)
        block_index += 1

    db.add_all(blocks)
    db.commit()
