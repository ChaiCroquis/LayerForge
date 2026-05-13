"""Embedding clients (Phase 2a).

Default is sentence-transformers `paraphrase-multilingual-mpnet-base-v2`,
matching the SCA reference impl (example.py:42).
"""
from __future__ import annotations

import hashlib
from typing import Protocol

import numpy as np


class EmbeddingClient(Protocol):
    """Contract used by `parse_to_structure`."""

    def embed(self, texts: list[str]) -> np.ndarray: ...


class SentenceTransformersEmbedding:
    """Local, deterministic embedding via sentence-transformers.

    Models loaded on first use, then cached. `convert_to_numpy=True` and
    `show_progress_bar=False` keep the call deterministic and quiet.
    """

    def __init__(
        self,
        model_name: str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
        device: str | None = None,
        normalize: bool = True,
    ) -> None:
        self.model_name = model_name
        self.device = device
        self.normalize = normalize
        self._model = None

    def _load(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer  # type: ignore

            self._model = SentenceTransformer(self.model_name, device=self.device)
        return self._model

    def embed(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, 0), dtype=float)
        model = self._load()
        vecs = model.encode(
            texts,
            convert_to_numpy=True,
            show_progress_bar=False,
            normalize_embeddings=self.normalize,
        )
        return np.asarray(vecs, dtype=float)


class HashEmbedding:
    """Deterministic hash-based pseudo-embedding for offline tests / no-deps mode."""

    def __init__(self, dim: int = 64) -> None:
        self.dim = dim

    def embed(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, self.dim), dtype=float)
        out = np.zeros((len(texts), self.dim), dtype=float)
        for i, t in enumerate(texts):
            for tok in t.lower().split():
                h = int(hashlib.sha1(tok.encode("utf-8")).hexdigest(), 16)
                out[i, h % self.dim] += 1.0
        norms = np.linalg.norm(out, axis=1, keepdims=True)
        safe = np.where(norms == 0, 1.0, norms)
        return out / safe
