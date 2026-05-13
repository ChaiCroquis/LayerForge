"""A3: Cowan 4±1 axioms (docs/04 §T3)."""
from __future__ import annotations

import numpy as np
import pytest

from layerforge.constants import (
    LAYER_COUNT_MAX,
    LAYER_COUNT_MIN,
    LAYER_COUNT_OPTIMAL,
    MAX_RECURSION_DEPTH,
)
from layerforge.core.modularity import build_similarity_matrix
from layerforge.core.scale_finder import (
    find_valid_scale,
    is_layer_count_valid,
)
from layerforge.exceptions import NoValidScaleError


def test_layer_count_constants():
    """T3.1: 4±1 = [3, 5], optimal = 4."""
    assert LAYER_COUNT_MIN == 3
    assert LAYER_COUNT_MAX == 5
    assert LAYER_COUNT_OPTIMAL == 4


@pytest.mark.parametrize("n,expected", [
    (2, False),
    (3, True),
    (4, True),
    (5, True),
    (6, False),
    (10, False),
])
def test_is_layer_count_valid(n, expected):
    """T3.2."""
    assert is_layer_count_valid(n) == expected


def test_scale_search_converges_to_4_plus_minus_1(synthetic_layered_embeddings):
    """T3.3."""
    S = build_similarity_matrix(synthetic_layered_embeddings)
    theta, n_layers = find_valid_scale(S, target_range=(3, 5))
    assert LAYER_COUNT_MIN <= n_layers <= LAYER_COUNT_MAX
    assert -1.0 <= theta <= 1.0


def test_unresolvable_problem_raises():
    """T3.5: when 4±1 cannot be reached, NoValidScaleError is raised.

    A 2-node fully connected matrix yields at most 2 components — outside [3,5].
    """
    S = np.array([[1.0, 0.99], [0.99, 1.0]])
    with pytest.raises(NoValidScaleError):
        find_valid_scale(S, target_range=(3, 5))


def test_max_recursion_depth_constant():
    """T3.6 (constant)."""
    assert MAX_RECURSION_DEPTH == 4
