"""4±1 sensitivity analysis — vary K across the hallucination corpus.

Reuses the existing small fictional corpus (24 passages, 12 questions) to
sweep K ∈ {2, 4, 6, 10, 20} and measure:
  - actual layer count detected
  - average layer size
  - modularity Q at that K
  - routing accuracy: for each answerable question, does the chosen layer
    contain the ground-truth source passage?
  - compression ratio (chars in chosen layer / chars in full corpus)

No subagent calls — pure mechanical measurement of LayerForge behaviour
under different K targets. Result tells us whether Cowan's 4±1 (the
default) is empirically distinguished from other K's.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np

from layerforge.cli.decompose import run as decompose_run
from layerforge.inference.embedding import SentenceTransformersEmbedding

from scripts.halluc_benchmark.corpus import (
    PASSAGES,
    QUESTIONS,
    PASSAGE_BY_ID,
)


EMBED_MODEL = "sentence-transformers/paraphrase-MiniLM-L3-v2"


def _normalize(vecs: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    safe = np.where(norms == 0, 1.0, norms)
    return vecs / safe


def _build_payload(target_min: int, target_max: int) -> dict:
    return {
        "nodes": [{"id": p.id, "text": p.text} for p in PASSAGES],
        "options": {
            "embedding_backend": "sentence_transformers",
            "embedding_model": EMBED_MODEL,
            "random_seed": 42,
            "target_layer_count_min": target_min,
            "target_layer_count_max": target_max,
        },
    }


def _route_and_score(layers: list[dict], embedder, passage_id_to_idx) -> dict:
    """For each answerable question, route to best layer and check whether
    its source passage falls in that layer."""
    passage_embeds = embedder.embed([p.text for p in PASSAGES])
    layer_ids = [l["id"] for l in layers]
    centroids = []
    for l in layers:
        idxs = [passage_id_to_idx[pid] for pid in l["member_node_ids"]]
        centroids.append(passage_embeds[idxs].mean(axis=0))
    centroid_matrix = _normalize(np.stack(centroids))

    answerable = [q for q in QUESTIONS if q.answerable]
    q_embeds = _normalize(embedder.embed([q.text for q in answerable]))
    sims = q_embeds @ centroid_matrix.T
    chosen_idx = np.argmax(sims, axis=1)

    correct = 0
    per_q = []
    chosen_layer_sizes = []
    for i, q in enumerate(answerable):
        chosen_layer_id = layer_ids[int(chosen_idx[i])]
        chosen_layer = next(l for l in layers if l["id"] == chosen_layer_id)
        chosen_members = chosen_layer["member_node_ids"]
        chosen_layer_sizes.append(len(chosen_members))
        is_correct = q.source_passage_id in chosen_members
        if is_correct:
            correct += 1
        per_q.append({
            "q_id": q.id,
            "source_pid": q.source_passage_id,
            "chosen_layer_id": chosen_layer_id,
            "chosen_layer_size": len(chosen_members),
            "correct": is_correct,
        })

    return {
        "answerable_n": len(answerable),
        "routing_correct": correct,
        "routing_accuracy": correct / len(answerable) if answerable else 0.0,
        "avg_chosen_layer_size": float(np.mean(chosen_layer_sizes)),
        "per_question": per_q,
    }


def main() -> int:
    out_dir = Path(__file__).resolve().parent
    out_dir.mkdir(exist_ok=True)

    embedder = SentenceTransformersEmbedding(model_name=EMBED_MODEL)
    passage_id_to_idx = {p.id: i for i, p in enumerate(PASSAGES)}
    total_chars = sum(len(p.text) for p in PASSAGES)

    # K ranges to test. (min, max) tuples.
    # min=max forces an exact K when possible.
    sweeps = [
        (1, 2, "K≈2 (very coarse)"),
        (3, 5, "K=3-5 (4±1 default)"),
        (6, 8, "K=6-8 (above Cowan)"),
        (10, 12, "K=10-12 (fine)"),
        (15, 20, "K=15-20 (near per-passage)"),
        (20, 24, "K≈N (top-1 RAG-like)"),
    ]

    rows = []
    for target_min, target_max, label in sweeps:
        print(f"\n=== {label}  (target {target_min}-{target_max}) ===")
        try:
            result = decompose_run(_build_payload(target_min, target_max))
        except Exception as e:
            print(f"  FAILED: {e}")
            rows.append({
                "label": label,
                "target_min": target_min,
                "target_max": target_max,
                "status": "error",
                "error": str(e),
            })
            continue

        if result.get("status") != "ok":
            print(f"  status={result['status']}")
            rows.append({
                "label": label,
                "target_min": target_min,
                "target_max": target_max,
                "status": result["status"],
                "error_type": result.get("error_type"),
            })
            continue

        layers = result["layers"]
        qm = result["quality_metrics"]
        sizes = [len(l["member_node_ids"]) for l in layers]
        chosen_chars = []
        for l in layers:
            chars = sum(len(PASSAGE_BY_ID[pid].text) for pid in l["member_node_ids"])
            chosen_chars.append(chars)
        avg_layer_chars = sum(chosen_chars) / len(layers)
        avg_compression_per_layer = avg_layer_chars / total_chars

        routing = _route_and_score(layers, embedder, passage_id_to_idx)

        row = {
            "label": label,
            "target_min": target_min,
            "target_max": target_max,
            "status": "ok",
            "actual_K": qm["layer_count"],
            "modularity_Q": round(qm["modularity"], 3),
            "quality_class": qm["quality_class"],
            "avg_layer_size_nodes": round(sum(sizes) / len(sizes), 1),
            "avg_compression_ratio": round(avg_compression_per_layer, 3),
            "routing_accuracy": round(routing["routing_accuracy"], 3),
            "routing_correct": f"{routing['routing_correct']}/{routing['answerable_n']}",
            "avg_chosen_layer_size_for_correct": round(routing["avg_chosen_layer_size"], 1),
            "per_question": routing["per_question"],
        }
        rows.append(row)
        print(f"  actual K={row['actual_K']}, Q={row['modularity_Q']} ({row['quality_class']}), "
              f"avg layer size={row['avg_layer_size_nodes']:.1f}")
        print(f"  routing: {row['routing_correct']} correct, accuracy={row['routing_accuracy']:.0%}")
        print(f"  avg compression per layer: {row['avg_compression_ratio']:.1%}")

    out_path = out_dir / "data_archive" / "results.json"
    out_path.parent.mkdir(exist_ok=True)
    out_path.write_text(json.dumps({"sweeps": rows, "total_chars": total_chars},
                                   ensure_ascii=False, indent=2),
                        encoding="utf-8")

    # Markdown summary
    print("\n\n=== Summary table ===")
    print("| K range | actual | Q | class | avg layer size | compression | routing acc |")
    print("|---|---:|---:|---|---:|---:|---:|")
    for r in rows:
        if r["status"] != "ok":
            print(f"| {r['target_min']}-{r['target_max']} | err | - | - | - | - | - |")
            continue
        print(f"| {r['target_min']}-{r['target_max']} | {r['actual_K']} | {r['modularity_Q']:.3f} | "
              f"{r['quality_class']} | {r['avg_layer_size_nodes']:.1f} | "
              f"{r['avg_compression_ratio']:.1%} | {r['routing_accuracy']:.0%} ({r['routing_correct']}) |")

    print(f"\nResults written to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
