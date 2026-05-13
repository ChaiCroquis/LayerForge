# `data_current/` — paper v8 で参照中の最新測定データ

このフォルダは **現在の paper draft (docs/09 v8) で参照されている検証データ** を集約。
すべて **Newman + CPM の dual-method 測定** で、`community_method` option 切替後 (PR #3 以降) の結果。

## ファイル一覧

| ファイル | 行/エントリ | 生成スクリプト | 参照される paper section |
|---|---:|---|---|
| `correlation_data.csv` | 119 rows | `scripts/k_sweep/correlation_data.py` | §3.5 reproducibility / §4 metrics (Q, routing, compression, etc.) |
| `heatmap_data.csv` | 167 rows | `scripts/k_sweep/heatmap_N_x_K.py` | §4.1 Q peak K / §4.2 above-limit monotone / §5.2 above-limit table |
| `cpm_compare_data.csv` | 95 rows | `scripts/k_sweep/cpm_compare.py` | §4.3 ARI by N (Newman vs CPM) |
| `k10_multi_corpus_results.json` | 8 conditions × 2 methods | `scripts/k_sweep/k10_multi_corpus.py` | §4.5 K=10 self-routing |
| `multi_corpus_results_v2.json` | 8 conditions × 2 methods | `scripts/k_sweep/multi_corpus_verify_v2.py` | §2.4b (docs/08), supportive evidence for §4.4 |
| `robustness_results.json` | 32 aggregates × 8 K-range sweep | `scripts/k_sweep/run_robustness.py` | §4.4 H_struct (Newman 14/16 vs CPM 3/16) |

## 再生成

```bash
cd <repo-root>
export LAYERFORGE_KDF_DOCS=/path/to/your/corpus

python -X utf8 scripts/k_sweep/correlation_data.py
python -X utf8 scripts/k_sweep/heatmap_N_x_K.py
python -X utf8 scripts/k_sweep/cpm_compare.py
python -X utf8 scripts/k_sweep/k10_multi_corpus.py
python -X utf8 scripts/k_sweep/multi_corpus_verify_v2.py
python -X utf8 scripts/k_sweep/run_robustness.py
```

各スクリプトは出力を `data_current/` 配下に上書き保存。

## paper v8 integrity 状態

これらのファイルの数値は paper v8 (commit `1bb7c14` 系統) と完全一致状態。
本フォルダのファイルを更新する場合は paper の対応箇所も同期する必要あり (`docs/09 §4` の table を参照)。
