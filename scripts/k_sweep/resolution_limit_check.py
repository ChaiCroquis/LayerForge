"""Fortunato & Barthélemy (2007) resolution-limit check.

For each K target in the existing sweep:
  1. Build the similarity matrix (sentence-transformers).
  2. Run LayerForge core; capture θ chosen by find_valid_scale.
  3. Threshold the similarity matrix at θ → adjacency.
  4. Count total edges L.
  5. Compute the resolution-limit threshold √(L/2).
  6. For each community, count internal edges e_c.
  7. Verdict per community:
       e_c >  √(L/2) → "above limit, signal is real"
       e_c ≈  √(L/2) → "near limit, ambiguous"
       e_c <  √(L/2) → "below limit, resolution-limit artifact possible"

We report:
  - per-community status
  - aggregate: fraction of communities above the threshold
  - whether the Q peak at the user's "interesting" K is in safe territory
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np

from layerforge.cli.decompose import run as decompose_run
from layerforge.core.modularity import build_similarity_matrix
from layerforge.core.scale_finder import find_valid_scale
from layerforge.inference.embedding import SentenceTransformersEmbedding

from scripts.halluc_benchmark.corpus import PASSAGES


EMBED_MODEL = "sentence-transformers/paraphrase-MiniLM-L3-v2"


def _internal_edges(A: np.ndarray, member_idx: list[int]) -> int:
    """Count edges with both endpoints in member_idx. Adjacency is binary."""
    sub = A[np.ix_(member_idx, member_idx)]
    # Symmetric; off-diagonal sum / 2 = edge count
    return int(sub.sum() // 2)


def _theta_for_K(similarity: np.ndarray, target_min: int, target_max: int) -> float:
    """Re-run find_valid_scale to recover θ for this K range."""
    theta, _ = find_valid_scale(similarity, target_range=(target_min, target_max))
    return theta


def main() -> int:
    out_dir = Path(__file__).resolve().parent
    embedder = SentenceTransformersEmbedding(model_name=EMBED_MODEL)
    embeddings = embedder.embed([p.text for p in PASSAGES])
    similarity = build_similarity_matrix(embeddings)

    sweeps = [
        (1, 2),
        (3, 5),
        (6, 8),
        (10, 12),
        (15, 20),
        (20, 24),
    ]

    rows = []
    for tmin, tmax in sweeps:
        # Decompose to get layers
        payload = {
            "nodes": [{"id": p.id, "text": p.text} for p in PASSAGES],
            "options": {
                "embedding_backend": "sentence_transformers",
                "embedding_model": EMBED_MODEL,
                "random_seed": 42,
                "target_layer_count_min": tmin,
                "target_layer_count_max": tmax,
            },
        }
        try:
            r = decompose_run(payload)
            if r.get("status") != "ok":
                rows.append({"K_range": f"{tmin}-{tmax}", "status": "skip"})
                continue
        except Exception as e:
            rows.append({"K_range": f"{tmin}-{tmax}", "status": "error", "msg": str(e)})
            continue

        # Recover the θ that find_valid_scale chose
        theta = _theta_for_K(similarity, tmin, tmax)
        A = (similarity > theta).astype(float)
        np.fill_diagonal(A, 0.0)
        L = int(A.sum() // 2)  # total edges (undirected)
        if L == 0:
            rows.append({
                "K_range": f"{tmin}-{tmax}",
                "actual_K": r["quality_metrics"]["layer_count"],
                "Q": round(r["quality_metrics"]["modularity"], 3),
                "theta": round(theta, 4),
                "L": 0,
                "resolution_limit_sqrtL_over_2": 0.0,
                "status": "no_edges",
            })
            continue

        rl_threshold = math.sqrt(L / 2.0)

        # Map passage IDs to integer indices for adjacency lookup.
        pid_to_idx = {p.id: i for i, p in enumerate(PASSAGES)}
        community_stats = []
        above_count = 0
        for layer in r["layers"]:
            member_idx = [pid_to_idx[pid] for pid in layer["member_node_ids"]]
            e_c = _internal_edges(A, member_idx)
            verdict = (
                "above" if e_c > rl_threshold
                else ("near" if e_c >= rl_threshold * 0.8 else "below")
            )
            if verdict == "above":
                above_count += 1
            community_stats.append({
                "layer_id": layer["id"],
                "members": len(member_idx),
                "internal_edges": e_c,
                "verdict": verdict,
            })

        n_communities = len(community_stats)
        rows.append({
            "K_range": f"{tmin}-{tmax}",
            "actual_K": r["quality_metrics"]["layer_count"],
            "Q": round(r["quality_metrics"]["modularity"], 3),
            "theta": round(theta, 4),
            "L_total_edges": L,
            "resolution_limit_sqrt_L_over_2": round(rl_threshold, 2),
            "communities_above_limit": f"{above_count}/{n_communities}",
            "above_fraction": round(above_count / n_communities, 2) if n_communities else 0.0,
            "communities": community_stats,
        })

    (out_dir / "data_archive").mkdir(exist_ok=True)
    (out_dir / "data_archive" / "resolution_limit_results.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print("=" * 90)
    print(f"Fortunato-Barthélemy resolution limit check")
    print(f"Corpus: 24 passages, embedding: {EMBED_MODEL}")
    print("=" * 90)
    print()
    print(f"{'K range':<10} {'actual K':>8} {'Q':>6} {'θ':>6} {'L':>5} {'√(L/2)':>8} {'above limit':>12}")
    print("-" * 90)
    for row in rows:
        if row.get("status") in ("skip", "error", "no_edges"):
            print(f"{row['K_range']:<10}  {row.get('status', '-')}")
            continue
        print(
            f"{row['K_range']:<10} "
            f"{row['actual_K']:>8} "
            f"{row['Q']:>6.3f} "
            f"{row['theta']:>6.3f} "
            f"{row['L_total_edges']:>5} "
            f"{row['resolution_limit_sqrt_L_over_2']:>8.2f} "
            f"{row['communities_above_limit']:>12}"
        )

    print()
    print("Per-community detail (K=3-5 = 4±1 default):")
    print()
    for row in rows:
        if row["K_range"] != "3-5":
            continue
        for c in row["communities"]:
            mark = "OK " if c["verdict"] == "above" else ("?  " if c["verdict"] == "near" else "!! ")
            print(f"  {mark} L{c['layer_id']}: {c['members']} members, "
                  f"{c['internal_edges']} internal edges  (threshold √(L/2) = "
                  f"{row['resolution_limit_sqrt_L_over_2']:.2f})  → {c['verdict']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
