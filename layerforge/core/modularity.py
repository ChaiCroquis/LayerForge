"""Newman modularity Q and spectral algorithm (F4).

Reference: Newman (2006) PNAS 103(23):8577-8582.
"""
from __future__ import annotations

from typing import Union

import numpy as np
import scipy.sparse as sp

from layerforge.constants import (
    MODULARITY_THRESHOLD_ACCEPTABLE,
    MODULARITY_THRESHOLD_GOOD,
)


SimilarityMatrix = Union[np.ndarray, sp.spmatrix]


def _adjacency(
    similarity_matrix: SimilarityMatrix, threshold: float
) -> SimilarityMatrix:
    """Threshold similarity to {0,1} adjacency (diagonal zeroed).

    Returns dense ndarray for dense input, sparse csr_matrix for sparse input.
    """
    if sp.issparse(similarity_matrix):
        # Filter stored entries only — `> threshold` on sparse densifies
        # whenever threshold < 0 (implicit zeros become True).
        coo = similarity_matrix.tocoo()
        mask = (coo.data > threshold) & (coo.row != coo.col)
        return sp.csr_matrix(
            (coo.data[mask].astype(float), (coo.row[mask], coo.col[mask])),
            shape=similarity_matrix.shape,
        )
    A = (similarity_matrix > threshold).astype(float)
    np.fill_diagonal(A, 0.0)
    return A


def compute_modularity(
    similarity_matrix: SimilarityMatrix,
    cluster_labels: np.ndarray,
    threshold: float = 0.0,
) -> float:
    """Multi-community modularity Q (F4.2).

    Q = (1/2m) Σ_ij [A_ij - k_i k_j / 2m] δ(c_i, c_j)

    Accepts dense ndarray or scipy.sparse matrices; both yield the same Q.
    """
    if similarity_matrix.shape[0] != similarity_matrix.shape[1]:
        raise ValueError("similarity_matrix must be square")
    if len(cluster_labels) != similarity_matrix.shape[0]:
        raise ValueError("cluster_labels length mismatch")

    A = _adjacency(similarity_matrix, threshold)
    is_sparse = sp.issparse(A)
    if is_sparse:
        k = np.asarray(A.sum(axis=1)).ravel()
        m_total = float(A.sum()) / 2.0
    else:
        k = A.sum(axis=1)
        m_total = A.sum() / 2.0
    if m_total == 0.0:
        return 0.0

    labels = np.asarray(cluster_labels)
    Q = 0.0
    for label in np.unique(labels):
        idx = np.where(labels == label)[0]
        if idx.size == 0:
            continue
        if is_sparse:
            sub_A = A[idx, :][:, idx]
            sub_A_sum = float(sub_A.sum())
        else:
            sub_A_sum = float(A[np.ix_(idx, idx)].sum())
        sub_k_sum = float(k[idx].sum())
        Q += sub_A_sum - (sub_k_sum ** 2) / (2.0 * m_total)
    return float(Q / (2.0 * m_total))


def _modularity_matrix(A: np.ndarray) -> np.ndarray:
    k = A.sum(axis=1)
    m_total = A.sum() / 2.0
    if m_total == 0.0:
        return np.zeros_like(A)
    return A - np.outer(k, k) / (2.0 * m_total)


def compute_modularity_spectral(
    similarity_matrix: np.ndarray,
    threshold: float = 0.0,
) -> tuple[np.ndarray, float, bool]:
    """Newman's spectral partitioning (F4.3).

    Returns:
        (labels, Q, is_indivisible)
    """
    A = _adjacency(similarity_matrix, threshold)
    n = A.shape[0]
    m_total = A.sum() / 2.0
    if m_total == 0.0:
        return np.zeros(n, dtype=int), 0.0, True

    B = _modularity_matrix(A)
    eigvals, eigvecs = np.linalg.eigh(B)
    # eigh returns ascending; take largest at -1
    beta_1 = float(eigvals[-1])
    u_1 = eigvecs[:, -1]

    if beta_1 <= 0:
        return np.zeros(n, dtype=int), 0.0, True

    labels = (u_1 > 0).astype(int)
    # Edge case: degenerate partition (all on one side) → indivisible
    if labels.sum() == 0 or labels.sum() == n:
        return np.zeros(n, dtype=int), 0.0, True

    Q = compute_modularity(similarity_matrix, labels, threshold)
    return labels, Q, False


def compute_generalized_modularity_matrix(
    similarity_matrix: np.ndarray,
    subgraph_indices: list[int] | tuple[int, ...] | np.ndarray,
    threshold: float = 0.0,
) -> np.ndarray:
    """Newman 2006 Eq. 6: B^(g)_ij = B_ij - δ_ij · Σ_{k∈g} B_ik.

    Row/column sums of the returned matrix are zero.
    """
    A = _adjacency(similarity_matrix, threshold)
    B = _modularity_matrix(A)
    idx = np.asarray(list(subgraph_indices), dtype=int)
    sub_B = B[np.ix_(idx, idx)]
    row_sums = sub_B.sum(axis=1)
    return sub_B - np.diag(row_sums)


def can_subdivide_layer(
    similarity_matrix: np.ndarray,
    threshold: float = 0.0,
) -> bool:
    """F4.9: True iff leading eigenvalue of modularity matrix > 0."""
    _, _, is_indivisible = compute_modularity_spectral(similarity_matrix, threshold)
    return not is_indivisible


def newman_recursive_subdivision(
    similarity_matrix: np.ndarray,
    threshold: float = 0.0,
    max_communities: int | None = None,
) -> np.ndarray:
    """Recursive spectral partitioning using generalized modularity matrix.

    Stops when subgraphs become indivisible (β_1 ≤ 0).
    """
    n = similarity_matrix.shape[0]
    labels = np.zeros(n, dtype=int)
    next_label = 1
    # Stack of (indices_belonging_to_current_subgraph)
    stack: list[np.ndarray] = [np.arange(n)]

    while stack:
        idx = stack.pop()
        if idx.size < 2:
            continue
        if max_communities is not None and (np.unique(labels).size >= max_communities):
            break

        sub_sim = similarity_matrix[np.ix_(idx, idx)]
        # Use generalized modularity matrix for the subgraph
        A = _adjacency(sub_sim, threshold)
        m_total = A.sum() / 2.0
        if m_total == 0.0:
            continue
        sub_B = _modularity_matrix(A)
        # apply the δ_ij · row_sum correction (Eq. 6)
        row_sums = sub_B.sum(axis=1)
        Bg = sub_B - np.diag(row_sums)

        eigvals, eigvecs = np.linalg.eigh(Bg)
        beta_1 = float(eigvals[-1])
        if beta_1 <= 1e-12:
            continue
        u_1 = eigvecs[:, -1]
        split = u_1 > 0
        if split.sum() == 0 or split.sum() == idx.size:
            continue

        left = idx[~split]
        right = idx[split]
        labels[right] = next_label
        next_label += 1
        stack.append(left)
        stack.append(right)

    return labels


def classify_separation_quality(Q: float) -> str:
    """F4.7: classify modularity into good/acceptable/poor."""
    if Q >= MODULARITY_THRESHOLD_GOOD:
        return "good"
    if Q >= MODULARITY_THRESHOLD_ACCEPTABLE:
        return "acceptable"
    return "poor"


def build_similarity_matrix(embeddings: np.ndarray) -> np.ndarray:
    """Cosine similarity matrix. Numerically stable for zero-norm rows.

    Dense, O(n²) memory. For n ≳ 30,000 use ``build_sparse_similarity_matrix``.
    """
    if embeddings.ndim != 2:
        raise ValueError("embeddings must be 2-D")
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    safe = np.where(norms == 0, 1.0, norms)
    normalized = embeddings / safe
    S = normalized @ normalized.T
    # Clip floating noise
    return np.clip(S, -1.0, 1.0)


def build_sparse_similarity_matrix(
    embeddings: np.ndarray,
    top_k: int = 50,
    chunk_size: int = 1024,
) -> sp.csr_matrix:
    """Sparse top-k cosine kNN similarity, symmetrized.

    For each row, keeps the ``top_k`` highest-similarity off-diagonal entries.
    Then symmetrizes via element-wise max(A, A.T) so the graph is undirected.
    Memory: O(n × top_k); compute: O(n²·d) but chunked so peak memory is
    O(chunk_size × n).

    Suitable for n in roughly [5,000, 200,000]. Beyond ~200K, switch to an
    approximate-kNN library (e.g. faiss, NMSLIB) — out of scope here.
    """
    if embeddings.ndim != 2:
        raise ValueError("embeddings must be 2-D")
    n = embeddings.shape[0]
    if n == 0:
        return sp.csr_matrix((0, 0), dtype=float)

    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    safe = np.where(norms == 0, 1.0, norms)
    normalized = (embeddings / safe).astype(np.float32)

    k_plus = min(top_k + 1, n)  # +1 to budget the self-match drop

    rows_list: list[np.ndarray] = []
    cols_list: list[np.ndarray] = []
    vals_list: list[np.ndarray] = []

    for start in range(0, n, chunk_size):
        end = min(start + chunk_size, n)
        chunk = normalized[start:end]                        # (m, d)
        sims = chunk @ normalized.T                          # (m, n)
        np.clip(sims, -1.0, 1.0, out=sims)
        # For each row pick the top k_plus indices.
        if k_plus < n:
            idx_part = np.argpartition(-sims, k_plus - 1, axis=1)[:, :k_plus]
        else:
            idx_part = np.tile(np.arange(n), (end - start, 1))
        m = end - start
        row_ids = np.repeat(np.arange(start, end), idx_part.shape[1])
        col_ids = idx_part.ravel()
        vals = sims[np.repeat(np.arange(m), idx_part.shape[1]), col_ids]
        # Drop self-pairs.
        mask = row_ids != col_ids
        rows_list.append(row_ids[mask])
        cols_list.append(col_ids[mask])
        vals_list.append(vals[mask])

    rows = np.concatenate(rows_list)
    cols = np.concatenate(cols_list)
    data = np.concatenate(vals_list)
    sparse = sp.csr_matrix((data, (rows, cols)), shape=(n, n), dtype=float)
    # Symmetrize: union of A and A^T (keep the larger value for each pair).
    sparse = sparse.maximum(sparse.T)
    return sparse
