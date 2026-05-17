# LayerForge v9 Peer Review Report — Round 1

Reviewer: Claude Code subagent (= self-preference bias disclosure: see §6)
Date: 2026-05-17
Paper (round 1 revised): `paper/v9/round1/v9_main_text.md` + `paper/v9/round1/v9_appendix_text.md`
Author response: `paper/v9/round1/response_to_reviewers_1.md` (11 revisions + 1 false-positive rejection)
Cross-checked against: `scripts/fidelity_recall/v029a_cost_latency_results.json`, `v042_bis_n30_results.json`, `v042_tri_n100_stat_results.json`, `v042_quad_livedoor_results.json`, `docs/verification_index.md` v6, `docs/parameter_baseline.md` v8.

---

## 1. 総合評価 (Overview & Recommendation)

- **判定（暫定）**: **Minor Revision**
- **要約**: Round 0 で指摘した Major 1-3 はいずれも substantively addressed されている (Figure 4 軸単位は per-query mean + CI に再構築、"quintuple-evidence" は metric-multiple/corpus-dual 表現に書き換え + §2 disclaimer 段落新設、§4.5 optimality 主張は "freeze under bounded ablation budget" に弱化)。Minor 1/3/4/5/6 と Question 1-4 への対応も適切。ただし (a) **修正の propagation が 2 箇所で incomplete** (Abstract line 25 に `(3) baseline parameter optimality across 14 ablations` が残存 = Major 3 修正と矛盾、Appendix C Table caption が `All ablations confirm baseline parameter optimality` のまま = Appendix C preface 修正と矛盾)、(b) 著者 Minor 2 false-positive 棄却は raw 確認上正しいが、reviewer-side stale extract の root cause が response 内で audit trail 化されているのみで manuscript 側に痕跡なし (acceptable)、(c) 新たに minor な内部整合性 gap が 1 件 (Appendix B 範囲書きと "16/16 verifications" 古い文言の整合性) を検出。Round 2 ではこの 2-3 件の文字列 patch のみで Accept 水準に到達見込み。

## 2. 主な強み (Major Strengths)

- **Major 1 修正の数値再現性が極めて高い**: §4.4 本文 (`v9_main_text.md` line 229-239) と Figure 4 caption (line 241-257) は per-query 平均を `v029a_cost_latency_results.json` から直接再構成しており、独立検証で full = 22006/5 = 4401.2 (≈4.4k)、f4_hybrid = 3561/5 = 712.2 (≈0.7k) と一致。95% CI [14.7%, 94.7%] / [0%, 52.2%] も N=5 の exact-binomial で再計算可能 (Clopper-Pearson 5/3、5/0 で同値域)。"CIs overlap substantially" + shaded uncertainty band + V-030 pending の三重ガードで、過剰主張 risk は構造的に閉じている。
- **Major 2 修正は ordinal claim を構造的に排除している**: Abstract (line 19-23)、§2 (line 78-99)、§8 (line 371-376) いずれも `quintuple` を除去、§2 末尾 disclaimer 段落 (line 89-99) は metric multiplicity vs corpus multiplicity の混同を明示禁止しており、独立観測仮定の濫用を語彙レベルで block している。Appendix D Plot 2 caption (line 318-328) も `constitutive fact-level FAIL` に同期更新済で cross-consistency check 1 が manuscript に landed されている。
- **Major 3 修正の epistemic 区別が明確**: §4.5 (line 261-274) は "empirical statement about the ablation search budget, not a claim of global optimality" と articulate、SNIPPET_CHARS / CPM gamma / ASCII tokenizer の 3 candidate と V-032-bis の N=5→N=30 direction reversal を本文内で enumerate、Appendix C preface (line 237-245) も同期更新済。"freeze decision under bounded ablation budget" は absence of evidence と evidence of optimality の混同を読者側で復活させない frame として有効。
- **Question 1 への boundary-layer paragraph 追加が constitutive vs probe API の論理緊張を解消**: §2 末尾 (line 101-112) は I-101/I-103 を boundary-layer intervention として明示分類、§7 序文 (line 356-367) もこの分類を反映、ADR-026 constitutive 性と future-work の non-contradiction が読者に伝わる構造になった。
- **Question 3 cost-adjusted 段落の raw evidence**: §4.3 (line 214-225) は `v042_bis_n30_results.json` line 9 (comp_mean=188.47) と line 23 (comp_mean=272.57) を独立確認、+44.6% overhead 数値も `(272.57 - 188.47) / 188.47 = 0.4462` で一致。+0.098 tok_recall improvement も `summary.delta_tok.ensemble_vs_layerforge = 0.0978` (line 28) と一致。"per-deployment trade-off decision, not a universal recommendation" の弱化も recommendation creep を防ぐ frame として適切。

## 3. 重大な欠陥・懸念事項 (Major Concerns)

> ※論文の採否に直結する論理的破綻、前提の誤り、または決定的な説明不足。

### 【指摘 1】 Abstract Claim (3) と §4.5 / Appendix C preface / §8 の **内部矛盾** — high severity

- **問題点**: Major 3 修正で §4.5 (line 261-274)、Appendix C preface (line 237-245)、§8 (line 379-382) はすべて "no parameter change above the IMPROVEMENT-LARGE threshold... not an optimality claim / frozen under bounded ablation budget" に書き換えられているが、**Abstract line 25 だけ `(3) baseline parameter optimality across 14 ablations` という古い optimality claim 表現が残存**している。Abstract は paper の第一印象を決める文章であり、本文と矛盾する claim を残したまま submit すれば reviewer / 読者は本文と Abstract のいずれを信じればよいか判断できない。著者 response の cross-consistency check では §8 と Appendix B caption の propagation は明示的にカバーされているが、**Abstract の Claim (3) は propagation list から欠落**している (response 末尾 "Three deferred propagation actions" 参照、Abstract が含まれていない)。
- **理由・背景**: Major 3 修正の核心 (optimality claim weakening) は Abstract まで propagate されてはじめて意味を持つ。本文だけ慎重に書き換えて Abstract が optimistic ということは、reviewer に「Abstract と本文を別人が書いている」と評価されかねず、Round 0 reviewer report §3 Major Concern 3 が指摘した inferential 飛躍が **Abstract に局所的に残存** している状態。
- **必要な修正アクション**:
  1. Abstract line 25 `(3) baseline parameter optimality across 14 ablations` → `(3) baseline parameter values frozen under bounded ablation budget (no improvement-LARGE threshold reached across 14 ablations under tested N=5-30)` に書き換え。
  2. 同時に Abstract 全体を §4.5 / §8 / Appendix C preface と用語一貫させ、`optimality` 単語を Abstract から除去する (= 該当 1 箇所のみ)。
  3. response_to_reviewers_1.md の cross-consistency check に Abstract Claim (3) を追加する round-2 audit note 化。

### 【指摘 2】 Appendix C Table C caption と Table 本体の post-fix 整合 — medium severity

- **問題点**: Appendix C preface (line 237-245) は Major 3 修正で "freeze decision under bounded ablation budget — no parameter change reached the IMPROVEMENT-LARGE threshold... This is not an optimality claim" に更新済だが、**直後の Table C caption (line 299-301) は `All ablations confirm baseline parameter optimality; snapshot v1 unchanged.` という pre-revision の optimality claim をそのまま残している**。Table C は Appendix C preface の直接下流であり、preface で "not an optimality claim" と articulate した直後の table caption で "confirm baseline parameter optimality" と書くと、読者は preface と caption のどちらが著者の真意か判断できない (= 自己矛盾の典型 pattern)。
- **理由・背景**: cross-consistency check として preface 修正は landed されたが、同 Appendix 内 Table caption への propagation が漏れた。Round 0 反復 → Round 1 修正 → 修正 propagation という 3-step loop の最終 step が incomplete。
- **必要な修正アクション**:
  1. Appendix C Table C caption (line 299-301) を `Table C. Parameter ablation full details (16 entries: 14 ablation + 2 articulation correction). No parameter change reached IMPROVEMENT-LARGE threshold (>0.30 delta) under tested N (5-30); baseline snapshot v1 frozen under bounded ablation budget (see Section 4.5).` に書き換え。
  2. cross-consistency check に Table C caption を追加し、Round 2 で同 pattern の漏れを再発させない。

## 4. 軽微な指摘・修正要求 (Minor Points)

### 【指摘 1】 §6 Limitations "16/16 verifications" の数 vs Appendix B Table B1/B2 の数

§6 Limitations (line 329-330) は `Coverage bias: EN long-form dominated by hotpotqa (16/16 verifications)` と articulate するが、Appendix B Table B2 を hotpotqa が dataset として明示されている行で数えると V-021/023/024/024-bis/027/029-a/032/032-bis/033/034/035/036/037/V-024-tri/V-024-quad/V-042/V-042-bis/V-042-tri = 18 行 (V-024-tri/V-024-quad は parameter sweep だが対象 dataset は hotpotqa)。"16/16" の出典が round 0 以前 (V-040 時点) であれば、Phase 2b の現時点 verification 数と整合しない可能性が高い。**Round 2 で正確な hotpotqa-on-fact-level 行数を再カウントし、`16/16` を実数に更新するか、対象範囲 (例: "fact-level EN long-form verifications") を限定して articulate する**ことを推奨。

### 【指摘 2】 §3 Method の "Formal Anthropic API plus Haiku 4.5 confirmation is pending for paper-level claims; current evidence is direction-only" と §6 Limitations Minor 3 修正 (= 同 bias 開示) の二重記述

§3 Method (line 136-139) と §6 Limitations bias bullet (line 317-327) はどちらも self-preference bias を開示するが、§6 は LLM-judged subset (V-024/024-bis/V-025) と metric-only subset (V-042 family) を明示分離する Minor 3 修正後の精密版に対し、§3 は "current evidence is direction-only" という古い包括的表現のまま。**§3 を §6 と同期させ、direction-only claim を LLM-judged subset に限定する**か、または §3 を「detail は §6 参照」に短縮することを推奨。現状は同 paper 内で同じ bias を二度、しかも片方は精密、もう片方は包括的に articulate しており、reviewer が「§3 と §6 のどちらが著者の current position か」を判断する必要が出る。

### 【指摘 3】 Abstract で "Hybrid ensemble path... hotpotqa N=100 p=2.7e-05, livedoor N=27 p=5.1e-08" の p 値選択根拠

Abstract line 24-25 は ensemble の significance を `p=2.7e-05` (hotpotqa) と `p=5.1e-08` (livedoor) で報告するが、raw JSON 直接確認では (a) v042_tri_n100_stat_results.json `ensemble_vs_lf.p_t = 2.694e-05`、(b) v042_quad_livedoor_results.json `ensemble_vs_lf.p = 5.130e-08` であり、いずれも **ensemble vs LayerForge alone** の p 値。一方 ensemble_vs_km の p 値はそれぞれ 2.4e-03 と 1.3e-10 で、特に livedoor では vs K-means の方が更に小さい (p=1.3e-10)。Abstract で vs LayerForge の p のみを選択的に articulate するのは "ensemble > LayerForge" 方向の strength を強調する frame として読まれる可能性がある。**Abstract で `(ensemble vs LayerForge alone)` を明示する**か、Table 1 を Abstract から直接参照する形 (例: "see Table 1") に切り替えることを推奨。Round 0 では指摘していないが、self-preference bias counter として metric 選択透明性は強化すべき。

### 【指摘 4】 Plot 5 caption (Appendix D line 346-360) と Figure 4 caption (main line 241-257) の冗長度

両 caption は per-query mean / 95% CI / shaded region / V-030 pending を full duplicate しており、約 90% 文字一致。**Appendix D Plot 5 caption を main Figure 4 と完全一致させるか、Plot 5 は "(see main Figure 4 for caption details)" に短縮**することを推奨。現状は同一情報の二重メンテナンスとなり、round 2 以降の caption update で drift risk がある (例: 今 round で main Figure 4 caption を更新したが Plot 5 caption 旧版だった場合、cross-consistency check で漏れる)。

### 【指摘 5】 References URL は resolve 済だが repo の **public/private 状態** の articulate なし

References [11]-[15] (line 417-436) は `<owner>` placeholder が `ChaiCroquis/LayerForge-dev` に resolve 済で round 0 Minor 6 の指摘は close されているが、author response Note (`response_to_reviewers_1.md` line 442) で「If the repository is currently private, [15] should instead point to an archived `.tar.gz` deposit URL」と articulate されていた条件分岐の選択結果が manuscript 側で明示されていない。**現在 repo が public で reviewer / 読者が GitHub URL を resolve できる状態**なのか、または DOI deposit pending の note は repository public 化と並行か、Abstract / References 序文で 1 sentence 明示することを推奨。Round 0 Minor 6 は dereference 不能を主問題としていたが、Round 1 では URL を resolve 済で「実際にアクセスできるか」が次の論点に移っている。

## 5. 著者への質問 (Questions for the Authors)

1. **Major Concern 1 (Abstract Claim (3) 残存) は意図的か propagation 漏れか**: §4.5 / §8 / Appendix C preface が一貫して "freeze under bounded ablation budget" に書き換えられている中、Abstract Claim (3) のみ `baseline parameter optimality` が残存している。これは (a) Abstract は意図的に optimality claim を保持しているのか、(b) cross-consistency check 時に Abstract が propagation list から漏れたのか、いずれか明示してほしい。(b) であれば round 2 で 1 行修正、(a) であれば Abstract と本文の用語不整合の根拠を §4.5 内で説明する必要がある。

2. **Minor 2 false-positive 棄却の reviewer-side root cause**: 著者 response Minor 2 で「reviewer's subagent operated on a stale text extract that pre-dated `build_appendix.js` regeneration」と分析しているが、**round 1 reviewer (= 本査読者) も同じ stale extract risk に晒されている可能性**がある。本査読は `v9_main_text.md` / `v9_appendix_text.md` の latest commit を直接 Read tool で参照しており、上記 review は最新 text に基づいているが、reviewer が paper PDF (build_*.js 生成物) ではなく source markdown を見ていることが round 2 で問題化しないか、author 側で「reviewer は source markdown を見ても PDF を見ても同一 content である」ことを物理層 (例: build pipeline の diff check) で保証している invariant があるか教えてほしい。

3. **§4.3 cost-adjusted 段落で V-042-bis のみ articulate された理由**: 著者 response Question 3 は V-042-bis (N=30 hotpotqa) の comp_mean を articulate するが、V-042-tri (N=100 hotpotqa) と V-042-quad (N=27 livedoor) には触れていない。Table 1 の headline は V-042-tri / V-042-quad の statistical significance であり、cost-adjusted view も **headline 側 (V-042-tri/quad) で報告するのが自然** ではないか。V-042-bis のみ articulate した根拠 (e.g., V-042-bis の comp_mean が raw JSON で直接読める形で保存されている vs V-042-tri/quad では未 dump) があれば明示してほしい。

4. **Minor 1 で指摘した §3 と §6 bias 開示の二重化**: §3 Method と §6 Limitations の self-preference bias 開示を二重に持つ frame は意図的か (= 読者の bias 認知を強化するため複数箇所で articulate する design) か、それとも §6 が Minor 3 で修正された後に §3 の同期 update が忘れられた propagation 漏れか。前者であれば不整合を残す根拠を 1 sentence 補強、後者であれば §3 を §6 と同期させる修正を round 2 で実施。

## 6. Round-2 Author Agenda 評価

response_to_reviewers_1.md 末尾 "Round-2 reviewer agenda" は 4 項目を予測している:

1. **§2 boundary-layer paragraph adequacy**: 本査読 Strengths §4 で「論理緊張を解消」と評価済。Round 2 で reclassification の必要性は低い。
2. **Figure 4 V-029-a pilot framing の十分性**: 本査読 Strengths §1 で「3 重ガードで過剰主張 risk は構造的に閉じている」と評価済。Round 2 で Figure 4 を V-030 まで完全 defer する必要性は低い (現 framing で acceptable)。
3. **§2 metric-vs-corpus disclaimer を §6 から参照**: 本査読では指摘していないが、author agenda の通り「§2 disclaimer を §6 Limitations bullet (Coverage bias 行) で参照する」のは cross-section integrity 強化として有用。Round 2 で 1 行追記推奨。
4. **Table 1 に comp_mean 列追加**: 本査読 Question 3 で「V-042-tri/quad の cost-adjusted を articulate すべき」と質問しており、author agenda 4 と整合。Round 2 で Table 1 に `comp_mean (LF)` / `comp_mean (Ens)` の 2 列追加が望ましい。

**Author Agenda 妥当性総評**: 4 項目すべて構造的に妥当、特に項目 3-4 は round 2 で確実に実施推奨。本査読が新たに追加すべき agenda 候補は (a) Abstract Claim (3) propagation (Major 1)、(b) Appendix C Table caption propagation (Major 2)、(c) §3 / §6 bias 開示二重化解消 (Minor 2)、(d) repository public/private articulate (Minor 5) の 4 件で、いずれも文字列 patch 水準で round 2 closure 可能。

## 7. Self-preference bias disclosure (本査読 limitation)

本査読は Claude Code subagent (Sonnet/Opus) によって実施された。著者 chai が Claude を用いて作成した paper を、別 Claude session が査読するため、構造的に positive direction に biased される可能性がある (= LLM-as-judge self-preference bias、Anthropic 公式 acknowledged limitation: [Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) で「we should use a different model for evaluation than the one used for generating the content」と明示)。

本査読では bias を構造的に counter するため以下を実施した:
- Major Concerns / Minor Points は **必ず raw JSON / verification record / manuscript line 番号の具体行を cross-check した evidence ベース** で記述 (例: Major 1 は `v9_main_text.md` line 25 vs line 261-274 / 237-245 / 379-382 の直接比較、Major 2 は line 299-301 vs line 237-245 の直接比較)。
- Round 0 review の Major Concern 1 (Figure 4 軸単位) は raw JSON 直接再計算で著者修正値 (4.4k / 0.7k tokens/query) と一致確認、Strengths §1 で具体 numeric を提示。
- 「妥当」「特に問題なし」articulate は禁止、Strengths 5 項目すべて具体的な file path / line / raw JSON value を併記。
- 「Major Concerns 最低 1 件、Minor Points 最低 3 件」の指示に従い、bias 下でも Major 2 件 (Abstract propagation 漏れ + Table C caption propagation 漏れ) + Minor 5 件を明示的に検出。

それでも本査読 report の信頼度を formal 化するには以下のいずれか必要:
- (a) 独立 human reviewer による cross-check
- (b) 別 LLM family (GPT-4 / Gemini / Mistral) reviewer による cross-check
- (c) Anthropic API direct + Haiku 4.5 (vs subagent fallback) による cross-check
- (d) 同 family であっても session 完全分離 + raw JSON re-verification の strict re-run

本 round 1 review の特徴: Round 0 で指摘した Major 1-3 は **bias 下でも substantively addressed と判定**、ただし bias を counter するため新規 propagation 漏れ (Major 1-2) を厳格に検出している。総合評価 Minor Revision は subjective で、別 reviewer は Accept (= 残存 issue は editorial level として扱う) または Major Revision (= Abstract propagation 漏れを重大視) のいずれにも divergent する可能性がある。Author 側の round 2 修正 (Abstract Claim (3) 修正 + Table C caption 修正) が landed すれば、本査読者の position は Accept に向かう見込み。
