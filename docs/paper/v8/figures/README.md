# `docs/paper/v8/figures/` — paper v8 unique figures

重複避けるため、本 folder には **paper v8 で新規に作成した figures のみ** を保管:

- `refined/` (6 PNG) — `scripts/k_sweep/plots/` の subset を paper-publication style で **再 render** (300 dpi、English labels、serif font、consistent color)
- `new/` (3 PNG) — paper v8 で新規追加した figures (§4.4, §4.6, §5)

**source figures (matplotlib default)** は `scripts/k_sweep/plots/` を参照 (重複コピーは本 folder には置かない、PR #21 で cleanup)。

**投稿用 vector PDF** は `docs/paper/v8/submission/figures/` を参照 (refined 6 + new 3 = 9 PDFs)。

生成 script: `scripts/k_sweep/generate_paper_figures.py`

## paper section → figure mapping

| Section | Figure (recommend) | Path |
|---|---|---|
| §4.1 Q peak K bouncy | Newman side of Q heatmap | `refined/heatmap_Q_N_x_K.png` |
| §4.1 (alternative) | Q vs K per N line | `refined/Q_vs_K_per_N.png` |
| §4.2 above-limit monotone | dual heatmap | `refined/heatmap_above_limit_N_x_K.png` |
| §4.3 ARI by N | ARI vs K per N | `refined/cpm_vs_newman_ari.png` |
| **§4.4 H_struct** | **scatter K_actual vs n_themes** | **`new/fig_h_struct.png`** |
| §4.5 K=10 self-routing | self-routing vs K | `refined/self_routing_acc_vs_K.png` |
| **§4.6 20NG ARI** | **bar chart Newman/CPM × K** | **`new/fig_20ng_ari.png`** |
| **§5 CPM mechanism** | **penalty curves** | **`new/fig_cpm_mechanism.png`** |
| §6 Pareto (appendix) | Q × compression | `refined/pareto_Q_vs_compression.png` |

## 再生成

```bash
cd <repo-root>
python -X utf8 scripts/k_sweep/generate_paper_figures.py
# → refined/ と new/ に PNG、submission/figures/ に vector PDF
```
