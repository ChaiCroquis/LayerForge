# v8 version notes

## Freeze 日時

2026-05-13 (PR #16 で v8 確定、その後 #17 / #18 / #19 / #20 で repository hygiene 適用)

## v8 の source of truth (重複避けるため)

本 folder には **freeze 用 metadata** と **paper unique 成果物** のみ。content の source は以下を参照:

| 内容 | 場所 (source of truth) |
|---|---|
| paper 本文 (Markdown) | `docs/09_paper_draft.md` (working copy) |
| paper 本文 (v8 freeze snapshot) | `docs/paper/v8/submission/paper_draft.md` (= pandoc input) |
| paper 本文 (LaTeX) | `docs/paper/v8/submission/paper.tex` |
| paper 本文 (PDF preview) | `docs/paper/v8/submission/paper.pdf` |
| 引用 references | `docs/REFERENCES.md` (URL 形式) + `docs/paper/v8/submission/references.bib` (BibTeX) |
| **source figures (default style)** | **`scripts/k_sweep/plots/`** (本 folder では duplicate しない) |
| paper-publication style figures (PNG) | `docs/paper/v8/figures/refined/` (本 folder 内 unique) |
| 新規追加 figures (PNG) | `docs/paper/v8/figures/new/` (本 folder 内 unique) |
| 投稿用 vector figures (PDF) | `docs/paper/v8/submission/figures/` (本 folder 内 unique) |
| データ source CSVs/JSONs | `scripts/k_sweep/data_current/` |

## v8 で確定した内容

- 全数値が `scripts/k_sweep/data_current/` の実 CSV/JSON と一致 (v6 で realignment 完了)
- Method-attribution (Newman vs CPM) が全 claim で正しい (v7 で audit 完了)
- Cross-reference dangling reference ゼロ
- §5.2 methodology asymmetry を明示 disclosure
- 公開準備: License (MIT), README, env-var test corpus path 完備

## v8 commit hash (git history で source 取得可)

| 段階 | commit | PR |
|---|---|---|
| v8 freeze | `750fe1f67f3529b64f2fbad3ee1266830f01dd02` | #16 |
| v8 + folder split | `1a38fedb46b1b96839e909f12a79a78b7c01ce97` | #17 |
| v8 + row count fix | `f08850fa7516a6e4fa4950a992bf6a56471de184` | #18 |
| v8 figures bundle | `bc29bab...` | #19 |
| v8 submission bundle | `d367f55...` | #20 |
| **v8 cleanup (本 PR)** | (本 PR で確定) | **#21** |

過去 paper 内容を取得する場合: `git show <commit>:docs/09_paper_draft.md`

## v9 を始めるとき

1. 編集中の `docs/09_paper_draft.md` を継続編集
2. iteration 確定時、本 `version_notes.md` と同じ書式の `docs/paper/v9/version_notes.md` を新規作成
3. paper unique 成果物 (refined figures など) のみ v9/ 配下に配置、source content は重複させない
4. `docs/paper/archive/README.md` に v8 row 追加
