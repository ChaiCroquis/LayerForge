"""Scale-coefficient binary search (F1.4).

Searches for a similarity threshold θ such that the resulting graph's
connected-component count falls inside the Cowan 4±1 range.
"""
from __future__ import annotations

import numpy as np
import scipy.sparse as sp
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components

from layerforge.constants import (
    LAYER_COUNT_MAX,
    LAYER_COUNT_MIN,
    SCALE_SEARCH_MAX_ITER,
    SCALE_SEARCH_TOLERANCE,
)
from layerforge.exceptions import NoValidScaleError
from layerforge.schema.intermediate import ScaleSearchResult


def count_clusters_at_threshold(
    similarity_matrix,
    threshold: float,
) -> int:
    """Count connected components when edges with sim > threshold are kept.

    Accepts dense ndarray or scipy.sparse matrices.
    """
    n = similarity_matrix.shape[0]
    if n == 0:
        return 0
    if sp.issparse(similarity_matrix):
        # Filter stored entries only — avoid `> threshold` on sparse, which
        # densifies whenever threshold < 0 (implicit zeros become True).
        coo = similarity_matrix.tocoo()
        mask = (coo.data > threshold) & (coo.row != coo.col)
        if not mask.any():
            return int(n)
        A = sp.csr_matrix(
            (coo.data[mask].astype(np.int8), (coo.row[mask], coo.col[mask])),
            shape=similarity_matrix.shape,
        )
        n_components, _ = connected_components(A, directed=False)
        return int(n_components)
    A = (similarity_matrix > threshold).astype(np.int8)
    np.fill_diagonal(A, 0)
    sparse = csr_matrix(A)
    n_components, _ = connected_components(sparse, directed=False)
    return int(n_components)


def find_valid_scale(
    similarity_matrix: np.ndarray,
    target_range: tuple[int, int] = (LAYER_COUNT_MIN, LAYER_COUNT_MAX),
    initial_theta: float | None = None,
    max_iter: int = SCALE_SEARCH_MAX_ITER,
    tolerance: float = SCALE_SEARCH_TOLERANCE,
) -> tuple[float, int]:
    """F1.4 binary search over the threshold θ.

    Higher θ → fewer edges → more components.
    Returns (theta, n_clusters).
    """
    if similarity_matrix.shape[0] == 0:
        raise NoValidScaleError("empty similarity matrix")

    # For sparse top-k kNN, only positive similarities are stored; binary
    # search over negative θ is meaningless and inefficient.
    lo, hi = (0.0, 1.0) if sp.issparse(similarity_matrix) else (-1.0, 1.0)
    best: tuple[float, int] | None = None

    for _ in range(max_iter):
        mid = (lo + hi) / 2.0 if initial_theta is None else initial_theta
        initial_theta = None  # only used once
        n = count_clusters_at_threshold(similarity_matrix, mid)

        if target_range[0] <= n <= target_range[1]:
            return mid, n

        if n < target_range[0]:
            # Too few clusters — raise threshold (more edges removed → more components)
            lo = mid
        else:
            # Too many clusters — lower threshold (fewer components)
            hi = mid

        if best is None or abs(n - sum(target_range) / 2) < abs(
            best[1] - sum(target_range) / 2
        ):
            best = (mid, n)

        if hi - lo < tolerance:
            break

    # Sparse-safe stats for the diagnostic.
    if sp.issparse(similarity_matrix):
        data = similarity_matrix.data
        stats = {
            "mean_stored": float(np.mean(data)) if data.size else 0.0,
            "std_stored": float(np.std(data)) if data.size else 0.0,
            "nnz": int(similarity_matrix.nnz),
            "sparse": True,
        }
    else:
        stats = {
            "mean": float(np.mean(similarity_matrix)),
            "std": float(np.std(similarity_matrix)),
            "sparse": False,
        }
    raise NoValidScaleError(
        f"No θ in [{lo:.2f}, {hi:.2f}] yields layer count in {target_range}; "
        f"best attempt θ={best[0]:.4f}, n={best[1]}",
        similarity_stats=stats,
    )


def find_valid_scale_detailed(
    similarity_matrix: np.ndarray,
    target_range: tuple[int, int] = (LAYER_COUNT_MIN, LAYER_COUNT_MAX),
    max_iter: int = SCALE_SEARCH_MAX_ITER,
    tolerance: float = SCALE_SEARCH_TOLERANCE,
) -> ScaleSearchResult:
    """Variant returning a structured record."""
    lo, hi = -1.0, 1.0
    last = (0.0, -1)
    for it in range(max_iter):
        mid = (lo + hi) / 2.0
        n = count_clusters_at_threshold(similarity_matrix, mid)
        last = (mid, n)
        if target_range[0] <= n <= target_range[1]:
            return ScaleSearchResult(theta=mid, n_clusters=n, iterations=it + 1, converged=True)
        if n < target_range[0]:
            lo = mid
        else:
            hi = mid
        if hi - lo < tolerance:
            break
    return ScaleSearchResult(
        theta=last[0], n_clusters=last[1], iterations=max_iter, converged=False
    )


def adjust_scale(
    similarity_matrix: np.ndarray,
    initial_theta: float,
    target_range: tuple[int, int] = (LAYER_COUNT_MIN, LAYER_COUNT_MAX),
) -> tuple[float, int]:
    """Convenience wrapper around find_valid_scale starting from initial_theta."""
    return find_valid_scale(similarity_matrix, target_range, initial_theta=initial_theta)


def is_layer_count_valid(n_layers: int) -> bool:
    """F3.2."""
    return LAYER_COUNT_MIN <= n_layers <= LAYER_COUNT_MAX


def compute_initial_scale(similarity_matrix) -> float:
    """Heuristic seed: median of off-diagonal similarities.

    For sparse input, computes the median of stored non-diagonal entries
    (typical for top-k kNN graphs where unstored = 0 implicitly).
    """
    n = similarity_matrix.shape[0]
    if n < 2:
        return 0.0
    if sp.issparse(similarity_matrix):
        coo = similarity_matrix.tocoo()
        mask = coo.row != coo.col
        if not mask.any():
            return 0.0
        return float(np.median(coo.data[mask]))
    mask = ~np.eye(n, dtype=bool)
    return float(np.median(similarity_matrix[mask]))
