from backend.services.vector.vector_store import client, COLLECTION_NAME
from backend.services.llm.llm_provider import embed_texts
from backend.database.database import SessionLocal
from backend.models.document_chunk import DocumentChunk
from backend.models.document import Document

from qdrant_client.models import Filter, FieldCondition, MatchValue

from sqlalchemy import or_


def is_csv_file_type(file_type: str | None, filename: str | None = None) -> bool:
    file_type = (file_type or "").lower()
    filename = (filename or "").lower()

    return file_type in ("text/csv", "application/csv") or filename.endswith(".csv")


def search_chunks(query: str, workspace_id: int, document_id: int | None = None, limit: int = 8):
    """
    Hybrid Retrieval for text-based documents:
    - Vector Search (Qdrant)
    - Keyword Search (SQL)

    CSV files are excluded here because they use the separate
    structured SQL-based CSV chat flow.
    """

    db = SessionLocal()

    try:
        # ------- VECTOR SEARCH -------
        vector = embed_texts([query])[0]

        must_conditions = [
            FieldCondition(
                key="workspace_id",
                match=MatchValue(value=workspace_id)
            )
        ]

        if document_id is not None:
            must_conditions.append(
                FieldCondition(
                    key="document_id",
                    match=MatchValue(value=document_id)
                )
            )

        results = client.query_points(
            collection_name=COLLECTION_NAME,
            query=vector,
            limit=limit * 3,
            with_payload=True,
            query_filter=Filter(must=must_conditions)
        )

        points = getattr(results, "points", [])
        vector_chunks = []

        for p in points:
            payload = p.payload or {}
            payload_document_id = payload.get("document_id")

            document = db.query(Document).filter(Document.id == payload_document_id).first()

            if not document:
                continue

            if is_csv_file_type(document.file_type, document.filename):
                continue

            vector_chunks.append({
                "text": payload.get("_text"),
                "document_id": payload_document_id,
                "page": payload.get("page_start"),
                "section": payload.get("section_title"),
                "score": p.score,
                "source": "vector"
            })

            if len(vector_chunks) >= limit:
                break

        # ------- KEYWORD SEARCH -------
        keyword_chunks = []

        keywords = [w.strip() for w in query.split() if len(w) > 3]

        if keywords:
            query_builder = (
                db.query(DocumentChunk)
                .join(Document, DocumentChunk.document_id == Document.id)
                .filter(
                    Document.workspace_id == workspace_id,
                    ~Document.filename.ilike("%.csv"),
                    Document.file_type.notin_(["text/csv", "application/csv"]),
                    or_(
                        *[
                            DocumentChunk.text.ilike(f"%{kw}%")
                            for kw in keywords
                        ]
                    )
                )
            )

            if document_id is not None:
                query_builder = query_builder.filter(
                    DocumentChunk.document_id == document_id
                )

            rows = query_builder.limit(limit).all()
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

        # ------- MERGE RESULTS -------
        combined = vector_chunks + keyword_chunks

        seen = set()
        unique_chunks = []

        for c in combined:
            if c["text"] and c["text"] not in seen:
                unique_chunks.append(c)
                seen.add(c["text"])

        unique_chunks.sort(key=lambda x: x["score"] or 0, reverse=True)

        return unique_chunks[:limit]

    finally:
        db.close()
