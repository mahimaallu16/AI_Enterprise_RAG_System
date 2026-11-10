"""
config.py
---------
Centralized application configuration.

Loads all secrets and tunables from the .env file so that no credentials
or environment-specific values are ever hard-coded in the source tree.
Every other module should import settings from here rather than calling
os.getenv() directly, so we have a single source of truth.
"""

import os
from dotenv import load_dotenv

# Load variables from .env into the process environment as early as possible.
load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Config:
    """Application-wide configuration values."""

    # --- Flask ---
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key")
    DEBUG: bool = os.getenv("FLASK_DEBUG", "True").lower() == "true"
    MAX_CONTENT_LENGTH: int = int(os.getenv("MAX_CONTENT_LENGTH_MB", "25")) * 1024 * 1024

    # --- Gemini LLM ---
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

    # --- Embeddings ---
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

    # --- Storage ---
    UPLOAD_FOLDER: str = os.path.join(BASE_DIR, os.getenv("UPLOAD_FOLDER", "documents/uploaded_files"))
    CHROMA_PERSIST_DIR: str = os.path.join(BASE_DIR, os.getenv("CHROMA_PERSIST_DIR", "database/chroma_db"))
    COLLECTION_NAME: str = os.getenv("COLLECTION_NAME", "enterprise_rag_docs")

    # --- RAG tuning ---
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1000"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "150"))
    TOP_K: int = int(os.getenv("TOP_K", "4"))

    # --- Uploads ---
    ALLOWED_EXTENSIONS = {"pdf", "txt", "md", "markdown", "docx"}

    @staticmethod
    def ensure_directories() -> None:
        """Create required runtime directories if they don't already exist."""
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(Config.CHROMA_PERSIST_DIR, exist_ok=True)


def validate_config() -> list[str]:
    """Return startup warnings for missing Gemini configuration."""
    if not Config.GOOGLE_API_KEY or Config.GOOGLE_API_KEY == "your_google_api_key_here":
        return [
            "GOOGLE_API_KEY is not set. Add a Gemini API key from Google AI Studio "
            "to the .env file before using chat."
        ]
    return []
