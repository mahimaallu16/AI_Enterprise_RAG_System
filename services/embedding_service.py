"""
services/embedding_service.py
--------------------------------
Thin, reusable wrapper around the HuggingFace sentence-transformers
embedding model. Keeping this isolated means:
  1. The model is loaded exactly once (module-level singleton).
  2. Swapping embedding models later only touches this one file.
"""

from typing import List

from langchain_huggingface import HuggingFaceEmbeddings

from config import Config
from utils.logger import get_logger

logger = get_logger(__name__)

_embeddings_instance = None


def get_embedding_function() -> HuggingFaceEmbeddings:
    """
    Lazily instantiate and cache the embedding model.

    Lazy loading avoids paying the (multi-second) model load cost on every
    import (e.g. during tests), only when embeddings are actually needed.
    """
    global _embeddings_instance
    if _embeddings_instance is None:
        logger.info("Loading embedding model: %s", Config.EMBEDDING_MODEL)
        _embeddings_instance = HuggingFaceEmbeddings(
            model_name=Config.EMBEDDING_MODEL,
            encode_kwargs={"normalize_embeddings": True},  # normalize -> cosine similarity works cleanly
        )
    return _embeddings_instance


def embed_texts(texts: List[str]) -> List[List[float]]:
    """Embed a batch of texts (e.g. chunks) into vectors."""
    embedder = get_embedding_function()
    return embedder.embed_documents(texts)


def embed_query(text: str) -> List[float]:
    """Embed a single query string (e.g. a user question) into a vector."""
    embedder = get_embedding_function()
    return embedder.embed_query(text)
