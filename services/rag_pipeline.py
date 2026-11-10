"""
services/rag_pipeline.py
---------------------------
Orchestrates the end-to-end pipelines:

  Ingestion:  file -> load -> clean -> split -> embed -> store -> registry
  Query:      question -> embed -> retrieve -> build prompt -> Google Gemini ->
              grounded answer + citations

Route handlers should only ever call functions from this module for the
actual AI logic (per project requirement: "avoid writing AI logic inside
route files").
"""

from typing import Optional

from models.document import Document
from services import document_registry
from services.document_loader import load_document, DocumentLoadError
from services.text_splitter import split_pages_into_chunks
from services.vector_store import add_chunks, delete_document as vector_delete_document
from services.retriever import retrieve
from services.citation_service import build_citations, format_citations_for_prompt
from services.llm_service import build_context_block, generate_answer, generate_document_summary
from services.memory import get_history_text, add_message
from models.chat import ChatMessage
from utils.file_handler import save_file, delete_file, FileValidationError
from utils.logger import get_logger

logger = get_logger(__name__)


class PipelineError(Exception):
    """Raised for any user-facing pipeline failure (upload or query side)."""


# ---------------------------------------------------------------------------
# Ingestion pipeline
# ---------------------------------------------------------------------------

def ingest_file(file, generate_summary: bool = True) -> Document:
    """
    Full ingestion pipeline for a single uploaded file.

    Steps: validate+save -> load -> split -> embed+store -> register.
    Raises PipelineError with a user-friendly message on any failure.
    """
    try:
        saved = save_file(file)
    except FileValidationError as e:
        raise PipelineError(str(e)) from e

    document = Document(
        doc_id=saved["doc_id"],
        original_name=saved["original_name"],
        stored_path=saved["stored_path"],
        extension=saved["extension"],
        size_bytes=saved["size_bytes"],
        status="processing",
    )
    document_registry.register(document)

    try:
        pages = load_document(document.stored_path, document.extension)
        chunks = split_pages_into_chunks(pages, document.doc_id, document.original_name)

        if not chunks:
            raise PipelineError("Document produced no usable text chunks.")

        add_chunks(chunks)

        document.total_pages = len(pages)
        document.total_chunks = len(chunks)
        document.status = "processed"

        if generate_summary:
            try:
                full_text = "\n".join(p[0] for p in pages)
                document.error_message = None
                summary = generate_document_summary(full_text)
                document_registry.update(document.doc_id, status="processed", total_pages=document.total_pages,
                                          total_chunks=document.total_chunks)
                document.summary = summary  # dynamic attribute, safe on dataclass instance
            except Exception:
                logger.warning("Summary generation skipped (Gemini unavailable)")

        document_registry.update(
            document.doc_id,
            status="processed",
            total_pages=document.total_pages,
            total_chunks=document.total_chunks,
        )
        logger.info("Successfully ingested '%s'", document.original_name)
        return document

    except (DocumentLoadError, PipelineError) as e:
        document_registry.update(document.doc_id, status="failed", error_message=str(e))
        raise PipelineError(str(e)) from e
    except Exception as e:
        logger.exception("Unexpected ingestion failure for %s", document.original_name)
        document_registry.update(document.doc_id, status="failed", error_message=str(e))
        raise PipelineError(f"Unexpected error while processing document: {e}") from e


def delete_document_everywhere(doc_id: str) -> bool:
    """Remove a document's vectors, its file on disk, and its registry entry."""
    doc = document_registry.get(doc_id)
    if not doc:
        return False

    vector_delete_document(doc_id)
    delete_file(doc.stored_path)
    document_registry.remove(doc_id)
    logger.info("Removed document '%s' (%s) from system", doc.original_name, doc_id)
    return True


# ---------------------------------------------------------------------------
# Query pipeline
# ---------------------------------------------------------------------------

def answer_question(
    question: str,
    session_id: str,
    document_filter: Optional[str] = None,
    top_k: Optional[int] = None,
) -> dict:
    """
    Full RAG query pipeline: retrieve -> build prompt -> Gemini -> citations.

    Returns a dict: {answer, citations, retrieved_chunks, usage}
    """
    if not question or not question.strip():
        raise PipelineError("Question cannot be empty.")

    retrieved = retrieve(question, top_k=top_k, document_filter=document_filter)

    if not retrieved:
        answer_text = "I don't know based on the provided documents."
        add_message(session_id, ChatMessage(role="user", content=question))
        add_message(session_id, ChatMessage(role="assistant", content=answer_text))
        return {
            "answer": answer_text,
            "citations": [],
            "retrieved_chunks": [],
            "usage": {"input_tokens": 0, "output_tokens": 0},
        }

    citations = build_citations(retrieved)
    context_block = build_context_block(retrieved)
    citation_list = format_citations_for_prompt(citations)
    history = get_history_text(session_id)

    try:
        result = generate_answer(
            question=question, history=history, context=context_block, citation_list=citation_list
        )
    except RuntimeError as e:
        # Missing API key or Gemini configuration errors.
        raise PipelineError(str(e)) from e
    except Exception as e:
        logger.exception("Gemini call failed")
        raise PipelineError(f"The language model request failed: {e}") from e

    add_message(session_id, ChatMessage(role="user", content=question))
    add_message(
        session_id,
        ChatMessage(role="assistant", content=result["answer"], citations=citations),
    )

    return {
        "answer": result["answer"],
        "citations": [c.to_dict() for c in citations],
        "retrieved_chunks": [
            {
                "text": c["text"][:300],
                "document_name": c["metadata"].get("document_name"),
                "page_number": None if c["metadata"].get("page_number") == -1 else c["metadata"].get("page_number"),
                "similarity": round(c["similarity"], 4),
            }
            for c in retrieved
        ],
        "usage": {"input_tokens": result["input_tokens"], "output_tokens": result["output_tokens"]},
    }
