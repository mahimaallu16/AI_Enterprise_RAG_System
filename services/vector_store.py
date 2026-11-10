"""
services/vector_store.py
---------------------------
Wraps ChromaDB so the rest of the app never touches the Chroma client
directly. Responsible for: adding chunks, similarity search (cosine),
deleting a document's vectors, and reporting collection statistics.
"""

from typing import List, Optional

import chromadb
from chromadb.config import Settings

from config import Config
from models.document import Chunk
from services.embedding_service import embed_texts, embed_query
from utils.logger import get_logger

logger = get_logger(__name__)

_client = None
_collection = None


def _get_client():
    global _client
    if _client is None:
        Config.ensure_directories()
        _client = chromadb.PersistentClient(
            path=Config.CHROMA_PERSIST_DIR,
            settings=Settings(anonymized_telemetry=False),
        )
    return _client


def get_collection():
    """Get (or create) the single Chroma collection used by this app.

    cosine similarity is set explicitly via hnsw:space so retrieval scores
    are directly comparable/interpretable in the UI.
    """
    global _collection
    if _collection is None:
        client = _get_client()
        _collection = client.get_or_create_collection(
            name=Config.COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def add_chunks(chunks: List[Chunk]) -> int:
    """Embed and store a list of chunks in the vector store. Returns count added."""
    if not chunks:
        return 0

    collection = get_collection()
    texts = [c.text for c in chunks]
    vectors = embed_texts(texts)

    collection.add(
        ids=[c.chunk_id for c in chunks],
        embeddings=vectors,
        documents=texts,
        metadatas=[c.to_metadata() for c in chunks],
    )
    logger.info("Added %d chunks to vector store", len(chunks))
    return len(chunks)


def similarity_search(query: str, top_k: Optional[int] = None) -> List[dict]:
    """
    Run a cosine similarity search for `query` and return the top_k matches.

    Each result dict has: text, metadata, distance, similarity (1 - distance).
    """
    top_k = top_k or Config.TOP_K
    collection = get_collection()

    if collection.count() == 0:
        return []

    query_vector = embed_query(query)
    results = collection.query(
        query_embeddings=[query_vector],
        n_results=min(top_k, collection.count()),
    )

    matches = []
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    dists = results.get("distances", [[]])[0]

    for text, meta, dist in zip(docs, metas, dists):
        matches.append(
            {
                "text": text,
                "metadata": meta,
                "distance": dist,
                "similarity": max(0.0, 1.0 - dist),
            }
        )
    return matches


def delete_document(doc_id: str) -> int:
    """Delete all chunks belonging to a given document. Returns count deleted."""
    collection = get_collection()
    existing = collection.get(where={"doc_id": doc_id})
    ids = existing.get("ids", [])
    if ids:
        collection.delete(ids=ids)
        logger.info("Deleted %d chunks for doc_id=%s", len(ids), doc_id)
    return len(ids)


def collection_stats() -> dict:
    """Return basic counts used by the dashboard's statistics cards."""
    collection = get_collection()
    total_chunks = collection.count()

    doc_ids = set()
    if total_chunks:
        all_meta = collection.get()["metadatas"]
        doc_ids = {m.get("doc_id") for m in all_meta if m}

    return {"total_chunks": total_chunks, "total_documents_in_index": len(doc_ids)}


def reset_collection() -> None:
    """Wipe the entire collection (used by 'refresh embeddings' / dev resets)."""
    global _collection
    client = _get_client()
    try:
        client.delete_collection(Config.COLLECTION_NAME)
    except Exception:
        pass
    _collection = None
    get_collection()
    logger.warning("Vector store collection reset")
