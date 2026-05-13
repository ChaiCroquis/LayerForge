"""Constant Potts Model (CPM) community detection — pure-MIT implementation.

Reference: Traag, Van Dooren, Nesterov (2011), "Narrow scope for
resolution-limit-free community detection", Phys. Rev. E 84, 016114.

CPM is resolution-limit-free under the subgraph-invariance property
(unlike Newman modularity which suffers from the Fortunato-Barthélemy
resolution limit, see docs/08 §1.4).

Self-implementation rationale (see ADR-018):
- ``leidenalg`` is GPLv3 → would contaminate LayerForge's MIT license.
- ``graspologic-native`` v1.2.5 has a Rust-level panic in CPM mode
  (``use_modularity=False``); confirmed across versions 1.2.2-1.2.5.
- ``graspologic`` (high-level) doesn't install on Python 3.13 (gensim
  build failure + numpy<2.0 pin).
- Pure-Python CPM-Louvain on top of numpy/scipy is the MIT-clean path.

Algorithm: classical Louvain greedy local moves with the CPM quality
function (Traag 2011 eq. 4 in the (n_c choose 2) form):

    H(P) = Σ_c [ m_c - γ * (n_c choose 2) ]   (MAXIMIZE)

For a node v moving from community c1 to c2:

    ΔH = (k_{v,c2} - k_{v,c1}) + γ * (n_{c1} - 1 - n_{c2})

where k_{v,c} is the edge-weight sum from v to community c, and n_c is
the size of community c. Moves with ΔH > 0 (strict) are kept.

K is controlled by γ: higher γ → more communities, lower γ → fewer.
"""
from __future__ import annotations

import numpy as np
import scipy.sparse as sp


def _build_adjacency(similarity, edge_floor: float = 0.0):
    """Return a CSR adjacency from (dense or sparse) similarity.

    Diagonal zeroed, edges ≤ ``edge_floor`` dropped. Symmetric weighted.
    """
    n = similarity.shape[0]
    if sp.issparse(similarity):
        coo = similarity.tocoo()
        mask = (coo.row != coo.col) & (coo.data > edge_floor)
        adj = sp.coo_matrix(
            (coo.data[mask], (coo.row[mask], coo.col[mask])),
            shape=(n, n),
        ).tocsr()
        return adj
    arr = np.asarray(similarity, dtype=np.float64).copy()
    np.fill_diagonal(arr, 0.0)
    arr[arr <= edge_floor] = 0.0
    return sp.csr_matrix(arr)


def _neighbor_view(adj_csr, v: int):
    """Return (neighbor_indices, neighbor_weights) for node v in a CSR adj."""
    s, e = adj_csr.indptr[v], adj_csr.indptr[v + 1]
    return adj_csr.indices[s:e], adj_csr.data[s:e]


def _cpm_quality(adj_csr, labels: np.ndarray, gamma: float) -> float:
    """H = Σ_c [m_c - γ * (n_c choose 2)] where m_c is intra-community edge sum."""
    n = labels.size
    if n == 0:
        return 0.0
    # m_c per community via vectorized iteration over edges in CSR
    h = 0.0
    unique, counts = np.unique(labels, return_counts=True)
    intra = {int(c): 0.0 for c in unique}
    for v in range(n):
        nb_idx, nb_w = _neighbor_view(adj_csr, v)
        for u, w in zip(nb_idx, nb_w):
            if u > v and labels[u] == labels[v]:  # count each edge once
                intra[int(labels[v])] += float(w)
    for c, n_c in zip(unique, counts):
        h += intra[int(c)] - gamma * n_c * (n_c - 1) / 2.0
    return h


def cpm_partition(
    similarity,
    resolution: float = 0.05,
    seed: int = 42,
    max_passes: int = 50,
    edge_floor: float = 0.0,
) -> tuple[np.ndarray, float, int]:
    """Run CPM-Louvain partitioning.

    Parameters
    ----------
    similarity : ndarray or sparse, shape (N, N)
        Pairwise similarity (symmetric, non-negative on kept edges).
    resolution : float, default 0.05
        CPM γ. Larger γ → more communities, smaller → fewer.
    seed : int, default 42
        Determines node-visit order (numpy default_rng).
    max_passes : int, default 50
        Cap on Louvain passes; usually converges in 5-20 on N≤1000.
    edge_floor : float, default 0.0
        Edges with weight ≤ ``edge_floor`` are dropped before optimization.

    Returns
    -------
    labels : ndarray of int, shape (N,)
        Community label per node, compacted to 0..K-1.
    h_value : float
        CPM quality at the returned partition.
    k : int
        Number of communities.
    """
    n = similarity.shape[0]
    if n == 0:
        return np.array([], dtype=np.int64), 0.0, 0
    if n == 1:
        return np.zeros(1, dtype=np.int64), 0.0, 1

    adj = _build_adjacency(similarity, edge_floor=edge_floor)
    gamma = float(resolution)

    labels = np.arange(n, dtype=np.int64)
    comm_size: dict[int, int] = {int(c): 1 for c in labels}
    rng = np.random.default_rng(seed)

    for _ in range(max_passes):
        improved = False
        order = rng.permutation(n)
        for v in order:
            v = int(v)
            c1 = int(labels[v])
            n_c1 = comm_size[c1]

            nb_idx, nb_w = _neighbor_view(adj, v)
            if nb_idx.size == 0:
                continue

            # Aggregate edge weights by neighboring community
            cw: dict[int, float] = {}
            for u, w in zip(nb_idx, nb_w):
                cu = int(labels[u])
                cw[cu] = cw.get(cu, 0.0) + float(w)
            k_v_c1 = cw.get(c1, 0.0)

            best_gain = 0.0
            best_c = c1
            for c2, k_v_c2 in cw.items():
                if c2 == c1:
                    continue
                n_c2 = comm_size[c2]
                gain = (k_v_c2 - k_v_c1) + gamma * (n_c1 - 1 - n_c2)
                if gain > best_gain + 1e-12:
                    best_gain = gain
                    best_c = c2

            # Consider singleton split (only if v is not already alone)
            if n_c1 > 1:
                gain_singleton = -k_v_c1 + gamma * (n_c1 - 1)
                if gain_singleton > best_gain + 1e-12:
                    best_gain = gain_singleton
                    # Use an ID not already in use
                    new_id = max(comm_size) + 1
                    while new_id in comm_size:
                        new_id += 1
                    best_c = new_id

            if best_c != c1:
                labels[v] = best_c
                comm_size[c1] -= 1
                if comm_size[c1] == 0:
                    del comm_size[c1]
                comm_size[best_c] = comm_size.get(best_c, 0) + 1
                improved = True

        if not improved:
            break

    # Compact labels to 0..K-1 (stable order by first-member index for
    # reproducibility — matches Hierarchy convention).
    unique_in_order: list[int] = []
    seen: set[int] = set()
    for lbl in labels.tolist():
        if lbl not in seen:
            seen.add(lbl)
            unique_in_order.append(lbl)
    remap = {old: new for new, old in enumerate(unique_in_order)}
    compact_labels = np.array([remap[int(lbl)] for lbl in labels], dtype=np.int64)

    h_value = _cpm_quality(adj, compact_labels, gamma)
    k = len(unique_in_order)
    return compact_labels, h_value, k


def find_cpm_resolution(
    similarity,
    target_range: tuple[int, int] = (3, 5),
    seed: int = 42,
    gamma_lo: float = 1e-4,
    gamma_hi: float = 5.0,
    max_iter: int = 40,
    edge_floor: float = 0.0,
) -> tuple[float, np.ndarray, float, int]:
    """Bisect γ on log scale to land community count K inside ``target_range``.

    K is (approximately) monotone non-decreasing in γ. We bisect on
    log(γ) and prefer the smallest K within range (analog to
    ``find_valid_scale``'s "first valid θ" semantics — smaller K is the
    coarser, more interpretable partition).

    Returns
    -------
    gamma_used : float
    labels : ndarray
    h_value : float
    k : int

    Raises
    ------
    NoValidScaleError
        If no γ in ``[gamma_lo, gamma_hi]`` produces K in target_range.
    """
    from layerforge.exceptions import NoValidScaleError

    K_min, K_max = int(target_range[0]), int(target_range[1])
    if not (1 <= K_min <= K_max):
        raise ValueError(
            f"target_range must have 1 <= min <= max; got {target_range}"
        )

    # Endpoint probes
    labels_lo, h_lo, k_lo = cpm_partition(
        similarity, resolution=gamma_lo, seed=seed, edge_floor=edge_floor,
    )
    if K_min <= k_lo <= K_max:
        return gamma_lo, labels_lo, h_lo, k_lo
    if k_lo > K_max:
        # Even γ_lo gives too many → graph is too sparse for this range
        raise NoValidScaleError(
            f"CPM: even γ={gamma_lo} produces K={k_lo} > {K_max}."
        )

    labels_hi, h_hi, k_hi = cpm_partition(
        similarity, resolution=gamma_hi, seed=seed, edge_floor=edge_floor,
    )
    if K_min <= k_hi <= K_max:
        return gamma_hi, labels_hi, h_hi, k_hi
    if k_hi < K_min:
        raise NoValidScaleError(
            f"CPM: even γ={gamma_hi} produces K={k_hi} < {K_min}."
        )

    # Bisection on log γ (geometric mean = midpoint in log space)
    lo, hi = float(gamma_lo), float(gamma_hi)
    best: tuple[float, np.ndarray, float, int] | None = None
    for _ in range(max_iter):
        mid = float(np.sqrt(lo * hi))
        labels, h, k = cpm_partition(
            similarity, resolution=mid, seed=seed, edge_floor=edge_floor,
        )
        if K_min <= k <= K_max:
            best = (mid, labels, h, k)
            hi = mid  # prefer smaller γ (smaller K)
        elif k < K_min:
            lo = mid
        else:
            hi = mid
        if hi / lo < 1.01:
            break

    if best is None:
        raise NoValidScaleError(
            f"CPM: no γ in [{gamma_lo}, {gamma_hi}] produces K in {target_range} "
            f"after {max_iter} iterations."
        )
    return best
