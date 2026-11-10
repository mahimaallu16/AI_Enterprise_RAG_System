"""
utils/token_counter.py
-----------------------
Approximate token counting for Gemini usage.

Tiktoken is only an approximation for Gemini, so a ~4-characters-per-token
heuristic is used as a fallback. The selected model is intended for Gemini's
free tier; actual access and quotas depend on the Google AI Studio account.
"""

try:
    import tiktoken
    _ENCODER = tiktoken.get_encoding("cl100k_base")
except Exception:  # pragma: no cover - fallback if tiktoken/model not available
    _ENCODER = None

def count_tokens(text: str) -> int:
    """Estimate the number of tokens in a string of text."""
    if not text:
        return 0
    if _ENCODER is not None:
        try:
            return len(_ENCODER.encode(text))
        except Exception:
            pass
    # Fallback heuristic: ~4 characters per token.
    return max(1, len(text) // 4)


def estimate_cost(input_tokens: int, output_tokens: int) -> float:
    """Estimate cost for the configured free-tier Gemini model."""
    return 0.0


class UsageTracker:
    """
    In-memory running total of token usage for the session.

    A simple singleton-style tracker used to power the token usage dashboard.
    Not persisted across restarts by design (keeps things simple/stateless).
    """

    def __init__(self) -> None:
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_requests = 0

    def record(self, input_tokens: int, output_tokens: int) -> None:
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_requests += 1

    def summary(self) -> dict:
        cost = estimate_cost(self.total_input_tokens, self.total_output_tokens)
        return {
            "total_requests": self.total_requests,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
            "estimated_cost_usd": cost,
        }


# Shared instance imported by services/routes.
usage_tracker = UsageTracker()
