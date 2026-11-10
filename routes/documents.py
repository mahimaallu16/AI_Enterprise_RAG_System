"""
routes/documents.py
---------------------
Document library management: list uploaded documents, delete a document
(and its vectors), and refresh/rebuild embeddings.
"""

from flask import Blueprint, jsonify

from services import document_registry
from services.rag_pipeline import delete_document_everywhere, ingest_file, PipelineError
from services.vector_store import reset_collection
from utils.helpers import success_response, error_response
from utils.decorators import login_required
from utils.logger import get_logger

logger = get_logger(__name__)

documents_bp = Blueprint("documents", __name__, url_prefix="/api/documents")


@documents_bp.route("", methods=["GET"])
@login_required
def list_documents():
    docs = [d.to_dict() for d in document_registry.list_all()]
    return jsonify(success_response(data=docs))


@documents_bp.route("/<doc_id>", methods=["DELETE"])
@login_required
def delete_document(doc_id):
    deleted = delete_document_everywhere(doc_id)
    if not deleted:
        return jsonify(error_response("Document not found.", "NOT_FOUND")), 404
    return jsonify(success_response(message="Document deleted."))


@documents_bp.route("/refresh-embeddings", methods=["POST"])
@login_required
def refresh_embeddings():
    """
    Rebuild the entire vector index from files still on disk.

    This is a destructive-but-recoverable operation: it wipes the Chroma
    collection then re-ingests every document currently in the registry.
    """
    docs = document_registry.list_all()
    reset_collection()

    rebuilt, failed = [], []
    for doc in docs:
        old_doc_id = doc.doc_id
        try:
            with open(doc.stored_path, "rb") as f:
                from werkzeug.datastructures import FileStorage
                storage = FileStorage(stream=f, filename=doc.original_name)
                ingest_file(storage, generate_summary=False)
            # ingest_file registers a fresh doc_id; drop the stale registry entry.
            document_registry.remove(old_doc_id)
            rebuilt.append(doc.original_name)
        except (PipelineError, FileNotFoundError, OSError) as e:
            logger.error("Failed to rebuild embeddings for %s: %s", doc.original_name, e)
            failed.append({"name": doc.original_name, "error": str(e)})

    return jsonify(success_response(data={"rebuilt": rebuilt, "failed": failed}))
