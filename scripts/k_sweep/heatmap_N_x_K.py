"""N × K heatmap — corpus size 依存性の可視化, Newman vs CPM.

Cross-domain mpnet corpus を per_theme = 2,3,4,5,6,8,10 で構築 →
N ∈ {8, 12, 16, 20, 24, 32, 40} と K ∈ {2..15} のマトリックス × method ∈ {newman, cpm}。

各 (method) で Q / above_limit_frac の heatmap を描画、両者を side-by-side
で並べた dual-heatmap も生成。Pattern:
  - K_optimal が N / method に依存するか (Newman は bouncy、CPM は?)
  - above-limit fraction が N / method でどう動くか
  - 両 method の partition agreement (隣の cell の差)
"""
from __future__ import annotations

import csv
import math
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from layerforge.core.modularity import build_similarity_matrix
from layerforge.core.scale_finder import compute_initial_scale
from layerforge.exceptions import NoValidScaleError
from layerforge.inference.embedding import SentenceTransformersEmbedding
from layerforge.pipeline import layerforge_core
from layerforge.schema.input_schema import (
    FormulationInput, Node, ScaleParams,
)


import os
KDF_DOCS = Path(os.environ.get("LAYERFORGE_KDF_DOCS", "./test_corpus/kdf-docs"))
MPNET = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
PER_THEME_VALUES = [2, 3, 4, 5, 6, 8, 10]
K_VALUES = list(range(2, 16))


def _split_sections(text, min_len=80, max_len=2000):
    text = text.replace("\r\n", "\n")
    chunks = re.split(r"(?=^##+ )", text, flags=re.MULTILINE)
    keep = []
    for chunk in chunks:
        chunk = chunk.strip()
        if chunk:
            if len(chunk) > max_len:
                chunk = chunk[:max_len]
            if len(chunk) >= min_len:
                keep.append(chunk)
    return keep


def _build_cross_corpus(per_theme: int):
    proofs_md = sorted((KDF_DOCS / "proofs").glob("*.md"))
    mapping = [
        ("phil",    KDF_DOCS / "KDF_Core_Philosophy.md"),
        ("explore", KDF_DOCS / "exploration/g11_hdfs_recurring_pre_reg.md"),
        ("proof",   proofs_md[0] if proofs_md else KDF_DOCS / "KDF_Verification_Report.md"),
        ("blog",    KDF_DOCS / "blog/medium-en-draft.md"),
    ]
    nodes = []
    for label, path in mapping:
        secs = _split_sections(path.read_text(encoding="utf-8"))
        stride = max(1, len(secs) // per_theme) if len(secs) >= per_theme else 1
        kept = [secs[i * stride] for i in range(min(per_theme, len(secs)))]
        for i, sec in enumerate(kept):
            nodes.append({"id": f"{label}-{i:02d}", "text": sec})
    return nodes


def _above_limit_frac_indices(layers_indices, sim_dense, theta):
    A = (sim_dense > theta).astype(float)
    np.fill_diagonal(A, 0.0)
    L = int(A.sum() // 2)
    if L == 0:
        return 0.0
    rl = math.sqrt(L / 2.0)
    above = 0
    for idx in layers_indices:
        idx_l = list(idx)
        e = int(A[np.ix_(idx_l, idx_l)].sum() // 2)
        if e > rl:
            above += 1
    return above / len(layers_indices)


def main() -> int:
    out_dir = Path(__file__).resolve().parent
    embedder = SentenceTransformersEmbedding(model_name=MPNET)

    methods = ("newman", "cpm")
    # Cell matrices per method: Q[N_idx, K_idx], AB[N_idx, K_idx]
    Q_matrix: dict[str, np.ndarray] = {
        m: np.full((len(PER_THEME_VALUES), len(K_VALUES)), np.nan) for m in methods
    }
    AB_matrix: dict[str, np.ndarray] = {
        m: np.full((len(PER_THEME_VALUES), len(K_VALUES)), np.nan) for m in methods
    }
    N_actual = []

    total = len(PER_THEME_VALUES) * len(K_VALUES) * len(methods)
    print(f"Running {total} cells (N × K × method)...")
    for ni, per_theme in enumerate(PER_THEME_VALUES):
        nodes = _build_cross_corpus(per_theme)
        N = len(nodes)
        N_actual.append(N)
        print(f"  per_theme={per_theme}, N={N}")
        embeds = embedder.embed([n["text"] for n in nodes])
        sim = build_similarity_matrix(embeds)
        formulation = FormulationInput(
            nodes=tuple(Node(id=n["id"], text=n["text"], metadata={"source": "heatmap"})
                        for n in nodes),
            embeddings=embeds,
            similarity_matrix=sim,
            initial_scale=ScaleParams(threshold=compute_initial_scale(sim)),
        )
        # method-independent reference θ for above-limit
        iu = np.triu_indices(N, k=1)
        ref_theta_cpm = float(np.median(sim[iu]))
        for ki, K in enumerate(K_VALUES):
            if K >= N:
                continue
            for method in methods:
                try:
                    result = layerforge_core(
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
                # For Newman, scale_coefficient is θ; for CPM it's γ.
                # Use Newman θ for both above-limit calcs so the per-cell value
                # is comparable across methods at the same K.
                ref_theta = (
                    float(result.quality_metrics.scale_coefficient)
                    if method == "newman"
                    else ref_theta_cpm
                )
                Q_matrix[method][ni, ki] = float(result.quality_metrics.modularity)
                layers_idx = [tuple(layer.member_indices) for layer in result.layers]
                AB_matrix[method][ni, ki] = _above_limit_frac_indices(
                    layers_idx, sim, ref_theta
                )

    # CSV — long format with method column
    csv_path = out_dir / "data_current" / "heatmap_data.csv"
    csv_path.parent.mkdir(exist_ok=True)
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["per_theme", "N", "K", "method", "Q", "above_limit_frac"])
        for ni, pt in enumerate(PER_THEME_VALUES):
            for ki, K in enumerate(K_VALUES):
                for method in methods:
                    q = Q_matrix[method][ni, ki]
                    if not np.isnan(q):
                        w.writerow([pt, N_actual[ni], K, method,
                                    round(float(q), 4),
                                    round(float(AB_matrix[method][ni, ki]), 4)])
    print(f"\nWrote {csv_path}")

    # ---- Dual Q heatmaps (Newman | CPM) side-by-side ----
    fig, axes = plt.subplots(1, 2, figsize=(18, 6), constrained_layout=True)
    for ax, method in zip(axes, methods):
        M = Q_matrix[method]
        im = ax.imshow(
            M, aspect="auto", cmap="viridis",
            extent=(K_VALUES[0] - 0.5, K_VALUES[-1] + 0.5,
                    len(PER_THEME_VALUES) - 0.5, -0.5),
        )
        fig.colorbar(im, ax=ax, label="Modularity Q")
        ax.set_yticks(range(len(PER_THEME_VALUES)),
                      [f"N={n}" for n in N_actual])
        ax.set_xticks(K_VALUES, [str(k) for k in K_VALUES])
        ax.set_xlabel("K")
        ax.set_title(f"Q heatmap — {method}")
        for ni in range(len(PER_THEME_VALUES)):
            for ki in range(len(K_VALUES)):
                v = M[ni, ki]
                if not np.isnan(v):
                    ax.text(K_VALUES[ki], ni, f"{v:.2f}", ha="center", va="center",
                            fontsize=6, color="white" if v < 0.4 else "black")
    axes[0].set_ylabel("Corpus size N (per-theme passages varied)")
    fig.suptitle("Q heatmap: N × K — Newman vs CPM (cross-domain mpnet)")
    out_png = out_dir / "plots" / "heatmap_Q_N_x_K.png"
    fig.savefig(out_png, dpi=120)
    plt.close(fig)
    print(f"Wrote {out_png}")

    # ---- Dual above-limit heatmaps ----
    fig, axes = plt.subplots(1, 2, figsize=(18, 6), constrained_layout=True)
    for ax, method in zip(axes, methods):
        M = AB_matrix[method]
        im = ax.imshow(
            M, aspect="auto", cmap="RdYlGn",
            extent=(K_VALUES[0] - 0.5, K_VALUES[-1] + 0.5,
                    len(PER_THEME_VALUES) - 0.5, -0.5),
            vmin=0, vmax=1,
        )
        fig.colorbar(im, ax=ax, label="above-limit fraction")
        ax.set_yticks(range(len(PER_THEME_VALUES)),
                      [f"N={n}" for n in N_actual])
        ax.set_xticks(K_VALUES, [str(k) for k in K_VALUES])
        ax.set_xlabel("K")
        ax.set_title(f"Above-limit fraction — {method}")
        for ni in range(len(PER_THEME_VALUES)):
            for ki in range(len(K_VALUES)):
                v = M[ni, ki]
                if not np.isnan(v):
                    ax.text(K_VALUES[ki], ni, f"{v:.1f}", ha="center", va="center",
                            fontsize=6, color="black")
    axes[0].set_ylabel("Corpus size N")
    fig.suptitle("Above-limit fraction heatmap: N × K — Newman vs CPM")
    out_png2 = out_dir / "plots" / "heatmap_above_limit_N_x_K.png"
    fig.savefig(out_png2, dpi=120)
    plt.close(fig)
    print(f"Wrote {out_png2}")

    # ---- Per-N Q vs K line plot (dual method) ----
    plt.figure(figsize=(11, 6))
    colors = plt.cm.viridis(np.linspace(0.1, 0.9, len(PER_THEME_VALUES)))
    for ni, pt in enumerate(PER_THEME_VALUES):
        for method, ls, marker in (("newman", "-", "o"), ("cpm", "--", "s")):
            ys = [Q_matrix[method][ni, ki] for ki in range(len(K_VALUES))]
            plt.plot(
                K_VALUES, ys,
                ls + marker, color=colors[ni],
                label=f"N={N_actual[ni]} [{method}]" if ni == 0 else f"N={N_actual[ni]}" if method == "newman" else None,
                linewidth=1.2, markersize=4,
                alpha=0.9 if method == "newman" else 0.6,
            )
    plt.xlabel("K")
    plt.ylabel("Modularity Q")
    plt.title("Q vs K, varying corpus size N — solid=Newman, dashed=CPM")
    handles, labels = plt.gca().get_legend_handles_labels()
    # Dedupe labels
    seen = set(); keep_h, keep_l = [], []
    for h, l in zip(handles, labels):
        if l and l not in seen:
            seen.add(l); keep_h.append(h); keep_l.append(l)
    plt.legend(keep_h, keep_l, loc="best", fontsize=7)
    plt.grid(alpha=0.3)
    plt.tight_layout()
    out_png3 = out_dir / "plots" / "Q_vs_K_per_N.png"
    plt.savefig(out_png3, dpi=120)
    plt.close()
    print(f"Wrote {out_png3}")

    # Summary: K_optimal (Q peak) per N, both methods
    print("\n=== Q peak per N (both methods) ===")
    print(f"{'N':>4} | {'Newman K':>10} {'Newman Q':>10} | {'CPM K':>10} {'CPM Q':>10}")
    for ni, pt in enumerate(PER_THEME_VALUES):
        N = N_actual[ni]
        row_str = f"{N:>4} |"
        for method in methods:
            valid = [(K_VALUES[ki], Q_matrix[method][ni, ki]) for ki in range(len(K_VALUES))
                     if not np.isnan(Q_matrix[method][ni, ki])]
            if valid:
                best = max(valid, key=lambda x: x[1])
                row_str += f" {best[0]:>10} {best[1]:>10.3f} |"
            else:
                row_str += f" {'-':>10} {'-':>10} |"
        print(row_str)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
