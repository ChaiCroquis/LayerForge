"""Community detection backend dispatcher.

Routes between the default Newman path (threshold-based θ scale finding
+ KMeans on embeddings) and the optional CPM path (Leiden CPM on the
weighted similarity graph, resolution-limit-free).

Both backends produce a ``Hierarchy`` with the same flat-labels
contract, so downstream pipeline stages (SCA distillation, inter-layer
relations, serialization) are backend-agnostic.

See docs/08 §1.6 for the Q-degeneracy / CPM motivation, and
docs/06 ADR-017 for the engineering choice rationale.
"""
from __future__ import annotations

from typing import Literal

import numpy as np

from layerforge.core.hierarchical import Hierarchy, HierarchyLayer


CommunityMethod = Literal["newman", "cpm"]


def _labels_to_hierarchy(
    labels: np.ndarray, embeddings: np.ndarray
) -> Hierarchy:
    """Build a ``Hierarchy`` from a flat label array + embeddings.

    Stable canonical labeling: order clusters by first-member index
    ascending. Matches ``hierarchical_kmeans``'s labeling convention so
    the two backends are wire-compatible.
    """
    unique_labels = np.unique(labels)
    first_indices = {
        lbl: int(np.where(labels == lbl)[0][0]) for lbl in unique_labels
    }
    order = sorted(unique_labels, key=lambda lbl: first_indices[lbl])
    remap = {old: new for new, old in enumerate(order)}
    canonical_labels = np.array([remap[lbl] for lbl in labels], dtype=np.int64)

    layers: list[HierarchyLayer] = []
    centroids_list = []
    for new_lbl in range(len(order)):
        members_arr = np.where(canonical_labels == new_lbl)[0]
        members = tuple(int(i) for i in members_arr)
        layer_embeds = embeddings[members_arr]
        centroid = layer_embeds.mean(axis=0)
        centroids_list.append(centroid)
        layers.append(
            HierarchyLayer(
                layer_id=new_lbl,
                member_indices=members,
                centroid=centroid,
                representation_vector=centroid,
            )
        )

    centroids = np.stack(centroids_list) if centroids_list else np.zeros(
        (0, embeddings.shape[1] if embeddings.ndim == 2 else 0)
    )
    return Hierarchy(
        layers=tuple(layers),
        flat_labels=canonical_labels,
        centroids=centroids,
    )


def detect_communities_cpm(
    similarity,
    embeddings: np.ndarray,
    target_range: tuple[int, int],
    seed: int,
) -> tuple[Hierarchy, float, float]:
    """CPM community detection (resolution-limit-free).

    Returns
    -------
    hierarchy : Hierarchy
    h_value : float
        CPM quality value at the chosen γ.
    gamma : float
        Resolution parameter γ actually used.
    """
    from layerforge.core.cpm_backend import find_cpm_resolution

    gamma, labels, h_value, _ = find_cpm_resolution(
        similarity,
        target_range=target_range,
        seed=seed,
    )
    hierarchy = _labels_to_hierarchy(labels, embeddings)
    return hierarchy, h_value, gamma
