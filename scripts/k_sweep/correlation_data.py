"""Fine-grained K sweep × 5 configurations × 2 methods → CSV + correlation plots.

For each of 5 configs (1 synthetic baseline + 4 KDF real-world) × each method
(``newman`` / ``cpm``):
  K ∈ {2..12, 15, 20}
  Metrics per (config, K, method):
    - actual_K
    - Q (modularity)
    - quality_class
    - self_routing_accuracy
    - compression_per_layer = (avg layer size) / N
    - above_limit_fraction (Fortunato-Barthélemy)
    - theme_purity_mean / theme_purity_min
    - community_method
    - cpm_h (None for newman, float for cpm)

Outputs:
  scripts/k_sweep/correlation_data.csv  (5 configs × 12 K × 2 methods = 120 rows max)
  scripts/k_sweep/plots/Q_vs_K.png             (one line per (config, method))
  scripts/k_sweep/plots/routing_vs_K.png
  scripts/k_sweep/plots/compression_vs_K.png
  scripts/k_sweep/plots/above_limit_vs_K.png
  scripts/k_sweep/plots/purity_vs_K.png

Pre-builds embeddings + FormulationInput once per config, then calls
``layerforge_core`` directly per (K, method) to avoid re-loading the
sentence-transformers model 120 times.
"""
from __future__ import annotations

import csv
import math
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np

from layerforge.core.modularity import build_similarity_matrix
from layerforge.core.scale_finder import compute_initial_scale, find_valid_scale
from layerforge.exceptions import NoValidScaleError
from layerforge.inference.embedding import SentenceTransformersEmbedding
from layerforge.pipeline import layerforge_core
from layerforge.schema.input_schema import (
    FormulationInput, Node, ScaleParams,
)

from scripts.halluc_benchmark.corpus import PASSAGES as SYNTHETIC_PASSAGES


import os
KDF_DOCS = Path(os.environ.get("LAYERFORGE_KDF_DOCS", "./test_corpus/kdf-docs"))
K_VALUES = [2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15, 20]


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


def _build_kdf_corpus(file_topic_map, per_theme: int):
    nodes = []
    truth = []
    for theme_label, filepath in file_topic_map:
        path = KDF_DOCS / filepath if not Path(filepath).is_absolute() else Path(filepath)
        text = path.read_text(encoding="utf-8")
        sections = _split_sections(text)
        stride = max(1, len(sections) // per_theme) if len(sections) >= per_theme else 1
        kept = [sections[i * stride] for i in range(min(per_theme, len(sections)))]
        for i, sec in enumerate(kept):
            nodes.append({"id": f"{theme_label}-{i:02d}", "text": sec})
            truth.append(theme_label)
    return nodes, truth


def _normalize(v):
    n = np.linalg.norm(v, axis=1, keepdims=True)
    return v / np.where(n == 0, 1.0, n)


def _self_routing(layers, passage_embeds, pids):
    pid_to_layer = {pid: l["id"] for l in layers for pid in l["member_node_ids"]}
    layer_ids = [l["id"] for l in layers]
    pid_to_idx = {pid: i for i, pid in enumerate(pids)}
    centroids = []
    for l in layers:
        idxs = [pid_to_idx[pid] for pid in l["member_node_ids"]]
        centroids.append(passage_embeds[idxs].mean(axis=0))
    cmat = _normalize(np.stack(centroids))
    qemb = _normalize(passage_embeds)
    chosen = np.argmax(qemb @ cmat.T, axis=1)
    correct = sum(1 for i, pid in enumerate(pids) if layer_ids[int(chosen[i])] == pid_to_layer[pid])
    return correct / len(pids) if pids else 0.0


def _above_limit_frac(passages, theta, layers, embeds):
    sim = build_similarity_matrix(embeds)
    A = (sim > theta).astype(float)
    np.fill_diagonal(A, 0.0)
    L = int(A.sum() // 2)
    if L == 0:
        return 0.0
    rl = math.sqrt(L / 2.0)
    pid_to_idx = {n["id"]: i for i, n in enumerate(passages)}
    above = 0
    for layer in layers:
        idx = [pid_to_idx[pid] for pid in layer["member_node_ids"]]
        e = int(A[np.ix_(idx, idx)].sum() // 2)
        if e > rl:
            above += 1
    return above / len(layers)


def _theme_purity(layers, pid_to_truth):
    purities = []
    for l in layers:
        themes = [pid_to_truth.get(pid) for pid in l["member_node_ids"]]
        themes = [t for t in themes if t is not None]
        if not themes:
            continue
        c = Counter(themes)
        purities.append(c.most_common(1)[0][1] / len(themes))
    if not purities:
        return (0.0, 0.0)
    return (sum(purities) / len(purities), min(purities))


def _layers_from_core(result) -> list[dict]:
    """Convert CoreResult.layers (dataclass) to the dict form the existing
    _self_routing / _theme_purity / _above_limit_frac helpers expect."""
    out = []
    for layer in result.layers:
        out.append({
            "id": layer.layer_id,
            "member_node_ids": [
                # member_indices are int positions; we still want the original
                # node IDs the helpers expect.
                None  # placeholder, filled below
                for _ in layer.member_indices
            ],
            "_indices": list(layer.member_indices),
        })
    return out


def sweep_config(label: str, nodes: list[dict], truth: list[str], embed_model: str, embedder: SentenceTransformersEmbedding | None = None):
    print(f"\n--- {label} (N={len(nodes)}, embedder={embed_model.split('/')[-1]}) ---")
    if embedder is None:
        embedder = SentenceTransformersEmbedding(model_name=embed_model)
    embeds = embedder.embed([n["text"] for n in nodes])
    sim = build_similarity_matrix(embeds)
    pid_to_truth = {n["id"]: t for n, t in zip(nodes, truth)}
    pids = [n["id"] for n in nodes]
    pid_by_idx = {i: n["id"] for i, n in enumerate(nodes)}

    formulation = FormulationInput(
        nodes=tuple(Node(id=n["id"], text=n["text"], metadata={"source": "correlation_data"})
                    for n in nodes),
        embeddings=embeds,
        similarity_matrix=sim,
        initial_scale=ScaleParams(threshold=compute_initial_scale(sim)),
    )

    rows = []
    for K in K_VALUES:
        if K >= len(nodes):
            continue
        for method in ("newman", "cpm"):
            try:
                result = layerforge_core(
                    formulation,
                    seed=42,
                    target_range=(K, K),
                    community_method=method,
                )
            except NoValidScaleError:
                # CPM γ-bisection may fail for some K targets
                continue
            except Exception as e:
                print(f"  K={K:>2} method={method}: {type(e).__name__}: {e}")
                continue
            # Build a layer dict list compatible with the existing helpers
            layers = [
                {
                    "id": layer.layer_id,
                    "member_node_ids": [pid_by_idx[i] for i in layer.member_indices],
                }
                for layer in result.layers
            ]
            # For Newman, theta is the threshold; for CPM, scale_coefficient is γ
            # — the above-limit reference graph for fair cross-comparison uses
            # the corpus-intrinsic median similarity (method-independent).
            n_loc = sim.shape[0]
            iu = np.triu_indices(n_loc, k=1)
            ref_theta = (
                float(result.quality_metrics.scale_coefficient)
                if method == "newman"
                else float(np.median(sim[iu]))
            )
            actual_K = int(result.quality_metrics.layer_count)
            Q = float(result.quality_metrics.modularity)
            qclass = result.quality_metrics.quality_class
            cpm_h = result.quality_metrics.cpm_h
            sr = _self_routing(layers, embeds, pids)
            comp = (sum(len(l["member_node_ids"]) for l in layers) / len(layers)) / len(nodes)
            above = _above_limit_frac(nodes, ref_theta, layers, embeds)
            pmean, pmin = _theme_purity(layers, pid_to_truth)
            row = {
                "config": label,
                "embedder": embed_model.split("/")[-1],
                "method": method,
                "N": len(nodes),
                "K_target": K,
                "K_actual": actual_K,
                "Q": round(Q, 4),
                "cpm_h": None if cpm_h is None else round(float(cpm_h), 4),
                "quality_class": qclass,
                "self_routing_acc": round(sr, 4),
                "compression_per_layer": round(comp, 4),
                "above_limit_frac": round(above, 4),
                "purity_mean": round(pmean, 4),
                "purity_min": round(pmin, 4),
            }
            rows.append(row)
            print(f"  K={K:>2} {method:<6}: Q={Q:.3f}, route={sr:.2f}, "
                  f"compr={comp:.3f}, above={above:.2f}, purity={pmean:.2f}")
    return rows


def main() -> int:
    out_dir = Path(__file__).resolve().parent
    plots_dir = out_dir / "plots"
    plots_dir.mkdir(exist_ok=True)

    # 5 configurations
    synth_passages = SYNTHETIC_PASSAGES
    synth_nodes = [{"id": p.id, "text": p.text} for p in synth_passages]
    synth_truth = [p.theme for p in synth_passages]

    same_domain = [
        ("phil", "KDF_Core_Philosophy.md"),
        ("apps", "KDF_Application_Areas.md"),
        ("ver",  "KDF_Verification_Report.md"),
        ("dev",  "KDF_Development_Journey.md"),
        ("lib",  "KDF_Library_Summary.md"),
    ]
    sd_nodes, sd_truth = _build_kdf_corpus(same_domain, per_theme=6)

    proofs_md = sorted((KDF_DOCS / "proofs").glob("*.md"))
    cross_domain = [
        ("phil",    "KDF_Core_Philosophy.md"),
        ("explore", "exploration/g11_hdfs_recurring_pre_reg.md"),
        ("proof",   str(proofs_md[0]) if proofs_md else "KDF_Verification_Report.md"),
        ("blog",    "blog/medium-en-draft.md"),
    ]
    cd_nodes, cd_truth = _build_kdf_corpus(cross_domain, per_theme=6)

    MINILM = "sentence-transformers/paraphrase-MiniLM-L3-v2"
    MPNET = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"

    configs = [
        ("synthetic-4theme (baseline, clean)",   synth_nodes, synth_truth, MINILM),
        ("same-domain-5theme",                    sd_nodes,    sd_truth,    MINILM),
        ("same-domain-5theme",                    sd_nodes,    sd_truth,    MPNET),
        ("cross-domain-4theme",                   cd_nodes,    cd_truth,    MINILM),
        ("cross-domain-4theme",                   cd_nodes,    cd_truth,    MPNET),
    ]

    # Cache one embedder per model to avoid reloading mpnet/MiniLM twice
    embedder_cache: dict[str, SentenceTransformersEmbedding] = {}
    all_rows = []
    for label, nodes, truth, model in configs:
        if model not in embedder_cache:
            print(f"\nLoading embedder once: {model.split('/')[-1]}")
            embedder_cache[model] = SentenceTransformersEmbedding(model_name=model)
        all_rows.extend(sweep_config(label, nodes, truth, model, embedder=embedder_cache[model]))

    # Write CSV
    csv_path = out_dir / "data_current" / "correlation_data.csv"
    csv_path.parent.mkdir(exist_ok=True)
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        if all_rows:
            writer = csv.DictWriter(f, fieldnames=list(all_rows[0].keys()))
            writer.writeheader()
            writer.writerows(all_rows)
    print(f"\nWrote {csv_path} ({len(all_rows)} rows)")

    # Plots
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not available, skipping plots")
        return 0

    # Group rows by (config, embedder, method) for separate series
    series = {}
    for row in all_rows:
        key = (row["config"], row["embedder"], row["method"])
        series.setdefault(key, []).append(row)
    for k in series:
        series[k].sort(key=lambda r: r["K_actual"])

    plot_specs = [
        ("Q", "Modularity Q vs K", "Q"),
        ("self_routing_acc", "Self-routing accuracy vs K", "self_routing_acc"),
        ("compression_per_layer", "Compression (avg layer / N) vs K", "compression_per_layer"),
        ("above_limit_frac", "Fortunato-Barthelemy above-limit fraction vs K", "above_limit_frac"),
        ("purity_mean", "Theme purity (mean) vs K", "purity_mean"),
    ]
    # Color by (config, embedder); marker/linestyle by method
    config_keys = sorted({(c, e) for (c, e, _) in series})
    color_for = {ck: plt.cm.tab10.colors[i % 10] for i, ck in enumerate(config_keys)}
    style_for = {"newman": ("o", "-"), "cpm": ("s", "--")}
    for metric, title, fname in plot_specs:
        plt.figure(figsize=(11, 6.5))
        for (config, embedder, method), rows in sorted(series.items()):
            color = color_for[(config, embedder)]
            marker, ls = style_for[method]
            xs = [r["K_actual"] for r in rows]
            ys = [r[metric] for r in rows]
            plt.plot(
                xs, ys,
                marker=marker, linestyle=ls,
                color=color,
                label=f"{config} [{embedder}] {method}",
                linewidth=1.3,
                markersize=5,
                alpha=0.9 if method == "newman" else 0.7,
            )
        plt.xlabel("K (number of layers)")
        plt.ylabel(metric)
        plt.title(f"{title}  (solid/o=Newman, dashed/□=CPM)")
        plt.grid(alpha=0.3)
        plt.legend(loc="best", fontsize=7)
        plt.tight_layout()
        out_png = plots_dir / f"{fname}_vs_K.png"
        plt.savefig(out_png, dpi=120)
        plt.close()
        print(f"  wrote {out_png}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
