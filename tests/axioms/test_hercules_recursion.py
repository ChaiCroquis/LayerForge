"""A1: HERCULES axioms (docs/04 §T1)."""
from __future__ import annotations

import numpy as np

from layerforge.core.hierarchical import hierarchical_kmeans


def test_kmeans_deterministic(synthetic_layered_embeddings):
    """T1.4: random_state 固定で完全再現."""
    h1 = hierarchical_kmeans(synthetic_layered_embeddings, k=4, random_state=42)
    h2 = hierarchical_kmeans(synthetic_layered_embeddings, k=4, random_state=42)
    np.testing.assert_array_equal(h1.flat_labels, h2.flat_labels)
    for c1, c2 in zip(h1.layers, h2.layers):
        assert c1.member_indices == c2.member_indices


def test_representation_vector_equals_mean_of_members(synthetic_layered_embeddings):
    """T1.3 direct mode: rep_vector(parent) = mean(members)."""
    X = synthetic_layered_embeddings
    h = hierarchical_kmeans(X, k=4, random_state=42, use_resampling=False)
    for layer in h.layers:
        members = X[list(layer.member_indices)]
        expected = members.mean(axis=0)
        np.testing.assert_allclose(layer.representation_vector, expected, rtol=1e-5)


def test_all_nodes_covered(synthetic_layered_embeddings):
    """T1.2: 全ノードがいずれかのクラスタに割り当てられる."""
    X = synthetic_layered_embeddings
    h = hierarchical_kmeans(X, k=4, random_state=42)
    covered = sorted(i for layer in h.layers for i in layer.member_indices)
    assert covered == list(range(X.shape[0]))


def test_canonical_label_ordering(synthetic_layered_embeddings):
    """Canonical labels are dense [0..k-1]."""
    X = synthetic_layered_embeddings
    h = hierarchical_kmeans(X, k=4, random_state=42)
    assert set(np.unique(h.flat_labels).tolist()) == set(range(4))
