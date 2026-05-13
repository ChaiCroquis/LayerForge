"""Determinism axioms (docs/04 §TD)."""
from __future__ import annotations

import numpy as np

from layerforge.pipeline import layerforge_core


def test_core_deterministic_same_input(synthetic_layered_formulation):
    """TD.1: 同一入力 → 同一出力."""
    r1 = layerforge_core(synthetic_layered_formulation, seed=42)
    r2 = layerforge_core(synthetic_layered_formulation, seed=42)
    assert r1.quality_metrics.layer_count == r2.quality_metrics.layer_count
    assert r1.quality_metrics.modularity == r2.quality_metrics.modularity
    assert r1.quality_metrics.scale_coefficient == r2.quality_metrics.scale_coefficient
    for l1, l2 in zip(r1.layers, r2.layers):
        assert l1.member_indices == l2.member_indices
        np.testing.assert_allclose(
            l1.representation_vector, l2.representation_vector, atol=1e-10
        )
