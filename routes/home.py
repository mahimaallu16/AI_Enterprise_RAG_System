"""
routes/home.py
---------------
Renders the main dashboard page. All AI/business logic lives in services;
this blueprint only handles page rendering.
"""

from flask import Blueprint, render_template

from config import validate_config
from utils.decorators import login_required

home_bp = Blueprint("home", __name__)


@home_bp.route("/")
@login_required
def index():
    warnings = validate_config()
    return render_template("index.html", config_warnings=warnings)


@home_bp.route("/upload-page")
@login_required
def upload_page():
    """Standalone upload page (the main dashboard also has an Upload tab)."""
    return render_template("upload.html")


@home_bp.route("/chat-page")
@login_required
def chat_page():
    """Standalone chat page (the main dashboard also has a Chat tab)."""
    return render_template("chat.html")
