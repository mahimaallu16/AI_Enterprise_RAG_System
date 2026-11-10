"""
services/document_registry.py
--------------------------------
Tracks Document objects (metadata + processing status) across requests.

ChromaDB stores the vectors/chunks themselves, but we still need a place to
track document-level state (status, page/chunk counts, errors, summaries)
for the dashboard's document library and statistics cards. This in-memory
registry is optionally mirrored to a JSON file so it survives app restarts
during local development.
"""

import json
import os
import threading
from typing import Dict, List, Optional

from models.document import Document
from utils.logger import get_logger

logger = get_logger(__name__)

_REGISTRY_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "database", "documents_registry.json"
)

_lock = threading.Lock()
_documents: Dict[str, Document] = {}


def _persist() -> None:
    os.makedirs(os.path.dirname(_REGISTRY_FILE), exist_ok=True)
    with open(_REGISTRY_FILE, "w", encoding="utf-8") as f:
        json.dump({doc_id: doc.to_dict() for doc_id, doc in _documents.items()}, f, indent=2)


def _load() -> None:
    if os.path.exists(_REGISTRY_FILE):
        try:
            with open(_REGISTRY_FILE, "r", encoding="utf-8") as f:
                raw = json.load(f)
            for doc_id, d in raw.items():
                _documents[doc_id] = Document(
                    doc_id=d["doc_id"],
                    original_name=d["original_name"],
                    stored_path="",
                    extension=d.get("extension", ""),
                    size_bytes=d.get("size_bytes", 0),
                    uploaded_at=d.get("uploaded_at", ""),
                    status=d.get("status", "processed"),
                    total_pages=d.get("total_pages", 0),
                    total_chunks=d.get("total_chunks", 0),
                    error_message=d.get("error_message"),
                )
        except Exception:
            logger.exception("Failed to load document registry from disk")


_load()


def register(document: Document) -> None:
    with _lock:
        _documents[document.doc_id] = document
        _persist()


def update(doc_id: str, **fields) -> Optional[Document]:
    with _lock:
        doc = _documents.get(doc_id)
        if not doc:
            return None
        for key, value in fields.items():
            setattr(doc, key, value)
        _persist()
        return doc


def get(doc_id: str) -> Optional[Document]:
    return _documents.get(doc_id)


def get_by_name(name: str) -> Optional[Document]:
    for doc in _documents.values():
        if doc.original_name == name:
            return doc
    return None


def remove(doc_id: str) -> bool:
    with _lock:
        if doc_id in _documents:
            del _documents[doc_id]
            _persist()
            return True
        return False


def list_all() -> List[Document]:
    return sorted(_documents.values(), key=lambda d: d.uploaded_at, reverse=True)


def stats() -> dict:
    docs = list_all()
    total_pages = sum(d.total_pages for d in docs)
    total_chunks = sum(d.total_chunks for d in docs)
    return {
        "total_documents": len(docs),
        "total_pages": total_pages,
        "total_chunks": total_chunks,
        "processed": len([d for d in docs if d.status == "processed"]),
        "failed": len([d for d in docs if d.status == "failed"]),
        "processing": len([d for d in docs if d.status == "processing"]),
    }
