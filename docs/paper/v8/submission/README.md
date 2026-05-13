# `docs/paper/v8/submission/` — 投稿用 bundle (paper v8)

## 内容

```
submission/
├── README.md              # 本ファイル (build + submit 手順)
├── paper_draft.md         # source Markdown (= v8 freeze copy, pandoc input)
├── paper.tex              # LaTeX source (pandoc で生成、TeX 系投稿用)
├── paper.pdf              # rendered PDF (preview / engineering note submission 向け)
├── references.bib         # BibTeX (26 entries — v8.1 で literature gap fix 後: Foundational / CD theory + benchmarks / Topic modeling + graph clustering / Hierarchical RAG + GraphRAG / Context + memory compression / Reference implementations)
├── LICENSE                # MIT (paper text + code)
└── figures/               # 9 vector PDF (fig_h_struct, fig_20ng_ari, fig_cpm_mechanism + 6 refined)
```

> **重複避け方針** (PR #21): paper Markdown は本 `submission/paper_draft.md` を **唯一の v8 freeze copy** とする (`docs/09_paper_draft.md` は working copy、本 file はその v8 freeze snapshot)。`docs/paper/v8/paper_draft.md` 重複は削除済み。Source style figures は `scripts/k_sweep/plots/` を直接参照、`figures/source/` 重複は削除済み。

## venue 別の使い方

### Zenodo preprint (推奨) — primary publication path

著者は独立研究者 (endorsement なし) のため、本 bundle の primary publication target は **Zenodo** (CERN 運営の汎用 research repository、preprint / dataset / software を 1 record にまとめ可能、DOI 自動発行)。先行 KDF preprint も同 platform で公開 (DOI: 10.5281/ZENODO.19651035)。

Zenodo workflow:

1. <https://zenodo.org/> にログイン (ORCID 経由 sign-in 推奨、ORCID linkage 自動化)
2. **New upload** → drag-and-drop で `paper.pdf` + `references.bib` + `figures/*.pdf` を全部 1 record に upload (Zenodo は record 単位で複数 file を許容)
3. Metadata 入力:
   - **Resource type**: Publication → Preprint
   - **Title**: paper の title をそのまま (Markdown 装飾は plain text 化)
   - **Authors**: Yasuhiro Kuroki (ORCID 0009-0006-8943-9344)、Affiliation 任意 ("Independent Researcher" 可)
   - **Description**: paper Abstract をそのまま貼付
   - **License**: paper text = `Creative Commons Attribution 4.0 International (CC-BY-4.0)` 推奨、code / figure は MIT (`Other (open)` で MIT を明示)
   - **Keywords**: community detection / topic modeling / Newman modularity / CPM / sentence embedding / passage clustering / Claude Code skill / 4±1 cognitive constraint / deterministic pipeline
   - **Communities** (任意): 関連 community に submit (例: independent-researchers、ai-tools 等)
4. **Publish** → DOI 自動発行 (例: 10.5281/ZENODO.NNNNNNNN)、ORCID profile に自動追加

```bash
# Optional: archive bundle for upload preparation
cd docs/paper/v8/submission
zip layerforge_paper_v8_zenodo.zip paper.pdf references.bib figures/*.pdf
```

### arXiv preprint (将来オプション、endorsement 取得後)

arXiv は新規 author に endorsement が必要 (= 既存 arXiv author の推薦)。endorsement 取得後の path:

- **PDF-only upload**: `paper.pdf` を直接、本 paper の body Japanese を CJK font 依存問題なく公開
- **TeX source upload**: `paper.tex` + `references.bib` + `figures/*.pdf` を tar.gz、ただし現状の paper.tex は CJK font declaration なしで body Japanese render 不可、事前修正必要
- category 候補: `cs.IR` (Information Retrieval) / `cs.CL` (Computation and Language) / `cs.SI` (Social and Information Networks)

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

**注意 (PDF 生成時の既知 warning)**: 標準 Latin Modern フォントには Greek 文字 (θ) や mathematical 記号 (≤, ≥) が含まれない。pandoc/xelatex は fallback で代替するが、視覚的に substitute される。Zenodo は PDF を直接 upload するため compile 環境依存はなし。気になる場合は `--variable=mainfont:"TeX Gyre Pagella"` (要インストール) で改善可。

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

Zenodo / arXiv 投稿時に paper text の license が要求される場合: **CC-BY 4.0** が paper text に推奨 (許容範囲は MIT より広く、academic citation 慣行に合う)。本 bundle の text を CC-BY 4.0 で投稿することは MIT との互換性あり (CC-BY は MIT の弱い superset)。

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

## 参考 (各 venue submit 時の分類例)

### Zenodo (primary)

- **Resource type**: Publication → Preprint
- **Communities**: 関連 community があれば submit (例: `independent-researchers`、`ai-research` 等、自由設定)
- **Keywords**: 上記 ZENODO submit 手順内の keyword list 参照

### arXiv (将来オプション、endorsement 取得後)

- **cs.IR** (Information Retrieval): RAG 系列の論文が主に投稿される、本 paper は適合
- **cs.CL** (Computation and Language): NLP 系列、共有可能 (cross-list)
- **cs.SI** (Social and Information Networks): Newman/CPM community detection の元 category、技術的 contribution として cross-list 価値あり
