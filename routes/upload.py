"""
routes/upload.py
------------------
Handles multi-file document uploads. Delegates all processing (loading,
cleaning, chunking, embedding, storage) to services.rag_pipeline.
"""

from flask import Blueprint, request, jsonify

from services.rag_pipeline import ingest_file, PipelineError
from utils.helpers import success_response, error_response
from utils.decorators import login_required
from utils.logger import get_logger

logger = get_logger(__name__)

upload_bp = Blueprint("upload", __name__, url_prefix="/api/upload")


@upload_bp.route("", methods=["POST"])
@login_required
def upload_documents():
    """
    Accept one or more files under the 'files' form field and process each
    through the full ingestion pipeline. Partial success is supported: some
    files can succeed while others fail, and both are reported back.
    """
    files = request.files.getlist("files")

    if not files:
        return jsonify(error_response("No files were provided.", "NO_FILES")), 400

    results = []
    for file in files:
        try:
            document = ingest_file(file)
            results.append({"success": True, "document": document.to_dict()})
        except PipelineError as e:
            logger.warning("Upload failed for '%s': %s", getattr(file, "filename", "?"), e)
            results.append(
                {"success": False, "filename": getattr(file, "filename", "unknown"), "error": str(e)}
            )

    any_success = any(r["success"] for r in results)
    status_code = 200 if any_success else 400

    return jsonify(success_response(data=results, message="Upload processed")), status_code
