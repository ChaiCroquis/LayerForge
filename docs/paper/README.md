# `docs/paper/` — 論文 version 別資材

## 構造

```
docs/paper/
├── README.md             # 本ファイル (navigation)
├── v8/                   # 現行 freeze version
│   ├── version_notes.md  # v8 metadata + 各 content の source-of-truth path
│   ├── figures/          # paper unique figures のみ (PR #21 で source/ 重複削除)
│   │   ├── refined/      # 6 PNGs (paper-publication 再 render)
│   │   └── new/          # 3 PNGs (v8 新規)
│   └── submission/       # arxiv-ready bundle (self-contained)
│       ├── README.md
│       ├── paper_draft.md / paper.tex / paper.pdf
│       ├── references.bib / LICENSE
│       └── figures/      # 9 vector PDFs
├── v9/ (将来)
└── archive/
    └── README.md         # v1-v7 の git hash 一覧
```

### source of truth (重複避け方針、PR #21)

| 内容 | 唯一の source |
|---|---|
| paper Markdown (working) | `docs/09_paper_draft.md` |
| paper Markdown (v8 freeze) | `docs/paper/v8/submission/paper_draft.md` |
| paper LaTeX / PDF | `docs/paper/v8/submission/paper.tex` / `paper.pdf` |
| references (URL) | `docs/REFERENCES.md` |
| references (BibTeX) | `docs/paper/v8/submission/references.bib` |
| source figures (matplotlib default) | `scripts/k_sweep/plots/` |
| refined/new figures (PNG) | `docs/paper/v8/figures/refined/` and `new/` |
| submission figures (vector PDF) | `docs/paper/v8/submission/figures/` |

## 現行 version

**v8** (2026-05-13 freeze):
- paper_draft.md は **`docs/09_paper_draft.md` の v8 freeze copy**
- working copy (今後の編集) は依然 `docs/09_paper_draft.md`、v9 close 時に v9/ にコピー
- 数値は **paper v8 整合性監査済み (PR #15, #16, #18)** + folder split (PR #17) 後の状態

## version 履歴

| version | freeze commit | 主要変更 |
|---|---|---|
| v1 | PR #8 (init) | initial draft |
| v2 | PR #10 | 17 fixes (致命的 3 + overclaim + clarity) |
| v3 | PR #11 | 9 follow-up (cross-ref + reviewer defense) |
| v4 | PR #12 | 5 follow-up |
| v5 | PR #13 | 3 optional polish |
| v6 | PR #14 | 数値 realignment (5 fixes) |
| v7 | PR #15 | method-attribution audit (4 fixes) |
| **v8** | **PR #16, #17, #18** | **§6.7 obs3 fix + folder separation + post-#17 stale row count** |

v1-v7 の paper 内容は `git log docs/09_paper_draft.md` で取得可能。`archive/README.md` 参照。

## 運用方針

- **編集中**: `docs/09_paper_draft.md` を直接編集
- **iteration 区切り**: 整合性監査終了時に `docs/paper/vN/paper_draft.md` にコピー保存
- **figures 再生成**: `scripts/k_sweep/plots/` で生成 → `docs/paper/vN/figures/source/` にコピー
- **paper-style refinement**: 生成時に refined/ 配下に別途出力 (300dpi, English labels)
- **references**: `docs/REFERENCES.md` を maintain、各 version freeze 時に `vN/references.md` にコピー
