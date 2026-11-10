"""
services/text_cleaner.py
--------------------------
Normalizes raw extracted text before it is chunked and embedded.

Cleaning happens BEFORE splitting so chunk boundaries are computed on
clean text, and BEFORE embedding so vectors aren't polluted by PDF
extraction artifacts (broken hyphenation, repeated whitespace, control
characters, etc.).
"""

import re


def clean_text(raw_text: str) -> str:
    """Apply a pipeline of cleaning steps to a block of extracted text."""
    if not raw_text:
        return ""

    text = raw_text

    # Remove non-printable / control characters (keep newlines and tabs).
    text = re.sub(r"[^\x09\x0A\x0D\x20-\x7E\u00A0-\uFFFF]", "", text)

    # Fix hyphenation split across a line break, e.g. "informa-\ntion" -> "information"
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)

    # Collapse 3+ newlines into a single paragraph break.
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Collapse repeated spaces/tabs (but keep newlines intact).
    text = re.sub(r"[ \t]{2,}", " ", text)

    # Trim trailing whitespace on each line.
    text = "\n".join(line.strip() for line in text.split("\n"))

    return text.strip()


def is_meaningful(text: str, min_chars: int = 10) -> bool:
    """Filter out chunks that are essentially empty/whitespace/noise."""
    return bool(text) and len(text.strip()) >= min_chars
