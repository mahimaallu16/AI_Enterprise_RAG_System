"""
app.py
------
Application entry point. Creates the Flask app, registers all blueprints,
wires up global error handlers, and starts the dev server.

Run with:  python app.py
"""

from flask import Flask, jsonify

from config import Config
from utils.logger import get_logger

from routes.auth import auth_bp
from routes.home import home_bp
from routes.upload import upload_bp
from routes.documents import documents_bp
from routes.chat import chat_bp
from routes.api import api_bp

logger = get_logger(__name__)


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = Config.SECRET_KEY
    app.config["MAX_CONTENT_LENGTH"] = Config.MAX_CONTENT_LENGTH

    Config.ensure_directories()

    # Register blueprints (routes separated from business logic, per spec).
    app.register_blueprint(auth_bp)
    app.register_blueprint(home_bp)
    app.register_blueprint(upload_bp)
    app.register_blueprint(documents_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(api_bp)

    @app.errorhandler(413)
    def file_too_large(_e):
        max_mb = Config.MAX_CONTENT_LENGTH // (1024 * 1024)
        return jsonify(success=False, message=f"File exceeds the {max_mb}MB limit."), 413

    @app.errorhandler(404)
    def not_found(_e):
        return jsonify(success=False, message="Resource not found."), 404

    @app.errorhandler(500)
    def server_error(e):
        logger.exception("Unhandled server error")
        return jsonify(success=False, message="Internal server error."), 500

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=Config.DEBUG)
