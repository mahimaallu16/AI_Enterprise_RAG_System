"""
services/retriever.py
------------------------
Retrieval layer sitting on top of the vector store. Provides:
  - top-k semantic retrieval
  - optional lightweight keyword re-ranking (hybrid search bonus feature)
  - metadata filtering by document name
"""

from typing import List, Optional

from config import Config
from services.vector_store import similarity_search
from utils.logger import get_logger

logger = get_logger(__name__)


def _keyword_overlap_score(query: str, text: str) -> float:
    """A cheap keyword-overlap score used to nudge semantic ranking (hybrid search)."""
    query_terms = {w.lower() for w in query.split() if len(w) > 2}
    if not query_terms:
        return 0.0
    text_lower = text.lower()
    hits = sum(1 for term in query_terms if term in text_lower)
    return hits / len(query_terms)


def retrieve(
    query: str,
    top_k: Optional[int] = None,
    document_filter: Optional[str] = None,
    hybrid: bool = True,
) -> List[dict]:
    """
    Retrieve the most relevant chunks for `query`.

    Args:
        query: user question.
        top_k: number of chunks to return (defaults to Config.TOP_K).
        document_filter: optional document_name to restrict retrieval to.
        hybrid: if True, blend a keyword-overlap score with semantic similarity.
    """
    top_k = top_k or Config.TOP_K

    # Pull a slightly larger candidate pool than top_k so hybrid re-ranking
    # and metadata filtering have something to work with.
    candidates = similarity_search(query, top_k=max(top_k * 3, top_k))

    if document_filter:
        candidates = [c for c in candidates if c["metadata"].get("document_name") == document_filter]

    if hybrid:
        for c in candidates:
            keyword_score = _keyword_overlap_score(query, c["text"])
            c["combined_score"] = 0.8 * c["similarity"] + 0.2 * keyword_score
        candidates.sort(key=lambda c: c["combined_score"], reverse=True)
    else:
        for c in candidates:
            c["combined_score"] = c["similarity"]
        candidates.sort(key=lambda c: c["combined_score"], reverse=True)

    top = candidates[:top_k]
    logger.info("Retrieved %d chunks for query (hybrid=%s)", len(top), hybrid)
    return top
