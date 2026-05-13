"""Performance benchmark for LayerForge deterministic core (Phase 1+2a/b).

Measures end-to-end `layerforge.cli.decompose.run()` latency across input
sizes, using deterministic hash embeddings so the result is reproducible
and network-free. Prints a markdown-friendly table.

Usage:
    python scripts/benchmark.py                     # default n=10,100,1000,3000
    python scripts/benchmark.py --sizes 10 100 1000 10000
    python scripts/benchmark.py --json results.json # also dump structured output
"""
from __future__ import annotations

import argparse
import gc
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

# Make `layerforge` importable when invoked from the repo root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from layerforge.cli import decompose


DEFAULT_SIZES: tuple[int, ...] = (10, 100, 1000, 3000)
THEMES_PER_GROUP: int = 4  # Always 4 themes; group size = n / 4.


def _synthetic_nodes(n: int) -> list[dict]:
    """Generate n nodes evenly split across 4 disjoint synthetic vocabularies.

    Each theme has a vocabulary that scales with input size (pool_size = max(32,
    per_theme//4)) so embeddings don't degenerate into a small set of duplicates
    at large n. Each node embeds a constant theme anchor token plus 5 sliding-
    window tokens, giving:
      - within-theme similarity ~ 1/6 baseline + window overlap (chain-like)
      - between-theme similarity = 0 (disjoint pools)

    This produces realistic-shape input where the 4-theme structure is
    detectable but not trivial — closer to actual user data than the original
    8-token-pool fixture, which collapsed to 32 unique patterns at n=10K.
    """
    nodes: list[dict] = []
    per_theme = max(1, n // THEMES_PER_GROUP)
    themes = ["alpha", "beta", "gamma", "delta"]
    pool_size = max(32, per_theme // 4)
    window = 5
    idx = 0
    for theme in themes:
        anchor = f"{theme}_anchor"
        pool = [f"{theme}_w{i:06d}" for i in range(pool_size)]
        for j in range(per_theme):
            toks = anchor + " " + " ".join(
                pool[(j * 3 + k) % pool_size] for k in range(window)
            )
            nodes.append({"id": f"n{idx:05d}", "text": toks})
            idx += 1
    # Fill any remainder from the last theme so n is exact.
    while len(nodes) < n:
        anchor = "delta_anchor"
        pool = [f"delta_w{i:06d}" for i in range(pool_size)]
        j = len(nodes)
        toks = anchor + " " + " ".join(
            pool[(j * 3 + k) % pool_size] for k in range(window)
        )
        nodes.append({"id": f"n{len(nodes):05d}", "text": toks})
    return nodes[:n]


def _time_run(n: int, sparse_top_k=None) -> dict[str, Any]:
    nodes = _synthetic_nodes(n)
    options: dict[str, Any] = {
        "embedding_backend": "hash",
        "random_seed": 42,
        "hash_dim": 1024,
    }
    if sparse_top_k is not None:
        options["sparse_top_k"] = sparse_top_k
    payload = {"nodes": nodes, "options": options}
    gc.collect()
    t0 = time.perf_counter()
    try:
        result = decompose.run(payload)
        elapsed_s = time.perf_counter() - t0
        status = result.get("status", "?")
        qm = result.get("quality_metrics") or {}
        return {
            "n": n,
            "elapsed_s": elapsed_s,
            "status": status,
            "layer_count": qm.get("layer_count"),
            "modularity": qm.get("modularity"),
            "quality_class": qm.get("quality_class"),
            "scale_coefficient": qm.get("scale_coefficient"),
        }
    except Exception as e:  # noqa: BLE001 — benchmark surface, capture all
        elapsed_s = time.perf_counter() - t0
        return {
            "n": n,
            "elapsed_s": elapsed_s,
            "status": "error",
            "error_type": type(e).__name__,
            "message": str(e),
        }


def _print_table(rows: list[dict]) -> None:
    print()
    print("| n     | elapsed (s) | status | layers | Q      | class      |")
    print("|------:|------------:|:-------|-------:|-------:|:-----------|")
    for r in rows:
        if r["status"] == "ok":
            print(
                f"| {r['n']:>5} | {r['elapsed_s']:>11.3f} | ok     | "
                f"{r['layer_count']:>6} | {r['modularity']:.3f}  | "
                f"{r['quality_class']:<10} |"
            )
        else:
            print(
                f"| {r['n']:>5} | {r['elapsed_s']:>11.3f} | error  |      - |      - | "
                f"{r.get('error_type', '?'):<10} |"
            )
    print()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="benchmark.py")
    parser.add_argument(
        "--sizes", type=int, nargs="+", default=list(DEFAULT_SIZES),
        help=f"Input sizes to benchmark (default: {DEFAULT_SIZES}).",
    )
    parser.add_argument(
        "--json", type=str, default=None, metavar="PATH",
        help="Also write structured results as JSON to PATH.",
    )
    parser.add_argument(
        "--sparse-top-k", default=None,
        help="If set (int or 'auto'), use sparse kNN similarity. "
             "'auto' = sparse when n >= 5000.",
    )
    args = parser.parse_args(argv)

    print(f"# LayerForge benchmark - sizes={args.sizes} sparse_top_k={args.sparse_top_k}")
    print(f"# python={sys.version.split()[0]}  pid={os.getpid()}")
    rows: list[dict] = []
    for n in args.sizes:
        print(f"  running n={n} ...", end="", flush=True)
        row = _time_run(n, sparse_top_k=args.sparse_top_k)
        row["sparse_top_k"] = args.sparse_top_k
        print(
            f" {row['elapsed_s']:.3f}s "
            f"({row['status']}, Q={row.get('modularity', '?')})"
        )
        rows.append(row)

    _print_table(rows)

    if args.json:
        Path(args.json).write_text(
            json.dumps({"results": rows}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"results written to {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
