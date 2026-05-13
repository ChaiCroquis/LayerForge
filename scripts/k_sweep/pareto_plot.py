"""Q × compression Pareto frontier plot.

Reads correlation_data.csv and plots each (K, config) as a point in
(compression, Q) space. The Pareto frontier shows configurations where
no other point has BOTH higher compression AND higher Q.

For AI cost optimization, the relevant point is "high compression, Q
still acceptable". K=10 typically sits near the frontier.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


HERE = Path(__file__).resolve().parent


def main() -> int:
    csv_path = HERE / "data_current" / "correlation_data.csv"
    rows = list(csv.DictReader(csv_path.open(encoding="utf-8")))
    for r in rows:
        r["Q"] = float(r["Q"])
        r["compression_per_layer"] = float(r["compression_per_layer"])
        r["K_actual"] = int(r["K_actual"])
        r["above_limit_frac"] = float(r["above_limit_frac"])
        # method column may or may not exist depending on CSV vintage
        r["method"] = r.get("method", "newman")

    # Group by (config, embedder, method) for separate series
    series = {}
    for r in rows:
        key = (r["config"], r["embedder"], r["method"])
        series.setdefault(key, []).append(r)

    # Color by (config, embedder); linestyle/marker by method
    config_keys = sorted({(c, e) for (c, e, _) in series})
    color_for = {ck: plt.cm.tab10.colors[i % 10] for i, ck in enumerate(config_keys)}
    style_for = {"newman": ("o", "-"), "cpm": ("s", "--")}
    annotate_K = {2, 4, 5, 10, 15, 20}

    plt.figure(figsize=(12, 7))
    for (config, embedder, method), items in sorted(series.items()):
        items.sort(key=lambda x: x["compression_per_layer"])
        xs = [r["compression_per_layer"] for r in items]
        ys = [r["Q"] for r in items]
        color = color_for[(config, embedder)]
        marker, ls = style_for.get(method, ("o", "-"))
        plt.plot(
            xs, ys, marker=marker, linestyle=ls,
            color=color, label=f"{config} [{embedder}] {method}",
            linewidth=1.1, markersize=5,
            alpha=0.9 if method == "newman" else 0.65,
        )
        # Annotate Newman-side selected K only (avoid clutter)
        if method == "newman":
            for r in items:
                if r["K_actual"] in annotate_K:
                    plt.annotate(
                        f"K={r['K_actual']}",
                        (r["compression_per_layer"], r["Q"]),
                        fontsize=7,
                        xytext=(4, 4),
                        textcoords="offset points",
                        color=color,
                    )

    # Highlight K=10 across configs with a vertical band (mean across all rows)
    k10_compressions = [r["compression_per_layer"] for r in rows if r["K_actual"] == 10]
    if k10_compressions:
        plt.axvline(x=sum(k10_compressions) / len(k10_compressions), color="black",
                    linestyle="--", alpha=0.4, linewidth=1)
        plt.text(0.105, 0.0, "K=10 (AI cost candidate)", fontsize=8, alpha=0.6, rotation=90)

    plt.xlabel("Compression per layer (avg layer size / N) — smaller = more compression")
    plt.ylabel("Modularity Q — higher = better algorithmic cohesion")
    plt.title("Pareto: Q vs Compression — Newman (solid/o) vs CPM (dashed/□)")
    plt.grid(alpha=0.3)
    plt.legend(loc="upper right", fontsize=7)
    plt.tight_layout()
    out_png = HERE / "plots" / "pareto_Q_vs_compression.png"
    plt.savefig(out_png, dpi=120)
    plt.close()
    print(f"Wrote {out_png}")

    # Q vs above-limit Pareto
    plt.figure(figsize=(12, 7))
    for (config, embedder, method), items in sorted(series.items()):
        items.sort(key=lambda x: x["above_limit_frac"])
        xs = [r["above_limit_frac"] for r in items]
        ys = [r["Q"] for r in items]
        color = color_for[(config, embedder)]
        marker, ls = style_for.get(method, ("o", "-"))
        plt.plot(
            xs, ys, marker=marker, linestyle=ls,
            color=color, label=f"{config} [{embedder}] {method}",
            linewidth=1.1, markersize=5,
            alpha=0.9 if method == "newman" else 0.65,
        )
        if method == "newman":
            for r in items:
                if r["K_actual"] in annotate_K:
                    plt.annotate(
                        f"K={r['K_actual']}",
                        (r["above_limit_frac"], r["Q"]),
                        fontsize=7,
                        xytext=(4, 4),
                        textcoords="offset points",
                        color=color,
                    )
    plt.xlabel("Above-limit fraction (Fortunato-Barthélemy) — fraction of communities above √(L/2)")
    plt.ylabel("Modularity Q")
    plt.title("Pareto: Q vs above-limit — Newman (solid/o) vs CPM (dashed/□)")
    plt.grid(alpha=0.3)
    plt.legend(loc="upper left", fontsize=7)
    plt.tight_layout()
    out_png2 = HERE / "plots" / "pareto_Q_vs_above_limit.png"
    plt.savefig(out_png2, dpi=120)
    plt.close()
    print(f"Wrote {out_png2}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
