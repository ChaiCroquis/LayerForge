"""Input-side schema (docs/05)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Union

import numpy as np
import scipy.sparse as sp


@dataclass(frozen=True)
class RawInput:
    """Entry point — user input or document set."""

    source_type: Literal["text", "document_list", "kdf_query"]
    content: str | list[str]
    metadata: dict | None = None


@dataclass(frozen=True)
class Node:
    """Single semantic unit after parsing."""

    id: str
    text: str
    metadata: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("Node id required")
        if not self.text:
            raise ValueError("Node text required")


@dataclass(frozen=True)
class ScaleParams:
    """Scale coefficient (重力係数の中立用語: ADR-004)."""

    threshold: float
    decay_exponent: float = 1.0
    kernel_type: str = "cosine"


@dataclass(frozen=True)
class FormulationInput:
    """Input to deterministic core (output of Boundary 1).

    ``similarity_matrix`` may be a dense ndarray or a scipy.sparse matrix;
    the deterministic core dispatches accordingly. Sparse is used for
    n ≳ 5,000 to avoid the O(n²) dense memory cost.
    """

    nodes: tuple[Node, ...]
    embeddings: np.ndarray
    similarity_matrix: Union[np.ndarray, "sp.spmatrix"]
    initial_scale: ScaleParams

    def __post_init__(self) -> None:
        n = len(self.nodes)
        if self.embeddings.shape[0] != n:
            raise ValueError(
                f"embeddings rows {self.embeddings.shape[0]} != n_nodes {n}"
            )
        if tuple(self.similarity_matrix.shape) != (n, n):
            raise ValueError(
                f"similarity_matrix shape {self.similarity_matrix.shape} != ({n},{n})"
            )
