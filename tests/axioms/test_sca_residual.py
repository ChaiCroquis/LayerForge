"""A2: SCA axioms (docs/04 §T2)."""
from __future__ import annotations

import numpy as np
import pytest

from layerforge.constants import (
    PURITY_THRESHOLD_ACCEPTABLE,
    PURITY_THRESHOLD_GOOD,
    SCA_DEFAULT_ALPHA,
    SCA_DEFAULT_MAX_ITER,
    SCA_DEFAULT_MIN_CLUSTER_SIZE,
    SCA_DEFAULT_MIN_SAMPLES,
    SCA_DEFAULT_MU,
    SCA_DEFAULT_NC_S,
    SCA_DEFAULT_NC_THRESHOLD,
    SCA_DEFAULT_RN_THRESHOLD,
    SCA_DEFAULT_THETA,
)
from layerforge.core.distillation import (
    compute_activations,
    compute_layer_purity,
    detect_giant_clusters,
    distill_layer,
    merge_overlapping_components,
    single_decomposition_step,
)
from layerforge.schema.input_schema import Node
from layerforge.schema.output_schema import DistillationResult


def _make_nodes(n: int) -> tuple[Node, ...]:
    return tuple(
        Node(id=f"n{i:03d}", text=f"sample text token{i} alpha beta gamma word{i}")
        for i in range(n)
    )


# -------- T2.1 component norms --------

def test_components_are_unit_vectors():
    np.random.seed(0)
    centers = np.random.randn(3, 32) * 5
    X = np.concatenate([c + np.random.randn(20, 32) * 0.3 for c in centers])
    nodes = _make_nodes(len(X))
    distillation = distill_layer(nodes, X, min_cluster_size=5, min_samples=2)
    for v in distillation.components:
        assert abs(np.linalg.norm(v) - 1.0) < 1e-6


# -------- T2.2 merging --------

def test_merging_by_token_overlap():
    np.random.seed(0)
    v_a = np.random.randn(8)
    v_a /= np.linalg.norm(v_a)
    v_b = np.random.randn(8)
    v_b /= np.linalg.norm(v_b)
    v_c = np.random.randn(8)
    v_c /= np.linalg.norm(v_c)
    components = [v_a, v_b, v_c]
    token_reps = [
        {"foo", "bar", "baz", "qux", "alpha", "beta", "gamma", "delta", "eps", "zeta"},
        {"foo", "bar", "baz", "qux", "alpha", "x1", "x2", "x3", "x4", "x5"},
        {"y1", "y2", "y3", "y4", "y5", "y6", "y7", "y8", "y9", "y10"},
    ]
    merged_comp, merged_tokens = merge_overlapping_components(
        components, token_reps, theta=0.4
    )
    assert len(merged_comp) == 2
    assert "foo" in merged_tokens[0]
    assert "y1" in merged_tokens[1]


def test_merging_no_overlap_means_no_merge():
    np.random.seed(0)
    v1 = np.random.randn(8)
    v1 /= np.linalg.norm(v1)
    components = [v1, v1.copy()]
    distinct_tokens = [
        {f"a{i}" for i in range(10)},
        {f"b{i}" for i in range(10)},
    ]
    merged_comp, _ = merge_overlapping_components(
        components, distinct_tokens, theta=0.5
    )
    assert len(merged_comp) == 2


# -------- T2.3 conditional activation --------

def test_conditional_activation_below_threshold():
    x = np.array([0.0, 1.0, 0.0])
    v = np.array([1.0, 0.0, 0.0])
    acts = compute_activations(np.array([x]), [v], mu=0.95, alpha=0.20)
    assert acts[0, 0] == 0.0


def test_activation_value_when_above_threshold():
    x = np.array([0.8, 0.6, 0.0])
    v = np.array([1.0, 0.0, 0.0])
    acts = compute_activations(np.array([x]), [v], mu=0.95, alpha=0.20)
    expected = 0.95 * np.dot(x, v)
    assert abs(acts[0, 0] - expected) < 1e-6


# -------- T2.4 residual after decomposition --------

def test_residual_after_decomposition():
    np.random.seed(42)
    x = np.random.randn(64)
    v = np.random.randn(64)
    v /= np.linalg.norm(v)
    mu = 0.95
    alpha = 0.20
    alpha_ij = np.dot(x, v) / np.linalg.norm(x)
    if alpha_ij > alpha:
        expected = x - mu * np.dot(x, v) * v
    else:
        expected = x.copy()
    result = single_decomposition_step(x, v, mu=mu, alpha=alpha)
    np.testing.assert_allclose(result, expected, atol=1e-6)


def test_decomposition_full_mu_makes_residual_orthogonal():
    np.random.seed(0)
    x = np.random.randn(64)
    v = np.random.randn(64)
    v /= np.linalg.norm(v)
    # Force decomposition by setting alpha=-1 so condition always true
    x_residual = single_decomposition_step(x, v, mu=1.0, alpha=-1.0)
    assert abs(np.dot(x_residual, v)) < 1e-5


def test_partial_decomposition_with_mu():
    np.random.seed(1)
    x = np.random.randn(64)
    v = np.random.randn(64)
    v /= np.linalg.norm(v)
    mu = 0.5
    x_residual = single_decomposition_step(x, v, mu=mu, alpha=-1.0)
    original = np.dot(x, v)
    residual = np.dot(x_residual, v)
    expected = original * (1 - mu)
    assert abs(residual - expected) < 1e-5


# -------- T2.5 / T2.6 / T2.7 stopping criteria --------

def test_stopping_criterion_max_iter():
    np.random.seed(0)
    X = np.random.randn(40, 16)
    nodes = _make_nodes(len(X))
    d_short = distill_layer(nodes, X, max_iter=1, min_cluster_size=4, min_samples=2)
    d_long = distill_layer(nodes, X, max_iter=10, min_cluster_size=4, min_samples=2)
    assert len(d_short.components) <= len(d_long.components) + 5


def test_stopping_criterion_NC_S_returns_finite_components():
    np.random.seed(0)
    X = np.random.randn(60, 32)
    nodes = _make_nodes(len(X))
    d = distill_layer(
        nodes, X, max_iter=20, nc_s=2, nc_threshold=5,
        min_cluster_size=4, min_samples=2,
    )
    assert len(d.components) < 200


# -------- T2.8 defaults --------

def test_hyperparameter_defaults():
    assert SCA_DEFAULT_MU == 0.95
    assert SCA_DEFAULT_ALPHA == 0.20
    assert SCA_DEFAULT_THETA == 0.5
    assert SCA_DEFAULT_MIN_CLUSTER_SIZE == 100
    assert SCA_DEFAULT_MIN_SAMPLES == 50
    assert SCA_DEFAULT_MAX_ITER == 10
    assert SCA_DEFAULT_NC_S == 2
    assert SCA_DEFAULT_NC_THRESHOLD == 5
    assert SCA_DEFAULT_RN_THRESHOLD == 0.01


# -------- T2.9 determinism --------

def test_distillation_deterministic():
    np.random.seed(0)
    X = np.random.randn(50, 32)
    nodes = _make_nodes(len(X))
    d1 = distill_layer(nodes, X, min_cluster_size=4, min_samples=2, random_state=42)
    d2 = distill_layer(nodes, X, min_cluster_size=4, min_samples=2, random_state=42)
    assert len(d1.components) == len(d2.components)
    for v1, v2 in zip(d1.components, d2.components):
        np.testing.assert_allclose(v1, v2, atol=1e-8)


# -------- T2.10 schema --------

def test_distillation_result_schema():
    np.random.seed(0)
    X = np.random.randn(30, 16)
    nodes = _make_nodes(len(X))
    d = distill_layer(nodes, X, min_cluster_size=4, min_samples=2)
    assert isinstance(d.components, tuple)
    for v in d.components:
        assert v.shape[0] == X.shape[1]
    assert d.activations.shape == (len(X), len(d.components))
    assert d.residuals.shape == X.shape
    assert d.residual_norms.shape == (len(X),)
    assert isinstance(d.token_representations, tuple)
    assert len(d.token_representations) == len(d.components)
    assert all(isinstance(t, frozenset) for t in d.token_representations)
    assert isinstance(d.is_converged, bool)


def test_distillation_result_is_frozen():
    np.random.seed(0)
    X = np.random.randn(20, 8)
    nodes = _make_nodes(len(X))
    d = distill_layer(nodes, X, min_cluster_size=3, min_samples=2)
    with pytest.raises(Exception):
        d.components = ()  # type: ignore[misc]


# -------- T2.11 purity --------

def test_purity_threshold_constants():
    assert PURITY_THRESHOLD_GOOD == 0.7
    assert PURITY_THRESHOLD_ACCEPTABLE == 0.5
    assert PURITY_THRESHOLD_GOOD > PURITY_THRESHOLD_ACCEPTABLE


def test_purity_bounds():
    np.random.seed(0)
    X = np.random.randn(20, 16)
    nodes = _make_nodes(len(X))
    d = distill_layer(nodes, X, min_cluster_size=3, min_samples=2)
    p = compute_layer_purity(d, X)
    assert 0.0 <= p <= 1.0


# -------- T2.13 giant cluster --------

def test_giant_cluster_warning():
    """Synthetic distillation with one giant active component."""
    n = 100
    activations = np.zeros((n, 2))
    activations[:60, 0] = 1.0  # giant: 60% of samples
    activations[:10, 1] = 1.0
    distillation = DistillationResult(
        components=(np.array([1.0, 0.0]), np.array([0.0, 1.0])),
        activations=activations,
        residuals=np.zeros((n, 2)),
        residual_norms=np.zeros(n),
        token_representations=(frozenset(), frozenset()),
        is_converged=True,
    )
    warnings_list = detect_giant_clusters(distillation, threshold_ratio=0.3)
    assert 0 in warnings_list
    assert 1 not in warnings_list
