"""
utils/decorators.py
----------------------
Route-protection decorator for the simulated login system.

Applied directly to view functions across routes/ so it's obvious, at each
route definition, whether authentication is required — no hidden
blueprint-level magic.
"""

from functools import wraps
from urllib.parse import urlparse

from flask import session, redirect, url_for, request, jsonify

from utils.logger import get_logger

logger = get_logger(__name__)


def _is_safe_next_path(path: str) -> bool:
    """Only allow redirecting back to a relative, in-app path (avoid open redirects)."""
    if not path:
        return False
    parsed = urlparse(path)
    return not parsed.netloc and not parsed.scheme and path.startswith("/")


def login_required(view_func):
    """
    Protect a view. JSON/API routes get a 401 JSON response; page routes get
    redirected to the login page with a `next` parameter to return to.
    """

    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if "username" not in session:
            if request.path.startswith("/api/"):
                return jsonify(success=False, message="Authentication required. Please log in."), 401

            next_path = request.path if _is_safe_next_path(request.path) else None
            return redirect(url_for("auth.login", next=next_path) if next_path else url_for("auth.login"))

        return view_func(*args, **kwargs)

    return wrapped


def current_username() -> str:
    """Convenience accessor used by services that need to scope data per-user."""
    return session.get("username", "anonymous")
