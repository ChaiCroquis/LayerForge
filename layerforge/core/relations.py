"""Inter-layer relation extraction (docs/05)."""
from __future__ import annotations

import numpy as np

from layerforge.core.hierarchical import Hierarchy
from layerforge.schema.output_schema import (
    DistillationResult,
    InterLayerRelation,
    LayerSummary,
)


def extract_inter_layer_relations(
    layers: tuple[LayerSummary, ...],
) -> tuple[InterLayerRelation, ...]:
    """Compute pairwise cosine similarity between layer representation vectors.

    Pairs above a small threshold are emitted as "constrains" with strength
    equal to the cosine similarity. This is a minimal, deterministic relation
    extractor; richer typing is left to Phase 2+.
    """
    relations: list[InterLayerRelation] = []
    n = len(layers)
    if n < 2:
        return tuple(relations)

    reps = np.stack([l.representation_vector for l in layers])
    norms = np.linalg.norm(reps, axis=1, keepdims=True)
    safe = np.where(norms == 0, 1.0, norms)
    normed = reps / safe
    sim = normed @ normed.T

    for i in range(n):
        for j in range(i + 1, n):
            strength = float(sim[i, j])
            if strength > 0.0:
                relations.append(
                    InterLayerRelation(
                        from_layer_id=layers[i].layer_id,
                        to_layer_id=layers[j].layer_id,
                        relation_type="constrains",
                        strength=strength,
                    )
                )
    return tuple(relations)


def hierarchy_to_layer_summaries(
    hierarchy: Hierarchy,
    nodes: tuple,
    distillations: tuple[DistillationResult, ...],
) -> tuple[LayerSummary, ...]:
    """Pack Hierarchy + distillations into LayerSummary tuple."""
    out: list[LayerSummary] = []
    for layer, distillation in zip(hierarchy.layers, distillations):
        out.append(
            LayerSummary(
                layer_id=layer.layer_id,
                member_indices=layer.member_indices,
                member_nodes=tuple(nodes[i] for i in layer.member_indices),
                representation_vector=layer.representation_vector,
                distillation=distillation,
            )
        )
    return tuple(out)
