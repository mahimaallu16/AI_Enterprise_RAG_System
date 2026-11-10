"""
models/user.py
---------------
Simple user dataclass for the simulated authentication system. This is not
backed by a real database — see services/auth_service.py for the in-memory
user store — but keeping a typed shape here matches the pattern used by
models/document.py and models/chat.py.
"""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class User:
    """Represents an authenticated (or registered) application user."""

    username: str
    password_hash: str
    display_name: str
    role: str = "user"  # "user" | "admin"
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

    def to_dict(self) -> dict:
        """Public-safe representation (never includes the password hash)."""
        return {
            "username": self.username,
            "display_name": self.display_name,
            "role": self.role,
            "created_at": self.created_at,
        }
