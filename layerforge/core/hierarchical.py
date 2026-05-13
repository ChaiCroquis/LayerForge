"""HERCULES-adapted hierarchical KMeans clustering (F1.3, F1.5).

LayerForge currently builds a single level (flat clustering at the chosen K)
and exposes it as a one-level hierarchy.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.cluster import KMeans

from layerforge.constants import DETERMINISTIC_SEED


@dataclass(frozen=True)
class HierarchyLayer:
    """A single layer (cluster) at one level of the hierarchy."""

    layer_id: int
    member_indices: tuple[int, ...]
    centroid: np.ndarray
    representation_vector: np.ndarray


@dataclass(frozen=True)
class Hierarchy:
    """One-level clustering result."""

    layers: tuple[HierarchyLayer, ...]
    flat_labels: np.ndarray
    centroids: np.ndarray

    @property
    def all_clusters(self) -> tuple[HierarchyLayer, ...]:
        return self.layers


def _resampling_refine(
    embeddings: np.ndarray,
    initial_labels: np.ndarray,
    initial_centroids: np.ndarray,
    k: int,
    n_resample: int,
    refine_iters: int,
    random_state: int,
) -> tuple[np.ndarray, np.ndarray]:
    """F1.3 optional resampling refinement.

    For each cluster, keep the n_resample points nearest its centroid,
    refit KMeans on that subset, then reassign all points.
    """
    labels = initial_labels.copy()
    centroids = initial_centroids.copy()
    for _ in range(refine_iters):
        kept_indices: list[int] = []
        for j in range(k):
            members = np.where(labels == j)[0]
            if members.size == 0:
                continue
            d = np.linalg.norm(embeddings[members] - centroids[j], axis=1)
            order = np.argsort(d, kind="stable")
            take = members[order[: min(n_resample, members.size)]]
            kept_indices.extend(take.tolist())
        if len(kept_indices) < k:
            break
        R = embeddings[kept_indices]
        km = KMeans(n_clusters=k, random_state=random_state, n_init=10)
        km.fit(R)
        centroids = km.cluster_centers_
        # Reassign all points to the new centroids
        d_all = np.linalg.norm(
            embeddings[:, None, :] - centroids[None, :, :], axis=2
        )
        labels = np.argmin(d_all, axis=1)
    return labels, centroids


def hierarchical_kmeans(
    embeddings: np.ndarray,
    k: int,
    use_resampling: bool = True,
    n_resample: int = 10,
    refine_iters: int = 3,
    random_state: int = DETERMINISTIC_SEED,
) -> Hierarchy:
    """One-level clustering (F1.3 single-pass).

    Args:
        embeddings: shape (n, d)
        k: number of clusters
        use_resampling: enable F1.3 iterative resampling refinement
        random_state: deterministic seed
    """
    if embeddings.ndim != 2:
        raise ValueError("embeddings must be 2-D")
    n = embeddings.shape[0]
    if k <= 0:
        raise ValueError("k must be positive")
    if k > n:
        k = n

    km = KMeans(n_clusters=k, random_state=random_state, n_init=10)
    km.fit(embeddings)
    labels = km.labels_
    centroids = km.cluster_centers_

    if use_resampling and k > 1:
        labels, centroids = _resampling_refine(
            embeddings, labels, centroids, k,
            n_resample=n_resample,
            refine_iters=refine_iters,
            random_state=random_state,
        )

    # Stable canonical labeling: order clusters by first-member index ascending
    unique_labels = np.unique(labels)
    first_indices = {lbl: int(np.where(labels == lbl)[0][0]) for lbl in unique_labels}
    order = sorted(unique_labels, key=lambda lbl: first_indices[lbl])
    remap = {old: new for new, old in enumerate(order)}
    canonical_labels = np.array([remap[l] for l in labels])
    canonical_centroids = np.stack([centroids[lbl] for lbl in order])

    layers: list[HierarchyLayer] = []
    for new_lbl in range(len(order)):
        members = tuple(int(i) for i in np.where(canonical_labels == new_lbl)[0])
        rep = embeddings[list(members)].mean(axis=0)
        layers.append(
            HierarchyLayer(
                layer_id=new_lbl,
                member_indices=members,
                centroid=canonical_centroids[new_lbl],
                representation_vector=rep,
            )
        )

    return Hierarchy(
        layers=tuple(layers),
        flat_labels=canonical_labels,
        centroids=canonical_centroids,
    )
