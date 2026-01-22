import os
from dotenv import load_dotenv
from typing import List, Dict
import chromadb
from chromadb.config import Settings

from backend.services.llm_provider import embed_texts as provider_embed_texts

load_dotenv()

# Persist locally (Create folder)
CHROMA_DIR = "backend/storage/chroma"
COLLECTION_NAME = "insightai_chunks"

os.makedirs(CHROMA_DIR, exist_ok=True)

chroma_client = chromadb.PersistentClient(
    path=CHROMA_DIR,
    settings=Settings(anonymized_telemetry=False),
)
collection = chroma_client.get_or_create_collection(name=COLLECTION_NAME)


def upsert_document_chunks(document_id: int, chunks: List[Dict]):
    """
    chunks: list of dicts like:
      {
        "id": <chunk_db_id or unique id>,
        "text": "...",
        "metadata": { ... }
      }
    """
    if not chunks:
        return

    ids = [f"doc{document_id}_chunk{c['id']}" for c in chunks]
    texts = [c["text"] for c in chunks]
    metadatas = [{
        **c.get("metadata", {}),
        "document_id": document_id,
        "keywords": ", ".join(c["keywords"]) if "keywords" in c else ""
    } for c in chunks]

    embeddings = provider_embed_texts(texts)

    collection.upsert(
        ids=ids,
        documents=texts,
        metadatas=metadatas,
        embeddings=embeddings,
    )


def query_similar_chunks(document_id: int, query: str, k: int = 5) -> List[Dict]:
    """Return top-k chunks (text + metadata) for a document_id."""
    q_emb = provider_embed_texts([query])[0]

    response = collection.query(
        query_embeddings=[q_emb],
        n_results=k,
        where={"document_id": document_id},
        include=["documents", "metadatas", "distances"],
    )

    hits = []
    for i in range(len(response["ids"][0])):
        hits.append({
            "id": response["ids"][0][i],
            "text": response["documents"][0][i],
            "metadata": response["metadatas"][0][i],
            "distance": response["distances"][0][i],
        })
    return hits


def delete_document_chunks(document_id: int):
    """Delete all chunks for a document."""
    collection.delete(where={"document_id": document_id})
