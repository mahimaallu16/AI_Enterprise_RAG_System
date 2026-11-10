"""
routes/chat.py
----------------
Chat endpoints: ask a question (runs the full RAG pipeline), clear a
session's history, and export chat history (bonus feature).

Conversation memory is scoped per logged-in user: the client-supplied
session_id (one per browser tab) is namespaced under the current username
so that (a) different users never see each other's chat history, and
(b) multiple tabs for the same user can still keep independent threads.
"""

from flask import Blueprint, request, jsonify

from services.rag_pipeline import answer_question, PipelineError
from services.memory import clear_session, export_session
from utils.helpers import success_response, error_response
from utils.decorators import login_required, current_username
from utils.logger import get_logger

logger = get_logger(__name__)

chat_bp = Blueprint("chat", __name__, url_prefix="/api/chat")


def _scoped_session_id(raw_session_id: str) -> str:
    """Namespace a client-provided tab session id under the current user."""
    return f"{current_username()}::{raw_session_id or 'default'}"


@chat_bp.route("/ask", methods=["POST"])
@login_required
def ask():
    payload = request.get_json(silent=True) or {}
    question = (payload.get("question") or "").strip()
    session_id = _scoped_session_id(payload.get("session_id"))
    document_filter = payload.get("document_filter") or None

    if not question:
        return jsonify(error_response("Question cannot be empty.", "EMPTY_QUESTION")), 400

    try:
        result = answer_question(question, session_id, document_filter=document_filter)
        return jsonify(success_response(data=result))
    except PipelineError as e:
        logger.warning("Chat pipeline error: %s", e)
        return jsonify(error_response(str(e), "PIPELINE_ERROR")), 400
    except Exception as e:
        logger.exception("Unexpected chat error")
        return jsonify(error_response(f"Unexpected server error: {e}", "SERVER_ERROR")), 500


@chat_bp.route("/clear", methods=["POST"])
@login_required
def clear():
    payload = request.get_json(silent=True) or {}
    session_id = _scoped_session_id(payload.get("session_id"))
    clear_session(session_id)
    return jsonify(success_response(message="Chat history cleared."))


@chat_bp.route("/export", methods=["GET"])
@login_required
def export():
    session_id = _scoped_session_id(request.args.get("session_id", "default"))
    data = export_session(session_id)
    return jsonify(success_response(data=data))
