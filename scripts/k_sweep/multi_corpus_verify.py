"""Multi-corpus verification — does LayerForge's K_optimal track corpus structure?

Builds 3 real-world corpora from KDF-perovskite project docs, each with a
DIFFERENT known theme count. For each, sweep K and find:
  - K_optimal (peak Q within K=2..8)
  - Above-resolution-limit fraction at K_optimal
  - Above-resolution-limit fraction at K = expected N_themes

If K_optimal tracks N_themes across multiple corpora, this addresses the
docs/08 §3 "N=1 corpus でしか検証していない" limitation.
"""
from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np

from layerforge.cli.decompose import run as decompose_run
from layerforge.core.modularity import build_similarity_matrix
from layerforge.core.scale_finder import find_valid_scale
from layerforge.inference.embedding import SentenceTransformersEmbedding


import os
KDF_DOCS = Path(os.environ.get("LAYERFORGE_KDF_DOCS", "./test_corpus/kdf-docs"))
EMBED_MODEL = "sentence-transformers/paraphrase-MiniLM-L3-v2"


def _split_paragraphs(text: str, min_len: int = 80, max_len: int = 2000) -> list[str]:
    """Split markdown into ### subsection-level chunks (KDF docs are heavily
    structured with markdown headings; treating each ### / ## subsection
    as one passage gives coherent thematic units)."""
    # Split on heading markers (### or ##), keep heading as part of chunk
    # First normalize line endings
    text = text.replace("\r\n", "\n")
    # Split into sections by ## or ### markers
    chunks = re.split(r"(?=^##+ )", text, flags=re.MULTILINE)
    keep = []
    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
        # Truncate
        if len(chunk) > max_len:
            chunk = chunk[:max_len]
        if len(chunk) >= min_len:
            keep.append(chunk)
    return keep


def _build_corpus(file_topic_map: list[tuple[str, str]], per_theme: int) -> tuple[list[dict], list[str]]:
    """Build a corpus: list of nodes + parallel ground-truth theme labels."""
    nodes = []
    truth = []
    for theme_label, filename in file_topic_map:
        path = KDF_DOCS / filename
        text = path.read_text(encoding="utf-8")
        paragraphs = _split_paragraphs(text)
        if len(paragraphs) < per_theme:
            print(f"  warning: {filename} only has {len(paragraphs)} paragraphs (need {per_theme})")
            kept = paragraphs
        else:
            # Take evenly-spaced paragraphs to avoid concentration in one section
            stride = max(1, len(paragraphs) // per_theme)
            kept = [paragraphs[i * stride] for i in range(per_theme)]
        for i, para in enumerate(kept):
            pid = f"{theme_label}-{i:02d}"
            nodes.append({"id": pid, "text": para})
            truth.append(theme_label)
    return nodes, truth


def _resolution_limit_check(passages: list[dict], theta: float, embedder, layers: list[dict]) -> dict:
    embeddings = embedder.embed([n["text"] for n in passages])
    similarity = build_similarity_matrix(embeddings)
    A = (similarity > theta).astype(float)
    np.fill_diagonal(A, 0.0)
    L = int(A.sum() // 2)
    if L == 0:
        return {"L": 0, "sqrtLover2": 0.0, "above_count": 0, "total": len(layers)}
    rl = math.sqrt(L / 2.0)
    pid_to_idx = {n["id"]: i for i, n in enumerate(passages)}
    above = 0
    for layer in layers:
        idx = [pid_to_idx[pid] for pid in layer["member_node_ids"]]
        e = int(A[np.ix_(idx, idx)].sum() // 2)
        if e > rl:
            above += 1
    return {"L": L, "sqrtLover2": round(rl, 2), "above_count": above, "total": len(layers)}


def _theme_purity(layers: list[dict], pid_to_truth: dict[str, str]) -> dict:
    """Per-layer dominant-theme purity (max-share)."""
    purities = []
    for layer in layers:
        themes = [pid_to_truth.get(pid, "?") for pid in layer["member_node_ids"]]
        if not themes:
            continue
        from collections import Counter
        c = Counter(themes)
        dominant = c.most_common(1)[0][1]
        purities.append(dominant / len(themes))
    return {
        "min": round(min(purities), 2) if purities else 0.0,
        "mean": round(sum(purities) / len(purities), 2) if purities else 0.0,
        "max": round(max(purities), 2) if purities else 0.0,
    }


def sweep_one_corpus(corpus_label: str, file_topic_map: list[tuple[str, str]], per_theme: int):
    print(f"\n{'='*80}")
    print(f"CORPUS: {corpus_label}  (expected N_themes = {len(file_topic_map)})")
    print(f"{'='*80}")
    nodes, truth = _build_corpus(file_topic_map, per_theme)
    pid_to_truth = {n["id"]: t for n, t in zip(nodes, truth)}
    N = len(nodes)
    print(f"  N passages = {N}, themes = {len(set(truth))}")

    embedder = SentenceTransformersEmbedding(model_name=EMBED_MODEL)
    # Precompute similarity once
    embeddings = embedder.embed([n["text"] for n in nodes])
    similarity = build_similarity_matrix(embeddings)

    results = []
    for K in range(2, min(10, N) + 1):
        try:
            r = decompose_run({
                "nodes": nodes,
                "options": {
                    "embedding_backend": "sentence_transformers",
                    "embedding_model": EMBED_MODEL,
                    "random_seed": 42,
                    "target_layer_count_min": K,
                    "target_layer_count_max": K,
                },
            })
            if r["status"] != "ok":
                continue
        except Exception as e:
            print(f"  K={K}: failed ({e})")
            continue
        theta, _ = find_valid_scale(similarity, target_range=(K, K))
        rl = _resolution_limit_check(nodes, theta, embedder, r["layers"])
        purity = _theme_purity(r["layers"], pid_to_truth)
        results.append({
            "K": K,
            "Q": round(r["quality_metrics"]["modularity"], 3),
            "quality_class": r["quality_metrics"]["quality_class"],
            "theta": round(theta, 3),
            "above_limit": f"{rl['above_count']}/{rl['total']}",
            "above_frac": round(rl["above_count"] / rl["total"], 2) if rl["total"] else 0,
            "purity_mean": purity["mean"],
            "purity_min": purity["min"],
        })

    print(f"\n{'K':>3} {'Q':>6} {'class':<11} {'θ':>5} {'above-limit':>12} {'purity_mean':>11} {'purity_min':>10}")
    print("-" * 80)
    for r in results:
        marker = " "
        print(f"{marker}{r['K']:>2} {r['Q']:>6} {r['quality_class']:<11} {r['theta']:>5} "
              f"{r['above_limit']:>12} {r['purity_mean']:>11} {r['purity_min']:>10}")

    # Find optimal K: highest Q with above_frac == 1.0 (all communities above limit)
    pure_above = [r for r in results if r["above_frac"] == 1.0]
    if pure_above:
        peak = max(pure_above, key=lambda x: (x["Q"], x["purity_mean"]))
    else:
        peak = max(results, key=lambda x: x["Q"])
    print(f"\n  → K_optimal = {peak['K']}  (Q={peak['Q']}, above-limit={peak['above_limit']}, "
          f"purity_mean={peak['purity_mean']})")
    print(f"  → expected N_themes = {len(file_topic_map)}")
    print(f"  → match: {'YES' if peak['K'] == len(file_topic_map) else 'close (Δ=' + str(abs(peak['K'] - len(file_topic_map))) + ')'}")

    return {
        "corpus_label": corpus_label,
        "expected_N_themes": len(file_topic_map),
        "N_passages": N,
        "K_optimal": peak["K"],
        "Q_at_optimal": peak["Q"],
        "above_limit_at_optimal": peak["above_limit"],
        "purity_at_optimal": peak["purity_mean"],
        "sweep": results,
    }


def main() -> int:
    out_dir = Path(__file__).resolve().parent
    # Three corpora with different known theme counts.
    corpus_A = [  # 3 themes
        ("phil", "KDF_Core_Philosophy.md"),
        ("apps", "KDF_Application_Areas.md"),
        ("ver",  "KDF_Verification_Report.md"),
    ]
    corpus_B = [  # 4 themes (= same as fictional default)
        ("phil", "KDF_Core_Philosophy.md"),
        ("apps", "KDF_Application_Areas.md"),
        ("ver",  "KDF_Verification_Report.md"),
        ("dev",  "KDF_Development_Journey.md"),
    ]
    corpus_C = [  # 5 themes
        ("phil", "KDF_Core_Philosophy.md"),
        ("apps", "KDF_Application_Areas.md"),
        ("ver",  "KDF_Verification_Report.md"),
        ("dev",  "KDF_Development_Journey.md"),
        ("lib",  "KDF_Library_Summary.md"),
    ]
    corpus_D = [  # 6 themes
        ("phil", "KDF_Core_Philosophy.md"),
        ("apps", "KDF_Application_Areas.md"),
        ("ver",  "KDF_Verification_Report.md"),
        ("dev",  "KDF_Development_Journey.md"),
        ("lib",  "KDF_Library_Summary.md"),
        ("adv",  "KDF_Advanced_Applications.md"),
    ]

    all_results = []
    for label, mapping in [
        ("A: 3 themes (philosophy/applications/verification)", corpus_A),
        ("B: 4 themes (+ development)",                          corpus_B),
        ("C: 5 themes (+ library)",                              corpus_C),
        ("D: 6 themes (+ advanced)",                             corpus_D),
    ]:
        result = sweep_one_corpus(label, mapping, per_theme=6)
        all_results.append(result)

    # Summary
    print(f"\n{'='*80}")
    print("FINAL SUMMARY — K_optimal vs N_themes (across corpora)")
    print(f"{'='*80}")
    print(f"\n{'corpus':<60} {'expected N':>10} {'K_optimal':>10} {'Q':>6} {'match':>8}")
    print("-" * 100)
    for r in all_results:
        match = "YES" if r["K_optimal"] == r["expected_N_themes"] else f"Δ={r['K_optimal'] - r['expected_N_themes']:+d}"
        print(f"{r['corpus_label']:<60} {r['expected_N_themes']:>10} {r['K_optimal']:>10} "
              f"{r['Q_at_optimal']:>6} {match:>8}")

    (out_dir / "data_archive").mkdir(exist_ok=True)
    (out_dir / "data_archive" / "multi_corpus_results.json").write_text(
        json.dumps(all_results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\nResults written to {out_dir / 'data_archive' / 'multi_corpus_results.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
