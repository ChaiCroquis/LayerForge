"""Phase 2a — embedding client tests."""
from __future__ import annotations

import numpy as np
import pytest

from layerforge.inference.embedding import HashEmbedding, SentenceTransformersEmbedding


# ----- HashEmbedding -----


def test_hash_embedding_deterministic():
    e = HashEmbedding(dim=32)
    a = e.embed(["alpha beta", "gamma delta"])
    b = e.embed(["alpha beta", "gamma delta"])
    np.testing.assert_array_equal(a, b)


def test_hash_embedding_normalized():
    e = HashEmbedding(dim=32)
    a = e.embed(["alpha beta gamma"])
    np.testing.assert_allclose(np.linalg.norm(a, axis=1), 1.0, atol=1e-10)


def test_hash_embedding_empty_input():
    e = HashEmbedding(dim=32)
    a = e.embed([])
    assert a.shape == (0, 32)


# ----- SentenceTransformersEmbedding (skipped if dep missing) -----


def _st_available() -> bool:
    try:
        import sentence_transformers  # noqa: F401

        return True
    except ImportError:
        return False


@pytest.mark.skipif(not _st_available(), reason="sentence-transformers not installed")
def test_sentence_transformers_smoke():
    e = SentenceTransformersEmbedding(
        model_name="sentence-transformers/paraphrase-MiniLM-L3-v2",
    )
    vecs = e.embed(["alpha beta", "gamma delta"])
    assert vecs.shape[0] == 2
    assert vecs.shape[1] > 0
    np.testing.assert_allclose(np.linalg.norm(vecs, axis=1), 1.0, atol=1e-5)
