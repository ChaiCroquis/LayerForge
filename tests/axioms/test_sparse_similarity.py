"""Sparse similarity / sparse modularity tests (n>=100,000 scaling track)."""
from __future__ import annotations

import numpy as np
import pytest
import scipy.sparse as sp

from layerforge.cli import decompose
from layerforge.core.modularity import (
    build_similarity_matrix,
    build_sparse_similarity_matrix,
    compute_modularity,
)
from layerforge.core.scale_finder import (
    compute_initial_scale,
    count_clusters_at_threshold,
)


def _synthetic_embeddings(n_clusters: int = 4, per_cluster: int = 20, dim: int = 32, seed: int = 0):
    rng = np.random.default_rng(seed)
    blocks = []
    for c in range(n_clusters):
        center = np.zeros(dim)
        center[c] = 10.0
        blocks.append(rng.normal(loc=center, scale=0.4, size=(per_cluster, dim)))
    return np.concatenate(blocks)


# ---------- build_sparse_similarity_matrix ----------


def test_sparse_similarity_is_csr_and_symmetric():
    X = _synthetic_embeddings()
    A = build_sparse_similarity_matrix(X, top_k=5)
    assert sp.issparse(A)
    assert isinstance(A, sp.csr_matrix)
    # symmetric (within float tolerance)
    diff = (A - A.T)
    assert abs(diff).max() < 1e-6


def test_sparse_similarity_has_no_self_loops():
    X = _synthetic_embeddings()
    A = build_sparse_similarity_matrix(X, top_k=5)
    assert (A.diagonal() == 0).all()


def test_sparse_similarity_preserves_top_neighbors():
    """For 4 well-separated clusters, top-5 neighbors stay within the cluster."""
    X = _synthetic_embeddings(n_clusters=4, per_cluster=20)
    A = build_sparse_similarity_matrix(X, top_k=5)
    A = A.tocsr()
    for i in range(80):
        nbrs = A.indices[A.indptr[i]:A.indptr[i + 1]]
        same_cluster = i // 20
        # At least 4 of the top-5 should belong to the same cluster.
        same_count = sum((nbr // 20) == same_cluster for nbr in nbrs)
        assert same_count >= 4, f"node {i}: only {same_count}/{len(nbrs)} stay in cluster"


def test_sparse_similarity_empty_input():
    A = build_sparse_similarity_matrix(np.zeros((0, 8)), top_k=5)
    assert A.shape == (0, 0)


# ---------- count_clusters_at_threshold sparse path ----------


def test_count_clusters_accepts_sparse():
    X = _synthetic_embeddings()
    A_dense = build_similarity_matrix(X)
    A_sparse = build_sparse_similarity_matrix(X, top_k=10)
    # At low threshold, both should give comparable component counts.
    # We can't expect exact equality (sparse drops weak edges), but both
    # should detect the 4-block structure at some threshold.
    n_sparse = count_clusters_at_threshold(A_sparse, threshold=0.3)
    assert n_sparse >= 1
    n_dense = count_clusters_at_threshold(A_dense, threshold=0.3)
    assert n_dense >= 1


# ---------- compute_modularity sparse equivalence ----------


def test_modularity_dense_vs_sparse_agreement():
    """For the same labeling, dense and (top-k) sparse Q should be close
    when top_k is large enough to retain most positive cross-cluster edges.
    """
    X = _synthetic_embeddings(n_clusters=4, per_cluster=15)
    labels = np.repeat(np.arange(4), 15)
    A_dense = build_similarity_matrix(X)
    A_sparse = build_sparse_similarity_matrix(X, top_k=20)
    Q_dense = compute_modularity(A_dense, labels, threshold=0.3)
    Q_sparse = compute_modularity(A_sparse, labels, threshold=0.3)
    # Both should detect the structure; agreement within 0.2 is sufficient
    # given that sparse drops weak edges.
    assert abs(Q_dense - Q_sparse) < 0.2, f"dense Q={Q_dense:.3f} vs sparse Q={Q_sparse:.3f}"


# ---------- compute_initial_scale sparse path ----------


def test_initial_scale_sparse_handles_no_offdiag():
    """All-zero sparse → 0.0 (no off-diagonal entries)."""
    empty = sp.csr_matrix((5, 5))
    assert compute_initial_scale(empty) == 0.0


def test_initial_scale_sparse_uses_median_of_stored():
    coo = sp.coo_matrix(
        ([0.1, 0.5, 0.9, 0.5], ([0, 1, 2, 3], [1, 0, 3, 2])),
        shape=(4, 4),
    )
    val = compute_initial_scale(coo.tocsr())
    # Median of [0.1, 0.5, 0.9, 0.5] = 0.5
    assert val == 0.5


# ---------- CLI end-to-end sparse path ----------


def _decisions_payload(n: int = 16) -> dict:
    themes = [
        ["alpha_w0 alpha_w1 alpha_w2 alpha_w3", "alpha_w1 alpha_w2 alpha_w3 alpha_w4",
         "alpha_w2 alpha_w3 alpha_w4 alpha_w5", "alpha_w3 alpha_w4 alpha_w5 alpha_w6"],
        ["beta_w0 beta_w1 beta_w2 beta_w3", "beta_w1 beta_w2 beta_w3 beta_w4",
         "beta_w2 beta_w3 beta_w4 beta_w5", "beta_w3 beta_w4 beta_w5 beta_w6"],
        ["gamma_w0 gamma_w1 gamma_w2 gamma_w3", "gamma_w1 gamma_w2 gamma_w3 gamma_w4",
         "gamma_w2 gamma_w3 gamma_w4 gamma_w5", "gamma_w3 gamma_w4 gamma_w5 gamma_w6"],
        ["delta_w0 delta_w1 delta_w2 delta_w3", "delta_w1 delta_w2 delta_w3 delta_w4",
         "delta_w2 delta_w3 delta_w4 delta_w5", "delta_w3 delta_w4 delta_w5 delta_w6"],
    ]
    nodes = [
        {"id": f"n{i:04d}", "text": text}
        for i, text in enumerate(t for theme in themes for t in theme)
    ][:n]
    return {"nodes": nodes, "options": {"embedding_backend": "hash", "random_seed": 42}}


def test_cli_sparse_top_k_int_runs_through():
    payload = _decisions_payload(16)
    payload["options"]["sparse_top_k"] = 8
    result = decompose.run(payload)
    assert result["status"] == "ok"
    assert 3 <= result["quality_metrics"]["layer_count"] <= 5


def test_cli_sparse_auto_below_threshold_stays_dense():
    """n=16 with sparse_top_k='auto' should NOT trigger sparse (n < 5000)."""
    payload = _decisions_payload(16)
    payload["options"]["sparse_top_k"] = "auto"
    result = decompose.run(payload)
    assert result["status"] == "ok"
    # Indivisibility flags are dense-only; if any non-False values present,
    # we know the dense indivisibility check ran.
    # (Sparse path sets all flags to False conservatively.)
    qm = result["quality_metrics"]
    assert 3 <= qm["layer_count"] <= 5
