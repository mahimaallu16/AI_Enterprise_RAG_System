"""
tests/test_embeddings.py
--------------------------
Tests for the embedding service. These download/load the real
sentence-transformers model on first run, so they are slower than the
other test modules; mark with @pytest.mark.slow if you wire up markers
in CI.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from services.embedding_service import embed_texts, embed_query


def test_embed_query_returns_vector():
    vector = embed_query("What is retrieval-augmented generation?")
    assert isinstance(vector, list)
    assert len(vector) > 0
    assert all(isinstance(x, float) for x in vector[:5])


def test_embed_texts_returns_one_vector_per_input():
    texts = ["Enterprise RAG platform", "Vector databases store embeddings", "Gemini is a large language model"]
    vectors = embed_texts(texts)
    assert len(vectors) == len(texts)
    # all vectors should have the same dimensionality
    dims = {len(v) for v in vectors}
    assert len(dims) == 1


def test_embeddings_are_normalized():
    """We enable normalize_embeddings=True so cosine similarity behaves well."""
    import math

    vector = embed_query("normalization test")
    norm = math.sqrt(sum(x * x for x in vector))
    assert abs(norm - 1.0) < 0.05
