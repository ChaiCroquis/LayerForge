"""Cross-corpus / cross-model / cross-seed / cross-method K sweep for robustness.

For each (n_themes, embedder, seed, method) combination, sweep K over a range
and find the K that gives:
  - peak modularity Q (algorithmic optimality)
  - 100% routing accuracy with min K (smallest K still routing correctly)

Hypothesis to test:
  H_struct: optimal K (peak Q) tracks n_themes (corpus structure)
  → if true: 4±1 is not magic, it's just that our default corpora had 4 themes
  → if false: 4±1 has some universal property we don't yet understand

If H_struct holds across embedders, seeds, AND community-detection methods,
the conclusion is robust to all three orthogonal axes.

2026-05-13 update: adds community_method ∈ {newman, cpm} dimension.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np

from layerforge.core.modularity import build_similarity_matrix
from layerforge.core.scale_finder import compute_initial_scale
from layerforge.exceptions import NoValidScaleError
from layerforge.inference.embedding import SentenceTransformersEmbedding
from layerforge.pipeline import layerforge_core
from layerforge.schema.input_schema import FormulationInput, Node, ScaleParams

from scripts.k_sweep.corpora import make_corpus


SWEEPS = [
    # (target_min, target_max, label)
    (1, 2,    "K=1-2"),
    (2, 3,    "K=2-3"),
    (3, 4,    "K=3-4"),
    (3, 5,    "K=3-5"),
    (5, 7,    "K=5-7"),
    (6, 8,    "K=6-8"),
    (8, 10,   "K=8-10"),
    (10, 12,  "K=10-12"),
]


def _normalize(v):
    n = np.linalg.norm(v, axis=1, keepdims=True)
    return v / np.where(n == 0, 1.0, n)


def _route_accuracy(layers, passage_embeds, passage_id_to_idx, passages):
    """For each passage, pretend its text IS the question and check if it
    routes back to its own layer."""
    layer_ids = [l["id"] for l in layers]
    centroids = []
    for l in layers:
        idxs = [passage_id_to_idx[pid] for pid in l["member_node_ids"]]
        centroids.append(passage_embeds[idxs].mean(axis=0))
    centroid_matrix = _normalize(np.stack(centroids))

    # Build pid → containing-layer map
    pid_to_layer = {}
    for l in layers:
        for pid in l["member_node_ids"]:
            pid_to_layer[pid] = l["id"]

    q_embeds = _normalize(passage_embeds)
    sims = q_embeds @ centroid_matrix.T
    chosen = np.argmax(sims, axis=1)

    correct = 0
    for i, p in enumerate(passages):
        chosen_layer_id = layer_ids[int(chosen[i])]
        if chosen_layer_id == pid_to_layer[p.id]:
            correct += 1
    return correct, len(passages)


def run_one(passages, formulation, passage_embeds, target_min, target_max, seed=42, method="newman"):
    """Run layerforge_core for one (range, method) and compute routing accuracy.

    Pre-computed ``formulation`` and ``passage_embeds`` avoid reloading the
    embedder for each cell.
    """
    try:
        r = layerforge_core(
            formulation,
            seed=seed,
            target_range=(target_min, target_max),
            community_method=method,
        )
    except NoValidScaleError:
        return None
    except Exception as e:
        print(f"    ! K=({target_min},{target_max}) method={method}: {type(e).__name__}: {e}")
        return None

    # Build layer-id-keyed view for the routing helper
    pid_by_idx = {i: p.id for i, p in enumerate(passages)}
    layers = [
        {
            "id": layer.layer_id,
            "member_node_ids": [pid_by_idx[i] for i in layer.member_indices],
        }
        for layer in r.layers
    ]
    pid_to_idx = {p.id: i for i, p in enumerate(passages)}
    correct, total = _route_accuracy(layers, passage_embeds, pid_to_idx, passages)
    routing = correct / total if total else 0.0
    return {
        "actual_K": int(r.quality_metrics.layer_count),
        "method": method,
        "Q": round(float(r.quality_metrics.modularity), 4),
        "cpm_h": (None if r.quality_metrics.cpm_h is None
                  else round(float(r.quality_metrics.cpm_h), 4)),
        "quality_class": r.quality_metrics.quality_class,
        "routing_accuracy": round(routing, 3),
    }


def main() -> int:
    out_dir = Path(__file__).resolve().parent
    settings = []

    for embed_backend, embed_model, embedder_label in [
        ("sentence_transformers", "sentence-transformers/paraphrase-MiniLM-L3-v2", "MiniLM-L3"),
        ("sentence_transformers", "sentence-transformers/paraphrase-multilingual-mpnet-base-v2", "mpnet"),
    ]:
        embedder = SentenceTransformersEmbedding(model_name=embed_model)
        for n_themes in [3, 4, 5, 7]:
            for seed in [42, 123]:
                settings.append((n_themes, embedder, embed_backend, embed_model, embedder_label, seed))

    all_results = []
    for n_themes, embedder, embed_backend, embed_model, embedder_label, seed in settings:
        passages = make_corpus(n_themes=n_themes, per_theme=6, seed=seed)
        N = len(passages)
        print(f"\n=== n_themes={n_themes} (N={N}), embedder={embedder_label}, seed={seed} ===",
              flush=True)
        # Pre-compute embeddings + FormulationInput once per (corpus, embedder, seed)
        passage_embeds = embedder.embed([p.text for p in passages])
        sim = build_similarity_matrix(passage_embeds)
        formulation = FormulationInput(
            nodes=tuple(Node(id=p.id, text=p.text, metadata={"source": "robustness"})
                        for p in passages),
            embeddings=passage_embeds,
            similarity_matrix=sim,
            initial_scale=ScaleParams(threshold=compute_initial_scale(sim)),
        )
        for method in ("newman", "cpm"):
            sweep_results = []
            for tmin, tmax, label in SWEEPS:
                if tmax > N:
                    continue
                r = run_one(passages, formulation, passage_embeds, tmin, tmax,
                            seed=seed, method=method)
                if r is None:
                    continue
                sweep_results.append({"label": label, "tmin": tmin, "tmax": tmax, **r})
                print(f"  [{method}] {label}: K={r['actual_K']}, Q={r['Q']}, "
                      f"routing={r['routing_accuracy']}", flush=True)
            if not sweep_results:
                continue
            peak_Q = max(sweep_results, key=lambda x: x["Q"])
            peak_routing = max(
                sweep_results,
                key=lambda x: (x["routing_accuracy"], -x["actual_K"]),
            )
            all_results.append({
                "n_themes": n_themes,
                "N": N,
                "embedder": embedder_label,
                "seed": seed,
                "method": method,
                "peak_Q_at_K": peak_Q["actual_K"],
                "peak_Q_value": peak_Q["Q"],
                "best_routing_K": peak_routing["actual_K"],
                "best_routing_acc": peak_routing["routing_accuracy"],
                "sweep": sweep_results,
            })
            print(f"  --> [{method}] peak Q at K={peak_Q['actual_K']} (Q={peak_Q['Q']}); "
                  f"best routing at K={peak_routing['actual_K']} "
                  f"(acc={peak_routing['routing_accuracy']})", flush=True)

    # Write JSON
    (out_dir / "data_current").mkdir(exist_ok=True)
    (out_dir / "data_current" / "robustness_results.json").write_text(
        json.dumps(all_results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\nWrote {out_dir / 'data_current' / 'robustness_results.json'} ({len(all_results)} rows)")

    # Summary table
    print("\n\n=== Summary: peak-Q K vs n_themes × method ===")
    print("| n_themes | embedder | seed | method | N | peak-Q K | peak Q | best-routing K | routing acc |")
    print("|---:|---|---:|---|---:|---:|---:|---:|---:|")
    for r in all_results:
        print(f"| {r['n_themes']} | {r['embedder']:<7} | {r['seed']} | {r['method']:<6} | {r['N']} | "
              f"{r['peak_Q_at_K']} | {r['peak_Q_value']:.3f} | "
              f"{r['best_routing_K']} | {r['best_routing_acc']:.0%} |")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
