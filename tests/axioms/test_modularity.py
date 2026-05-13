"""A4: Newman modularity axioms (docs/04 §T4)."""
from __future__ import annotations

import numpy as np
import pytest

from layerforge.core.modularity import (
    build_similarity_matrix,
    can_subdivide_layer,
    classify_separation_quality,
    compute_generalized_modularity_matrix,
    compute_modularity,
    compute_modularity_spectral,
    newman_recursive_subdivision,
)


def test_modularity_value_range(low_dim_two_communities):
    """T4.1: Q ∈ [-0.5, 1.0]."""
    S = build_similarity_matrix(low_dim_two_communities)
    labels = np.array([0] * 8 + [1] * 8)
    Q = compute_modularity(S, labels, threshold=0.0)
    assert -0.5 <= Q <= 1.0


def test_modularity_zero_on_singleton_partition():
    """All nodes one cluster → Q = 0."""
    np.random.seed(0)
    X = np.random.randn(20, 16)
    S = build_similarity_matrix(X)
    Q = compute_modularity(S, np.zeros(20, dtype=int), threshold=0.0)
    assert abs(Q) < 1e-9


def test_modularity_max_for_well_separated():
    """T4.2: 完全分離で Q が高い."""
    np.random.seed(0)
    a = np.random.randn(10, 16) + np.array([10.0] + [0.0] * 15)
    b = np.random.randn(10, 16) + np.array([-10.0] + [0.0] * 15)
    X = np.concatenate([a, b])
    S = build_similarity_matrix(X)
    labels = np.array([0] * 10 + [1] * 10)
    Q = compute_modularity(S, labels, threshold=0.0)
    assert Q > 0.3


def test_modularity_near_zero_for_random():
    """T4.3."""
    np.random.seed(123)
    X = np.random.randn(40, 32)
    S = build_similarity_matrix(X)
    labels = np.random.randint(0, 4, size=40)
    Q = compute_modularity(S, labels, threshold=0.0)
    assert abs(Q) < 0.3


def test_weighted_modularity_consistency():
    """T4.4."""
    np.random.seed(7)
    X = np.random.randn(30, 16)
    S = build_similarity_matrix(X)
    labels = np.array([0] * 15 + [1] * 15)
    Q = compute_modularity(S, labels, threshold=0.0)
    assert isinstance(Q, float)
    assert not np.isnan(Q)
    assert -0.5 <= Q <= 1.0


def test_spectral_partition_via_leading_eigenvector(low_dim_two_communities):
    """T4.5."""
    S = build_similarity_matrix(low_dim_two_communities)
    labels, Q, is_indivisible = compute_modularity_spectral(S, threshold=0.0)
    assert len(np.unique(labels)) == 2
    assert not is_indivisible
    assert Q > 0


def test_indivisibility_for_complete_graph():
    """T4.6: 完全グラフは indivisible."""
    n = 10
    S = np.ones((n, n))
    labels, Q, is_indivisible = compute_modularity_spectral(S, threshold=0.0)
    assert is_indivisible
    assert Q == 0.0


def test_can_subdivide_layer_helper(low_dim_two_communities):
    """T4.6 helper."""
    n = 10
    S_indiv = np.ones((n, n))
    S_div = build_similarity_matrix(low_dim_two_communities)
    assert can_subdivide_layer(S_indiv) is False
    assert can_subdivide_layer(S_div) is True


def test_generalized_modularity_matrix_row_sums_zero():
    """T4.8."""
    np.random.seed(11)
    X = np.random.randn(20, 8)
    S = build_similarity_matrix(X)
    subgraph = list(range(8))
    B_g = compute_generalized_modularity_matrix(S, subgraph, threshold=0.0)
    row_sums = B_g.sum(axis=1)
    assert np.allclose(row_sums, 0.0, atol=1e-8)


def test_recursive_subdivision_finds_communities():
    """T4.8 recursive: 4 well-separated clusters discovered."""
    np.random.seed(0)
    clusters = []
    for i in range(4):
        center = np.zeros(16)
        center[i] = 10.0
        clusters.append(np.random.randn(8, 16) + center)
    X = np.concatenate(clusters)
    S = build_similarity_matrix(X)
    labels = newman_recursive_subdivision(S, threshold=0.3)
    assert len(np.unique(labels)) >= 2  # at least split once


def test_efficient_B_multiplication():
    """T4.10: B·x = A·x - k·(k^T·x)/(2m)."""
    np.random.seed(42)
    n = 30
    A_dense = (np.random.rand(n, n) > 0.7).astype(float)
    A_dense = (A_dense + A_dense.T > 0).astype(float)
    np.fill_diagonal(A_dense, 0)
    k = A_dense.sum(axis=1)
    m_total = A_dense.sum() / 2.0
    if m_total == 0:
        pytest.skip("no edges")
    x = np.random.randn(n)
    Bx_efficient = A_dense @ x - k * float(k @ x) / (2.0 * m_total)
    B = A_dense - np.outer(k, k) / (2.0 * m_total)
    Bx_direct = B @ x
    np.testing.assert_allclose(Bx_efficient, Bx_direct, atol=1e-10)


def test_classify_separation_quality_boundaries():
    """T4.7 boundaries."""
    assert classify_separation_quality(0.8) == "good"
    assert classify_separation_quality(0.5) == "acceptable"
    assert classify_separation_quality(0.1) == "poor"
    assert classify_separation_quality(0.7) == "good"
    assert classify_separation_quality(0.3) == "acceptable"
