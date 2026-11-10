"""
services/text_splitter.py
----------------------------
Splits cleaned, page-tagged text into overlapping chunks suitable for
embedding, while preserving document name, page number, and a stable
chunk_id/chunk_index for citations.
"""

from typing import List, Tuple

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:  # older langchain versions bundle it under langchain.text_splitter
    from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import Config
from models.document import Chunk
from utils.helpers import new_id
from utils.logger import get_logger

logger = get_logger(__name__)

_splitter = RecursiveCharacterTextSplitter(
    chunk_size=Config.CHUNK_SIZE,
    chunk_overlap=Config.CHUNK_OVERLAP,
    separators=["\n\n", "\n", ". ", " ", ""],
)


def split_pages_into_chunks(
    pages: List[Tuple[str, int]], doc_id: str, document_name: str
) -> List[Chunk]:
    """
    Turn a list of (page_text, page_number) into a flat list of Chunk objects.

    A stable, incrementing chunk_index is assigned across the whole document
    (not per page) so ordering is preserved for display/debugging.
    """
    chunks: List[Chunk] = []
    chunk_index = 0

    for page_text, page_number in pages:
        pieces = _splitter.split_text(page_text)
        for piece in pieces:
            if not piece.strip():
                continue
            chunk = Chunk(
                chunk_id=new_id("chunk"),
                doc_id=doc_id,
                document_name=document_name,
                page_number=page_number,
                text=piece,
                chunk_index=chunk_index,
            )
            chunks.append(chunk)
            chunk_index += 1

    logger.info("Split '%s' into %d chunks across %d pages", document_name, len(chunks), len(pages))
    return chunks
