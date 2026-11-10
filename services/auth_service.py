"""
services/auth_service.py
---------------------------
Simulated authentication for the Enterprise RAG demo.

This is intentionally simple: an in-memory user store (seeded with a couple
of demo accounts) with hashed passwords via Werkzeug's security helpers.
There's no real database — swapping this for a proper user table later
only requires changing this one file, since routes/auth.py only calls the
functions defined here.
"""

import threading
from typing import Dict, Optional

from werkzeug.security import generate_password_hash, check_password_hash

from models.user import User
from utils.logger import get_logger

logger = get_logger(__name__)

_lock = threading.Lock()
_users: Dict[str, User] = {}


def _seed_demo_users() -> None:
    """Seed a couple of ready-to-use demo accounts so the app is testable
    immediately without a signup step."""
    demo_accounts = [
        ("admin", "admin123", "Administrator", "admin"),
        ("demo", "demo123", "Demo User", "user"),
    ]
    for username, password, display_name, role in demo_accounts:
        _users[username] = User(
            username=username,
            password_hash=generate_password_hash(password),
            display_name=display_name,
            role=role,
        )
    logger.info("Seeded %d demo user account(s)", len(demo_accounts))


_seed_demo_users()


class AuthError(Exception):
    """Raised for any user-facing authentication failure."""


def register_user(username: str, password: str, display_name: Optional[str] = None) -> User:
    """Create a new simulated user account. Raises AuthError on conflict/invalid input."""
    username = (username or "").strip().lower()
    if not username or not password:
        raise AuthError("Username and password are required.")
    if len(password) < 6:
        raise AuthError("Password must be at least 6 characters long.")

    with _lock:
        if username in _users:
            raise AuthError(f"Username '{username}' is already taken.")

        user = User(
            username=username,
            password_hash=generate_password_hash(password),
            display_name=display_name or username.title(),
        )
        _users[username] = user
        logger.info("Registered new user: %s", username)
        return user


def verify_credentials(username: str, password: str) -> User:
    """Validate a login attempt. Raises AuthError with a generic message on failure."""
    username = (username or "").strip().lower()
    user = _users.get(username)
    if not user or not check_password_hash(user.password_hash, password or ""):
        # Deliberately generic message — never reveal whether the username exists.
        raise AuthError("Invalid username or password.")
    return user


def get_user(username: str) -> Optional[User]:
    return _users.get((username or "").strip().lower())
