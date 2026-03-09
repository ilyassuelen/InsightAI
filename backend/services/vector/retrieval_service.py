from backend.services.vector.vector_store import client, COLLECTION_NAME
from backend.services.llm.llm_provider import embed_texts
from backend.database.database import SessionLocal
from backend.models.document_chunk import DocumentChunk
from backend.models.document import Document

from qdrant_client.models import Filter, FieldCondition, MatchValue

from sqlalchemy import or_

def search_chunks(query: str, workspace_id: int, limit: int = 8):
    """
    Hybrid Retrieval:
    - Vector Search (Qdrant)
    - Keyword Search (SQL)
    Returns top matching document chunks.
    """

    # ----------- VECTOR SEARCH -----------
    vector = embed_texts([query])[0]

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=vector,
        limit=limit,
        with_payload=True,
        query_filter=Filter(
            must=[
                FieldCondition(
                    key="workspace_id",
                    match=MatchValue(value=workspace_id)
                )
            ]
        )
    )

    points = getattr(results, "points", [])
    vector_chunks = []

    for p in points:
        payload = p.payload or {}

        vector_chunks.append({
            "text": payload.get("_text"),
            "document_id": payload.get("document_id"),
            "page": payload.get("page_start"),
            "section": payload.get("section_title"),
            "score": p.score,
            "source": "vector"
        })

    # ----------- KEYWORD SEARCH -----------
    db = SessionLocal()

    try:
        keyword_chunks = []

        keywords = [w.strip() for w in query.split() if len(w) > 3]

        if keywords:
            rows = (
                db.query(DocumentChunk)
                .join(Document, DocumentChunk.document_id == Document.id)
                .filter(
                    Document.workspace_id == workspace_id,
                    or_(
                        *[
                            DocumentChunk.text.ilike(f"%{kw}%")
                            for kw in keywords
                        ]
                    )
                )
                .limit(limit)
                .all()
            )
        else:
            rows = []

        for r in rows:
            keyword_chunks.append({
                "text": r.text,
                "document_id": r.document_id,
                "page": getattr(r, "page_start", None),
                "section": getattr(r, "section_title", None),
                "score": 0.65,
                "source": "keyword"
            })

    finally:
        db.close()

    # ----------- MERGE RESULTS -----------
    combined = vector_chunks + keyword_chunks

    seen = set()
    unique_chunks = []

    for c in combined:
        if c["text"] and c["text"] not in seen:
            unique_chunks.append(c)
            seen.add(c["text"])

    # Sort by score (Vector results higher)
    unique_chunks.sort(key=lambda x: x["score"] or 0, reverse=True)

    return unique_chunks[:limit]
