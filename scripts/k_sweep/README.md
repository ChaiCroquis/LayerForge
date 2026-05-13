# `scripts/k_sweep/` — verification scripts and data

## ディレクトリ構造 (2026-05-13 整理)

```
scripts/k_sweep/
├── *.py                    # 検証スクリプト
├── data_current/           # 最新測定 (paper v8 で参照中、PR #3 以降の dual-method)
│   ├── README.md           # 各ファイルの paper 参照箇所一覧
│   ├── correlation_data.csv     (119 rows, Newman + CPM)
│   ├── heatmap_data.csv         (167 rows, dual-method)
│   ├── cpm_compare_data.csv     (95 rows + ARI/NMI)
│   ├── k10_multi_corpus_results.json
│   ├── multi_corpus_results_v2.json
│   └── robustness_results.json
├── data_archive/           # 旧測定 (paper 非参照、historical trace)
│   ├── README.md           # 旧ファイルの置換先一覧
│   ├── k_exact_results.json     (K=3,4,5 exact, synthetic 4-theme)
│   ├── multi_corpus_results.json (v1 Newman-only)
│   ├── resolution_limit_results.json
│   └── results.json            (initial run.py output)
└── plots/                  # 全プロット (paper で参照)
    └── README.md           # 各 plot の解釈ガイド
```

詳細は `data_current/README.md` と `data_archive/README.md` を参照。

## 検証スクリプト一覧

**Current 系 (dual-method, Newman + CPM、出力先: `data_current/`)**

| スクリプト | 出力 |
|---|---|
| `correlation_data.py` | `data_current/correlation_data.csv` |
| `heatmap_N_x_K.py` | `data_current/heatmap_data.csv` |
| `cpm_compare.py` | `data_current/cpm_compare_data.csv` |
| `multi_corpus_verify_v2.py` | `data_current/multi_corpus_results_v2.json` |
| `k10_multi_corpus.py` | `data_current/k10_multi_corpus_results.json` |
| `run_robustness.py` | `data_current/robustness_results.json` |
| `pareto_plot.py` | `plots/pareto_*.png` (reads `data_current/correlation_data.csv`) |

**Archive 系 (旧 Newman-only、出力先: `data_archive/`)**

| スクリプト | 出力 | 置換先 |
|---|---|---|
| `run.py` | `data_archive/results.json` | `correlation_data.csv` |
| `multi_corpus_verify.py` (v1) | `data_archive/multi_corpus_results.json` | `multi_corpus_results_v2.json` |
| `resolution_limit_check.py` | `data_archive/resolution_limit_results.json` | `heatmap_data.csv` の above_limit_frac 列 |

---

## 初期 4±1 (Cowan) sensitivity analysis — historical record

(以下は初期 single-method sweep の歴史記録、現在の paper v8 はこの観察を `data_current/` の dual-method 測定で更新済み。本節は当時の判断 trace として保存。)

### 概要

LayerForge は Cowan の 4±1 = (3, 5) を default で採用してきたが、その経験的根拠を測ったことが無かった。本実験で K を [1-2, 3-5, 6-8, 10-12, 15-20, 20-24] にスイープし、3 指標を計測:

1. **routing accuracy**: 各 answerable 質問が source passage を含む layer に route されるか
2. **compression ratio**: 選ばれた layer の chars / 全 corpus chars
3. **modularity Q**: 算法内部の凝集性指標

corpus: 既存の 24 passage 架空 corpus (4 themes × 6 each)、9 answerable questions
embedding: `paraphrase-MiniLM-L3-v2` (sentence-transformers)

## 結果

| K range | actual K | Q | class | avg layer size | compression | routing acc |
|---|---:|---:|---|---:|---:|---:|
| 1-2 | 1 | 0.000 | poor | 24.0 | 100.0% | 100% (9/9) |
| **3-5 (4±1)** | **5** | **0.695** | **acceptable** | **4.8** | **20.0%** | **100% (9/9)** |
| 6-8 | 6 | 0.623 | acceptable | 4.0 | 16.7% | 89% (8/9) |
| 10-12 | 10 | 0.466 | acceptable | 2.4 | 10.0% | 100% (9/9) |
| 15-20 | 19 | 0.180 | poor | 1.3 | 5.3% | 89% (8/9) |
| 20-24 | 24 | 0.000 | poor | 1.0 | 4.2% | 89% (8/9) |

### 観察

**1. Q 値 (modularity) は K=3-5 が最高 (0.695, acceptable に最も近い "good")**

これは Newman modularity の素直な性質: corpus の自然な構造 (4 theme × 6) に K=4-5 が最も合致する。K を増やすと「テーマ内分割」になり Q が下がる。K=24 ではすべてが singleton 化して Q=0。

**2. routing accuracy は K=3-5 と K=10-12 で 100%、他で 89% (1 件 misroute)**

misroute 全件 (3 conditions: K=6, K=19, K=24) で **同じ質問 (q03 "phlogiston の wavelength と温度")** が **同じ wrong layer に逃げた**。原因: 質問文が "wavelength" "temperature" を含み、これらの語彙が theme C (vimnar の体温など) や theme A (Zelgar の年代など) と微妙に近い。K=4-5 では theme A/B/C/D が綺麗に分かれて q03 が確実に B (phlogiston) に飛ぶが、K を増減すると theme B が分裂・統合され、route が乱れる。

K=10-12 で 100% に戻るのは興味深い: phlogiston 6 件が 2-3 個の sub-cluster に分かれるが、いずれも phlogiston 内で q03 source (b1) を含む。

**3. compression は K に反比例 (期待通り)**

- K=1: 0% 圧縮 (全 corpus)
- K=5: 80% 圧縮 (1/5 残す)
- K=24: 96% 圧縮 (1/24 残す = top-1 RAG)

### 結論

**4±1 default は経験的にも妥当な選択**:

| K | trade-off |
|---|---|
| K<3 | 圧縮効果ほぼゼロ。LayerForge を介する意味薄い |
| **K=3-5 (4±1)** | **Q 最高、routing 100%、認知単位として人間処理可能** |
| K=6-8 | routing が落ちる (8/9)、Q もやや下がる |
| K=10-12 | routing 戻るが Q 落ちる、compression 強い |
| K>15 | Q が poor、ほぼ traditional top-K RAG と等価、coherent grouping 消失 |

つまり **4±1 は「人間の認知都合」だけでなく、本 corpus の Newman modularity 最大点とも一致** していた。これは事後的な発見:
- Cowan 由来で人間都合と思っていた
- 実は本コーパス構造 (4 theme) と偶然合致
- 一般化: corpus 構造に合った K を選ぶのが最適、それが必ずしも 4±1 ではない

### 「4±1 を取っ払う」と何が起こるか

**K を corpus 構造に合わせて最適化すれば routing/Q は良い**。ただし:
- routing は K=5 vs K=10 でどちらも 100%、有意差なし
- compression は K=10 のほうが良い (10% vs 20%)
- Q は K=5 が良い (0.695 vs 0.466)

つまり目的により最適 K が違う:
- **AI cost 最適化** (圧縮重視) → K=10-15
- **凝集性重視** (人間理解 / 関連情報まとめて表示) → K=4-5
- **traditional RAG 化** → K=N

**4±1 を強制する根拠は「人間の認知処理上限」のみで、AI 単独最適化ではない**。これが今回 sweep で確認できた事実。

### LayerForge の修正された positioning

「K を 4±1 に **強制** する装置」ではなく、「K を corpus 構造に合わせて **自動探索** + 認知上限で打ち切る装置」と捉え直すべき。`--target-layer-min/max` でユーザが目的に応じて選べるよう CLI 化済 (本実験で plumbing 完了)。
