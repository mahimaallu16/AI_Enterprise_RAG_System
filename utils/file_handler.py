"""
utils/file_handler.py
----------------------
Validates and saves uploaded files. Keeps upload-route code thin by
centralizing all file-system + validation concerns here.
"""

import os
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

from config import Config
from utils.helpers import new_id
from utils.logger import get_logger

logger = get_logger(__name__)


class FileValidationError(Exception):
    """Raised when an uploaded file fails validation."""


def allowed_file(filename: str) -> bool:
    """Check the file extension against the whitelist in Config."""
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in Config.ALLOWED_EXTENSIONS


def get_extension(filename: str) -> str:
    return filename.rsplit(".", 1)[1].lower() if "." in filename else ""


def validate_file(file: FileStorage) -> None:
    """
    Validate an incoming file before it touches disk.

    Raises FileValidationError with a user-friendly message on any problem.
    """
    if file is None or file.filename == "":
        raise FileValidationError("No file was selected.")

    if not allowed_file(file.filename):
        allowed = ", ".join(sorted(Config.ALLOWED_EXTENSIONS))
        raise FileValidationError(
            f"Unsupported file type for '{file.filename}'. Allowed types: {allowed}."
        )

    # Determine size without loading the whole file into memory.
    file.stream.seek(0, os.SEEK_END)
    size = file.stream.tell()
    file.stream.seek(0)

    if size == 0:
        raise FileValidationError(f"'{file.filename}' is empty.")

    if size > Config.MAX_CONTENT_LENGTH:
        max_mb = Config.MAX_CONTENT_LENGTH // (1024 * 1024)
        raise FileValidationError(f"'{file.filename}' exceeds the {max_mb} MB size limit.")


def save_file(file: FileStorage) -> dict:
    """
    Validate then persist an uploaded file to the upload folder.

    Returns metadata about the saved file: id, original name, stored path,
    extension, and size in bytes.
    """
    validate_file(file)

    Config.ensure_directories()

    original_name = secure_filename(file.filename)
    doc_id = new_id("doc")
    ext = get_extension(original_name)
    stored_name = f"{doc_id}.{ext}"
    stored_path = os.path.join(Config.UPLOAD_FOLDER, stored_name)

    file.save(stored_path)
    size = os.path.getsize(stored_path)

    logger.info("Saved upload '%s' -> %s (%d bytes)", original_name, stored_path, size)

    return {
        "doc_id": doc_id,
        "original_name": original_name,
        "stored_path": stored_path,
        "extension": ext,
        "size_bytes": size,
    }


def delete_file(stored_path: str) -> bool:
    """Delete a stored file from disk. Returns True if it existed and was removed."""
    if stored_path and os.path.exists(stored_path):
        os.remove(stored_path)
        logger.info("Deleted file from disk: %s", stored_path)
        return True
    return False
