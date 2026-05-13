"""K=10 (AI agent input compression candidate) cross-corpus verification, dual method.

Tests whether K=10 maintains self-routing accuracy AND meaningful compression
across the same 4 multi-corpus configurations as v2. For each (corpus,
embedder, K, method) combination, measures:

  - self-routing accuracy: for each passage, embed its text and route to
    the closest layer centroid; check if the chosen layer contains it.
    (This approximates "AI query asks about content in passage P, does
    LayerForge correctly route the query to P's layer?")
  - compression ratio: avg layer size / total nodes
  - Q (modularity)
  - above-limit fraction

Compares K=4 (theme-count optimum) vs K=8 vs K=10 (AI cost optimum candidate)
under BOTH Newman and CPM. The headline claim "K=10 → 100% self-routing × 10x
compression" should remain robust across method choice.

2026-05-13 update: adds CPM dimension (was Newman-only baseline).
"""
from __future__ import annotations

import json
import math
import os
import re
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


KDF_DOCS = Path(os.environ.get("LAYERFORGE_KDF_DOCS", "./test_corpus/kdf-docs"))


def _split_sections(text: str, min_len: int = 80, max_len: int = 2000) -> list[str]:
    text = text.replace("\r\n", "\n")
    chunks = re.split(r"(?=^##+ )", text, flags=re.MULTILINE)
    keep = []
    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
        if len(chunk) > max_len:
            chunk = chunk[:max_len]
        if len(chunk) >= min_len:
            keep.append(chunk)
    return keep


def _build_corpus(file_topic_map, per_theme: int):
    nodes = []
    truth = []
    for theme_label, filepath in file_topic_map:
        path = KDF_DOCS / filepath if not Path(filepath).is_absolute() else Path(filepath)
        text = path.read_text(encoding="utf-8")
        sections = _split_sections(text)
        if len(sections) < per_theme:
            kept = sections
        else:
            stride = max(1, len(sections) // per_theme)
            kept = [sections[i * stride] for i in range(per_theme)]
        for i, sec in enumerate(kept):
            pid = f"{theme_label}-{i:02d}"
            nodes.append({"id": pid, "text": sec})
            truth.append(theme_label)
    return nodes, truth


def _normalize(v: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(v, axis=1, keepdims=True)
    return v / np.where(n == 0, 1.0, n)


def _self_routing_accuracy(layers, passage_embeds, passage_ids):
    """For each passage, find layer with most similar centroid. Did we route
    to the layer that actually contains the passage?"""
    pid_to_layer = {}
    for l in layers:
        for pid in l["member_node_ids"]:
            pid_to_layer[pid] = l["id"]
    layer_ids = [l["id"] for l in layers]
    centroids = []
    pid_to_idx = {pid: i for i, pid in enumerate(passage_ids)}
    for l in layers:
        idxs = [pid_to_idx[pid] for pid in l["member_node_ids"]]
        centroids.append(passage_embeds[idxs].mean(axis=0))
    centroid_matrix = _normalize(np.stack(centroids))
    q_embeds = _normalize(passage_embeds)
    sims = q_embeds @ centroid_matrix.T
    chosen = np.argmax(sims, axis=1)
    correct = 0
    for i, pid in enumerate(passage_ids):
        if layer_ids[int(chosen[i])] == pid_to_layer[pid]:
            correct += 1
    return correct, len(passage_ids)


def _resolution_limit(passages, theta, embedder, layers):
    embeddings = embedder.embed([n["text"] for n in passages])
    similarity = build_similarity_matrix(embeddings)
    A = (similarity > theta).astype(float)
    np.fill_diagonal(A, 0.0)
    L = int(A.sum() // 2)
    if L == 0:
        return 0, len(layers)
    rl = math.sqrt(L / 2.0)
    pid_to_idx = {n["id"]: i for i, n in enumerate(passages)}
    above = 0
    for layer in layers:
        idx = [pid_to_idx[pid] for pid in layer["member_node_ids"]]
        e = int(A[np.ix_(idx, idx)].sum() // 2)
        if e > rl:
            above += 1
    return above, len(layers)


def run_K(nodes, similarity, formulation, embedder, embeds, K: int, method: str):
    try:
        r = layerforge_core(
            formulation,
            seed=42,
            target_range=(K, K),
            community_method=method,
        )
    except NoValidScaleError:
        return None
    except Exception as e:
        print(f"    ! K={K} method={method}: {type(e).__name__}: {e}")
        return None
    pid_by_idx = {i: n["id"] for i, n in enumerate(nodes)}
    layers = [
        {
            "id": layer.layer_id,
            "member_node_ids": [pid_by_idx[i] for i in layer.member_indices],
        }
        for layer in r.layers
    ]
    pids = [n["id"] for n in nodes]
    routing_correct, routing_total = _self_routing_accuracy(layers, embeds, pids)
    # Reference θ for above-limit (Newman: own θ; CPM: median sim)
    if method == "newman":
        ref_theta = float(r.quality_metrics.scale_coefficient)
    else:
        iu = np.triu_indices(similarity.shape[0], k=1)
        ref_theta = float(np.median(similarity[iu]))
    above, total = _resolution_limit(nodes, ref_theta, embedder, layers)
    sizes = [len(l["member_node_ids"]) for l in layers]
    return {
        "K": int(r.quality_metrics.layer_count),
        "method": method,
        "Q": round(float(r.quality_metrics.modularity), 3),
        "cpm_h": (None if r.quality_metrics.cpm_h is None
                  else round(float(r.quality_metrics.cpm_h), 3)),
        "class": r.quality_metrics.quality_class,
        "avg_layer_size": round(sum(sizes) / len(sizes), 1),
        "compression_per_layer": round((sum(sizes) / len(sizes)) / len(nodes), 3),
        "self_routing_accuracy": round(routing_correct / routing_total, 3),
        "self_routing_correct": f"{routing_correct}/{routing_total}",
        "above_limit": f"{above}/{total}",
        "above_frac": round(above / total, 2) if total else 0.0,
    }


def main() -> int:
    out_dir = Path(__file__).resolve().parent

    same_domain_5themes = [
        ("phil", "KDF_Core_Philosophy.md"),
        ("apps", "KDF_Application_Areas.md"),
        ("ver",  "KDF_Verification_Report.md"),
        ("dev",  "KDF_Development_Journey.md"),
        ("lib",  "KDF_Library_Summary.md"),
    ]
    # Cross-domain 4 themes (proofs resolves to first .md in dir)
    proofs_md = sorted((KDF_DOCS / "proofs").glob("*.md"))
    cross_domain = [
        ("phil",    "KDF_Core_Philosophy.md"),
        ("explore", "exploration/g11_hdfs_recurring_pre_reg.md"),
        ("proof",   str(proofs_md[0]) if proofs_md else "KDF_Verification_Report.md"),
        ("blog",    "blog/medium-en-draft.md"),
    ]

    all_results = []
    for embed_label, embed_model in [
        ("MiniLM", "sentence-transformers/paraphrase-MiniLM-L3-v2"),
        ("mpnet",  "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"),
    ]:
        print(f"\nLoading embedder once: {embed_label}", flush=True)
        embedder = SentenceTransformersEmbedding(model_name=embed_model)
        for corpus_label, mapping in [
            ("same-domain 5 themes (all KDF)",   same_domain_5themes),
            ("cross-domain 4 themes",            cross_domain),
        ]:
            nodes, truth = _build_corpus(mapping, per_theme=6)
            N = len(nodes)
            n_themes = len({t for t in truth})
            print(f"\n{'='*100}")
            print(f"{corpus_label} | embedder={embed_label} | N={N}, N_themes={n_themes}")
            print(f"{'='*100}", flush=True)

            embeds = embedder.embed([n["text"] for n in nodes])
            similarity = build_similarity_matrix(embeds)
            formulation = FormulationInput(
                nodes=tuple(Node(id=n["id"], text=n["text"], metadata={"source": "k10"})
                            for n in nodes),
                embeddings=embeds,
                similarity_matrix=similarity,
                initial_scale=ScaleParams(threshold=compute_initial_scale(similarity)),
            )

            row = {"corpus": corpus_label, "embedder": embed_label, "N": N, "N_themes": n_themes,
                   "by_K_method": {}}
            test_Ks = sorted(set([n_themes, 4, 8, 10, min(15, N - 1)]))
            print(f"  {'K':>3} {'method':<8} {'Q':>6} {'class':<11} "
                  f"{'self-route':>10} {'above':>6} {'compression':>11} {'avg_layer':>10}")
            print("  " + "-" * 85)
            for K in test_Ks:
                if K < 2 or K > N - 1:
                    continue
                for method in ("newman", "cpm"):
                    r = run_K(nodes, similarity, formulation, embedder, embeds, K, method)
                    if not r:
                        print(f"  {K:>3} {method:<8}  (failed)")
                        continue
                    row["by_K_method"].setdefault(K, {})[method] = r
                    marker = "*" if K == 10 else (" " if K != n_themes else "T")
                    print(f"  {marker}{r['K']:>2} {method:<8} {r['Q']:>6} {r['class']:<11} "
                          f"{r['self_routing_correct']:>10} {r['above_limit']:>6} "
                          f"{r['compression_per_layer']:>11} {r['avg_layer_size']:>10}",
                          flush=True)
            all_results.append(row)

    print(f"\n{'='*100}")
    print("FINAL SUMMARY — K=10 (AI cost candidate) vs K=N_themes (theme count) "
          "across corpora × methods")
    print(f"{'='*100}")
    print(f"\n{'corpus':<45} {'embedder':<8} {'K':>3} {'method':<8} "
          f"{'Q':>6} {'self-route':>10} {'compression':>11}")
    print("-" * 105)
    for row in all_results:
        for K, by_m in sorted(row["by_K_method"].items()):
            for method, r in by_m.items():
                tag = " "
                if K == 10:
                    tag = "*"
                elif K == row["N_themes"]:
                    tag = "T"
                print(f"{tag} {row['corpus']:<43} {row['embedder']:<8} {K:>3} {method:<8} "
                      f"{r['Q']:>6} {r['self_routing_correct']:>10} {r['compression_per_layer']:>11}")

    (out_dir / "data_current").mkdir(exist_ok=True)
    (out_dir / "data_current" / "k10_multi_corpus_results.json").write_text(
        json.dumps(all_results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\nWrote {out_dir / 'data_current' / 'k10_multi_corpus_results.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
