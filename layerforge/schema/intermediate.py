"""Intermediate data structures used inside the deterministic core."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class FlatHierarchy:
    """Single-level clustering result (LayerForge currently builds one level)."""

    flat_labels: np.ndarray
    centroids: np.ndarray
    member_indices_per_cluster: tuple[tuple[int, ...], ...]


@dataclass(frozen=True)
class ScaleSearchResult:
    """Output of F1.4 binary search."""

    theta: float
    n_clusters: int
    iterations: int
    converged: bool
