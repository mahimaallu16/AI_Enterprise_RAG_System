"""
services/memory.py
---------------------
Simple in-memory conversation store keyed by session_id.

For a production system this would be backed by Redis or a database, but
an in-process dict is sufficient here and keeps the project dependency-free.
Each Flask session (browser tab) gets its own ChatSession so follow-up
questions have conversational context.
"""

from typing import Dict

from models.chat import ChatSession, ChatMessage
from utils.logger import get_logger

logger = get_logger(__name__)

_sessions: Dict[str, ChatSession] = {}


def get_or_create_session(session_id: str) -> ChatSession:
    if session_id not in _sessions:
        _sessions[session_id] = ChatSession(session_id=session_id)
        logger.info("Created new chat session: %s", session_id)
    return _sessions[session_id]


def add_message(session_id: str, message: ChatMessage) -> None:
    session = get_or_create_session(session_id)
    session.add(message)


def get_history_text(session_id: str, max_turns: int = 6) -> str:
    session = get_or_create_session(session_id)
    return session.history_as_text(max_turns=max_turns)


def clear_session(session_id: str) -> None:
    if session_id in _sessions:
        _sessions[session_id] = ChatSession(session_id=session_id)
        logger.info("Cleared chat session: %s", session_id)


def export_session(session_id: str) -> dict:
    """Return the full session as a dict, used by the chat-export bonus feature."""
    return get_or_create_session(session_id).to_dict()
