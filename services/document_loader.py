"""
services/document_loader.py
-----------------------------
Loads raw text + page-level metadata out of uploaded files.

Supports PDF, TXT, Markdown, and DOCX (bonus). Each loader returns a list
of (text, page_number) tuples so downstream splitting can preserve page
numbers for citations, regardless of source format.
"""

from typing import List, Tuple

from langchain_community.document_loaders import PyPDFLoader, TextLoader

from services.text_cleaner import clean_text
from utils.logger import get_logger

logger = get_logger(__name__)


class DocumentLoadError(Exception):
    """Raised when a document cannot be read/parsed."""


def _load_pdf(path: str) -> List[Tuple[str, int]]:
    """Load a PDF, returning cleaned text per page with 1-indexed page numbers."""
    loader = PyPDFLoader(path)
    pages = loader.load()
    result = []
    for i, page in enumerate(pages):
        text = clean_text(page.page_content)
        if text:
            result.append((text, i + 1))
    return result


def _load_txt(path: str) -> List[Tuple[str, int]]:
    """Load a plain text file. Text files have no concept of 'pages', so page=1."""
    loader = TextLoader(path, encoding="utf-8", autodetect_encoding=True)
    docs = loader.load()
    text = clean_text("\n".join(d.page_content for d in docs))
    return [(text, 1)] if text else []


def _load_markdown(path: str) -> List[Tuple[str, int]]:
    """Load a Markdown file as plain text (rendered structure isn't needed for RAG)."""
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        raw = f.read()
    text = clean_text(raw)
    return [(text, 1)] if text else []


def _load_docx(path: str) -> List[Tuple[str, int]]:
    """Load a DOCX file paragraph by paragraph (bonus format)."""
    try:
        import docx  # python-docx
    except ImportError as e:
        raise DocumentLoadError(
            "python-docx is required to read .docx files. Install it via requirements.txt."
        ) from e

    doc = docx.Document(path)
    raw = "\n".join(p.text for p in doc.paragraphs)
    text = clean_text(raw)
    return [(text, 1)] if text else []


_LOADERS = {
    "pdf": _load_pdf,
    "txt": _load_txt,
    "md": _load_markdown,
    "markdown": _load_markdown,
    "docx": _load_docx,
}


def load_document(path: str, extension: str) -> List[Tuple[str, int]]:
    """
    Load a document from disk, returning a list of (cleaned_text, page_number).

    Raises DocumentLoadError on unsupported types or parse failures so the
    upload route can surface a meaningful error to the user.
    """
    loader_fn = _LOADERS.get(extension.lower())
    if loader_fn is None:
        raise DocumentLoadError(f"No loader available for extension '.{extension}'.")

    try:
        pages = loader_fn(path)
    except DocumentLoadError:
        raise
    except Exception as e:
        logger.exception("Failed to load document %s", path)
        raise DocumentLoadError(f"Could not parse file: {e}") from e

    if not pages:
        raise DocumentLoadError("No extractable text was found in this document.")

    return pages
