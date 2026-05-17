"""Regenerate V-040 Pareto plots with English labels for v9 paper publication.

scope: chai 「論文は英語で公開、日本語にする必要はない」 直接応答、
docs/images/v040_plot*.png の日本語 label tofu 問題を英語化で resolve。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

_THIS_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _THIS_DIR.parent.parent.parent
_FIDELITY = _REPO_ROOT / "scripts" / "fidelity_recall"


def aggregate_evidence():
    """V-040 同 logic で全 verification 数値集約。"""
    ev = {"points": []}
    ev["points"].append({"vid": "V-004", "dataset": "WildChat", "n": 100,
                         "reduction": 0.930, "theme_cosine": 0.575,
                         "fact_substring": None, "color": "blue"})
    ev["points"].append({"vid": "V-007", "dataset": "WildChat F4", "n": 6,
                         "reduction": 0.85, "theme_cosine": 0.939, "theme_bertscore_roberta": 0.927,
                         "theme_bertscore_mbert": 0.838, "fact_substring": None, "color": "green"})
    with open(_FIDELITY / "v021_factual_recall_results.json", encoding="utf-8") as f:
        v021 = json.load(f)
    s = v021["summary"]
    ev["points"].append({"vid": "V-021", "dataset": "hotpotqa", "n": 10,
                         "reduction": s["reduction_chars"]["mean"],
                         "fact_substring": s["ans_in_compressed_substring"]["rate"],
                         "fact_tok_recall": s["tok_recall_compressed"]["mean"],
                         "theme_cosine": None, "color": "red"})
    with open(_FIDELITY / "v022_rouge_livedoor_results.json", encoding="utf-8") as f:
        v022 = json.load(f)
    s = v022["summary"]
    ev["points"].append({"vid": "V-022", "dataset": "livedoor", "n": 9,
                         "reduction": s["reduction_chars_mean"],
                         "theme_rougeL_lead": s["rougeL_decomposed_lead_mean"],
                         "fact_substring": None, "color": "orange"})
    ev["points"].append({"vid": "V-024", "dataset": "hotpotqa F3", "n": 5,
                         "reduction": 0.99, "downstream_accuracy": 0.0,
                         "downstream_baseline": 0.6, "refusal_rate": 1.0, "color": "darkred"})
    with open(_FIDELITY / "v024_bis_eval_result.json", encoding="utf-8") as f:
        v024b = json.load(f)
    ev["points"].append({"vid": "V-024-bis", "dataset": "hotpotqa F4", "n": 5,
                         "reduction": 0.838, "downstream_accuracy": v024b["f4_hybrid"]["contains"],
                         "downstream_baseline": v024b["baseline"]["contains"],
                         "refusal_rate": 0.0, "color": "purple"})
    with open(_FIDELITY / "v025_bertscore_retro_results.json", encoding="utf-8") as f:
        v025 = json.load(f)
    ev["points"].append({"vid": "V-025", "dataset": "WildChat F4 BERTScore", "n": 6,
                         "reduction": 0.85,
                         "theme_bertscore_roberta": v025["roberta_mean"],
                         "theme_bertscore_mbert": v025["mbert_mean"], "color": "green"})
    with open(_FIDELITY / "v029d_livedoor_title_bertscore_results.json", encoding="utf-8") as f:
        v029d = json.load(f)
    ev["points"].append({"vid": "V-029-d", "dataset": "livedoor JA title", "n": 27,
                         "reduction": 0.916,
                         "theme_bertscore_mbert": v029d["summary"]["decomposed_layerforge_vs_title_mean"],
                         "color": "olive"})
    with open(_FIDELITY / "v029f_cnndm_rouge_bertscore_results.json", encoding="utf-8") as f:
        v029f = json.load(f)
    ev["points"].append({"vid": "V-029-f", "dataset": "CNN/DM EN", "n": 10,
                         "reduction": 0.85,
                         "theme_bertscore_roberta": v029f["bertscore_f1"]["decomposed_mean"],
                         "color": "navy"})
    ev["reduction_only"] = [
        ("V-010-mtbench", "mt_bench_101", 0.77, "EN short"),
        ("V-010-jmulti-d", "jmultiwoz_JA_default", 0.16, "JA short default"),
        ("V-011", "loogle", 0.99, "EN long"),
        ("V-013", "livedoor_JA_default", 0.025, "JA mid default"),
        ("V-014", "livedoor_JA_MeCab", 0.864, "JA mid MeCab"),
        ("V-015", "jmultiwoz_JA_MeCab", 0.755, "JA short MeCab"),
        ("V-017", "jawiki_long", 0.937, "JA long MeCab"),
        ("V-018-sg", "ShareGPT", 0.977, "EN mid"),
        ("V-018-lb", "LongBench hotpot", 0.991, "EN long"),
        ("V-019-aozora", "Aozora", 0.993, "JA long MeCab"),
        ("V-019-bsd-mec", "BSD JA MeCab", 0.57, "JA short MeCab"),
        ("V-019-bsd-en", "BSD EN default", 0.40, "EN short"),
        ("V-019-bsd-jad", "BSD JA default", -0.05, "JA short default"),
    ]
    return ev


def plot_1(ev, out):
    fig, ax = plt.subplots(figsize=(10, 7))
    pts = []
    for p in ev["points"]:
        if p.get("theme_cosine") is not None:
            pts.append((p["reduction"], p["theme_cosine"], "cosine", p["vid"], p["dataset"]))
        if p.get("theme_bertscore_roberta") is not None:
            pts.append((p["reduction"], p["theme_bertscore_roberta"], "BERTScore-roberta", p["vid"], p["dataset"]))
        if p.get("theme_bertscore_mbert") is not None:
            pts.append((p["reduction"], p["theme_bertscore_mbert"], "BERTScore-mbert", p["vid"], p["dataset"]))
    markers = {"cosine": "o", "BERTScore-roberta": "s", "BERTScore-mbert": "^"}
    colors = {"cosine": "blue", "BERTScore-roberta": "green", "BERTScore-mbert": "orange"}
    seen = set()
    for red, fid, metric, vid, ds in pts:
        label = metric if metric not in seen else None
        seen.add(metric)
        ax.scatter(red, fid, marker=markers[metric], color=colors[metric], s=120, label=label, alpha=0.8, edgecolor="black")
        ax.annotate(f"{vid}\n{ds[:14]}", (red, fid), fontsize=7, xytext=(5, 5), textcoords="offset points")
    sorted_pts = sorted(pts, key=lambda x: x[0])
    pareto = []
    best_fid = -1
    for red, fid, metric, vid, ds in sorted_pts:
        if fid > best_fid:
            pareto.append((red, fid))
            best_fid = fid
    if len(pareto) >= 2:
        pareto.sort()
        xs, ys = zip(*pareto)
        ax.plot(xs, ys, "k--", alpha=0.4, linewidth=1.5, label="Pareto frontier (upper envelope)")
    ax.axhline(0.80, color="red", linestyle=":", alpha=0.5, label="ADR-022 Claim 2 threshold (0.80)")
    ax.axvline(0.90, color="purple", linestyle=":", alpha=0.5, label="Reduction PASS threshold (0.90)")
    ax.set_xlabel("Reduction (chars or tokens)")
    ax.set_ylabel("Theme-level fidelity (cosine / BERTScore F1)")
    ax.set_title("Plot 1: Reduction vs Theme-level Fidelity\n(upper-right = optimal; points on Pareto frontier dominate)")
    ax.legend(loc="lower left", fontsize=8)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, 1.05)
    ax.set_ylim(0, 1.05)
    fig.tight_layout()
    fig.savefig(out, dpi=120)
    plt.close(fig)
    return pareto


def plot_2(ev, out):
    fig, ax = plt.subplots(figsize=(10, 7))
    pts = []
    for p in ev["points"]:
        if p.get("fact_substring") is not None:
            pts.append((p["reduction"], p["fact_substring"], "substring", p["vid"], p["dataset"]))
        if p.get("downstream_accuracy") is not None:
            pts.append((p["reduction"], p["downstream_accuracy"], "LLM accuracy", p["vid"], p["dataset"]))
        if p.get("fact_tok_recall") is not None:
            pts.append((p["reduction"], p["fact_tok_recall"], "token recall", p["vid"], p["dataset"]))
    markers = {"substring": "o", "LLM accuracy": "x", "token recall": "+"}
    colors = {"substring": "red", "LLM accuracy": "darkred", "token recall": "orange"}
    seen = set()
    for red, fid, metric, vid, ds in pts:
        label = metric if metric not in seen else None
        seen.add(metric)
        ax.scatter(red, fid, marker=markers[metric], color=colors[metric], s=150, label=label, alpha=0.8)
        ax.annotate(f"{vid}\n{ds[:14]}", (red, fid), fontsize=7, xytext=(5, 5), textcoords="offset points")
    ax.axhline(0.70, color="green", linestyle=":", alpha=0.5, label="PRESERVE-PASS threshold (0.70)")
    ax.axhline(0.30, color="orange", linestyle=":", alpha=0.5, label="PRESERVE-PARTIAL threshold (0.30)")
    ax.set_xlabel("Reduction (chars or tokens)")
    ax.set_ylabel("Fact-level fidelity (substring rate / LLM accuracy)")
    ax.set_title("Plot 2: Reduction vs Fact-level Fidelity\n(all points below PRESERVE-PARTIAL threshold = quintuple-FAIL visualization)")
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, 1.05)
    ax.set_ylim(-0.1, 1.05)
    fig.tight_layout()
    fig.savefig(out, dpi=120)
    plt.close(fig)


def plot_3(ev, out):
    fig, ax = plt.subplots(figsize=(10, 7))
    pts = [
        (0.939, 0.0, "V-007 + V-024", "F3", "navy"),
        (0.939, 0.0, "V-007 + V-024-bis", "F4 hybrid", "purple"),
        (0.587, 0.10, "V-029-d + V-021 (proxy)", "cross-corpus", "olive"),
        (0.801, 0.10, "V-029-f + V-021 (proxy)", "cross-corpus EN", "navy"),
        (0.927, 0.10, "V-025 + V-021 (proxy)", "cross-corpus", "green"),
    ]
    for theme, fact, label, marker_label, color in pts:
        ax.scatter(theme, fact, s=200, color=color, alpha=0.7, edgecolor="black")
        ax.annotate(f"{label}\n({marker_label})", (theme, fact), fontsize=8, xytext=(8, 5), textcoords="offset points")
    ax.axhline(0.70, color="orange", linestyle=":", alpha=0.5, label="Fact PRESERVE-PASS (0.70)")
    ax.axvline(0.80, color="green", linestyle=":", alpha=0.5, label="Theme PASS (0.80)")
    ax.text(0.85, 0.85, "IDEAL\n(theme + fact both preserved)", fontsize=9, ha="center", color="gray")
    ax.text(0.85, 0.20, "Current LayerForge\n(theme PASS / fact FAIL)\n= Two-layer fidelity",
            fontsize=10, ha="center", color="darkblue", weight="bold")
    ax.text(0.30, 0.85, "Fact tool alone", fontsize=9, ha="center", color="gray")
    ax.text(0.30, 0.20, "Failure region", fontsize=9, ha="center", color="gray")
    ax.set_xlabel("Theme-level fidelity (cosine / BERTScore)")
    ax.set_ylabel("Fact-level fidelity (substring / accuracy)")
    ax.set_title("Plot 3: Theme x Fact Two-layer Fidelity Structure\n(LayerForge variants are in lower-right quadrant = theme PASS / fact FAIL)")
    ax.legend(loc="upper left", fontsize=8)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, 1.05)
    ax.set_ylim(-0.05, 1.05)
    fig.tight_layout()
    fig.savefig(out, dpi=120)
    plt.close(fig)


def plot_4(ev, out):
    fig, ax = plt.subplots(figsize=(12, 7))
    datasets = ev["reduction_only"]
    x = list(range(len(datasets)))
    reductions = [d[2] for d in datasets]
    labels = [d[3] for d in datasets]
    names = [d[1] for d in datasets]
    cmap = {
        "EN short": "skyblue", "EN long": "blue", "EN mid": "steelblue",
        "JA long MeCab": "darkgreen", "JA mid MeCab": "green", "JA short MeCab": "lightgreen",
        "JA mid default": "lightsalmon", "JA short default": "red",
    }
    colors = [cmap.get(l, "gray") for l in labels]
    ax.bar(x, reductions, color=colors, alpha=0.8, edgecolor="black")
    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("Reduction (chars)")
    ax.set_title("Plot 4: Reduction Landscape (14 datasets; color = language x tokenization)\n"
                 "Ceiling 99% (Aozora) language-agnostic confirmed; floor -5% (BSD JA default) = JA requires MeCab")
    handles = [plt.Rectangle((0, 0), 1, 1, color=c, label=l) for l, c in cmap.items()]
    ax.legend(handles=handles, loc="lower right", fontsize=8)
    ax.axhline(0.0, color="black", linewidth=0.5)
    ax.axhline(0.90, color="red", linestyle=":", alpha=0.5)
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(out, dpi=120)
    plt.close(fig)


def plot_5(ev, out):
    fig, ax = plt.subplots(figsize=(10, 7))
    pts = [
        (22006, 0.60, "Baseline (full 20k)", "blue"),
        (222, 0.0, "F3 pure (V-024 100% refusal)", "darkred"),
        (3561, 0.0, "F4 hybrid (V-024-bis 0% accuracy)", "purple"),
    ]
    pts_hyp = [
        (8000, 0.50, "F4 hybrid + RAG (hypothesis)", "green"),
    ]
    for tok, acc, label, color in pts:
        ax.scatter(tok, acc, s=200, color=color, alpha=0.8, edgecolor="black")
        ax.annotate(label, (tok, acc), fontsize=9, xytext=(8, 5), textcoords="offset points")
    for tok, acc, label, color in pts_hyp:
        ax.scatter(tok, acc, s=200, color=color, alpha=0.4, edgecolor="black", marker="^")
        ax.annotate(label, (tok, acc), fontsize=9, xytext=(8, 5), textcoords="offset points")
    ax.set_xscale("log")
    ax.set_xlabel("Input tokens (log scale; proxy for cost / latency)")
    ax.set_ylabel("Downstream LLM accuracy (contains rate)")
    ax.set_title("Plot 5: Cost vs Accuracy (operational sweet spot search)\n"
                 "Baseline 22k tokens at 60% accuracy is current best; F4 hybrid + RAG (hypothesis) is candidate intersection")
    ax.grid(True, alpha=0.3, which="both")
    ax.set_xlim(100, 50000)
    ax.set_ylim(-0.05, 1.0)
    fig.tight_layout()
    fig.savefig(out, dpi=120)
    plt.close(fig)


def main():
    print("Regenerating V-040 plots with English labels for v9 paper")
    print("=" * 60)
    ev = aggregate_evidence()
    out_dir = _THIS_DIR
    plot_1(ev, out_dir / "v040_plot1_reduction_vs_theme_fidelity_en.png")
    plot_2(ev, out_dir / "v040_plot2_reduction_vs_fact_fidelity_en.png")
    plot_3(ev, out_dir / "v040_plot3_theme_vs_fact_en.png")
    plot_4(ev, out_dir / "v040_plot4_reduction_landscape_en.png")
    plot_5(ev, out_dir / "v040_plot5_cost_vs_accuracy_en.png")
    print(f"Generated 5 plots in {out_dir}")


if __name__ == "__main__":
    main()
