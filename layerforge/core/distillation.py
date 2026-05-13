"""SCA (Semantic Component Analysis) distillation (F2).

Reference: Eichin, Schuster, Groh, Hedderich (2024), arXiv:2410.21054v3.

LayerForge uses SCA as the per-layer distillation step. UMAP + HDBSCAN
are imported lazily; if unavailable, a deterministic KMeans fallback
clusters the embeddings instead. The fallback preserves the same
v_i = centroid / ||centroid|| semantic-component definition (F2.2).
"""
from __future__ import annotations

import numpy as np
from sklearn.cluster import KMeans

from layerforge.constants import (
    DETERMINISTIC_SEED,
    GIANT_CLUSTER_RATIO_THRESHOLD,
    SCA_DEFAULT_ALPHA,
    SCA_DEFAULT_MAX_ITER,
    SCA_DEFAULT_MIN_CLUSTER_SIZE,
    SCA_DEFAULT_MIN_SAMPLES,
    SCA_DEFAULT_MU,
    SCA_DEFAULT_NC_S,
    SCA_DEFAULT_NC_THRESHOLD,
    SCA_DEFAULT_RN_THRESHOLD,
    SCA_DEFAULT_THETA,
    SCA_EPS_COMPONENT,
    SCA_UMAP_MIN_DIST,
    SCA_UMAP_N_COMPONENTS,
    SCA_UMAP_N_EPOCHS,
    SCA_UMAP_N_NEIGHBORS,
)
from layerforge.schema.input_schema import Node
from layerforge.schema.output_schema import DistillationResult


# ----------------------------------------------------------------------
# Step-level primitives (F2.3)
# ----------------------------------------------------------------------


def single_decomposition_step(
    x: np.ndarray,
    v: np.ndarray,
    mu: float = SCA_DEFAULT_MU,
    alpha: float = SCA_DEFAULT_ALPHA,
) -> np.ndarray:
    """Eq. 2: x' = x - μ · 1_{α_ij > α} · ⟨x, v⟩ · v."""
    norm_x = float(np.linalg.norm(x))
    if norm_x < 1e-12:
        return x.copy()
    inner = float(np.dot(x, v))
    alpha_ij = inner / norm_x
    if alpha_ij > alpha:
        return x - mu * inner * v
    return x.copy()


def compute_activations(
    embeddings: np.ndarray,
    components: list[np.ndarray] | tuple[np.ndarray, ...],
    mu: float = SCA_DEFAULT_MU,
    alpha: float = SCA_DEFAULT_ALPHA,
) -> np.ndarray:
    """F2.5: a_j = μ · 1_{α_ij > α} · ⟨x'_i, v_j⟩, sequentially over components."""
    n = embeddings.shape[0]
    k = len(components)
    activations = np.zeros((n, k))
    if k == 0:
        return activations

    working = embeddings.copy()
    for i, v in enumerate(components):
        for j in range(n):
            x_j = working[j]
            norm_x = float(np.linalg.norm(x_j))
            if norm_x < 1e-12:
                continue
            inner = float(np.dot(x_j, v))
            alpha_ij = inner / norm_x
            if alpha_ij > alpha:
                activations[j, i] = mu * inner
                working[j] = x_j - mu * inner * v
    return activations


# ----------------------------------------------------------------------
# Step 1 — clustering (UMAP + HDBSCAN, or KMeans fallback)
# ----------------------------------------------------------------------


def _cluster_step(
    embeddings: np.ndarray,
    min_cluster_size: int,
    min_samples: int,
    random_state: int,
) -> np.ndarray:
    """Return cluster labels (-1 = noise, F2.4 Step 1).

    Tries UMAP+HDBSCAN; falls back to KMeans on cosine-normalized vectors.
    """
    try:
        import umap  # type: ignore
        import hdbscan  # type: ignore

        # Adapt cluster size to small inputs (paper §C.1 default is 100)
        effective_mcs = max(2, min(min_cluster_size, max(2, embeddings.shape[0] // 4)))
        effective_ms = max(1, min(min_samples, effective_mcs))
        n_neighbors = max(2, min(SCA_UMAP_N_NEIGHBORS, embeddings.shape[0] - 1))
        reducer = umap.UMAP(
            n_components=min(SCA_UMAP_N_COMPONENTS, embeddings.shape[1]),
            metric="cosine",
            n_neighbors=n_neighbors,
            n_epochs=SCA_UMAP_N_EPOCHS,
            min_dist=SCA_UMAP_MIN_DIST,
            random_state=random_state,
            init="random",
        )
        reduced = reducer.fit_transform(embeddings)
        clusterer = hdbscan.HDBSCAN(
            min_cluster_size=effective_mcs,
            min_samples=effective_ms,
            metric="euclidean",
            cluster_selection_method="eom",
            prediction_data=True,
        )
        return clusterer.fit_predict(reduced)
    except Exception:
        return _kmeans_fallback_labels(embeddings, random_state=random_state)


def _kmeans_fallback_labels(
    embeddings: np.ndarray,
    random_state: int = DETERMINISTIC_SEED,
    max_k: int = 8,
) -> np.ndarray:
    """Pick K by silhouette over a small range. No noise label."""
    n = embeddings.shape[0]
    if n < 2:
        return np.zeros(n, dtype=int)

    upper = min(max_k, max(2, n - 1))
    best_labels = np.zeros(n, dtype=int)
    best_inertia = float("inf")
    # Prefer smaller K when ties — favor stability
    for k in range(2, upper + 1):
        km = KMeans(n_clusters=k, random_state=random_state, n_init=10)
        labels = km.fit_predict(embeddings)
        if km.inertia_ < best_inertia * 0.8:
            best_inertia = km.inertia_
            best_labels = labels
    return best_labels


# ----------------------------------------------------------------------
# Step 2 — centroid → unit vector (F2.2)
# ----------------------------------------------------------------------


def _cluster_centroids_to_components(
    embeddings: np.ndarray,
    labels: np.ndarray,
    eps_component: float = SCA_EPS_COMPONENT,
) -> list[np.ndarray]:
    """Centroids whose pre-normalization norm < eps_component are dropped
    (matches reference impl semantic_components/decomposition.py:448)."""
    components: list[np.ndarray] = []
    for cid in np.unique(labels):
        if cid == -1:
            continue
        members = embeddings[labels == cid]
        if members.size == 0:
            continue
        v_prime = members.mean(axis=0)
        norm = float(np.linalg.norm(v_prime))
        if norm < eps_component:
            continue
        components.append(v_prime / norm)
    return components


# ----------------------------------------------------------------------
# F2.4 — SCA iterative procedure
# ----------------------------------------------------------------------


def run_sca(
    X: np.ndarray,
    mu: float = SCA_DEFAULT_MU,
    alpha: float = SCA_DEFAULT_ALPHA,
    theta: float = SCA_DEFAULT_THETA,
    max_iter: int = SCA_DEFAULT_MAX_ITER,
    nc_s: int = SCA_DEFAULT_NC_S,
    nc_threshold: int = SCA_DEFAULT_NC_THRESHOLD,
    rn_threshold: float = SCA_DEFAULT_RN_THRESHOLD,
    min_cluster_size: int = SCA_DEFAULT_MIN_CLUSTER_SIZE,
    min_samples: int = SCA_DEFAULT_MIN_SAMPLES,
    random_state: int = DETERMINISTIC_SEED,
) -> tuple[list[np.ndarray], np.ndarray]:
    """SCA core loop with three stopping criteria (F, NC-S, RN)."""
    components: list[np.ndarray] = []
    new_per_iter: list[int] = []
    embeddings = X.copy().astype(float)

    for _ in range(max_iter):
        labels = _cluster_step(
            embeddings,
            min_cluster_size=min_cluster_size,
            min_samples=min_samples,
            random_state=random_state,
        )
        new_components = _cluster_centroids_to_components(embeddings, labels)
        new_per_iter.append(len(new_components))
        components.extend(new_components)

        # Step 3 — decomposition with the components added this iteration
        if new_components:
            for j in range(embeddings.shape[0]):
                for v in new_components:
                    embeddings[j] = single_decomposition_step(
                        embeddings[j], v, mu=mu, alpha=alpha
                    )

        # RN stop
        if float(np.linalg.norm(embeddings)) < rn_threshold:
            break
        # NC-S stop
        if len(new_per_iter) >= nc_s:
            recent = sum(new_per_iter[-nc_s:])
            if recent < nc_threshold:
                break

    return components, embeddings


# ----------------------------------------------------------------------
# Step 6 — merging
# ----------------------------------------------------------------------


def merge_overlapping_components(
    components: list[np.ndarray] | tuple[np.ndarray, ...],
    token_representations: list[set[str] | frozenset[str]] | tuple[set[str] | frozenset[str], ...],
    theta: float = SCA_DEFAULT_THETA,
) -> tuple[list[np.ndarray], list[set[str]]]:
    """F2.4 Step 6: O(R1, R2) = |R1 ∩ R2| / 10.

    The first component encountered wins; subsequent overlapping ones are dropped.
    """
    merged_components: list[np.ndarray] = []
    merged_tokens: list[set[str]] = []
    for v, tokens in zip(components, token_representations):
        tokens_set = set(tokens)
        merged = False
        for existing in merged_tokens:
            overlap = len(tokens_set & existing) / 10.0
            if overlap > theta:
                merged = True
                break
        if not merged:
            merged_components.append(v)
            merged_tokens.append(tokens_set)
    return merged_components, merged_tokens


# ----------------------------------------------------------------------
# Token representation — approximate c-TF-IDF on raw whitespace tokens
# ----------------------------------------------------------------------


def _tokenize(text: str) -> list[str]:
    return [t.lower() for t in text.split() if t.strip()]


def compute_ctfidf_per_cluster(
    nodes: tuple[Node, ...],
    components: list[np.ndarray],
    embeddings: np.ndarray,
    top_k: int = 10,
) -> list[frozenset[str]]:
    """Approximate c-TF-IDF representation per component.

    Assigns each node to the component with highest cosine similarity, then
    picks the top_k tokens by raw frequency in that cluster.
    """
    if not components:
        return []
    if len(nodes) == 0:
        return [frozenset() for _ in components]

    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    safe = np.where(norms == 0, 1.0, norms)
    normalized = embeddings / safe
    comp_matrix = np.stack(components)
    # cosine since components are unit vectors and normalized embeddings are unit
    sim = normalized @ comp_matrix.T
    assignments = np.argmax(sim, axis=1)

    out: list[frozenset[str]] = []
    for k in range(len(components)):
        member_idx = np.where(assignments == k)[0]
        counts: dict[str, int] = {}
        for i in member_idx:
            for tok in _tokenize(nodes[i].text):
                counts[tok] = counts.get(tok, 0) + 1
        top_tokens = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:top_k]
        out.append(frozenset(tok for tok, _ in top_tokens))
    return out


# ----------------------------------------------------------------------
# F2.6 — distill_layer
# ----------------------------------------------------------------------


def distill_layer(
    layer_nodes: tuple[Node, ...],
    embeddings: np.ndarray,
    mu: float = SCA_DEFAULT_MU,
    alpha: float = SCA_DEFAULT_ALPHA,
    theta: float = SCA_DEFAULT_THETA,
    max_iter: int = SCA_DEFAULT_MAX_ITER,
    nc_s: int = SCA_DEFAULT_NC_S,
    nc_threshold: int = SCA_DEFAULT_NC_THRESHOLD,
    rn_threshold: float = SCA_DEFAULT_RN_THRESHOLD,
    min_cluster_size: int = SCA_DEFAULT_MIN_CLUSTER_SIZE,
    min_samples: int = SCA_DEFAULT_MIN_SAMPLES,
    random_state: int = DETERMINISTIC_SEED,
) -> DistillationResult:
    """Per-layer SCA distillation."""
    components, final_residuals = run_sca(
        embeddings,
        mu=mu,
        alpha=alpha,
        theta=theta,
        max_iter=max_iter,
        nc_s=nc_s,
        nc_threshold=nc_threshold,
        rn_threshold=rn_threshold,
        min_cluster_size=min_cluster_size,
        min_samples=min_samples,
        random_state=random_state,
    )

    token_reps = compute_ctfidf_per_cluster(layer_nodes, components, embeddings)
    components, token_reps_list = merge_overlapping_components(
        components, token_reps, theta=theta
    )

    activations = compute_activations(embeddings, components, mu=mu, alpha=alpha)
    residual_norms = np.linalg.norm(final_residuals, axis=1)
    is_converged = float(np.linalg.norm(final_residuals)) < rn_threshold

    return DistillationResult(
        components=tuple(components),
        activations=activations,
        residuals=final_residuals,
        residual_norms=residual_norms,
        token_representations=tuple(frozenset(t) for t in token_reps_list),
        is_converged=is_converged,
    )


# ----------------------------------------------------------------------
# F2.7 — purity
# ----------------------------------------------------------------------


def compute_layer_purity(
    distillation: DistillationResult,
    embeddings: np.ndarray,
) -> float:
    """purity = 1 - max(residual) / max(embedding_norm), clipped to [0, 1]."""
    if distillation.residual_norms.size == 0:
        return 0.0
    max_residual = float(np.max(distillation.residual_norms))
    max_emb = float(np.max(np.linalg.norm(embeddings, axis=1)))
    if max_emb == 0.0:
        return 0.0
    return max(0.0, min(1.0, 1.0 - max_residual / max_emb))


# ----------------------------------------------------------------------
# F2.8 — giant-cluster detection (LayerForge extension)
# ----------------------------------------------------------------------


def detect_giant_clusters(
    distillation: DistillationResult,
    threshold_ratio: float = GIANT_CLUSTER_RATIO_THRESHOLD,
    activation_threshold: float = 0.0,
) -> list[int]:
    """Return component indices whose activation covers > threshold_ratio of samples."""
    if distillation.activations.size == 0:
        return []
    n = distillation.activations.shape[0]
    active = (distillation.activations > activation_threshold).sum(axis=0)
    ratios = active / n
    return [int(i) for i, r in enumerate(ratios) if r > threshold_ratio]
