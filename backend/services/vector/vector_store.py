import os
import uuid
import logging
from typing import List, Dict, Any

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

# Keep embeddings consistent OpenAI only (no Gemini embedding fallback)
from backend.services.llm.llm_provider import embed_texts as embed_texts_openai

logger = logging.getLogger(__name__)

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "insightai_chunks")

client = QdrantClient(url=QDRANT_URL)

# Cache: If the collection exists, stop calling get_collections()
_COLLECTION_READY = False


def ensure_collection(vector_size: int):
    """
    Ensure the Qdrant collection exists.
    Uses a cached flag to avoid repeated GET /collections calls.
    """
    global _COLLECTION_READY
    if _COLLECTION_READY:
        return

    existing = [c.name for c in client.get_collections().collections]
    if COLLECTION_NAME in existing:
        _COLLECTION_READY = True
        return

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=qmodels.VectorParams(
            size=vector_size,
            distance=qmodels.Distance.COSINE,
        ),
    )
    logger.info(f"[Qdrant] Created collection: {COLLECTION_NAME}")
    _COLLECTION_READY = True


def upsert_document_chunks(document_id: int, chunks: List[Dict], batch_size: int = 512):
    if not chunks:
        return

    texts = [c["text"] for c in chunks]

    vectors = embed_texts_openai(texts)

    if not vectors or not vectors[0]:
        logger.warning("[Qdrant] No embeddings generated")
        return

    ensure_collection(vector_size=len(vectors[0]))

    # Delete old chunks of this document to prevent mixing documents
    try:
        client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=qmodels.Filter(
                must=[
                    qmodels.FieldCondition(
                        key="document_id",
                        match=qmodels.MatchValue(value=document_id),
                    )
                ]
            ),
        )

        logger.info(f"[Qdrant] Deleted old vectors for document_id={document_id}")

    except Exception as e:
        logger.warning(
            f"[Qdrant] Delete-by-filter failed for document_id={document_id}: {e}"
        )

    # IDs
    ids = [
        str(uuid.uuid5(uuid.NAMESPACE_URL, f"doc{document_id}_chunk{c['id']}"))
        for c in chunks
    ]

    # Payloads
    payloads: List[Dict[str, Any]] = []
    for c in chunks:
        md = c.get("metadata") or {}
        payloads.append(
            {
                "document_id": document_id,
                "chunk_db_id": c["id"],
                "_text": c["text"],
                "chunk_index": md.get("chunk_index"),
                "page_start": md.get("page_start"),
                "page_end": md.get("page_end"),
                "section_title": md.get("section_title"),
                "keywords": c.get("keywords", []),
            }
        )

    # Upsert in batches
    for start in range(0, len(ids), batch_size):
        end = start + batch_size
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=qmodels.Batch(
                ids=ids[start:end],
                vectors=vectors[start:end],
                payloads=payloads[start:end],
            ),
        )

    logger.info(f"[Qdrant] Upserted {len(ids)} chunks for document_id={document_id}")


def query_similar_chunks(document_id: int, query: str, k: int = 5) -> List[Dict]:
    """Return top-k chunks (text + metadata) for a document_id."""
    q_vec = embed_texts_openai([query])[0]
    if not q_vec:
        return []

    # Ensure collection with real vector size
    ensure_collection(vector_size=len(q_vec))

    flt = qmodels.Filter(
        must=[
            qmodels.FieldCondition(
                key="document_id",
                match=qmodels.MatchValue(value=document_id),
            )
        ]
    )

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=q_vec,
        limit=k,
        query_filter=flt,
        with_payload=True,
    )

    points = getattr(results, "points", [])

    hits = []
    for p in points:
        payload = getattr(p, "payload", None) or {}
        hits.append(
            {
                "id": getattr(p, "id", None),
                "text": payload.get("_text", ""),
                "metadata": {
                    "chunk_index": payload.get("chunk_index"),
                    "page_start": payload.get("page_start"),
                    "page_end": payload.get("page_end"),
                    "section_title": payload.get("section_title"),
                },
                "distance": getattr(p, "score", None),
            }
        )
    return hits


def delete_document_chunks(document_id: int):
    global _COLLECTION_READY

    # Collection existence check without guessing vector size
    if not _COLLECTION_READY:
        existing = [c.name for c in client.get_collections().collections]
        if COLLECTION_NAME not in existing:
            logger.info(f"[Qdrant] Collection not found: {COLLECTION_NAME}")
            return
        _COLLECTION_READY = True

    client.delete(
        collection_name=COLLECTION_NAME,
        points_selector=qmodels.Filter(
            must=[
                qmodels.FieldCondition(
                    key="document_id",
                    match=qmodels.MatchValue(value=document_id),
                )
            ]
        ),
    )
    logger.info(f"[Qdrant] Deleted chunks for document_id={document_id}")
