# `data_archive/` — 旧測定データ (superseded、現 paper 非参照)

このフォルダは **CPM backend 実装 (PR #3) より前の Newman-only 測定** または **後続の改良版 script で置き換えられた古い測定** を保管。
**paper v8 (docs/09) は現状これらを直接参照していない** (1 件の例外: §3 safe claims table の K=4 exact measurement)。

## ファイル一覧

| ファイル | 性質 | 生成スクリプト | 置換先 / 後継 |
|---|---|---|---|
| `k_exact_results.json` | 初期 K=3,4,5 exact 測定 (synthetic 4-theme corpus) | (script 削除済 / 履歴のみ) | 後継なし、docs/08 §3.2 safe claims で唯一参照 |
| `multi_corpus_results.json` | v1 multi_corpus_verify (Newman-only、KDF docs 4 corpora) | `scripts/k_sweep/multi_corpus_verify.py` (v1) | `data_current/multi_corpus_results_v2.json` (v2 = cross-domain + mpnet + CPM dual) |
| `resolution_limit_results.json` | 初期 Fortunato-Barthélemy resolution limit standalone check | `scripts/k_sweep/resolution_limit_check.py` | `data_current/heatmap_data.csv` の above_limit_frac 列が dual-method 版 |
| `results.json` | 初期 benchmark sweep (run.py) | `scripts/k_sweep/run.py` | `data_current/correlation_data.csv` がより包括的 |

## 保管理由

1. **再現性** — paper v6 で `k_exact_results.json` の Q=0.712 が docs/08 §3.2 で「safe claim」として記録、出典として保管
2. **historical record** — 反復過程の trace を残す (ADR-018 の精神に沿って、AI 推論誤り訂正含む試行錯誤の trace)
3. **regenerate コスト回避** — 旧 script は now scope 外だが、何かの reference に必要になった時のために file は残す

## 再生成

各旧 script は出力を本フォルダ (`data_archive/`) に書き込む設定:

```bash
python -X utf8 scripts/k_sweep/run.py                       # → data_archive/results.json
python -X utf8 scripts/k_sweep/multi_corpus_verify.py       # → data_archive/multi_corpus_results.json (v1)
python -X utf8 scripts/k_sweep/resolution_limit_check.py    # → data_archive/resolution_limit_results.json
```

`k_exact_results.json` の生成スクリプトは本リポジトリに含まれていない (履歴上の artifact)。

## 注意

paper v8 で「現状の主張」を支える証拠としては `data_current/` を見るべき。
本フォルダは「過程の trace」と「v6 で記録した K=4 exact measurement」のための保管庫。
