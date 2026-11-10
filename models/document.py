"""
models/document.py
-------------------
Data classes representing documents and their chunks as they flow through
the ingestion pipeline (upload -> load -> clean -> split -> embed -> store).

These are plain dataclasses (not a DB ORM) since document metadata itself
lives in ChromaDB alongside the vectors; these classes exist to give the
rest of the codebase typed, well-documented shapes to pass around.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


@dataclass
class Chunk:
    """A single chunk of text produced by the text splitter."""

    chunk_id: str
    doc_id: str
    document_name: str
    page_number: Optional[int]
    text: str
    chunk_index: int

    def to_metadata(self) -> dict:
        """Metadata dict stored alongside the vector in ChromaDB."""
        return {
            "chunk_id": self.chunk_id,
            "doc_id": self.doc_id,
            "document_name": self.document_name,
            "page_number": self.page_number if self.page_number is not None else -1,
            "chunk_index": self.chunk_index,
        }


@dataclass
class Document:
    """Represents an uploaded document and its processing state."""

    doc_id: str
    original_name: str
    stored_path: str
    extension: str
    size_bytes: int
    uploaded_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    status: str = "pending"  # pending | processing | processed | failed
    total_pages: int = 0
    total_chunks: int = 0
    error_message: Optional[str] = None
    chunks: List[Chunk] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "doc_id": self.doc_id,
            "original_name": self.original_name,
            "extension": self.extension,
            "size_bytes": self.size_bytes,
            "uploaded_at": self.uploaded_at,
            "status": self.status,
            "total_pages": self.total_pages,
            "total_chunks": self.total_chunks,
            "error_message": self.error_message,
        }
