"""Output-side schema (docs/05)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np

from layerforge.schema.input_schema import Node


@dataclass(frozen=True)
class DistillationResult:
    """Per-layer SCA distillation (F2.6)."""

    components: tuple[np.ndarray, ...]
    activations: np.ndarray
    residuals: np.ndarray
    residual_norms: np.ndarray
    token_representations: tuple[frozenset[str], ...]
    is_converged: bool


@dataclass(frozen=True)
class LayerSummary:
    """Metadata for a single layer.

    ``children`` and ``depth`` support F3.4 recursive depth (4×4×4×4 = 256
    nodes max). ``children`` is empty when the layer is a leaf (either
    depth == MAX_RECURSION_DEPTH-1, layer is indivisible, or member count
    is below the recursion threshold).
    """

    layer_id: int
    member_indices: tuple[int, ...]
    member_nodes: tuple[Node, ...]
    representation_vector: np.ndarray
    distillation: DistillationResult
    layer_name: str | None = None
    depth: int = 0
    children: tuple["LayerSummary", ...] = ()


@dataclass(frozen=True)
class InterLayerRelation:
    """Relation between two layers."""

    from_layer_id: int
    to_layer_id: int
    relation_type: Literal["contains", "constrains", "specializes"]
    strength: float


@dataclass(frozen=True)
class QualityMetrics:
    """Decomposition quality indicators.

    ``modularity`` is the Newman Q computed on the (thresholded) similarity
    graph, regardless of community-detection method. When CPM was used,
    ``cpm_h`` carries the CPM quality value and ``community_method`` records
    which backend ran. ``scale_coefficient`` is θ for Newman path, γ for CPM.
    """

    modularity: float
    layer_count: int
    scale_coefficient: float
    is_within_4_plus_minus_1: bool
    quality_class: Literal["good", "acceptable", "poor"]
    indivisibility_flags: tuple[bool, ...] = ()
    community_method: Literal["newman", "cpm"] = "newman"
    cpm_h: float | None = None


@dataclass(frozen=True)
class CoreResult:
    """Deterministic core output."""

    layers: tuple[LayerSummary, ...]
    inter_layer_relations: tuple[InterLayerRelation, ...]
    quality_metrics: QualityMetrics


@dataclass(frozen=True)
class NaturalLanguageOutput:
    """Final output (Boundary 2)."""

    text: str
    layer_sections: tuple[str, ...]
    metadata_summary: str
