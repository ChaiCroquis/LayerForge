"""Generate paper-publication-quality figures.

Two output sets:
1. `refined/` — re-renders of the existing 13 figures with paper-style:
   - 300 dpi
   - English labels (no Japanese)
   - Consistent Times-style serif font (matplotlib's default mathtext)
   - Tight margins, consistent color scheme

2. `new/` — three new figures for paper sections that previously had
   only tables:
   - figure_h_struct: §4.4 H_struct (Newman vs CPM K_actual vs n_themes)
   - figure_20ng_ari: §4.6 20NG ARI bar (Newman / CPM × K)
   - figure_cpm_mechanism: §5 CPM under-merging conceptual

Reads from `scripts/k_sweep/data_current/`. Writes to
`docs/paper/v8/figures/refined/` and `docs/paper/v8/figures/new/`.

Usage:
    python -X utf8 scripts/k_sweep/generate_paper_figures.py
"""
from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import rcParams


# ──────── Paper-publication style ────────
rcParams["figure.dpi"] = 100  # display
rcParams["savefig.dpi"] = 300  # save (publication quality)
rcParams["font.family"] = "serif"
rcParams["font.serif"] = ["DejaVu Serif", "Times New Roman", "Computer Modern Roman"]
rcParams["font.size"] = 11
rcParams["axes.labelsize"] = 12
rcParams["axes.titlesize"] = 13
rcParams["legend.fontsize"] = 9
rcParams["xtick.labelsize"] = 10
rcParams["ytick.labelsize"] = 10
rcParams["savefig.bbox"] = "tight"
rcParams["savefig.pad_inches"] = 0.05

# Consistent color scheme
COLOR_NEWMAN = "#1f77b4"  # blue
COLOR_CPM = "#d62728"     # red
COLOR_CHANCE = "#7f7f7f"  # gray
MARKER_NEWMAN = "o"
MARKER_CPM = "s"
LS_NEWMAN = "-"
LS_CPM = "--"


HERE = Path(__file__).resolve().parent
DATA_CURRENT = HERE / "data_current"
PAPER_ROOT = Path(__file__).resolve().parents[2] / "docs" / "paper" / "v8"
OUT_REFINED = PAPER_ROOT / "figures" / "refined"
OUT_NEW = PAPER_ROOT / "figures" / "new"
OUT_SUBMISSION = PAPER_ROOT / "submission" / "figures"  # vector PDF for submission
OUT_REFINED.mkdir(parents=True, exist_ok=True)
OUT_NEW.mkdir(parents=True, exist_ok=True)
OUT_SUBMISSION.mkdir(parents=True, exist_ok=True)


def _save_both(fig, basename: str, refined: bool = True):
    """Save PNG (paper folder) and vector PDF (submission folder)."""
    target_png = OUT_REFINED if refined else OUT_NEW
    fig.savefig(target_png / f"{basename}.png")
    fig.savefig(OUT_SUBMISSION / f"{basename}.pdf")  # vector for submission


# ──────── Refined existing figures (subset re-render with paper style) ────────

def refined_Q_vs_K_per_N():
    """heatmap_data.csv — Newman Q peak K bouncy across N."""
    data = list(csv.DictReader(open(DATA_CURRENT / "heatmap_data.csv")))
    K_vals = sorted(set(int(d["K"]) for d in data))
    N_vals = sorted(set(int(d["N"]) for d in data))

    fig, ax = plt.subplots(figsize=(7, 4.5))
    colors = plt.cm.viridis(np.linspace(0.15, 0.9, len(N_vals)))
    for ni, N in enumerate(N_vals):
        for method, ls, marker in (("newman", LS_NEWMAN, MARKER_NEWMAN), ("cpm", LS_CPM, MARKER_CPM)):
            xs, ys = [], []
            for d in data:
                if int(d["N"]) == N and d["method"] == method:
                    xs.append(int(d["K"]))
                    ys.append(float(d["Q"]))
            if not xs:
                continue
            order = np.argsort(xs)
            xs = np.array(xs)[order]
            ys = np.array(ys)[order]
            ax.plot(xs, ys, ls, marker=marker, color=colors[ni],
                    label=f"N={N} ({method})" if method == "newman" else None,
                    linewidth=1.1, markersize=4, alpha=0.95 if method == "newman" else 0.55)
    ax.set_xlabel("K (number of layers)")
    ax.set_ylabel("Modularity Q")
    ax.set_title("Q vs K, varying corpus size N (Newman solid, CPM dashed)")
    ax.grid(alpha=0.3)
    ax.legend(loc="best", fontsize=8, ncol=2)
    fig.savefig(OUT_REFINED / "Q_vs_K_per_N.png")
    fig.savefig(OUT_SUBMISSION / "Q_vs_K_per_N.pdf")
    plt.close(fig)
    print(f"  wrote {OUT_REFINED / 'Q_vs_K_per_N.png'}")


def refined_heatmap_Q():
    """Dual-panel Q heatmap (Newman | CPM)."""
    data = list(csv.DictReader(open(DATA_CURRENT / "heatmap_data.csv")))
    K_vals = sorted(set(int(d["K"]) for d in data))
    N_vals = sorted(set(int(d["N"]) for d in data))

    fig, axes = plt.subplots(1, 2, figsize=(14, 5), constrained_layout=True)
    for ax, method in zip(axes, ("newman", "cpm")):
        M = np.full((len(N_vals), len(K_vals)), np.nan)
        for d in data:
            if d["method"] != method:
                continue
            i = N_vals.index(int(d["N"]))
            j = K_vals.index(int(d["K"]))
            M[i, j] = float(d["Q"])
        im = ax.imshow(M, aspect="auto", cmap="viridis",
                       extent=(K_vals[0] - 0.5, K_vals[-1] + 0.5, len(N_vals) - 0.5, -0.5))
        fig.colorbar(im, ax=ax, label="Modularity Q")
        ax.set_yticks(range(len(N_vals)), [f"N={n}" for n in N_vals])
        ax.set_xticks(K_vals, [str(k) for k in K_vals])
        ax.set_xlabel("K")
        ax.set_title(f"{method.upper()}")
        for i, _ in enumerate(N_vals):
            for j, _ in enumerate(K_vals):
                if not np.isnan(M[i, j]):
                    ax.text(K_vals[j], i, f"{M[i,j]:.2f}", ha="center", va="center",
                            fontsize=6, color="white" if M[i, j] < 0.4 else "black")
    axes[0].set_ylabel("Corpus size N")
    fig.suptitle("Modularity Q heatmap: N × K — Newman vs CPM (cross-domain mpnet)")
    fig.savefig(OUT_REFINED / "heatmap_Q_N_x_K.png")
    fig.savefig(OUT_SUBMISSION / "heatmap_Q_N_x_K.pdf")
    plt.close(fig)
    print(f"  wrote {OUT_REFINED / 'heatmap_Q_N_x_K.png'}")


def refined_heatmap_above_limit():
    """Dual-panel above-limit fraction heatmap."""
    data = list(csv.DictReader(open(DATA_CURRENT / "heatmap_data.csv")))
    K_vals = sorted(set(int(d["K"]) for d in data))
    N_vals = sorted(set(int(d["N"]) for d in data))

    fig, axes = plt.subplots(1, 2, figsize=(14, 5), constrained_layout=True)
    for ax, method in zip(axes, ("newman", "cpm")):
        M = np.full((len(N_vals), len(K_vals)), np.nan)
        for d in data:
            if d["method"] != method:
                continue
            i = N_vals.index(int(d["N"]))
            j = K_vals.index(int(d["K"]))
            M[i, j] = float(d["above_limit_frac"])
        im = ax.imshow(M, aspect="auto", cmap="RdYlGn", vmin=0, vmax=1,
                       extent=(K_vals[0] - 0.5, K_vals[-1] + 0.5, len(N_vals) - 0.5, -0.5))
        fig.colorbar(im, ax=ax, label="above-limit fraction")
        ax.set_yticks(range(len(N_vals)), [f"N={n}" for n in N_vals])
        ax.set_xticks(K_vals, [str(k) for k in K_vals])
        ax.set_xlabel("K")
        ax.set_title(f"{method.upper()}")
        for i, _ in enumerate(N_vals):
            for j, _ in enumerate(K_vals):
                if not np.isnan(M[i, j]):
                    ax.text(K_vals[j], i, f"{M[i,j]:.1f}", ha="center", va="center",
                            fontsize=6, color="black")
    axes[0].set_ylabel("Corpus size N")
    fig.suptitle("Above-limit fraction (Fortunato-Barthélemy): N × K — Newman vs CPM")
    fig.savefig(OUT_REFINED / "heatmap_above_limit_N_x_K.png")
    fig.savefig(OUT_SUBMISSION / "heatmap_above_limit_N_x_K.pdf")
    plt.close(fig)
    print(f"  wrote {OUT_REFINED / 'heatmap_above_limit_N_x_K.png'}")


def refined_ari_vs_K():
    """ARI(Newman, CPM) vs K, per N."""
    data = list(csv.DictReader(open(DATA_CURRENT / "cpm_compare_data.csv")))
    fig, ax = plt.subplots(figsize=(7, 4.5))
    seen = set()
    by_n = {}
    for d in data:
        if d.get("ari_newman_vs_cpm", "") in ("", None):
            continue
        key = (int(d["N"]), int(d["K_actual"]))
        if key in seen:
            continue
        seen.add(key)
        by_n.setdefault(int(d["N"]), []).append((int(d["K_actual"]), float(d["ari_newman_vs_cpm"])))
    n_vals = sorted(by_n)
    colors = plt.cm.viridis(np.linspace(0.15, 0.9, len(n_vals)))
    for c, N in zip(colors, n_vals):
        pairs = sorted(by_n[N])
        xs = [p[0] for p in pairs]
        ys = [p[1] for p in pairs]
        ax.plot(xs, ys, "-o", color=c, label=f"N={N}", linewidth=1.3, markersize=5)
    ax.axhline(0.0, color=COLOR_CHANCE, linewidth=0.7, linestyle="--", label="chance baseline")
    ax.axhline(1.0, color="green", linewidth=0.7, linestyle=":", alpha=0.5, label="perfect match")
    ax.set_xlabel("K")
    ax.set_ylabel("ARI (Newman partition, CPM partition)")
    ax.set_title("Partition agreement between methods, by corpus size N")
    ax.legend(loc="best", fontsize=9)
    ax.grid(alpha=0.3)
    fig.savefig(OUT_REFINED / "cpm_vs_newman_ari.png")
    fig.savefig(OUT_SUBMISSION / "cpm_vs_newman_ari.pdf")
    plt.close(fig)
    print(f"  wrote {OUT_REFINED / 'cpm_vs_newman_ari.png'}")


def refined_self_routing():
    """Self-routing accuracy vs K (5 configs × 2 methods)."""
    data = list(csv.DictReader(open(DATA_CURRENT / "correlation_data.csv")))
    series = {}
    for d in data:
        key = (d["config"], d["embedder"], d["method"])
        series.setdefault(key, []).append((int(d["K_actual"]), float(d["self_routing_acc"])))

    config_keys = sorted({(c, e) for (c, e, _) in series})
    colors = {ck: plt.cm.tab10.colors[i % 10] for i, ck in enumerate(config_keys)}
    fig, ax = plt.subplots(figsize=(8, 5))
    for (config, embedder, method), pts in sorted(series.items()):
        pts.sort()
        xs, ys = zip(*pts)
        c = colors[(config, embedder)]
        marker, ls, alpha = (MARKER_NEWMAN, LS_NEWMAN, 0.95) if method == "newman" else (MARKER_CPM, LS_CPM, 0.65)
        ax.plot(xs, ys, ls + marker, color=c,
                label=f"{config[:25]} [{embedder[:6]}] {method}",
                linewidth=1.1, markersize=4, alpha=alpha)
    ax.axvline(10, color="black", linestyle=":", alpha=0.4, linewidth=1)
    ax.text(10.3, 0.05, "K=10\n(AI cost target)", fontsize=8, alpha=0.7)
    ax.set_xlabel("K")
    ax.set_ylabel("Self-routing accuracy")
    ax.set_title("Self-routing accuracy vs K — Newman (solid) vs CPM (dashed)")
    ax.legend(loc="lower left", fontsize=6, ncol=2)
    ax.grid(alpha=0.3)
    ax.set_ylim(-0.05, 1.1)
    fig.savefig(OUT_REFINED / "self_routing_acc_vs_K.png")
    fig.savefig(OUT_SUBMISSION / "self_routing_acc_vs_K.pdf")
    plt.close(fig)
    print(f"  wrote {OUT_REFINED / 'self_routing_acc_vs_K.png'}")


def refined_pareto_compression():
    """Q vs compression Pareto."""
    data = list(csv.DictReader(open(DATA_CURRENT / "correlation_data.csv")))
    series = {}
    for d in data:
        key = (d["config"], d["embedder"], d["method"])
        series.setdefault(key, []).append((float(d["compression_per_layer"]), float(d["Q"]),
                                            int(d["K_actual"])))
    config_keys = sorted({(c, e) for (c, e, _) in series})
    colors = {ck: plt.cm.tab10.colors[i % 10] for i, ck in enumerate(config_keys)}
    fig, ax = plt.subplots(figsize=(8, 5))
    annotate_K = {2, 4, 5, 10, 15, 20}
    for (config, embedder, method), pts in sorted(series.items()):
        pts.sort()
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        c = colors[(config, embedder)]
        marker, ls, alpha = (MARKER_NEWMAN, LS_NEWMAN, 0.95) if method == "newman" else (MARKER_CPM, LS_CPM, 0.65)
        ax.plot(xs, ys, ls + marker, color=c,
                label=f"{config[:25]} [{embedder[:6]}] {method}",
                linewidth=1.0, markersize=4, alpha=alpha)
        if method == "newman":
            for x, y, k in pts:
                if k in annotate_K:
                    ax.annotate(f"K={k}", (x, y), fontsize=7, xytext=(3, 3),
                                textcoords="offset points", color=c)
    ax.set_xlabel("Compression per layer (avg layer / N) — smaller = more compression")
    ax.set_ylabel("Modularity Q")
    ax.set_title("Pareto: Q vs Compression")
    ax.legend(loc="upper right", fontsize=6)
    ax.grid(alpha=0.3)
    fig.savefig(OUT_REFINED / "pareto_Q_vs_compression.png")
    fig.savefig(OUT_SUBMISSION / "pareto_Q_vs_compression.pdf")
    plt.close(fig)
    print(f"  wrote {OUT_REFINED / 'pareto_Q_vs_compression.png'}")


# ──────── New figures ────────

def new_fig_h_struct():
    """§4.4 H_struct: K_actual vs n_themes per method (scatter + diagonal)."""
    data = json.load(open(DATA_CURRENT / "robustness_results.json"))
    fig, axes = plt.subplots(1, 2, figsize=(11, 5), sharex=True, sharey=True,
                             constrained_layout=True)
    for ax, method in zip(axes, ("newman", "cpm")):
        rows = [d for d in data if d["method"] == method]
        # Group by embedder for color
        for emb, color in (("MiniLM-L3", "#1f77b4"), ("mpnet", "#ff7f0e")):
            sub = [d for d in rows if d["embedder"] == emb]
            xs = [d["n_themes"] for d in sub]
            ys = [d["peak_Q_at_K"] for d in sub]
            ax.scatter(xs, ys, color=color, s=80, alpha=0.7, label=emb,
                       edgecolors="black", linewidths=0.5)
        # Diagonal: perfect tracking
        diag = np.linspace(2, 13, 50)
        ax.plot(diag, diag, "k:", linewidth=1, alpha=0.5, label="K = n_themes (perfect)")
        ax.set_xlim(2, 13)
        ax.set_ylim(0, 13)
        ax.set_xlabel("n_themes (ground truth)")
        ax.set_xticks([3, 4, 5, 7])
        match = sum(1 for d in rows if d["peak_Q_at_K"] == d["n_themes"])
        ax.set_title(f"{method.upper()}: {match}/{len(rows)} exact match "
                     f"({match/len(rows)*100:.1f}%)")
        ax.grid(alpha=0.3)
        ax.legend(loc="upper left", fontsize=9)
    axes[0].set_ylabel("Q peak K (predicted)")
    fig.suptitle("H_struct: does Q peak K track n_themes?\n"
                 "(16 settings = 4 n_themes × 2 embedders × 2 seeds)",
                 fontsize=12)
    fig.savefig(OUT_NEW / "fig_h_struct.png")
    fig.savefig(OUT_SUBMISSION / "fig_h_struct.pdf")
    plt.close(fig)
    print(f"  wrote {OUT_NEW / 'fig_h_struct.png'}")


def new_fig_20ng_ari():
    """§4.6 20NG ARI bar: Newman / CPM × K=3,4,5."""
    # Measured values (from PR #14 live re-run; reproducible)
    K_vals = [3, 4, 5]
    newman_aris = [0.430, 0.557, 0.313]
    cpm_aris = [0.239, 0.238, 0.240]

    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    x = np.arange(len(K_vals))
    width = 0.35
    bars1 = ax.bar(x - width/2, newman_aris, width, label="Newman",
                   color=COLOR_NEWMAN, edgecolor="black", linewidth=0.5)
    bars2 = ax.bar(x + width/2, cpm_aris, width, label="CPM",
                   color=COLOR_CPM, edgecolor="black", linewidth=0.5)
    ax.axhline(0.0, color=COLOR_CHANCE, linewidth=0.7, linestyle="--", label="chance baseline")
    # Annotate default K marker
    ax.annotate("default K (find_valid_scale)", xy=(0, 0.430), xytext=(0, 0.65),
                ha="center", fontsize=8,
                arrowprops=dict(arrowstyle="->", color="gray", lw=0.7))
    # Annotate best Newman
    ax.annotate(f"Newman best:\nK=4, ARI=0.557", xy=(1 - width/2, 0.557),
                xytext=(1.5, 0.75), fontsize=8,
                arrowprops=dict(arrowstyle="->", color=COLOR_NEWMAN, lw=0.7))
    # Bar value labels
    for bar, v in zip(bars1, newman_aris):
        ax.text(bar.get_x() + bar.get_width()/2, v + 0.015, f"{v:.3f}",
                ha="center", va="bottom", fontsize=9, color=COLOR_NEWMAN, fontweight="bold")
    for bar, v in zip(bars2, cpm_aris):
        ax.text(bar.get_x() + bar.get_width()/2, v + 0.015, f"{v:.3f}",
                ha="center", va="bottom", fontsize=9, color=COLOR_CPM, fontweight="bold")
    ax.set_xticks(x, [f"K={k}" for k in K_vals])
    ax.set_xlabel("Number of layers K (target_range = (3, 5))")
    ax.set_ylabel("ARI vs ground truth (4 newsgroups)")
    ax.set_title("20 Newsgroups (N=100, 4 topics): ARI by method × K")
    ax.set_ylim(-0.05, 0.85)
    ax.legend(loc="upper right", fontsize=9)
    ax.grid(alpha=0.3, axis="y")
    fig.savefig(OUT_NEW / "fig_20ng_ari.png")
    fig.savefig(OUT_SUBMISSION / "fig_20ng_ari.pdf")
    plt.close(fig)
    print(f"  wrote {OUT_NEW / 'fig_20ng_ari.png'}")


def new_fig_cpm_mechanism():
    """§5 CPM under-merging conceptual: penalty term vs cluster size."""
    n_c = np.arange(1, 21)
    # CPM penalty per community: γ × (n_c choose 2) = γ × n_c(n_c-1)/2
    gamma_low, gamma_high = 0.05, 0.2
    cpm_low = gamma_low * n_c * (n_c - 1) / 2
    cpm_high = gamma_high * n_c * (n_c - 1) / 2
    # Newman null model expected edges for cluster of size n_c (rough)
    # Q's null is k_i k_j / 2L, summed over pairs in cluster → ∝ (sum k_i)² / (2L)
    # For a graph with avg degree d, this scales linearly in cluster size at fixed d
    # For comparison, plot a linear reference
    newman_ref = 0.5 * n_c  # illustrative linear scaling

    fig, ax = plt.subplots(figsize=(7.5, 5))
    ax.plot(n_c, cpm_low, "-", color=COLOR_CPM, linewidth=2,
            label=f"CPM penalty γ × (n_c choose 2), γ = {gamma_low}")
    ax.plot(n_c, cpm_high, "--", color=COLOR_CPM, linewidth=2, alpha=0.6,
            label=f"CPM penalty γ × (n_c choose 2), γ = {gamma_high}")
    ax.plot(n_c, newman_ref, ":", color=COLOR_NEWMAN, linewidth=2,
            label="Newman null-model contribution (linear ref)")
    # Shade "under-merging zone" where CPM penalty dominates
    ax.fill_between(n_c, cpm_low, newman_ref, where=(cpm_low > newman_ref),
                    color=COLOR_CPM, alpha=0.1, label="under-merging zone\n(CPM penalty > Newman null)")
    ax.set_xlabel("Community size n_c")
    ax.set_ylabel("Penalty / null contribution (illustrative units)")
    ax.set_title("CPM quadratic penalty vs Newman null contribution\n"
                 "(why CPM under-merges in small-N text domain)")
    ax.legend(loc="upper left", fontsize=8)
    ax.grid(alpha=0.3)
    ax.set_xlim(1, 20)
    ax.annotate("Newman: linear-ish\nin cluster size",
                xy=(10, 5), xytext=(12, 3), fontsize=9,
                arrowprops=dict(arrowstyle="->", color=COLOR_NEWMAN, lw=0.7),
                color=COLOR_NEWMAN)
    ax.annotate("CPM: quadratic\n→ large clusters\npenalized heavily",
                xy=(15, cpm_low[14]), xytext=(7, 12), fontsize=9,
                arrowprops=dict(arrowstyle="->", color=COLOR_CPM, lw=0.7),
                color=COLOR_CPM)
    fig.savefig(OUT_NEW / "fig_cpm_mechanism.png")
    fig.savefig(OUT_SUBMISSION / "fig_cpm_mechanism.pdf")
    plt.close(fig)
    print(f"  wrote {OUT_NEW / 'fig_cpm_mechanism.png'}")


# ──────── Main ────────

def main() -> int:
    print("=== Refined figures (paper publication style) ===")
    refined_Q_vs_K_per_N()
    refined_heatmap_Q()
    refined_heatmap_above_limit()
    refined_ari_vs_K()
    refined_self_routing()
    refined_pareto_compression()

    print("\n=== New figures (paper sections previously table-only) ===")
    new_fig_h_struct()
    new_fig_20ng_ari()
    new_fig_cpm_mechanism()

    print("\nAll figures written to:")
    print(f"  refined: {OUT_REFINED}")
    print(f"  new:     {OUT_NEW}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
