"""
routes/auth.py
----------------
Login, logout, and registration for the simulated user-session system.
Session state is Flask's signed cookie session (server-side "who is this"
is just `session['username']`) — simple and sufficient for a demo/bonus
feature, not intended as a hardened multi-tenant auth system.
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify

from services.auth_service import verify_credentials, register_user, AuthError
from utils.decorators import _is_safe_next_path
from utils.helpers import success_response, error_response
from utils.logger import get_logger

logger = get_logger(__name__)

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        if "username" in session:
            return redirect(url_for("home.index"))
        next_path = request.args.get("next")
        return render_template("login.html", next_path=next_path, mode="login")

    # POST
    username = (request.form.get("username") or "").strip()
    password = request.form.get("password") or ""
    next_path = request.form.get("next")

    try:
        user = verify_credentials(username, password)
    except AuthError as e:
        return render_template("login.html", error=str(e), mode="login", next_path=next_path, prefill_username=username), 401

    session["username"] = user.username
    session["display_name"] = user.display_name
    session["role"] = user.role
    logger.info("User logged in: %s", user.username)

    if next_path and _is_safe_next_path(next_path):
        return redirect(next_path)
    return redirect(url_for("home.index"))


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        if "username" in session:
            return redirect(url_for("home.index"))
        return render_template("login.html", mode="register")

    username = (request.form.get("username") or "").strip()
    password = request.form.get("password") or ""
    display_name = (request.form.get("display_name") or "").strip()

    try:
        user = register_user(username, password, display_name)
    except AuthError as e:
        return render_template("login.html", error=str(e), mode="register", prefill_username=username), 400

    session["username"] = user.username
    session["display_name"] = user.display_name
    session["role"] = user.role
    logger.info("New user registered and logged in: %s", user.username)
    return redirect(url_for("home.index"))


@auth_bp.route("/logout", methods=["GET", "POST"])
def logout():
    username = session.get("username")
    session.clear()
    if username:
        logger.info("User logged out: %s", username)
    return redirect(url_for("auth.login"))


@auth_bp.route("/api/auth/me", methods=["GET"])
def me():
    """Small JSON endpoint the frontend can poll to check current session state."""
    if "username" not in session:
        return jsonify(error_response("Not authenticated.", "UNAUTHENTICATED")), 401
    return jsonify(
        success_response(
            data={
                "username": session["username"],
                "display_name": session.get("display_name"),
                "role": session.get("role"),
            }
        )
    )
