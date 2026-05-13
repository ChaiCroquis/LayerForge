"""Newman vs CPM — empirical comparison on the same N×K matrix.

For the cross-domain mpnet corpus (the best-signal config from
correlation_data.py), build several N values and sweep K, then run BOTH
community detection methods. Output:

  - CSV: per (N, K, method) row with Q / cpm_h / actual_K / above-limit
  - Line plot: Q peak K vs N for both methods (the bouncy/stable test)
  - Plot: above-limit fraction vs K for both methods (one panel per N)

This is the measurement that docs/08 §4 future-work item asks for:
"Newman modularity vs CPM (Traag 2011) — empirical comparison".

Optimization: call ``layerforge_core`` directly with a pre-built
``FormulationInput``, so the sentence-transformers model is loaded ONCE
per N (not once per cell). Earlier draft via ``decompose_run`` reloaded
the 1.1GB mpnet model on every cell and hung.
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
from layerforge.inference.embedding import SentenceTransformersEmbedding
from layerforge.pipeline import layerforge_core
from layerforge.schema.input_schema import (
    FormulationInput, Node, ScaleParams,
)


KDF_DOCS = Path(os.environ.get("LAYERFORGE_KDF_DOCS", "./test_corpus/kdf-docs"))
MPNET = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
PER_THEME_VALUES = [3, 5, 6, 8, 10]  # gives N = 12, 20, 24, 32, 40
K_VALUES = [2, 3, 4, 5, 6, 7, 8, 9, 10, 12]


def _split_sections(text, min_len=80, max_len=2000):
    text = text.replace("\r\n", "\n")
    chunks = re.split(r"(?=^##+ )", text, flags=re.MULTILINE)
    out = []
    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
        if len(chunk) > max_len:
            chunk = chunk[:max_len]
        if len(chunk) >= min_len:
            out.append(chunk)
    return out


def _build_corpus(per_theme: int):
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


def _above_limit_frac(layers, sim, theta):
    A = (sim > theta).astype(float)
    np.fill_diagonal(A, 0.0)
    L = int(A.sum() // 2)
    if L == 0:
        return 0.0
    rl = math.sqrt(L / 2.0)
    above = 0
    for layer in layers:
        idx = list(layer.member_indices)
        e = int(A[np.ix_(idx, idx)].sum() // 2)
        if e > rl:
            above += 1
    return above / len(layers)


def main() -> int:
    out_dir = Path(__file__).resolve().parent
    plots_dir = out_dir / "plots"
    plots_dir.mkdir(exist_ok=True)

    if not KDF_DOCS.exists():
        print(f"[cpm_compare] corpus dir not found: {KDF_DOCS}", file=sys.stderr)
        print("  set LAYERFORGE_KDF_DOCS to a directory containing the test docs.",
              file=sys.stderr)
        return 2

    print(f"Loading sentence-transformers model once ({MPNET})...", flush=True)
    embedder = SentenceTransformersEmbedding(model_name=MPNET)

    rows: list[dict] = []
    n_actual: dict[int, int] = {}
    total_cells = len(PER_THEME_VALUES) * len(K_VALUES) * 2
    print(f"Running {total_cells} cells (N × K × method)...", flush=True)
    cell_count = 0

    for pt in PER_THEME_VALUES:
        raw_nodes = _build_corpus(pt)
        N = len(raw_nodes)
        n_actual[pt] = N
        texts = [n["text"] for n in raw_nodes]
        embeds = embedder.embed(texts)
        sim = build_similarity_matrix(embeds)
        formulation = FormulationInput(
            nodes=tuple(Node(id=n["id"], text=n["text"], metadata={"source": "cpm_compare"})
                        for n in raw_nodes),
            embeddings=embeds,
            similarity_matrix=sim,
            initial_scale=ScaleParams(threshold=compute_initial_scale(sim)),
        )
        # A common reference θ for above-limit cross-comparison: median
        # off-diagonal similarity (corpus-intrinsic, method-independent).
        iu = np.triu_indices(N, k=1)
        ref_theta = float(np.median(sim[iu]))
        print(f"  per_theme={pt}, N={N}, ref_theta={ref_theta:.3f}", flush=True)

        for K in K_VALUES:
            if K >= N:
                continue
            # Run both methods, hold labels for ARI/NMI cross-comparison
            per_method: dict[str, dict] = {}
            for method in ("newman", "cpm"):
                cell_count += 1
                try:
                    result = layerforge_core(
                        formulation,
                        seed=42,
                        target_range=(K, K),
                        community_method=method,
                    )
                except Exception as e:
                    print(f"    ! K={K} method={method}: {type(e).__name__}: {e}",
                          flush=True)
                    continue
                actual_k = int(result.quality_metrics.layer_count)
                Q = float(result.quality_metrics.modularity)
                cpm_h = result.quality_metrics.cpm_h
                gamma_or_theta = float(result.quality_metrics.scale_coefficient)
                above = _above_limit_frac(result.layers, sim, theta=ref_theta)
                # Reconstruct flat labels from layer membership
                labels = np.full(N, -1, dtype=np.int64)
                for layer in result.layers:
                    for idx in layer.member_indices:
                        labels[idx] = layer.layer_id
                per_method[method] = {
                    "labels": labels,
                    "actual_k": actual_k,
                    "Q": Q,
                    "cpm_h": cpm_h,
                    "scale_coef": gamma_or_theta,
                    "above": above,
                }

            # Compute ARI/NMI between Newman and CPM (only if both succeeded)
            ari_value: float | None = None
            nmi_value: float | None = None
            if "newman" in per_method and "cpm" in per_method:
                from sklearn.metrics import (
                    adjusted_rand_score,
                    normalized_mutual_info_score,
                )
                ari_value = float(adjusted_rand_score(
                    per_method["newman"]["labels"], per_method["cpm"]["labels"]
                ))
                nmi_value = float(normalized_mutual_info_score(
                    per_method["newman"]["labels"], per_method["cpm"]["labels"]
                ))

            for method, d in per_method.items():
                rows.append({
                    "per_theme": pt,
                    "N": N,
                    "K_target": K,
                    "K_actual": d["actual_k"],
                    "method": method,
                    "Q": round(d["Q"], 4),
                    "cpm_h": None if d["cpm_h"] is None else round(float(d["cpm_h"]), 4),
                    "scale_coef": round(d["scale_coef"], 4),
                    "above_limit_frac": round(d["above"], 4),
                    "ari_newman_vs_cpm": None if ari_value is None else round(ari_value, 4),
                    "nmi_newman_vs_cpm": None if nmi_value is None else round(nmi_value, 4),
                })
        print(f"  ... cells done so far: {cell_count}/{total_cells}", flush=True)

    csv_path = out_dir / "data_current" / "cpm_compare_data.csv"
    csv_path.parent.mkdir(exist_ok=True)
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        if rows:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
    print(f"\nWrote {csv_path} ({len(rows)} rows)", flush=True)

    if not rows:
        print("No rows produced — aborting plots.", flush=True)
        return 1

    # ---- Plot 1: Q peak K per N, both methods ----
    by_n_method: dict[tuple[int, str], list[tuple[int, float]]] = {}
    for r in rows:
        by_n_method.setdefault((r["N"], r["method"]), []).append(
            (r["K_actual"], r["Q"])
        )

    n_values = sorted({r["N"] for r in rows})
    peaks_newman = []
    peaks_cpm = []
    for N in n_values:
        for method, dst in (("newman", peaks_newman), ("cpm", peaks_cpm)):
            pairs = by_n_method.get((N, method), [])
            if pairs:
                best_k, best_q = max(pairs, key=lambda x: x[1])
                dst.append((N, best_k, best_q))
            else:
                dst.append((N, None, None))

    plt.figure(figsize=(10, 6))
    plt.plot(
        [p[0] for p in peaks_newman if p[1] is not None],
        [p[1] for p in peaks_newman if p[1] is not None],
        "-o", color="C0", label="Newman: K at Q peak",
    )
    plt.plot(
        [p[0] for p in peaks_cpm if p[1] is not None],
        [p[1] for p in peaks_cpm if p[1] is not None],
        "-s", color="C3", label="CPM: K at Q peak",
    )
    plt.xlabel("Corpus size N")
    plt.ylabel("K at Q peak")
    plt.title("Q-peak K vs N — Newman (bouncy) vs CPM")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    out_png = plots_dir / "cpm_vs_newman_Qpeak_K.png"
    plt.savefig(out_png, dpi=120)
    plt.close()
    print(f"Wrote {out_png}", flush=True)

    # ---- Plot 2: above-limit fraction vs K for each N, both methods ----
    fig, axes = plt.subplots(1, len(n_values), figsize=(4 * len(n_values), 4.5), sharey=True)
    if len(n_values) == 1:
        axes = [axes]
    for ax, N in zip(axes, n_values):
        for method, color in (("newman", "C0"), ("cpm", "C3")):
            pts = sorted(
                [(r["K_actual"], r["above_limit_frac"]) for r in rows
                 if r["N"] == N and r["method"] == method]
            )
            if not pts:
                continue
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            ax.plot(xs, ys, "-o" if method == "newman" else "-s",
                    color=color, label=method)
        ax.set_title(f"N={N}")
        ax.set_xlabel("K")
        ax.set_ylim(-0.05, 1.05)
        ax.grid(alpha=0.3)
    axes[0].set_ylabel("above-limit fraction")
    axes[-1].legend(loc="best", fontsize=9)
    fig.suptitle("Above-limit fraction vs K — Newman vs CPM")
    fig.tight_layout()
    out_png2 = plots_dir / "cpm_vs_newman_above_limit.png"
    fig.savefig(out_png2, dpi=120)
    plt.close(fig)
    print(f"Wrote {out_png2}", flush=True)

    # ---- Plot 3: ARI/NMI between Newman and CPM partitions vs K ----
    # One line per N. ARI=1 → identical partition, 0 → chance, <0 → worse.
    plt.figure(figsize=(10, 6))
    for N in n_values:
        pts = sorted(
            {
                (r["K_actual"], r["ari_newman_vs_cpm"])
                for r in rows
                if r["N"] == N and r["method"] == "newman"
                   and r["ari_newman_vs_cpm"] is not None
            }
        )
        if not pts:
            continue
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        plt.plot(xs, ys, "-o", label=f"N={N}", linewidth=1.4)
    plt.axhline(0.0, color="gray", linewidth=0.7, linestyle="--", label="chance")
    plt.axhline(1.0, color="green", linewidth=0.7, linestyle=":", alpha=0.5)
    plt.xlabel("K")
    plt.ylabel("ARI(Newman partition, CPM partition)")
    plt.title("Partition agreement: Newman vs CPM (ARI vs K, per N)")
    plt.legend(loc="best", fontsize=8)
    plt.grid(alpha=0.3)
    plt.tight_layout()
    out_png3 = plots_dir / "cpm_vs_newman_ari.png"
    plt.savefig(out_png3, dpi=120)
    plt.close()
    print(f"Wrote {out_png3}", flush=True)

    # ARI summary table
    print("\n=== ARI(Newman vs CPM) summary per N ===", flush=True)
    print(f"{'N':>4} {'ARI mean':>10} {'ARI min':>10} {'ARI max':>10} {'cells':>6}",
          flush=True)
    for N in n_values:
        aris = [
            r["ari_newman_vs_cpm"] for r in rows
            if r["N"] == N and r["method"] == "newman"
               and r["ari_newman_vs_cpm"] is not None
        ]
        if not aris:
            continue
        print(
            f"{N:>4} {np.mean(aris):>10.3f} {min(aris):>10.3f} "
            f"{max(aris):>10.3f} {len(aris):>6}",
            flush=True,
        )

    # ---- Summary ----
    print("\n=== Q peak K per N (Newman vs CPM) ===", flush=True)
    print(f"{'N':>4} {'Newman K':>10} {'Newman Q':>10} {'CPM K':>10} {'CPM Q':>10}",
          flush=True)
    for (N, k_n, q_n), (_, k_c, q_c) in zip(peaks_newman, peaks_cpm):
        print(
            f"{N:>4} {str(k_n):>10} {('%.3f' % q_n) if q_n is not None else '-':>10}"
            f" {str(k_c):>10} {('%.3f' % q_c) if q_c is not None else '-':>10}",
            flush=True,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
