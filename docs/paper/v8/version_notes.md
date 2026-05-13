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
| v8 cleanup | `5726bab` | #21 |
| **v8.1 段階 1.5 開始** — internal logic + framing fixes (audit Tier 1-3) | `5ad6550` | — |
| v8.1 literature gap v1 (initial Related Work) | `8c3be53` | — |
| v8.1 literature gap v2 (Bohdal Samsung critical) | `f3cf604` | — |
| v8.1 backlog 項目 1-4 作成 | `782e3da` | — |
| v8.1 backlog 項目 5 (verify-before-judge + meta-recursion) | `ae6fa27` | — |
| v8.1 publication-prep-checklist + 項目 6 | `f537c6a` | — |
| v8.1 problem-discovery-methodology (2 軸 background) | `1d0d77b` | — |
| v8.1 form cleanup (Finding 2 + 3 from methodology) | `783f6fb` | — |
| v8.1 Abstract framing fix (Finding 1) + 項目 7 = 段階 1.5 closure | `8601ac5` | — |
| **v8.1 single submission PDF consolidation** (確認用 + 投稿用 PDF を 1 本化) | `d696901` | — |
| post-1.5: public/private repo 分離 (LayerForge-dev = private working、LayerForge = new public) | (2026-05-13 同日 gh repo rename + create) | — |

過去 paper 内容を取得する場合: `git show <commit>:docs/09_paper_draft.md`

**Note**: PR 番号は段階 1.5 では使用せず (作業 repo `LayerForge-dev` 上に直接 commit、push 構成変更後)。各 commit は段階 1.5 内の sub-phase に対応、詳細は `docs/observations/2026-05-13_paper_v8_1_future_backlog.md` 履歴 section 参照。

## v9 を始めるとき

1. 編集中の `docs/09_paper_draft.md` を継続編集
2. iteration 確定時、本 `version_notes.md` と同じ書式の `docs/paper/v9/version_notes.md` を新規作成
3. paper unique 成果物 (refined figures など) のみ v9/ 配下に配置、source content は重複させない
4. `docs/paper/archive/README.md` に v8 row 追加
