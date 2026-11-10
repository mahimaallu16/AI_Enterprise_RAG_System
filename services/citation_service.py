"""
services/citation_service.py
-------------------------------
Builds Citation objects (document name, page number, chunk id, snippet)
from raw retrieval results, and renders them for display in the chat UI.
"""

from typing import List

from models.chat import Citation


def build_citations(retrieved_chunks: List[dict], snippet_length: int = 220) -> List[Citation]:
    """Convert raw retriever output into structured, de-duplicated Citation objects."""
    citations: List[Citation] = []
    seen_chunk_ids = set()

    for chunk in retrieved_chunks:
        meta = chunk.get("metadata", {})
        chunk_id = meta.get("chunk_id", "unknown")
        if chunk_id in seen_chunk_ids:
            continue
        seen_chunk_ids.add(chunk_id)

        text = chunk.get("text", "")
        snippet = (text[:snippet_length] + "...") if len(text) > snippet_length else text
        page_number = meta.get("page_number")
        if page_number == -1:
            page_number = None

        citations.append(
            Citation(
                document_name=meta.get("document_name", "Unknown document"),
                page_number=page_number,
                chunk_id=chunk_id,
                snippet=snippet,
                score=chunk.get("combined_score", chunk.get("similarity", 0.0)),
            )
        )
    return citations


def format_citations_for_prompt(citations: List[Citation]) -> str:
    """Render citations as a numbered reference list to embed in the LLM prompt."""
    lines = []
    for i, c in enumerate(citations, start=1):
        page_str = f", page {c.page_number}" if c.page_number else ""
        lines.append(f"[{i}] {c.document_name}{page_str} (chunk {c.chunk_id})")
    return "\n".join(lines)
