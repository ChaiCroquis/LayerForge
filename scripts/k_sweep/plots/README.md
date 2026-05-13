# K correlation graphs — interpretation guide

Source: `scripts/k_sweep/correlation_data.csv` (~120 rows = 5 configs × 12 K × 2 methods)

## 5 configurations × 2 community-detection methods

| series | corpus | embedder | N (passages) | N_themes |
|---|---|---|---:|---:|
| **synthetic baseline** | fictional 4-theme (clean disjoint vocab) | MiniLM-L3 | 24 | 4 |
| same-domain MiniLM | KDF concept docs (all about KDF) | MiniLM-L3 | 30 | 5 |
| same-domain mpnet | KDF concept docs | mpnet | 30 | 5 |
| cross-domain MiniLM | mixed (philosophy / exp pre-reg / proof / blog) | MiniLM-L3 | 24 | 4 |
| **cross-domain mpnet** | mixed (4 different document types) | mpnet | 24 | 4 |

K = 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15, 20

Method ∈ {**newman**, **cpm**} — selectable via `community_method` option.
See ADR-018 (`docs/06`) and `docs/08` §6.7 for the engineering choice.

**Plot convention**: solid line + ○ = Newman, dashed line + □ = CPM.

## What each plot shows

### `Q_vs_K.png` — Modularity Q (cross-eval for both methods)
- **Newman series**: Q peaks at specific K values (often N_themes or near it), classical pattern
- **CPM series**: Q values are persistently near zero or slightly negative — CPM optimizes its own H, not Q
- **Lesson**: don't compare Q across methods. CPM "looks worse" by Q only because Q isn't its objective.

### `self_routing_acc_vs_K.png` — KMeans / partition consistency
- Newman ≈ 1.0 for all K (passage as its own nearest centroid)
- CPM also ≈ 1.0 except occasional small drops where partitions split tight themes
- This is a weak test for both methods

### `compression_per_layer_vs_K.png` — context 削減率
- Identical 1/K curve for both methods (trivially, avg layer size = N/K)
- Method choice does not affect compression at fixed K

### `above_limit_frac_vs_K.png` — Fortunato-Barthélemy artifact gate
- Above-limit fraction declines as K rises for **both methods** — method-agnostic
- Newman's reference graph: θ-threshold at scale_coefficient
- CPM's reference graph: median off-diagonal similarity (corpus-intrinsic)
- **The supplementary K-selection metric**: stable across method choice

### `purity_mean_vs_K.png` — theme separation quality
- Both methods reach high purity at large K (sub-clustering trivializes purity)
- Newman tends to reach purity 1.0 slightly earlier
- Trivial-at-N caveat unchanged

## Heatmaps (cross-domain mpnet, 7 N values × 14 K values × 2 methods = 196 cells)

### `heatmap_Q_N_x_K.png` — dual heatmap (Newman | CPM)
- Newman side reproduces "Q peak K bouncy across N" (the §6.2 observation)
- CPM side shows Q dominated by near-zero / slightly negative values across all K
- Visual confirmation: Q peak interpretation is method-specific

### `heatmap_above_limit_N_x_K.png` — dual heatmap (Newman | CPM)
- Both sides show monotone-decreasing pattern with K
- Both sides stable across N (the §6.2 finding for Newman holds for CPM too)
- This is the engineering signal LayerForge picks for K recommendation

### `Q_vs_K_per_N.png` — Q vs K, varying N
- One color per N, both methods overlaid
- Newman lines (solid) show Q peaks at varying K — bouncy
- CPM lines (dashed) hug the baseline — different metric system

## Pareto plots

### `pareto_Q_vs_compression.png`
- Newman series form the Q-side Pareto frontier (high Q at moderate compression)
- CPM series sit near Q=0 line throughout — CPM's "value" is on its own H axis, not Q
- K=10 marker line still valid (compression axis is method-independent)

### `pareto_Q_vs_above_limit.png`
- Newman series show Q-vs-above-limit trade-off
- CPM series show similar above-limit pattern but on a different Q scale

## CPM-specific plots (from `cpm_compare.py`)

### `cpm_vs_newman_Qpeak_K.png`
Newman Q-peak K varies across N (bouncy: 4, 6, 9). CPM Q is monotone-near-zero
since Q isn't its objective. **Do not interpret as "CPM finds different K";**
both methods are forced to target_range and produce that K — what differs is
the partition's quality measured by Newman's Q vs CPM's H.

### `cpm_vs_newman_above_limit.png` (one panel per N)
Both methods produce similar above-limit fraction curves. This is the
**method-agnostic K-selection signal** LayerForge uses.

### `cpm_vs_newman_ari.png`
**Key new finding** (added 2026-05-13):

ARI(Newman, CPM) per K, one line per N:

| N | ARI mean | ARI max |
|---:|---:|---:|
| 12 | 0.87 | 1.00 |
| 20 | 0.73 | 1.00 |
| 24 | 0.69 | 1.00 |
| 32 | **0.49** | 0.78 |
| 40 | **0.41** | 0.84 |

- Small N (≤24): partitions agree highly (some K values: identical)
- Large N (≥32): partitions diverge materially (max < 0.85, never identical)
- LayerForge's typical operating range (N=20-40) is **in the divergence regime**

## Key tradeoffs visible in the graphs

1. **Q peak ≠ purity peak ≠ above-limit-fraction peak**: different metrics rate different K's
2. **Compression is monotone**: more K = more compression, no free lunch
3. **Above-limit fraction monotone decreases** with K: artifact risk grows
4. **Newman vs CPM partitions diverge for N≥32**: method choice matters in operating range
5. **Cross-method Q comparison is misleading**: CPM optimizes H, not Q

## How to choose K (decision matrix)

| 目的 | 重視する指標 | 推奨 K | 根拠 |
|---|---|---|---|
| 真のテーマ構造を表示 | Q max かつ above_limit=1.0 (Newman) | K=N_themes | synthetic K=4, cross-domain K=4 (Newman Q peak) |
| 人間 readability | above_limit + Cowan 4±1 | K=4-5 | working memory + algorithmic real signal |
| **AI Agent 入力圧縮** | **self_routing 維持 + 高 compression** | **K=10** | **全 config で routing 100% + 10x compression** |
| 細粒度 retrieval (top-1 RAG 互換) | compression max | K=N (≈20+) | coherent layer 解体、purity 1.0 trivial |

## How to choose method (Newman vs CPM)

| 目的 | 推奨 method | 根拠 |
|---|---|---|
| Q metric を主に使う | newman | Q が直接最適化対象 |
| Resolution-limit-free を保証 | cpm | Traag 2011、ただし γ tuning 必要 |
| 既存実装と互換 (default) | newman | LayerForge の v1 default |
| **両 method で頑健性確認** | dual run, ARI > 0.5 確認 | partition divergence の評価 |

## Reproduce

```bash
cd <repo-root>
export LAYERFORGE_KDF_DOCS=/path/to/your/corpus

# Sweep 5 configs × 12 K × 2 methods → CSV + 5 metric plots
python -X utf8 scripts/k_sweep/correlation_data.py

# N×K dual heatmaps (Newman / CPM)
python -X utf8 scripts/k_sweep/heatmap_N_x_K.py

# Pareto plots (reads correlation_data.csv)
python -X utf8 scripts/k_sweep/pareto_plot.py

# Focused Newman vs CPM comparison with ARI/NMI
python -X utf8 scripts/k_sweep/cpm_compare.py
```
