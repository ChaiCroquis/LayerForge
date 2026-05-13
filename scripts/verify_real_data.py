"""Real-world verification: 20 Newsgroups → LayerForge → vs ground truth.

Picks 4 thematically distinct newsgroup topics, samples K docs each, runs
LayerForge Mode A (decompose) with sentence-transformers embeddings, and
reports:
  - layer_count (should be 4 — within 4±1)
  - modularity Q
  - per-layer dominant topic + purity (max-topic ratio)
  - Adjusted Rand Index (ARI) vs ground-truth topic labels

First-run cost: sklearn downloads ~14 MB to ~/scikit_learn_data/, then HF
caches the embedding model.

Usage:
    python scripts/verify_real_data.py                    # default 4 topics, 25/each
    python scripts/verify_real_data.py --per-topic 50     # 50 docs per topic
    python scripts/verify_real_data.py --json out.json
"""
from __future__ import annotations

import argparse
import gc
import json
import re
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from layerforge.cli import decompose


# Four thematically distinct 20NG topics — high inter-topic separation.
DEFAULT_TOPICS: tuple[str, ...] = (
    "sci.med",
    "sci.space",
    "rec.sport.hockey",
    "talk.politics.guns",
)
DEFAULT_PER_TOPIC: int = 25
DEFAULT_EMBED_MODEL: str = "sentence-transformers/paraphrase-MiniLM-L3-v2"


def _strip_headers_and_quotes(text: str) -> str:
    """20NG docs contain email headers and quoted replies — remove for
    cleaner embeddings."""
    # Drop email headers (lines up to first blank line)
    parts = text.split("\n\n", 1)
    body = parts[1] if len(parts) == 2 else text
    # Drop quoted lines starting with '>' (common in newsgroup replies)
    body = "\n".join(line for line in body.splitlines() if not line.lstrip().startswith(">"))
    # Collapse whitespace
    body = re.sub(r"\s+", " ", body).strip()
    return body


def _load_20ng(topics: tuple[str, ...], per_topic: int) -> tuple[list[dict], list[int]]:
    """Return (nodes, ground_truth_topic_ids).

    Each node has ``id`` and ``text`` (header-stripped). Ground-truth list
    is parallel: ground_truth[i] = topic_id (0..len(topics)-1).
    """
    try:
        from sklearn.datasets import fetch_20newsgroups
    except ImportError as e:
        raise SystemExit(
            "scikit-learn is required (already in core deps). "
            f"Install: pip install scikit-learn — original error: {e}"
        )

    nodes: list[dict] = []
    truth: list[int] = []
    idx = 0
    for topic_id, topic in enumerate(topics):
        dataset = fetch_20newsgroups(
            subset="train",
            categories=[topic],
            remove=("headers", "footers", "quotes"),  # sklearn's built-in stripping
            random_state=42,
        )
        # Take the first per_topic docs that survive cleaning (non-trivial length).
        kept = 0
        for raw in dataset.data:
            body = _strip_headers_and_quotes(raw)
            if len(body) < 200:  # skip stubs
                continue
            nodes.append({"id": f"n{idx:04d}", "text": body[:2000]})  # cap doc length
            truth.append(topic_id)
            idx += 1
            kept += 1
            if kept >= per_topic:
                break
        if kept < per_topic:
            sys.stderr.write(
                f"[verify_real_data] note: only {kept}/{per_topic} docs for {topic}\n"
            )
    return nodes, truth


def _adjusted_rand_index(labels_true: list[int], labels_pred: list[int]) -> float:
    """ARI via sklearn — robust to label permutations."""
    from sklearn.metrics import adjusted_rand_score
    return float(adjusted_rand_score(labels_true, labels_pred))


def _per_layer_purity(
    layers: list[dict],
    node_id_to_truth: dict[str, int],
    topics: tuple[str, ...],
) -> list[dict]:
    """Per-layer dominant topic and purity (max-topic-count / total)."""
    out = []
    for layer in layers:
        counts = Counter(
            node_id_to_truth[mid] for mid in layer["member_node_ids"] if mid in node_id_to_truth
        )
        if not counts:
            out.append({"layer_id": layer["id"], "dominant": None, "purity": 0.0})
            continue
        dominant_topic_id, dominant_count = counts.most_common(1)[0]
        total = sum(counts.values())
        out.append({
            "layer_id": layer["id"],
            "dominant_topic": topics[dominant_topic_id],
            "purity": dominant_count / total,
            "size": total,
            "topic_distribution": {topics[tid]: c for tid, c in counts.most_common()},
        })
    return out


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="verify_real_data.py")
    parser.add_argument("--topics", nargs="+", default=list(DEFAULT_TOPICS),
                        help=f"20NG categories (default: {DEFAULT_TOPICS})")
    parser.add_argument("--per-topic", type=int, default=DEFAULT_PER_TOPIC,
                        help=f"Docs per topic (default {DEFAULT_PER_TOPIC})")
    parser.add_argument("--embedding-model", type=str, default=DEFAULT_EMBED_MODEL)
    parser.add_argument("--backend", type=str, default="sentence_transformers",
                        choices=["hash", "sentence_transformers"])
    parser.add_argument("--json", type=str, default=None)
    parser.add_argument("--community-method", type=str, default=None,
                        choices=["newman", "cpm"],
                        help="Community detection backend. Default: Newman (script default).")
    args = parser.parse_args(argv)

    topics = tuple(args.topics)
    print(f"# topics: {topics}")
    print(f"# per_topic: {args.per_topic}, backend: {args.backend}")
    if args.backend == "sentence_transformers":
        print(f"# embedding_model: {args.embedding_model}")

    print(f"\n[1/3] Fetching 20 Newsgroups...")
    t0 = time.perf_counter()
    nodes, truth = _load_20ng(topics, args.per_topic)
    t_load = time.perf_counter() - t0
    print(f"  loaded {len(nodes)} docs in {t_load:.2f}s")

    payload = {
        "nodes": nodes,
        "options": {
            "embedding_backend": args.backend,
            "embedding_model": args.embedding_model,
            "random_seed": 42,
        },
    }
    if args.community_method is not None:
        payload["options"]["community_method"] = args.community_method

    print(f"\n[2/3] Running LayerForge decompose...")
    gc.collect()
    t0 = time.perf_counter()
    result = decompose.run(payload)
    t_run = time.perf_counter() - t0
    print(f"  decompose done in {t_run:.2f}s")

    if result["status"] != "ok":
        print(f"\n[FAIL] status={result['status']}, error_type={result.get('error_type')}")
        print(f"       message: {result.get('message')}")
        return 1

    qm = result["quality_metrics"]
    print(f"\n[3/3] Results:")
    print(f"  layer_count      = {qm['layer_count']}  (within 4±1: {qm['is_within_4_plus_minus_1']})")
    print(f"  modularity Q     = {qm['modularity']:.3f}  ({qm['quality_class']})")
    print(f"  scale coefficient= {qm['scale_coefficient']:.3f}")

    # Build node_id -> truth_topic_id map (ordering of payload['nodes'] matches truth)
    node_id_to_truth = {n["id"]: truth[i] for i, n in enumerate(nodes)}

    # Per-layer breakdown
    per_layer = _per_layer_purity(result["layers"], node_id_to_truth, topics)
    print()
    for entry in per_layer:
        if entry.get("dominant_topic"):
            dist = ", ".join(
                f"{t.split('.')[-1]}={c}" for t, c in entry["topic_distribution"].items()
            )
            print(
                f"  L{entry['layer_id']}: {entry['dominant_topic']:<22} "
                f"purity={entry['purity']:.2f}  size={entry['size']}  ({dist})"
            )
        else:
            print(f"  L{entry['layer_id']}: (empty)")

    # ARI vs ground truth
    # Build parallel pred_labels list ordered like truth.
    pred_labels = [-1] * len(nodes)
    for layer in result["layers"]:
        for mid in layer["member_node_ids"]:
            i = int(mid[1:])  # nodes IDs are "n0001"
            pred_labels[i] = layer["id"]
    ari = _adjusted_rand_index(truth, pred_labels)
    print(f"\n  ARI vs ground truth = {ari:.3f}  (1.0 = perfect, 0.0 = random)")

    if args.json:
        out_data = {
            "topics": list(topics),
            "per_topic": args.per_topic,
            "backend": args.backend,
            "embedding_model": args.embedding_model if args.backend == "sentence_transformers" else None,
            "load_time_s": t_load,
            "decompose_time_s": t_run,
            "quality_metrics": qm,
            "per_layer": per_layer,
            "ari": ari,
            "n_docs": len(nodes),
        }
        Path(args.json).write_text(json.dumps(out_data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n  results written to {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
