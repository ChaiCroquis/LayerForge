# LayerForge v9 — Response to Reviewers (Round 1)

Author: chai (筆頭著者) · 2026-05-17
Reviewer report: `C:/work/LayerForge/paper/v9/peer_review.md` (Claude Code subagent, dated 2026-05-17)
Cross-checked against: raw `v029a_cost_latency_results.json`, `v042_bis_n30_results.json`, `docs/verification_index.md` v6, `docs/parameter_baseline.md` v8.

> Author Agent constraint: this document articulates **response text + Before/After manuscript diff only**. Actual code application to `build_main.js` / `build_appendix.js` is performed by the main thread in a separate step.
>
> Self-preference bias disclosure (Anthropic LLM-as-judge guidance): both Reviewer and Author are Claude Code subagents = same model family. Findings here should be cross-checked by either (a) a human reviewer, (b) a different LLM family (GPT-4 / Gemini / Mistral), or (c) Anthropic API + Haiku 4.5 direct, before being treated as formal acceptance evidence.

---

## Summary table

| # | Point | Disposition | Touchpoints |
|---|---|---|---|
| Major 1 | Figure 4 cost-axis 誤認 | **ACCEPTED — substantive revision** | §4.4 本文 + Figure 4 caption + Plot 5 caption (appendix) |
| Major 2 | "quintuple-evidence" ラベル | **ACCEPTED — terminology rewrite** | Abstract + §2 + §8 + 新規 §2 disclaimer 段落 |
| Major 3 | §4.5 baseline optimality 飛躍 | **ACCEPTED — claim weakening** | §4.5 本文 + Appendix C 序文 |
| Minor 1 | trade-off 数式 statistical 地位 | **ACCEPTED — qualifier 挿入** | §4.2 本文 |
| Minor 2 | UMass 6/6 残存 | **REJECTED — false positive (reviewer input 不整合)** | 修正不要、ただし audit trail 記載 |
| Minor 3 | self-preference bias 影響範囲 | **ACCEPTED — specificity 強化** | §6 Limitations 該当 bullet |
| Minor 4 | Abstract 47+ vs 46 | **ACCEPTED — 数値訂正** | Abstract 1 行 |
| Minor 5 | §1 v8 → v9 差分明示不足 | **ACCEPTED — 4 bullet 追記** | §1 末尾 |
| Minor 6 | References commit hash dereference 不能 | **ACCEPTED — repo URL 併記** | References [11]–[15] |
| Question 1 | §2 / §7 constitutive vs probe API 緊張 | **ACCEPTED — 境界明示 1 段落追加** | §2 末尾 + §7 序文 |
| Question 2 | §5.1 post-hoc rationalization | **ACCEPTED — cause attribution 弱化** | §5.1 |
| Question 3 | §4.3 ensemble computational overhead | **ACCEPTED — cost-adjusted 文追加** | §4.3 Table 1 後の段落 + §6 Limitations |
| Question 4 | V-008/V-009 K=4±1 boundary が main absent | **ACCEPTED — §6 Limitations に 1 bullet 追加** | §6 Limitations |

**Aggregate: 12 points addressed, 11 revisions + 1 rejected (Minor 2 false-positive).**

---

## ■ Response to Reviewer's Point: Major Concern 1

* **査読者の指摘（要約）**: §4.4 Figure 4 は "Full context achieves 60% accuracy at 22k tokens" と articulate しているが、22,006 は **N=5 全 sample 合計 token** (per-query 平均 4,401) であり、log-scale の "コスト" 軸で per-query 数値として読まれる現状の表現は読者を bias する。N=5 における 60% / 0% accuracy の CI も併記すべき。
* **著者らの回答（Response）**:
    > We thank the reviewer for the decisive cross-check against `v029a_cost_latency_results.json` (`totals.full = 22006`, `n_sample_tokens = 5`). We fully agree that conflating cumulative 5-sample totals with a per-query log-scale "cost" axis materially misleads readers. We have (a) restated all four numbers as **per-query means** (full = 4,401; F4-hybrid = 712; F3 = 44 tokens/query) recomputed directly from `per_sample_tokens[].full_tok / f4_tok / f3_tok`, (b) added exact-binomial 95% CIs for N=5 accuracy (60% → [14.7%, 94.7%]; 0% → [0%, 52.2%]) and explicitly noted that the CIs **overlap by construction**, demoting the figure's epistemic status from "demonstration" to "indicative pilot", (c) replaced the hypothesized sweet spot dot with a **shaded uncertainty region** to avoid the visual conflation with verified points, and (d) restated the V-030 trigger in the caption so the unverified status is repeated on the figure itself, not only in body text.

#### 【本文の修正差分 (Manuscript Changes)】
- **該当箇所**: §4.4 本文 + Figure 4 caption (main) + Plot 5 caption (appendix)

- **修正前 (Before)** — §4.4 本文:
  ```text
  Figure 4 plots input-token cost (log scale) versus downstream LLM
  accuracy. Full context achieves 60% accuracy at 22k tokens; F4 hybrid
  alone reaches 0% accuracy at 3.5k tokens. The hypothesized operational
  sweet spot is F4 hybrid plus RAG retrieval at around 8k tokens by 50%
  accuracy (implementation pending; V-030 future verification trigger).
  ```

- **修正後 (After)** — §4.4 本文:
  ```text
  Figure 4 plots per-query input-token cost (log scale) versus downstream
  LLM accuracy on V-029-a (N=5 hotpotqa pilot). Full context averages
  4.4k tokens/query at 60% accuracy (3/5; exact-binomial 95% CI [14.7%,
  94.7%]); F4-hybrid alone averages 0.7k tokens/query at 0% accuracy
  (0/5; 95% CI [0%, 52.2%]). The two CIs overlap substantially, so this
  figure is reported as a pilot-scale indication rather than a
  significance claim. The hypothesized operational region (F4-hybrid +
  RAG retrieval at approximately 1-10k tokens/query and 30-70% accuracy)
  is drawn as a shaded uncertainty band; per-query verification of this
  region requires V-030 (Pending). Raw per-sample token counts are in
  v029a_cost_latency_results.json.
  ```

- **修正前 (Before)** — Figure 4 caption:
  ```text
  Figure 4. Cost (input tokens, log scale) vs downstream LLM accuracy
  (V-040 Plot 5). Full baseline 22k tokens at 60% accuracy. F4 hybrid
  alone is cost-efficient but accuracy 0%. The hypothesized intersection
  (F4 hybrid + RAG, around 8k tokens by 50%) requires V-030 validation.
  ```

- **修正後 (After)** — Figure 4 caption:
  ```text
  Figure 4. Per-query input-token cost (log scale) vs downstream LLM
  accuracy, V-029-a hotpotqa N=5 pilot (V-040 Plot 5). Full baseline
  averages 4.4k tokens/query, accuracy 3/5 (60%, 95% CI [14.7%, 94.7%]).
  F4-hybrid alone averages 0.7k tokens/query, accuracy 0/5 (0%, 95% CI
  [0%, 52.2%]); CIs overlap. Shaded band: hypothesized F4-hybrid + RAG
  operational region, unverified, awaits V-030. N=5 pilot — axis values
  are indicative, not significance claims.
  ```

- **修正前 (Before)** — Plot 5 caption (appendix):
  ```text
  Plot 5. Cost vs downstream LLM accuracy (= main paper Figure 4). F4
  hybrid + RAG hypothesis intersection marked.
  ```

- **修正後 (After)** — Plot 5 caption (appendix):
  ```text
  Plot 5. Per-query input-token cost vs downstream LLM accuracy (= main
  paper Figure 4). N=5 pilot; means computed from
  v029a_cost_latency_results.json per_sample_tokens. F4-hybrid + RAG
  hypothesis is shown as an unverified shaded region (V-030 trigger).
  ```

---

## ■ Response to Reviewer's Point: Major Concern 2

* **査読者の指摘（要約）**: Abstract / §2 / §8 が "quintuple PASS / FAIL" を ordinal claim として繰り返すが、(a) `verification_index.md` v6 line 91 では fact-level FAIL は sextuple evidence と数えており論文と不一致、(b) hotpotqa 4 件 + livedoor 1 件 という構成上 metric-multiplication ≠ corpus-multiplication で、5 つの独立実験という印象は読者を誤導する。
* **著者らの回答（Response）**:
    > We thank the reviewer for surfacing the dual problem of (i) numerical mismatch with the verification index and (ii) the implicit independence claim embedded in the ordinal label. We agree that "quintuple" reads as "five independent experiments" when in fact the underlying evidence is **metric-multiple but corpus-dual** (4 metric families × 2 datasets, with hotpotqa contributing the majority of records). We have replaced every occurrence of `quintuple-evidence` with the descriptive formulation "multiple metric families across two datasets (hotpotqa EN / livedoor JA; 4 metric families: substring, ROUGE-L, attribute breakdown, downstream LLM accuracy)" and added a one-paragraph disclaimer at the end of §2 stating that **metric multiplicity must not be read as corpus multiplicity**. This also reconciles the count discrepancy with `verification_index.md` v6 by removing the ordinal claim entirely.

#### 【本文の修正差分 (Manuscript Changes)】
- **該当箇所**: Abstract + §2 + §8 + 新規 disclaimer 段落 (§2 末尾)

- **修正前 (Before)** — Abstract (該当 sentence):
  ```text
  We articulate (1) a two-layer fidelity structure with quintuple PASS at
  theme-level semantic preservation and quintuple FAIL at fact-level
  lexical preservation, (2) a statistically significant Hybrid ensemble
  path ...
  ```

- **修正後 (After)** — Abstract:
  ```text
  We articulate (1) a two-layer fidelity structure: theme-level semantic
  preservation passes across multiple metric families on two datasets
  (hotpotqa EN / livedoor JA), and fact-level lexical preservation fails
  across multiple metric families on the same two datasets, (2) a
  statistically significant Hybrid ensemble path ...
  ```

- **修正前 (Before)** — §2:
  ```text
  These layers are independent dimensions. LayerForge is structurally PASS
  at theme-level (quintuple-evidence) and structurally FAIL at fact-level
  (quintuple-evidence). The fact-level FAIL is constitutive (ADR-026
  design), not a defect; the remedy is hybrid pipeline (LayerForge plus
  NER/regex/RAG), not LayerForge internal modification. Figure 1
  visualizes this positioning.
  ```

- **修正後 (After)** — §2:
  ```text
  These layers are independent dimensions. LayerForge is structurally PASS
  at theme-level and structurally FAIL at fact-level. The theme-level PASS
  is corroborated by multiple metric families (response cosine, BERTScore
  F1, topic coherence UMass/NPMI) on two datasets (hotpotqa EN, livedoor
  JA). The fact-level FAIL is corroborated by four metric families
  (answer substring, ROUGE-L, attribute breakdown, downstream LLM
  accuracy) on the same two datasets. The fact-level FAIL is constitutive
  (ADR-026 design), not a defect; the remedy is hybrid pipeline
  (LayerForge plus NER/regex/RAG), not LayerForge internal modification.
  Figure 1 visualizes this positioning.

  Disclaimer (metric multiplicity vs corpus multiplicity). The above
  evidence is metric-multiple but corpus-dual. Distinct metric families
  applied to the same corpus are statistically correlated and do not
  constitute independent observations in the sense of independent draws
  from disjoint populations. Per-dataset hotpotqa records dominate the
  fact-level evidence count (see Appendix B); livedoor provides the only
  out-of-corpus replication for both theme-level and fact-level. We
  therefore refrain from any ordinal "n-tuple evidence" labeling and
  emphasize that broader corpus coverage (V-102 cross-domain extension,
  see §7) is required before generalization beyond the two-corpus span.
  ```

- **修正前 (Before)** — §8:
  ```text
  LayerForge v9 confirms a two-layer fidelity structure: theme-level
  semantic preservation is structurally PASS (quintuple-evidence),
  fact-level lexical preservation is structurally FAIL
  (quintuple-evidence).
  ```

- **修正後 (After)** — §8:
  ```text
  LayerForge v9 confirms a two-layer fidelity structure: theme-level
  semantic preservation is structurally PASS across multiple metric
  families on two datasets, and fact-level lexical preservation is
  structurally FAIL across multiple metric families on the same two
  datasets (hotpotqa EN, livedoor JA; see §2 disclaimer for the
  metric-vs-corpus multiplicity caveat).
  ```

---

## ■ Response to Reviewer's Point: Major Concern 3

* **査読者の指摘（要約）**: §4.5 の "14 ablations confirm baseline parameter optimality" は absence-of-evidence と evidence-of-optimality を混同しており、Appendix C の SNIPPET_CHARS PARTIAL-IMPROVEMENT、CPM gamma dataset-dependent、tokenizer pattern core-spec future、V-032-bis の N=5→N=30 direction reversal と整合しない。
* **著者らの回答（Response）**:
    > We accept this distinction without reservation; the original sentence collapsed two epistemically different claims. We have weakened §4.5 to "did not find any parameter change yielding >0.30 delta improvement under the tested N (5–30)" — a strictly empirical statement about the search budget rather than an optimality claim — and explicitly enumerated the three pending refinement candidates (SNIPPET_CHARS 240/480, CPM gamma dataset-dependent, ASCII tokenizer pattern core-spec future) as well as the V-032-bis direction reversal as evidence that ablation outcomes are N-sensitive. Appendix C preface is updated in parallel so that "baseline snapshot v1 is preserved unchanged" is decoupled from any optimality framing and stated as a freeze decision under bounded ablation budget.

#### 【本文の修正差分 (Manuscript Changes)】
- **該当箇所**: §4.5 本文 + Appendix C preface

- **修正前 (Before)** — §4.5:
  ```text
  14 ablations confirm baseline parameter values are at or near
  improvement-LARGE threshold (no parameter shows >0.30 delta
  improvement). Baseline snapshot v1 is preserved unchanged. Notable
  findings: V-027 (digit preservation NEGATIVE leads to core-spec
  modification trigger), V-032-bis (mpnet > MiniLM-L6 in N=30 reverses
  N=5 direction, illustrating careful-strategy Rule 3 importance). Full
  ablation table is in Appendix C.
  ```

- **修正後 (After)** — §4.5:
  ```text
  14 ablations did not find any parameter change yielding >0.30 delta
  improvement under the tested N (5-30). This is an empirical statement
  about the ablation search budget, not a claim of global optimality:
  three parameters remain pending-refinement candidates (SNIPPET_CHARS
  PARTIAL-IMPROVEMENT 240/480, CPM gamma dataset-dependent best, ASCII
  tokenizer pattern core-spec future), and at least one ablation
  exhibited N-sensitive direction reversal (V-032-bis: mpnet > MiniLM-L6
  at N=30 reverses the N=5 direction). Baseline snapshot v1 is therefore
  preserved unchanged as a freeze decision under bounded ablation budget,
  not as an optimality assertion. Small-N ablation results should be read
  as direction-only. Notable individual findings: V-027 (digit
  preservation NEGATIVE leads to core-spec modification trigger),
  V-032-bis (the N=5→N=30 reversal motivating careful-strategy Rule 3).
  Full ablation table is in Appendix C.
  ```

- **修正前 (Before)** — Appendix C preface:
  ```text
  All 14 parameter ablations with verdict, current value preservation
  status, and improvement path. Baseline snapshot v1 is preserved
  unchanged (no IMPROVEMENT-LARGE threshold reached).
  ```

- **修正後 (After)** — Appendix C preface:
  ```text
  All 14 parameter ablations with verdict, current value preservation
  status, and improvement path. Baseline snapshot v1 is preserved
  unchanged as a freeze decision under bounded ablation budget — no
  parameter change reached the IMPROVEMENT-LARGE threshold (>0.30 delta)
  under the tested N (5-30). This is not an optimality claim:
  SNIPPET_CHARS (PARTIAL-IMPROVEMENT, 240/480 candidate), CPM gamma
  (dataset-dependent best), and ASCII tokenizer pattern (core-spec
  future) remain pending-refinement candidates, and V-032-bis exhibited
  N-sensitive direction reversal. See main §4.5.
  ```

---

## ■ Response to Reviewer's Point: Minor 1

* **査読者の指摘（要約）**: §4.2 の `fidelity = 0.94 × (1 − reduction × 0.15)` は source script では "近似" / heuristic と記述されているのに、論文本文では regression と誤読される表現になっている。R²/CI を付けるか、heuristic と明示するか、削除する。
* **著者らの回答（Response）**:
    > We agree. The expression is a two-point visual heuristic derived from the V-040 Pareto frontier (V-007/V-025 endpoints), not a regression with reported R² or CI. We have qualified the sentence accordingly and pointed readers to `docs/verifications/2026-05-17_v040_pareto_analysis.md` for the underlying construction.

#### 【本文の修正差分 (Manuscript Changes)】
- **該当箇所**: §4.2 該当 sentence

- **修正前 (Before)**:
  ```text
  The trade-off curve is approximately fidelity =
  0.94 multiplied by (1 minus reduction times 0.15).
  ```

- **修正後 (After)**:
  ```text
  The trade-off between reduction and theme-level fidelity is summarized
  by the visual heuristic fidelity ≈ 0.94 × (1 − reduction × 0.15),
  obtained as a two-point interpolation between the V-007 and V-025
  Pareto endpoints (V-040 Pareto analysis). This is a heuristic
  approximation for reader orientation, not a regression fit; no R² or
  confidence interval is reported, and the expression should not be used
  for extrapolation outside the measured reduction range
  (approximately 0.77-0.99).
  ```

---

## ■ Response to Reviewer's Point: Minor 2

* **査読者の指摘（要約）**: Appendix B Table B2 V-026 行が "LF-COMPETITIVE NPMI + UMass best 6/6" のままで、`docs/verifications/2026-05-16_v026_topic_coherence.md` §9 correction の 5/6 と不整合。
* **著者らの回答（Response）（false-positive 棄却）**:
    > We thank the reviewer for raising this consistency check, but on direct re-inspection of `v9_appendix_text.md` line 156-158 the V-026 row already reads `"LF-COMPETITIVE NPMI + UMass best 5/6 (hotpot/4 NMF outlier)"` — the 5/6 correction had already been propagated to the appendix prior to the reviewer's pass. We hypothesize the reviewer's subagent operated on a stale text extract that pre-dated `build_appendix.js` regeneration; the most recent appendix PDF (committed alongside this round) contains "5/6". **We therefore decline to make any change in response to this point** and treat it as a reviewer-input inconsistency. For audit purposes, the canonical current text is reproduced below.

#### 【本文の修正差分 (Manuscript Changes)】
- **該当箇所**: Appendix B Table B2, V-026 行
- **Disposition**: **NO CHANGE** (false positive; reviewer input was stale)

- **現行 text (reference, no edit required)** — `v9_appendix_text.md` line 156-158:
  ```text
  V-026   ShareGPT+hotpotqa     6     LF-COMPETITIVE NPMI + UMass
          topic coherence             best 5/6 (hotpot/4 NMF
                                      outlier)
  ```

- **Audit note (recorded only in this response document, not added to manuscript)**:
  ```text
  Round 1 reviewer flagged "UMass best 6/6" as residual in Appendix B.
  Direct re-inspection of v9_appendix_text.md (line 156-158, commit
  current) confirms the value is already "5/6 (hotpot/4 NMF outlier)",
  consistent with the §9 correction landed in
  docs/verifications/2026-05-16_v026_topic_coherence.md. The reviewer's
  read appears to have been against a stale text extract pre-dating
  build_appendix.js regeneration. No manuscript change required.
  ```

---

## ■ Response to Reviewer's Point: Minor 3

* **査読者の指摘（要約）**: §6 Limitations の self-preference bias 開示が「どの結果がこの bias の影響を受けるか specific でない」。LLM judge 経由 (V-024/V-024-bis/V-025) を明示、metric-only (V-042 paired t-test) を bias-independent として明示すべき。
* **著者らの回答（Response）**:
    > We thank the reviewer for the request to make the bias scope explicit. We have rewritten the Limitations bullet to enumerate (i) the verifications that route through an LLM judge and are therefore subject to self-preference bias (V-024, V-024-bis, V-025), and (ii) the verifications whose primary metric is computed without an LLM judge (V-042 family paired t-test on tok_recall) and are therefore **structurally independent** of self-preference bias. This sharpens the differential claim status across our headline results.

#### 【本文の修正差分 (Manuscript Changes)】
- **該当箇所**: §6 Limitations, self-preference bias bullet

- **修正前 (Before)**:
  ```text
  - Self-preference bias: subagent fallback (Claude evaluating Claude).
    Formal Anthropic API plus Haiku 4.5 confirmation pending.
  ```

- **修正後 (After)**:
  ```text
  - Self-preference bias (scope-specific): downstream-LLM-judged
    verifications V-024 (F3 refusal), V-024-bis (F4-hybrid accuracy), and
    V-025 (BERTScore via Claude-rendered evaluation) route through a
    Claude subagent acting as judge on Claude-compressed context and are
    therefore subject to LLM-as-judge self-preference bias (Anthropic
    acknowledged limitation). The V-042 family (paired t-test on
    tok_recall, including V-042-tri hotpotqa p=2.7e-05 and V-042-quad
    livedoor p=5.1e-08) computes its primary metric without an LLM judge
    and is therefore structurally independent of this bias. Formal
    Anthropic API plus Haiku 4.5 cross-confirmation remains pending for
    the LLM-judged subset.
  ```

---

## ■ Response to Reviewer's Point: Minor 4

* **査読者の指摘（要約）**: Abstract "47+ verifications" は Appendix B Table B1/B2 の実カウント (20 + 25 + 1 = 46) と不一致。
* **著者らの回答（Response）**:
    > Confirmed by direct count of Appendix B Table B1 (V-001 through V-020 = 20 rows) and Table B2 (V-021 through V-042-quad + 1 cross-corpus row = 26 rows; correcting the reviewer's count of 25). Total is **46 V-IDs**. We have replaced "47+" with the exact count of 46 and removed the open-ended "+".

#### 【本文の修正差分 (Manuscript Changes)】
- **該当箇所**: Abstract 該当 sentence

- **修正前 (Before)**:
  ```text
  This v9 update reports Phase 2b: 47+ verifications and 14 parameter
  ablations across 14 datasets ...
  ```

- **修正後 (After)**:
  ```text
  This v9 update reports Phase 2b: 46 verifications and 14 parameter
  ablations across 14 datasets ...
  ```

---

## ■ Response to Reviewer's Point: Minor 5

* **査読者の指摘（要約）**: §1 末尾の scope statement に v8.1 → v9 の差分 (V-021 以降 fidelity 直接測定、V-040 Pareto、V-042 系 ensemble 統計的検証) が箇条書きで示されていない。
* **著者らの回答（Response）**:
    > We agree this serves readers who have not previously read v8.1. We append a four-bullet "What is new in v9" list immediately after the existing scope statement in §1.

#### 【本文の修正差分 (Manuscript Changes)】
- **該当箇所**: §1 Introduction 末尾

- **修正前 (Before)**:
  ```text
  This v9 update articulates what LayerForge can and cannot do, where
  structural limitations lie, and which improvement paths are
  evidence-grounded. Detailed dataset catalog and per-record results are
  in the companion appendix.
  ```

- **修正後 (After)**:
  ```text
  This v9 update articulates what LayerForge can and cannot do, where
  structural limitations lie, and which improvement paths are
  evidence-grounded. Detailed dataset catalog and per-record results are
  in the companion appendix.

  What is new in v9 (relative to v8.1):
  - Direct fact-level fidelity measurement (V-021 substring, V-022
    ROUGE-L, V-023 attribute breakdown, V-024/024-bis downstream LLM
    accuracy) — v8.1 reported only theme-level evidence.
  - Two-layer fidelity formalization (§2) and the Pareto plot set
    (V-040) consolidating 38 evidence points into 5 visualizations.
  - Hybrid ensemble path (LayerForge + K-means) with cross-corpus
    statistical significance (V-042-tri N=100 hotpotqa, V-042-quad N=27
    livedoor), establishing an evidence-grounded improvement direction
    without modifying v8.1 core.
  - Explicit extrapolation boundaries per pattern coverage, and a
    decoupled "freeze under bounded ablation budget" framing for the
    14-ablation result (§4.5).
  ```

---

## ■ Response to Reviewer's Point: Minor 6

* **査読者の指摘（要約）**: References [11]–[15] が `commit a2e91a8` 等 commit hash 形式で、外部読者は dereference できない。repo DOI/URL を付けるか、Appendix を self-contained にすべき。
* **著者らの回答（Response）**:
    > We agree on the self-containment principle. As an immediate fix for round 1 we annotate each commit-hash reference with the public repository root URL so that external readers can resolve the hash via `<repo>/blob/<hash>/<path>`. A formal repository DOI (Zenodo deposit) is added as a future-work item for the camera-ready submission.

#### 【本文の修正差分 (Manuscript Changes)】
- **該当箇所**: References [11]–[15]

- **修正前 (Before)**:
  ```text
  [11] LayerForge v9 Appendix (2026). docs/verification_index.md v6
  (commit a2e91a8).
  [12] LayerForge v9 Appendix (2026). docs/parameter_baseline.md v8
  (commit 8d792fe).
  [13] LayerForge v9 Appendix (2026). docs/capability_matrix.md (commit
  bce1e81).
  [14] LayerForge v9 Appendix (2026). docs/future_plan.md (commit
  c462618).
  [15] LayerForge v9 Appendix (2026). docs/06_decision_log.md ADR-013
  through ADR-026.
  ```

- **修正後 (After)**:
  ```text
  [11] LayerForge v9 Supplementary (2026). docs/verification_index.md
  v6, commit a2e91a8. Resolvable at
  https://github.com/<owner>/LayerForge/blob/a2e91a8/docs/verification_index.md
  (repository DOI deposit pending for camera-ready).
  [12] LayerForge v9 Supplementary (2026). docs/parameter_baseline.md
  v8, commit 8d792fe.
  https://github.com/<owner>/LayerForge/blob/8d792fe/docs/parameter_baseline.md
  [13] LayerForge v9 Supplementary (2026). docs/capability_matrix.md,
  commit bce1e81.
  https://github.com/<owner>/LayerForge/blob/bce1e81/docs/capability_matrix.md
  [14] LayerForge v9 Supplementary (2026). docs/future_plan.md, commit
  c462618.
  https://github.com/<owner>/LayerForge/blob/c462618/docs/future_plan.md
  [15] LayerForge v9 Supplementary (2026). docs/06_decision_log.md,
  ADR-013 through ADR-026. Repository root:
  https://github.com/<owner>/LayerForge (DOI deposit pending).
  ```

  Note to main thread: `<owner>` placeholder to be replaced by the actual GitHub organization/user handle when `build_main.js` is regenerated. If the repository is currently private, [15] should instead point to an archived `.tar.gz` deposit URL.

---

## ■ Response to Reviewer's Point: Question 1

* **査読者の指摘（要約）**: §2/§8 は fact-level FAIL を constitutive (ADR-026) と articulate するが、§7 で I-101 (probe API) / I-103 (output interpretation layer) を改善 path として挙げる。両者の論理的緊張、特に probe API / interpretation layer の改善が constitutive 性質を変えるのか別 dimension かを明示してほしい。
* **著者らの回答（Response）**:
    > We thank the reviewer for surfacing this tension. The intended distinction is between (a) **what LayerForge produces internally** (constitutively theme-level, fact-level FAIL is design property per ADR-026) and (b) **how consumers route and interpret that output** (where probe API and interpretation layer operate). I-101 / I-103 do not modify the constitutive property in (a); they sit at the **boundary** between LayerForge output and the consumer pipeline, helping consumers detect "this query needs fact-level routing → invoke NER/regex/RAG instead of trusting LayerForge output as-is". To remove the ambiguity, we have appended a clarifying paragraph to §2 distinguishing constitutive (internal) from boundary-layer (consumer-side) interventions, and a parallel one-sentence opener to §7 that explicitly classifies each future-work item by which side of this boundary it operates on.

#### 【本文の修正差分 (Manuscript Changes)】
- **該当箇所**: §2 末尾 (新規段落) + §7 序文

- **修正前 (Before)** — §2 末尾 (existing): ends at "Figure 1 visualizes this positioning." plus the Major-2 disclaimer added above.

- **修正後 (After)** — additional paragraph appended to §2 (after the Major-2 disclaimer):
  ```text
  Constitutive vs boundary-layer interventions. The fact-level FAIL is
  constitutive at the LayerForge core: it is a property of what
  LayerForge produces (theme-level representations via CPM-Louvain on
  sentence embeddings, ctfidf representation). It is not removed by any
  modification at the consumer boundary. The future-work items I-101
  (probe API) and I-103 (output interpretation layer) are explicitly
  boundary-layer interventions: they help downstream consumers detect
  when a query requires fact-level routing (i.e., NER / regex / RAG
  rather than trusting LayerForge output as-is), but they do not change
  the internal constitutive property. The operational implication
  ("fact-level use cases require the hybrid pipeline") therefore remains
  unchanged by I-101 / I-103.
  ```

- **修正前 (Before)** — §7 first sentence:
  ```text
  We articulate 15 future work items across 4 axes. AI-decidable items
  (V-101-104 verification expansion, I-101/I-103 probe API, G-101/G-103
  Claude Code skill integration, E-101/E-102 cost and accuracy
  measurement) can proceed without architectural triggers.
  ```

- **修正後 (After)** — §7 first paragraph:
  ```text
  We articulate 15 future work items across 4 axes. Following the §2
  constitutive vs boundary-layer distinction: I-101 (probe API) and
  I-103 (output interpretation layer) are boundary-layer interventions
  that do not modify the LayerForge core; V-101-104, G-101/G-103, and
  E-101/E-102 are observational / packaging items. None of these touch
  the v8.1 core spec. I-102 (routing logic) and I-104 (probe driver
  isolation), G-102/G-104 (framework / cross-tool integration), and
  E-103 (real deployment) are sovereign-trigger items because they
  either span v8.1 integrity or scope-expand beyond the personal-OS
  setting. AI-decidable items can proceed without architectural triggers;
  sovereign-trigger items await architectural and scope decisions.
  ```

---

## ■ Response to Reviewer's Point: Question 2

* **査読者の指摘（要約）**: §5.1 の cross-corpus direction reversal (hotpotqa K-means 優位 / livedoor LayerForge 優位) を "multi-hop QA vs JA news" の task 種別差として framing するのは post-hoc rationalization の risk。事前予測根拠 (既存文献 / 理論) がなければ "dataset-dependent" のみに留め、cause attribution を弱めるべき。
* **著者らの回答（Response）**:
    > We accept the post-hoc-risk concern. We had no pre-registered hypothesis predicting "token-frequency clustering favors multi-hop QA" before observing the V-042-tri / V-042-quad direction reversal, and we did not cite prior literature establishing this prediction. We have rewritten §5.1 to (i) report the reversal as a purely empirical dataset-dependent finding, (ii) demote the multi-hop-QA-vs-JA-news interpretation to a hypothesis flagged as unverified and post-hoc, and (iii) point to V-103 (direction-reversal root-cause investigation, already enumerated in Appendix E) as the formal future work for cause attribution.

#### 【本文の修正差分 (Manuscript Changes)】
- **該当箇所**: §5.1

- **修正前 (Before)**:
  ```text
  V-042-tri (hotpotqa) shows K-means superior to LayerForge alone
  (+0.080). V-042-quad (livedoor) shows LayerForge superior to K-means
  (+0.121, direction reversed). Both datasets confirm ensemble superior to
  both baselines. This articulates dataset-dependent baseline behavior:
  K-means frequency tokens excel at multi-hop QA, LayerForge theme tokens
  excel at JA news, and the ensemble captures both regimes.
  ```

- **修正後 (After)**:
  ```text
  V-042-tri (hotpotqa) shows K-means superior to LayerForge alone
  (+0.080). V-042-quad (livedoor) shows LayerForge superior to K-means
  (+0.121, direction reversed). Both datasets confirm ensemble superior
  to both baselines. As an empirical finding we report the reversal as
  dataset-dependent baseline behavior; we did not pre-register a
  hypothesis predicting this direction. A post-hoc interpretation —
  "K-means frequency tokens may favor multi-hop QA, LayerForge theme
  tokens may favor JA news" — is offered only as a candidate explanation
  pending V-103 (direction-reversal root cause, see Appendix E) and
  should not be read as a confirmed cause. The ensemble's headline
  property — absorbing both regimes regardless of which baseline
  dominates — does not depend on resolving the cause attribution.
  ```

---

## ■ Response to Reviewer's Point: Question 3

* **査読者の指摘（要約）**: Table 1 は ensemble p 値を報告するが cost/latency 比較がない。`v042_bis_n30_results.json` の `ensemble.comp_mean = 272.57` vs `layerforge.comp_mean = 188.47` は ensemble が ~45% 長い decomposition output (+ K-means 追加計算) を要する。cost-adjusted improvement を articulate せず recommendation を出すのは不十分。
* **著者らの回答（Response）**:
    > We thank the reviewer for the direct cross-check against `v042_bis_n30_results.json`. The numbers in question are summary.layerforge.comp_mean = 188.47 and summary.ensemble.comp_mean = 272.57 (units: characters of decomposition output per query, n=30). This is a +44.6% increase in output volume, which combines with the additional K-means clustering step to drive the runtime / token cost increase the reviewer flags. We have inserted a cost-adjusted paragraph immediately after Table 1 reporting the +11.3% tok_recall improvement against the +44.6% output-volume cost, and added a Limitations bullet stating that ensemble adoption requires a per-deployment cost / quality trade-off decision (not a universal recommendation). The downstream-LLM-cost extension itself is logged as E-101 (already in the future-work table).

#### 【本文の修正差分 (Manuscript Changes)】
- **該当箇所**: §4.3 — new paragraph immediately following Table 1; §6 Limitations — new bullet.

- **修正前 (Before)** — §4.3 text after Table 1: ends at "*Table 1. Hybrid ensemble N progression and cross-corpus statistical significance. Both datasets confirm ensemble > both baselines (paired t-test).*"

- **修正後 (After)** — new paragraph appended after the Table 1 caption:
  ```text
  Computational overhead (cost-adjusted view). Table 1 reports
  significance only; cost is reported here. On V-042-bis (hotpotqa
  N=30), the ensemble produces decomposition output averaging 272.6
  characters per query, against 188.5 for LayerForge alone (raw values:
  summary.ensemble.comp_mean and summary.layerforge.comp_mean in
  v042_bis_n30_results.json) — a +44.6% increase in output volume,
  before accounting for the additional K-means clustering step. The
  paired-t improvement of +0.098 tok_recall (Table 1, V-042-bis row)
  must therefore be read against this overhead. The ensemble path is a
  per-deployment trade-off decision (recall gain vs output / latency
  cost), not a universal recommendation; formal downstream-LLM-token
  cost measurement is filed as E-101 in the future-work roadmap.
  ```

- **修正前 (Before)** — §6 Limitations: existing 5 bullets (the self-preference one is rewritten under Minor 3).

- **修正後 (After)** — new bullet appended to §6:
  ```text
  - Ensemble cost overhead unquantified at the downstream-LLM-token
    level: V-042-bis shows +44.6% decomposition output volume for the
    ensemble vs LayerForge alone, but per-deployment cost / latency
    impact on the consuming LLM is unmeasured (E-101 pending).
  ```

---

## ■ Response to Reviewer's Point: Question 4

* **査読者の指摘（要約）**: Appendix B Table B1 で V-008 polbooks "AMBIGUOUS (ARI 0.6140, K=6 over-seg)" / V-009 football "K-FAIL but ARI 0.8549" と記載されているが、§4.2–§4.5 本文では言及されない。LayerForge core 仕様 K=4±1 cognitive constraint の外挿境界の根拠データを持つ唯一の experiment が main 本文 absent。
* **著者らの回答（Response）**:
    > We accept the criticism: V-008 / V-009 are the only verifications that probe the K=4±1 cognitive constraint against ground-truth K outside that range (polbooks K=3, football K=12), and their main-text absence weakens the boundary-condition disclosure. The natural home is §6 Limitations (rather than §4, which is about reduction and fidelity within the K=4±1 regime). We have added a Limitations bullet that names V-008 / V-009 explicitly, reports the ARI values, and frames the K=4±1 constraint as partially robust within the tested range and **undocumented outside it**.

#### 【本文の修正差分 (Manuscript Changes)】
- **該当箇所**: §6 Limitations — new bullet

- **修正前 (Before)** — §6 Limitations bullets (current set):
  ```text
  - Sample sizes N=5-100; formal population-scale not achieved.
  - Self-preference bias: ... (rewritten under Minor 3)
  - Coverage bias: EN long-form dominated by hotpotqa (16/16 ...).
  - Fact-level FAIL is constitutive (ADR-026 design) ...
  - Path 1 (core-spec ctfidf to tf hybrid) is unevaluated ...
  ```

- **修正後 (After)** — new bullet appended (in addition to the Question 3 bullet):
  ```text
  - K=4±1 cognitive constraint robustness is only partially verified
    outside the constraint range. The only experiments probing
    ground-truth K outside K=4±1 are V-008 (polbooks, ground-truth K=3,
    LayerForge K=6 over-segmentation, ARI 0.6140 AMBIGUOUS) and V-009
    (football, ground-truth K=12, K-FAIL with ARI 0.8549). These are
    graph-community benchmarks rather than text decomposition, and they
    indicate that the K=4±1 constraint produces partial agreement with
    out-of-range ground truth but is not validated for arbitrary K. Text
    decomposition with substantially different intrinsic K remains an
    extrapolation boundary.
  ```

---

## Cross-consistency check

After applying the above 11 revisions, the following internal consistency invariants were verified:

1. **"quintuple-evidence" string removed from Abstract / §2 / §8**: no other occurrence in main or appendix references the count "quintuple" as an ordinal label for evidence; Appendix D Plot 2 caption still says "quintuple-FAIL constitutive limit" — this should also be retermed (`build_appendix.js` action: replace "quintuple-FAIL" → "constitutive fact-level FAIL" in Plot 2 caption to maintain terminology coherence).
2. **"47+" replaced by "46"**: Abstract is the sole occurrence; Appendix B caption "(47+ entries)" should also be updated to "(46 entries)" — `build_appendix.js` action.
3. **§4.5 weakening propagates**: §8 currently says "All 14 parameter ablations confirm current baseline optimality" — this must also be weakened. Proposed §8 phrasing: "All 14 parameter ablations under tested N (5-30) produced no parameter change above the IMPROVEMENT-LARGE threshold; baseline snapshot v1 is frozen under bounded ablation budget" (see Major 3 disposition).
4. **§7 future-work classification (Question 1)** now explicitly classifies I-101 / I-103 as boundary-layer; no contradiction with §2.
5. **Minor 6 References** placeholder `<owner>` must be resolved by main thread at build time.
6. **Self-preference bias scoping (Minor 3)** is consistent with §3 (Method) existing disclosure; no rework needed in §3.

Three deferred propagation actions for `build_*.js` regeneration that follow directly from the above and were not enumerated as separate reviewer points:
- Abstract "(47+ entries)" → "(46 entries)" in Appendix B caption.
- Appendix D Plot 2 caption "quintuple-FAIL" → "constitutive fact-level FAIL".
- §8 "All 14 parameter ablations confirm current baseline optimality; snapshot v1 is preserved unchanged" → "All 14 parameter ablations under tested N (5-30) produced no parameter change above the IMPROVEMENT-LARGE threshold; baseline snapshot v1 is frozen under bounded ablation budget" (Major 3 propagation).

---

## Round-2 reviewer agenda (for next iteration)

Likely high-value reviewer focus areas after these revisions land:
- Whether the §2 boundary-layer paragraph adequately resolves the constitutive-vs-improvable tension, or whether I-101 / I-103 should be reclassified relative to ADR-026.
- Whether the V-029-a N=5 → CI-based pilot framing is enough, or whether Figure 4 should be deferred to V-030 entirely.
- Whether the metric-vs-corpus multiplicity disclaimer in §2 should also be referenced from §6 Limitations explicitly.
- Whether the ensemble cost-overhead bullet is sufficient, or whether Table 1 should add a `comp_mean` column for both datasets.
