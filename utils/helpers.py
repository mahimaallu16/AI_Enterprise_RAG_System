"""
utils/helpers.py
-----------------
Small, reusable, stateless helper functions used across services and routes.
Keeping these in one place avoids duplicated logic (per project standards).
"""

import uuid
import re
from datetime import datetime
from typing import Any, Dict


def new_id(prefix: str = "") -> str:
    """Generate a short, unique identifier, optionally namespaced with a prefix."""
    raw = uuid.uuid4().hex[:12]
    return f"{prefix}_{raw}" if prefix else raw


def now_iso() -> str:
    """Current UTC timestamp in ISO-8601 format, used for metadata/logging."""
    return datetime.utcnow().isoformat() + "Z"


def human_file_size(num_bytes: int) -> str:
    """Convert a byte count into a human-readable string (e.g. '1.4 MB')."""
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"


def sanitize_filename(filename: str) -> str:
    """Strip unsafe characters from an uploaded filename before saving to disk."""
    filename = filename.strip().replace(" ", "_")
    filename = re.sub(r"[^A-Za-z0-9._-]", "", filename)
    return filename or new_id("file")


def success_response(data: Any = None, message: str = "OK") -> Dict:
    """Standard shape for successful JSON API responses."""
    return {"success": True, "message": message, "data": data}


def error_response(message: str, code: str = "ERROR") -> Dict:
    """Standard shape for failed JSON API responses."""
    return {"success": False, "message": message, "error_code": code}
