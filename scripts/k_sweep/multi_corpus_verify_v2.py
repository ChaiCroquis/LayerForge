"""Multi-corpus verification v2 — orthogonal-domain corpus + mpnet check, dual method.

Lessons from v1:
- KDF internal docs (all about KDF) have heavy vocabulary overlap → Q stays poor for any K
- This is itself a valid observation: LayerForge correctly reports "no clean structure"

v2 adds:
  - Truly cross-domain corpus (philosophy / exploration / paper / proofs) — path via LAYERFORGE_KDF_DOCS env var
  - mpnet (multilingual) embedder for stronger disambiguation

2026-05-13 update (CPM integration):
  - Each (corpus × embedder) is swept under BOTH community_method values
  - Tests whether the "K_optimal tracks N_themes" finding holds under CPM
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


import os
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


def _build_corpus(file_topic_map: list[tuple[str, str]], per_theme: int) -> tuple[list[dict], list[str]]:
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


def _resolution_limit_check(passages, theta, embedder, layers):
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


def _theme_purity(layers, pid_to_truth):
    from collections import Counter
    purities = []
    for layer in layers:
        themes = [pid_to_truth.get(pid, "?") for pid in layer["member_node_ids"]]
        if not themes:
            continue
        c = Counter(themes)
        dominant = c.most_common(1)[0][1]
        purities.append(dominant / len(themes))
    return {
        "min": round(min(purities), 2) if purities else 0.0,
        "mean": round(sum(purities) / len(purities), 2) if purities else 0.0,
    }


def sweep_one(corpus_label, file_topic_map, per_theme, embedder_label, embedder, embed_model, method):
    nodes, truth = _build_corpus(file_topic_map, per_theme)
    pid_to_truth = {n["id"]: t for n, t in zip(nodes, truth)}
    N = len(nodes)
    n_themes = len({t for _, t in zip(nodes, truth)})

    embeddings = embedder.embed([n["text"] for n in nodes])
    similarity = build_similarity_matrix(embeddings)
    formulation = FormulationInput(
        nodes=tuple(Node(id=n["id"], text=n["text"], metadata={"source": "multi_corpus"})
                    for n in nodes),
        embeddings=embeddings,
        similarity_matrix=similarity,
        initial_scale=ScaleParams(threshold=compute_initial_scale(similarity)),
    )

    results = []
    pid_by_idx = {i: n["id"] for i, n in enumerate(nodes)}
    for K in range(2, min(10, N) + 1):
        try:
            r = layerforge_core(
                formulation,
                seed=42,
                target_range=(K, K),
                community_method=method,
            )
        except NoValidScaleError:
            continue
        except Exception as e:
            print(f"    ! K={K} method={method}: {type(e).__name__}: {e}")
            continue
        # Build layer dicts compatible with the existing helpers
        layers = [
            {
                "id": layer.layer_id,
                "member_node_ids": [pid_by_idx[i] for i in layer.member_indices],
            }
            for layer in r.layers
        ]
        # For Newman, scale_coefficient is θ; for CPM, use median-similarity as
        # the method-independent reference graph for the above-limit check.
        if method == "newman":
            ref_theta = float(r.quality_metrics.scale_coefficient)
        else:
            iu = np.triu_indices(N, k=1)
            ref_theta = float(np.median(similarity[iu]))
        rl = _resolution_limit_check(nodes, ref_theta, embedder, layers)
        purity = _theme_purity(layers, pid_to_truth)
        results.append({
            "K": int(r.quality_metrics.layer_count),
            "Q": round(float(r.quality_metrics.modularity), 3),
            "cpm_h": (None if r.quality_metrics.cpm_h is None
                      else round(float(r.quality_metrics.cpm_h), 3)),
            "class": r.quality_metrics.quality_class,
            "above": f"{rl['above_count']}/{rl['total']}",
            "above_frac": round(rl["above_count"] / rl["total"], 2) if rl["total"] else 0,
            "purity_mean": purity["mean"],
        })

    if not results:
        return {
            "corpus": corpus_label, "embedder": embedder_label, "method": method,
            "expected_N": n_themes, "K_optimal": None, "Q_at_optimal": None,
            "purity_at_optimal": None, "above_limit_at_optimal": None, "sweep": [],
        }
    pure_above = [r for r in results if r["above_frac"] == 1.0]
    peak = max(pure_above, key=lambda x: (x["Q"], x["purity_mean"])) if pure_above else max(results, key=lambda x: x["Q"])
    return {
        "corpus": corpus_label,
        "embedder": embedder_label,
        "method": method,
        "expected_N": n_themes,
        "K_optimal": peak["K"],
        "Q_at_optimal": peak["Q"],
        "purity_at_optimal": peak["purity_mean"],
        "above_limit_at_optimal": peak["above"],
        "sweep": results,
    }


def main() -> int:
    out_dir = Path(__file__).resolve().parent

    # Cross-domain corpus: pick truly different document types
    # (philosophy / experimental pre-reg / mathematical proofs / paper section)
    cross_domain = [
        ("phil",     "KDF_Core_Philosophy.md"),
        ("explore",  "exploration/g11_hdfs_recurring_pre_reg.md"),
        ("proof",    "proofs"),  # will resolve to first .md in dir
        ("blog",     "blog/medium-en-draft.md"),
    ]
    # Resolve proof dir to a single file
    proofs_dir = KDF_DOCS / "proofs"
    if proofs_dir.is_dir():
        proof_md = sorted(proofs_dir.glob("*.md"))
        if proof_md:
            cross_domain[2] = ("proof", str(proof_md[0]))

    # Corpora to test
    same_domain_5themes = [
        ("phil", "KDF_Core_Philosophy.md"),
        ("apps", "KDF_Application_Areas.md"),
        ("ver",  "KDF_Verification_Report.md"),
        ("dev",  "KDF_Development_Journey.md"),
        ("lib",  "KDF_Library_Summary.md"),
    ]

    all_results = []
    for embed_label, embed_model in [
        ("MiniLM", "sentence-transformers/paraphrase-MiniLM-L3-v2"),
        ("mpnet",  "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"),
    ]:
        print(f"\nLoading embedder once: {embed_label}", flush=True)
        embedder = SentenceTransformersEmbedding(model_name=embed_model)
        for corpus_label, mapping in [
            ("same-domain 5 themes (all KDF)",     same_domain_5themes),
            ("cross-domain 4 themes (phil/explore/proof/blog)", cross_domain),
        ]:
            for method in ("newman", "cpm"):
                print(f"\n{'='*80}")
                print(f"{corpus_label}  |  embedder: {embed_label}  |  method: {method}")
                print(f"{'='*80}", flush=True)
                r = sweep_one(corpus_label, mapping, per_theme=6,
                              embedder_label=embed_label, embedder=embedder,
                              embed_model=embed_model, method=method)
                print(f"  expected N_themes = {r['expected_N']}")
                print(f"  {'K':>3} {'Q':>6} {'class':<11} {'above':>6} {'purity':>7}")
                for s in r["sweep"]:
                    marker = "*" if r["K_optimal"] is not None and s["K"] == r["K_optimal"] else " "
                    print(f"  {marker}{s['K']:>2} {s['Q']:>6} {s['class']:<11} {s['above']:>6} {s['purity_mean']:>7}")
                print(f"  → K_optimal = {r['K_optimal']}  (Q={r['Q_at_optimal']}, "
                      f"purity={r['purity_at_optimal']})", flush=True)
                all_results.append(r)

    print(f"\n{'='*80}")
    print("FINAL SUMMARY")
    print(f"{'='*80}")
    print(f"\n{'corpus':<50} {'embedder':<8} {'method':<8} {'N_exp':>5} {'K_opt':>5} {'Q':>6} {'purity':>7}")
    print("-" * 100)
    for r in all_results:
        match = "*" if r["K_optimal"] == r["expected_N"] else " "
        K_opt_str = str(r["K_optimal"]) if r["K_optimal"] is not None else "-"
        Q_str = str(r["Q_at_optimal"]) if r["Q_at_optimal"] is not None else "-"
        purity_str = str(r["purity_at_optimal"]) if r["purity_at_optimal"] is not None else "-"
        print(f"{match} {r['corpus']:<48} {r['embedder']:<8} {r['method']:<8} "
              f"{r['expected_N']:>5} {K_opt_str:>5} {Q_str:>6} {purity_str:>7}")

    (out_dir / "data_current").mkdir(exist_ok=True)
    (out_dir / "data_current" / "multi_corpus_results_v2.json").write_text(
        json.dumps(all_results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\nWrote {out_dir / 'data_current' / 'multi_corpus_results_v2.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
