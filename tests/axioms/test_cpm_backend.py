"""Tests for the self-implemented CPM-Louvain backend.

Covers:
  - Determinism (same seed → same partition)
  - K target_range bisection on γ
  - Theme separation on a known 3-cluster synthetic graph
  - Format parity with the Newman path (output schema unchanged)
  - Failure modes (empty graph, target_range out of reach)
"""
from __future__ import annotations

import numpy as np
import pytest
import scipy.sparse as sp

from layerforge.cli.decompose import run as decompose_run
from layerforge.core.cpm_backend import (
    cpm_partition,
    find_cpm_resolution,
)
from layerforge.exceptions import NoValidScaleError


def _synthetic_3block_similarity(n_per_block: int = 5, intra: float = 0.9, inter: float = 0.05) -> np.ndarray:
    n = 3 * n_per_block
    sim = np.full((n, n), inter, dtype=np.float64)
    for b in range(3):
        s = b * n_per_block
        e = s + n_per_block
        sim[s:e, s:e] = intra
    np.fill_diagonal(sim, 1.0)
    return sim


def test_cpm_partition_separates_three_blocks():
    sim = _synthetic_3block_similarity()
    labels, h, k = cpm_partition(sim, resolution=0.5, seed=42)
    assert k == 3, f"expected 3 communities, got {k}"
    # Each block (5 consecutive nodes) should share a label
    for b in range(3):
        block_labels = labels[b * 5 : (b + 1) * 5]
        assert len(set(block_labels.tolist())) == 1, (
            f"block {b} split: labels={block_labels}"
        )


def test_cpm_partition_deterministic_with_seed():
    sim = _synthetic_3block_similarity()
    l1, h1, k1 = cpm_partition(sim, resolution=0.5, seed=42)
    l2, h2, k2 = cpm_partition(sim, resolution=0.5, seed=42)
    np.testing.assert_array_equal(l1, l2)
    assert h1 == h2
    assert k1 == k2


def test_cpm_partition_different_seeds_may_differ_but_K_stable():
    sim = _synthetic_3block_similarity()
    _, _, k1 = cpm_partition(sim, resolution=0.5, seed=42)
    _, _, k2 = cpm_partition(sim, resolution=0.5, seed=99)
    # K should be stable for the same γ on this well-separated graph
    assert k1 == k2 == 3


def test_cpm_partition_higher_gamma_more_communities():
    sim = _synthetic_3block_similarity()
    _, _, k_low = cpm_partition(sim, resolution=0.01, seed=42)
    _, _, k_high = cpm_partition(sim, resolution=2.0, seed=42)
    assert k_low <= k_high, f"K monotonicity in γ violated: {k_low} vs {k_high}"


def test_cpm_partition_handles_sparse_input():
    sim_dense = _synthetic_3block_similarity()
    sim_sparse = sp.csr_matrix(sim_dense)
    labels_d, h_d, k_d = cpm_partition(sim_dense, resolution=0.5, seed=42)
    labels_s, h_s, k_s = cpm_partition(sim_sparse, resolution=0.5, seed=42)
    assert k_d == k_s
    # Labels may differ in numbering; check partition equivalence by sorted sizes
    sizes_d = sorted(np.bincount(labels_d).tolist())
    sizes_s = sorted(np.bincount(labels_s).tolist())
    assert sizes_d == sizes_s


def test_cpm_partition_empty_graph_returns_singletons():
    n = 5
    sim = np.eye(n)  # only self-loops, no edges after diagonal removal
    labels, h, k = cpm_partition(sim, resolution=0.5, seed=42)
    assert k == n
    assert h == 0.0


def test_find_cpm_resolution_hits_target_range():
    sim = _synthetic_3block_similarity()
    gamma, labels, h, k = find_cpm_resolution(
        sim, target_range=(3, 3), seed=42
    )
    assert k == 3
    assert 0 < gamma < 5.0


def test_find_cpm_resolution_target_range_inclusive():
    sim = _synthetic_3block_similarity()
    gamma, labels, h, k = find_cpm_resolution(
        sim, target_range=(2, 5), seed=42
    )
    assert 2 <= k <= 5


def test_find_cpm_resolution_raises_when_target_unreachable():
    # Tiny graph (3 nodes) cannot have K=10
    sim = np.array([
        [1.0, 0.9, 0.9],
        [0.9, 1.0, 0.9],
        [0.9, 0.9, 1.0],
    ])
    with pytest.raises(NoValidScaleError):
        find_cpm_resolution(sim, target_range=(10, 20), seed=42)


# ---- Integration tests through the CLI ----


def _make_three_theme_nodes() -> list[dict]:
    texts = (
        ["python programming language interpreted dynamic typing"] * 4
        + ["football match goal striker midfielder defender"] * 4
        + ["quantum physics electron wave function entanglement"] * 4
    )
    return [
        {"id": f"n{i:02d}", "text": t + f" instance {i}"}
        for i, t in enumerate(texts)
    ]


def test_cli_cpm_mode_produces_same_schema_as_newman():
    nodes = _make_three_theme_nodes()
    common_opts = {
        "target_layer_count_min": 3,
        "target_layer_count_max": 3,
        "random_seed": 42,
    }
    r_newman = decompose_run({"nodes": nodes, "options": common_opts})
    r_cpm = decompose_run(
        {"nodes": nodes, "options": {**common_opts, "community_method": "cpm"}}
    )

    # Same schema keys
    assert set(r_newman.keys()) == set(r_cpm.keys())
    assert set(r_newman["quality_metrics"].keys()) == set(
        r_cpm["quality_metrics"].keys()
    )

    # Method recorded correctly
    assert r_newman["quality_metrics"]["community_method"] == "newman"
    assert r_cpm["quality_metrics"]["community_method"] == "cpm"

    # cpm_h is None for Newman, float for CPM
    assert r_newman["quality_metrics"]["cpm_h"] is None
    assert isinstance(r_cpm["quality_metrics"]["cpm_h"], float)

    # Both achieve K=3 on this well-separated corpus
    assert r_newman["quality_metrics"]["layer_count"] == 3
    assert r_cpm["quality_metrics"]["layer_count"] == 3


def test_cli_cpm_mode_deterministic():
    nodes = _make_three_theme_nodes()
    opts = {
        "target_layer_count_min": 3,
        "target_layer_count_max": 3,
        "random_seed": 42,
        "community_method": "cpm",
    }
    r1 = decompose_run({"nodes": nodes, "options": opts})
    r2 = decompose_run({"nodes": nodes, "options": opts})
    members_1 = sorted(
        tuple(sorted(layer["member_node_ids"])) for layer in r1["layers"]
    )
    members_2 = sorted(
        tuple(sorted(layer["member_node_ids"])) for layer in r2["layers"]
    )
    assert members_1 == members_2


def test_cli_rejects_invalid_community_method():
    nodes = _make_three_theme_nodes()
    with pytest.raises(ValueError, match="community_method"):
        decompose_run(
            {"nodes": nodes, "options": {"community_method": "louvain"}}
        )


def test_newman_default_when_community_method_unspecified():
    nodes = _make_three_theme_nodes()
    r = decompose_run({"nodes": nodes, "options": {"random_seed": 42}})
    assert r["quality_metrics"]["community_method"] == "newman"
