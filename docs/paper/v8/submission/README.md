# `docs/paper/v8/submission/` — 投稿用 bundle (paper v8)

## 内容

```
submission/
├── README.md              # 本ファイル (build + submit 手順)
├── paper_draft.md         # source Markdown (= v8 freeze copy, pandoc input)
├── paper.tex              # LaTeX source (pandoc で生成、arxiv 投稿向け)
├── paper.pdf              # rendered PDF (preview / engineering note submission 向け)
├── references.bib         # BibTeX (12 entries: Cowan, Newman, Fortunato-Barthélemy, Good, Traag×2, Eichin (SCA), Zachary, RAPTOR, GraphRAG + 2 reference impls)
├── LICENSE                # MIT (paper text + code)
└── figures/               # 9 vector PDF (fig_h_struct, fig_20ng_ari, fig_cpm_mechanism + 6 refined)
```

> **重複避け方針** (PR #21): paper Markdown は本 `submission/paper_draft.md` を **唯一の v8 freeze copy** とする (`docs/09_paper_draft.md` は working copy、本 file はその v8 freeze snapshot)。`docs/paper/v8/paper_draft.md` 重複は削除済み。Source style figures は `scripts/k_sweep/plots/` を直接参照、`figures/source/` 重複は削除済み。

## venue 別の使い方

### arXiv preprint (推奨) — **PDF-only upload path**

本 paper は body prose が日本語、Abstract が英語、章タイトル + 技術用語が英語の bilingual prose 構成。arXiv server の TeX engine は CJK font (MS Gothic / Noto Sans CJK 等) を保証しないため、**arXiv 上での LaTeX 自動 compile は CJK glyph missing risk あり**。本 bundle は **`paper.pdf` を直接 PDF upload する path** を推奨:

1. arXiv submit page で **PDF submission** を選択 (一部 category では別 path 指定が必要)
2. `paper.pdf` を upload
3. `references.bib` と `figures/*.pdf` は **ancillary files** として別 upload (= reproducibility 補助、本文 PDF とは別 download 可能)
4. category: `cs.IR` (Information Retrieval) / `cs.CL` (Computation and Language) / `cs.SI` (Social and Information Networks) のいずれか or cross-list
5. comments field に「LayerForge skill 形態の deterministic layer 分解 pipeline + Newman vs CPM small-N text 比較」等を明示

```bash
# (PDF-only upload なので tar.gz 不要)
# 但し ancillary bundle を作るなら:
cd docs/paper/v8/submission
zip layerforge_paper_v8_ancillary.zip references.bib figures/*.pdf
```

### arXiv preprint (代替) — TeX source upload path

CJK font dependency を解決する場合 (将来 English-only に翻訳 or arXiv server の Noto CJK を仮定):

```bash
cd docs/paper/v8/submission
tar -czf layerforge_paper_v8.tar.gz paper.tex references.bib figures/*.pdf
```

注意: 現状の `paper.tex` は CJK font declaration を持たない。arXiv compile で body Japanese が render される保証なし。本 path を採用する場合は事前検証必要。

### Engineering note (GitHub README extended)

1. `paper_draft.md` のまま使用 (図は relative path で参照)
2. GitHub Pages or wiki ページに配置

### 他 conference / workshop

template に依存。本 bundle の paper.tex を template に流し込む形が標準。

## ローカル再ビルド方法

### 前提

- pandoc 3.x: <https://pandoc.org/installing.html>
- LaTeX distribution: TeX Live / MiKTeX / MacTeX のいずれか (xelatex 必要)
- CJK font for Japanese: MS Gothic (Windows default) / Noto Sans CJK (Linux) / Hiragino Sans (macOS)

### LaTeX source 再生成

```bash
cd <repo-root>
pandoc docs/paper/v8/paper_draft.md \
  --from=gfm \
  --to=latex \
  --standalone \
  --output=docs/paper/v8/submission/paper.tex
```

### PDF 再生成

```bash
cd <repo-root>
pandoc docs/paper/v8/paper_draft.md \
  --from=gfm \
  --to=pdf \
  --output=docs/paper/v8/submission/paper.pdf \
  --pdf-engine=xelatex \
  --variable=documentclass:article \
  --variable=fontsize:10pt \
  --variable=geometry:margin=2.5cm \
  --variable=CJKmainfont:"MS Gothic"
```

**注意 (PDF 生成時の既知 warning)**: 標準 Latin Modern フォントには Greek 文字 (θ) や mathematical 記号 (≤, ≥) が含まれない。pandoc/xelatex は fallback で代替するが、視覚的に substitute される。arxiv の TeX engine では自動 fallback がより robust。気になる場合は `--variable=mainfont:"TeX Gyre Pagella"` (要インストール) で改善可。

### Figures 再生成

```bash
cd <repo-root>
python -X utf8 scripts/k_sweep/generate_paper_figures.py
# → figures/*.pdf (vector) + ../figures/refined/*.png + ../figures/new/*.png
```

## License

- Paper text (paper_draft.md, paper.tex, paper.pdf): **MIT License** (本 repo 全体と同一)
- Code (scripts/k_sweep/*.py, layerforge/*): **MIT License**
- Figures (figures/*.pdf, refined/*.png, new/*.png): **MIT License**
- BibTeX (references.bib): citations は public domain、本 .bib ファイル自体は MIT

arxiv 投稿時に license が要求される場合: **CC-BY 4.0** が paper text に推奨 (許容範囲は MIT より広く、academic citation 慣行に合う)。本 bundle の text を CC-BY 4.0 で arxiv 投稿することは MIT との互換性あり (CC-BY は MIT の弱い superset)。

## 監査 trail

- 全数値は `scripts/k_sweep/data_current/` の実 CSV/JSON と一致 (paper v6-v8 で realignment 完了、PR #14-#16-#18)
- Method attribution (Newman vs CPM) は全 8 claim で正しい (v7 audit、PR #15)
- Cross-reference dangling reference ゼロ (v3-v8 で解消)
- §5.2 の methodology asymmetry (Newman own θ vs CPM median similarity) を明示 disclosure (v7)
- データ整理: `scripts/k_sweep/data_current/` (paper 参照中) vs `data_archive/` (旧 single-method) を folder 分離 (PR #17)

## v9 へ持ち越す場合

- `docs/09_paper_draft.md` (working copy) を編集後、`docs/paper/v9/` に新規 freeze 作成
- 本 `submission/` は v8 の record として保持
- 必要なら `docs/paper/v9/submission/` を同様に作成

## 参考 (arxiv submit 時のテンプレ category 例)

- **cs.IR** (Information Retrieval): RAG 系列の論文が主に投稿される、本 paper は適合
- **cs.CL** (Computation and Language): NLP 系列、共有可能 (cross-list)
- **cs.SI** (Social and Information Networks): Newman/CPM community detection の元 category、技術的 contribution として cross-list 価値あり
