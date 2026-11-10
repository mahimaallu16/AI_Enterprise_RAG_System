"""
routes/api.py
---------------
General-purpose API endpoints: dashboard statistics, token usage/cost
dashboard, and a health check used for uptime monitoring.
"""

from flask import Blueprint, jsonify

from services import document_registry
from services.vector_store import collection_stats
from utils.token_counter import usage_tracker
from utils.helpers import success_response
from utils.decorators import login_required
from config import validate_config

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/stats", methods=["GET"])
@login_required
def stats():
    """Statistics for the dashboard's stat cards."""
    doc_stats = document_registry.stats()
    vector_stats = collection_stats()
    return jsonify(
        success_response(
            data={
                **doc_stats,
                **vector_stats,
            }
        )
    )


@api_bp.route("/usage", methods=["GET"])
@login_required
def usage():
    """Token usage + cost estimation dashboard (bonus feature)."""
    return jsonify(success_response(data=usage_tracker.summary()))


@api_bp.route("/health", methods=["GET"])
def health():
    warnings = validate_config()
    return jsonify(success_response(data={"status": "ok", "warnings": warnings}))
