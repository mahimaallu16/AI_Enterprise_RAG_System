"""
tests/test_retrieval.py
--------------------------
Tests the chunking, vector storage, and retrieval pipeline end-to-end
(without calling the LLM). Uses a temporary Chroma collection so tests
don't pollute the real database directory.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from models.document import Chunk
from services.text_splitter import split_pages_into_chunks
from services import vector_store
from services.retriever import retrieve


@pytest.fixture(autouse=True)
def isolate_collection(tmp_path, monkeypatch):
    """Point the vector store at a fresh temp directory for each test."""
    from config import Config

    monkeypatch.setattr(Config, "CHROMA_PERSIST_DIR", str(tmp_path))
    monkeypatch.setattr(Config, "COLLECTION_NAME", "test_collection")
    vector_store._client = None
    vector_store._collection = None
    yield
    vector_store._client = None
    vector_store._collection = None


def test_split_pages_into_chunks_preserves_metadata():
    pages = [("This is page one content about enterprise search.", 1),
             ("This is page two content about vector databases.", 2)]
    chunks = split_pages_into_chunks(pages, doc_id="doc123", document_name="test.pdf")
    assert len(chunks) >= 2
    assert all(isinstance(c, Chunk) for c in chunks)
    assert chunks[0].document_name == "test.pdf"
    assert chunks[0].page_number == 1


def test_add_chunks_and_similarity_search():
    pages = [
        ("Enterprise RAG platforms combine retrieval with generation.", 1),
        ("Bananas are a good source of potassium and fiber.", 1),
    ]
    chunks = split_pages_into_chunks(pages, doc_id="docA", document_name="mixed.txt")
    added = vector_store.add_chunks(chunks)
    assert added == len(chunks)

    results = vector_store.similarity_search("What is RAG used for?", top_k=1)
    assert len(results) == 1
    assert "retrieval" in results[0]["text"].lower() or "rag" in results[0]["text"].lower()


def test_delete_document_removes_its_chunks():
    pages = [("Some deletable content for testing removal.", 1)]
    chunks = split_pages_into_chunks(pages, doc_id="docDel", document_name="delete_me.txt")
    vector_store.add_chunks(chunks)

    deleted_count = vector_store.delete_document("docDel")
    assert deleted_count == len(chunks)

    stats = vector_store.collection_stats()
    assert stats["total_chunks"] == 0


def test_retrieve_returns_empty_list_when_collection_empty():
    results = retrieve("anything at all")
    assert results == []
