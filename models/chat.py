"""
models/chat.py
--------------
Data classes for chat messages, citations, and conversation sessions.
Conversation state is held in memory by services/memory.py; these classes
define the shape of that state.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


@dataclass
class Citation:
    """A single source citation returned alongside an assistant answer."""

    document_name: str
    page_number: Optional[int]
    chunk_id: str
    snippet: str
    score: float = 0.0

    def to_dict(self) -> dict:
        return {
            "document_name": self.document_name,
            "page_number": self.page_number,
            "chunk_id": self.chunk_id,
            "snippet": self.snippet,
            "score": round(self.score, 4),
        }


@dataclass
class ChatMessage:
    """A single turn in a conversation (either 'user' or 'assistant')."""

    role: str  # "user" | "assistant"
    content: str
    citations: List[Citation] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "content": self.content,
            "citations": [c.to_dict() for c in self.citations],
            "timestamp": self.timestamp,
        }


@dataclass
class ChatSession:
    """An in-memory conversation thread, keyed by session_id."""

    session_id: str
    messages: List[ChatMessage] = field(default_factory=list)

    def add(self, message: ChatMessage) -> None:
        self.messages.append(message)

    def history_as_text(self, max_turns: int = 6) -> str:
        """Render the last N turns as plain text for prompt context (memory)."""
        recent = self.messages[-max_turns:]
        lines = []
        for m in recent:
            speaker = "User" if m.role == "user" else "Assistant"
            lines.append(f"{speaker}: {m.content}")
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "messages": [m.to_dict() for m in self.messages],
        }
