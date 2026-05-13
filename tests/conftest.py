"""Shared fixtures (docs/04)."""
from __future__ import annotations

import numpy as np
import pytest

from layerforge.schema.input_schema import FormulationInput, Node, ScaleParams


@pytest.fixture
def fixed_seed():
    np.random.seed(42)
    return 42


@pytest.fixture
def synthetic_layered_embeddings(fixed_seed):
    """4 well-separated clusters of 10 nodes each (768-dim)."""
    np.random.seed(42)
    embeds_list = []
    for _ in range(4):
        center = np.random.randn(768) * 10
        cluster = center + np.random.randn(10, 768) * 0.5
        embeds_list.append(cluster)
    return np.concatenate(embeds_list)


@pytest.fixture
def synthetic_layered_formulation(synthetic_layered_embeddings):
    """FormulationInput backed by the layered fixture."""
    from layerforge.core.modularity import build_similarity_matrix
    from layerforge.core.scale_finder import compute_initial_scale

    X = synthetic_layered_embeddings
    nodes = tuple(
        Node(id=f"n{i:03d}", text=f"node {i} text content example", metadata={})
        for i in range(X.shape[0])
    )
    S = build_similarity_matrix(X)
    return FormulationInput(
        nodes=nodes,
        embeddings=X,
        similarity_matrix=S,
        initial_scale=ScaleParams(threshold=compute_initial_scale(S)),
    )


@pytest.fixture
def synthetic_flat_data():
    np.random.seed(42)
    return np.random.randn(40, 768)


@pytest.fixture
def low_dim_two_communities():
    """Tiny 2-community graph for spectral tests."""
    np.random.seed(0)
    a = np.random.randn(8, 16) + np.array([5.0] + [0.0] * 15)
    b = np.random.randn(8, 16) + np.array([-5.0] + [0.0] * 15)
    return np.concatenate([a, b])
