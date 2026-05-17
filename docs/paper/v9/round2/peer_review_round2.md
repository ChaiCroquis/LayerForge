# LayerForge v9 Peer Review Report — Round 2

Reviewer: Claude Code subagent (fresh-context, separate session) — see §6 self-preference bias disclosure
Date: 2026-05-17
Paper (round 2 revised): `paper/v9/round2/v9_main_text.md` + `paper/v9/round2/v9_appendix_text.md`
Author response: `paper/v9/round2/response_to_reviewers_2.md` (7 revisions in response to Round 1 Reviewer's 2 Major + 5 Minor + 4 Questions)
Prior round: `paper/v9/round1/peer_review_round1.md`
Cross-checked against (raw JSON, decoded via UTF-8): `scripts/fidelity_recall/v042_ensemble_hybrid_results.json`, `v042_bis_n30_results.json`, `v042_tri_n100_stat_results.json`, `v042_quad_livedoor_results.json`, `v029a_cost_latency_results.json`.

---

## 1. 総合評価 (Overview & Recommendation)

- **判定（暫定）**: **Accept**
- **要約**: Round 1 で指摘した Major 1-2 (Abstract Claim (3) optimality 残存 + Appendix C Table C caption "confirm baseline parameter optimality" 残存) は両方 verbatim に修正済で、`v9_main_text.md` 全文と `v9_appendix_text.md` 全文を grep した結果、`optimality` の出現箇所はすべて "not an optimality claim / not as an optimality assertion" の否定文脈に統一されている。Minor 1-5 もすべて指示通り landed (Coverage bias scoping decomposition / §3 bias を §6 への pointer に短縮 / Abstract "ensemble vs LayerForge alone" qualifier 追記 / Plot 5 caption を main Figure 4 reference に短縮 / References 序文に repo private 状態の articulation 追加)。Question 3 由来の Table 1 comp_mean 列追加も landed しているが、V-042-tri / V-042-quad で `n/a*` 表記となっており、その理由 (raw JSON が tok_recall fields のみ dump、comp_chars 未記録) を author が caption 内で正直に articulate しており、independent verification で `v042_tri_n100_stat_results.json` / `v042_quad_livedoor_results.json` の `summary` が空 + `means` が tok_recall のみ含むことを確認 — author articulation と raw JSON 一致。新規 internal inconsistency なし。Round 1 false-positive pattern (V-026 "6/6" stale extract) の再発もなし。Round-3 reviewer agenda として author 自身が予測した 3 件 (Table 1 directionality / References note placement / Coverage bias decomposition placement) は **paper-claim risk ではない presentational polish** であり、本 reviewer も独立に re-evaluate した結果、Minor として manuscript-side action を要請する水準には達していない (= sycophancy-inverse failure mode 防御で manufactured Minors は出さない、§7 で明示)。Round 2 closure として Accept 判定。

## 2. 主な強み (Major Strengths)

- **Major 1 修正の propagation completeness**: `v9_main_text.md` Abstract line 11 の Claim (3) は "frozen under bounded ablation budget --- no parameter change reached the IMPROVEMENT-LARGE threshold (\>0.30 delta) across 14 ablations under tested N (5-30); this is a freeze decision, not an optimality claim (see Section 4.5)" に書き換えられ、§4.5 line 101 ("This is an empirical statement about the ablation search budget, not a claim of global optimality"), §8 line 139 ("not an optimality claim"), Appendix C preface line 167 ("This is not an optimality claim"), Appendix C Table C caption line 205 ("not an optimality claim; see main Section 4.5") と用語完全一致 (`optimality` の単独 positive 使用が paper 全体で 0 件、独立 grep 確認)。Round 1 で指摘した内部矛盾は構造的に閉じた。
- **Minor 3 co-landed の bias counter 効果**: Abstract Claim (2) は "ensemble vs LayerForge alone: hotpotqa N=100 p=2.7e-05, livedoor N=27 p=5.1e-08; see Table 1 for vs K-means comparisons" に書き換えられ、reader が "報告された p 値は vs LayerForge であり vs K-means の方が livedoor では更に stringent (p=1.3e-10) である" ことを Table 1 直接参照で確認可能。selective citation frame risk は解消。
- **Table 1 comp_mean 列追加の raw JSON 透明性**: `v042_ensemble_hybrid_results.json` summary.layerforge.comp_mean=174.6 / summary.ensemble.comp_mean=264.0、`v042_bis_n30_results.json` summary.layerforge.comp_mean=188.47 / summary.ensemble.comp_mean=272.57 を independent decode で確認、Table 1 line 78-80 の (174.6, 264.0, 188.5, 272.6) と一致。V-042-tri / V-042-quad の `n/a*` 表記は `v042_tri_n100_stat_results.json` / `v042_quad_livedoor_results.json` で `summary={}` + `means` が tok_recall fields のみ含むことを確認、author の "the tri/quad evaluators recorded only tok_recall fields" articulation と一致。manufactured data の risk なし。
- **§4.3 cost-adjusted 段落の N=5 + N=30 directionality articulation**: paragraph line 89 で "V-042 hotpotqa N=5: 264.0 vs 174.6, +51.2%; V-042-bis hotpotqa N=30: 272.6 vs 188.5, +44.6%" と両 row の overhead を併記。independent calculation で (264.0-174.6)/174.6 = 0.5120 = +51.2%、(272.57-188.47)/188.47 = 0.4462 = +44.6% と一致、両 N で正方向の overhead が consistent。Round 1 で V-042-bis のみ articulate されていた問題は解消。
- **Minor 1 Coverage bias scoping の precise re-count**: §6 line 123 は "16/16 pure-hotpotqa-dataset rows in Appendix B Table B2; an additional 2 parameter-sweep rows V-024-tri/V-024-quad operate on hotpotqa data, and 2 mixed-corpus rows V-020/V-026 include hotpotqa alongside ShareGPT" と decomposition 化。independent re-count: V-021, V-023, V-024, V-024-bis, V-027, V-029-a, V-032, V-032-bis, V-033, V-034, V-035, V-036, V-037, V-042, V-042-bis, V-042-tri = 16 (一致)。+2 (V-024-tri TOP_MEMBERS sweep / V-024-quad SNIPPET sweep) + 2 (V-020 ShareGPT+hotpotqa / V-026 ShareGPT+hotpotqa) も Table B2 / Table B1 と一致。"16/16" の意味があいまいだった Round 1 指摘は構造的に解消。

## 3. 重大な欠陥・懸念事項 (Major Concerns)

> ※論文の採否に直結する論理的破綻、前提の誤り、または決定的な説明不足。

**該当なし**。Round 1 で指摘した Major 1-2 (Abstract Claim (3) optimality 残存 + Appendix C Table C caption optimality 残存) は両方とも verbatim 修正済で、独立 grep + line-by-line cross-check で内部矛盾が再発していないことを確認。新規 Major Concern を manufacture しない (§7 self-preference bias counter で明示済の判断基準: sycophancy-inverse failure mode 防御)。

## 4. 軽微な指摘・修正要求 (Minor Points)

> ※Round 1 で指摘した Minor 1-5 はすべて patch landed。本 round で新たに manuscript-side action を要請する Minor を **manufacture しない** (= §7 で明示の sycophancy-inverse 防御)。以下は **manuscript-side action 不要だが reviewer-side audit trail として残す観察事項のみ** で、author response Round-3 reviewer agenda (response_to_reviewers_2.md line 380-388) で author 自身が既に articulate している 3 件のうち、本 reviewer の独立評価で **「polish であり Minor 水準には達しない」と判定** した結果を簡記する。

### 【observation 1, NOT-Minor】 Table 1 V-042-tri / V-042-quad の `n/a*` 表記の future-work 解消

Table 1 caption の `(*) V-042-tri / V-042-quad did not dump summary.*.comp_mean in the raw JSON` という注記は **fact として正しい** ことを independent verification で確認した (`v042_tri_n100_stat_results.json.summary == {}`, `v042_quad_livedoor_results.json.summary == {}`)。これは raw data 側の不完全性であり、Round 2 で manuscript を patch しても改善できない (= re-evaluation が必要)。author が E-101 future-work に "back-filling comp_mean for V-042-tri / V-042-quad" として組み込んでいるのは適切。本 reviewer から要請する manuscript-side action なし。

### 【observation 2, NOT-Minor】 References repository access note の inline 配置

References line 163 の "Repository access note for [11]-[15]" は currently inline (= [10] と [11] の間に italic 段落として) 配置されている。author Round-3 agenda は "footnote on the first occurrence of a GitHub URL" への移動を polish 案として挙げているが、本 reviewer の評価では (a) inline は scope 限定 ([11]-[15] explicit に named) で読者は迷わない、(b) footnote 移動は markdown → docx pipeline 上の footnote 互換性に依存し process risk が上がる、(c) inline でも paper-claim risk なし、と判定。**manuscript-side action 不要**。

### 【observation 3, NOT-Minor】 §6 Coverage bias decomposition placement

§6 line 123 の Coverage bias bullet は (16/16 + 2 + 2) 内訳を inline で articulate しており、author Round-3 agenda は "move to Appendix B as a quantified caveat" を polish 案として挙げている。本 reviewer の評価では (a) §6 Limitations は headline claim level に直接 attach すべき内容であり、scope 数値も headline level で articulate されているのが望ましい、(b) Appendix B 移動は §6 から detail への遷移を増やし、Limitations の self-containment を弱める、(c) 現状の inline 配置は length 4 文で readable、と判定。**manuscript-side action 不要**。

## 5. 著者への質問 (Questions for the Authors)

> ※manuscript-side で resolution が必要な questions は **ない**。以下は Round 2 patch の独立 audit を完了したことを記録するための informational question のみ。

### 【Q1, informational only】 build pipeline diff guarantee の future-work 化

Round 1 Question 2 (= "source markdown vs PDF identity を物理層で保証する invariant があるか") に対する Round 2 author response は "no formal physical-layer invariant currently guarantees source-markdown vs PDF identity ... filed as a future-work / tooling item" であった。本 reviewer の Round 2 review は再び source markdown (`v9_main_text.md` / `v9_appendix_text.md`) を canonical surface として読んでおり、Round 1 false-positive pattern (V-026 "6/6" stale extract) は再発していない (= source markdown 上で当該の V-026 行は Appendix B Table B2 line 114 で "LF-COMPETITIVE NPMI + UMass best 5/6" と articulate されており、本 reviewer は誤読していない)。**Q1 への期待**: 次 round 以降 (もしあれば) で `build_main.js` / `build_appendix.js` から生成される PDF と source markdown の text-equivalence check が tooling 化された場合、その build artifact hash と source markdown commit hash の pair を References [15] か Appendix 末尾の build provenance note に明記することを推奨。これは Round 2 closure には不要 (= camera-ready 段階で対応可)。

## 6. Round-2 Author Agenda 評価

author の Round 2 response 末尾 "Round-3 reviewer agenda" (line 380-388) は 3 項目を予測している:

1. **Table 1 comp_mean directionality across N=5 / N=30**: author 自身が +51.2% (V-042 N=5) を本 round で paragraph line 89 に追加済で、+44.6% (V-042-bis N=30) と並べて記載。directionality は両 row で正方向 consistent、本 reviewer が independent calculation で確認済 (Strengths §4 参照)。**Round 2 で既に解消**。
2. **References private-repo note placement (inline vs footnote)**: 本 reviewer §4 observation 2 で manuscript-side action 不要と判定。
3. **§6 Coverage bias decomposition placement (§6 bullet vs Appendix B)**: 本 reviewer §4 observation 3 で manuscript-side action 不要と判定。

**Author Agenda 妥当性総評**: 3 項目すべて author 自身が "presentational polish, none of these are paper-claim risks" と articulate している通り、Round 2 closure を blocking しない。1 項目は本 round で実質的に解消 (paragraph 内 +51.2% 追記)、残る 2 項目は本 reviewer の independent 評価で polish のみと判定。**新規 Round-3 agenda 候補は提示しない** (Round 2 closure 適切と判断)。

## 7. Self-preference bias disclosure (本査読 limitation)

本査読は Claude Code subagent (Sonnet/Opus) によって実施された。著者 chai が Claude を用いて作成した paper を、別 Claude session が査読するため、構造的に positive direction に biased される可能性がある (= LLM-as-judge self-preference bias、Anthropic 公式 acknowledged limitation: [Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) で「we should use a different model for evaluation than the one used for generating the content」と明示)。Round 1 reviewer も同 model family、Round 1 Author / Round 2 Author も同 model family、= **author-reviewer-author loop が完全に同 model family 内に閉じている** = bias risk は構造的に最大水準。

本査読では bias を構造的に counter するため以下を実施した:

- Major Concerns / Minor Points は **raw JSON file の独立 decode (UTF-8 で `json.load`) + 数値 cross-check** に基づき判定 (例: V-042 N=5 comp_mean を `v042_ensemble_hybrid_results.json` から再読み込みで 174.6 / 264.0 確認、+51.2% を独立計算で確認、V-042-tri / V-042-quad の `summary == {}` を独立確認)。
- "Round 1 で指摘した内容が landed したかどうか" を `v9_main_text.md` / `v9_appendix_text.md` の line-by-line read で確認 (例: Abstract Claim (3) は line 11 の string verbatim 一致、Appendix C Table C caption は line 205 の string verbatim 一致)。
- **manufactured Minors 禁止** (= sycophancy-inverse failure mode 防御): "appearance のために Minor を捻り出す" 行為は author への disservice であり、本 review では Round 1 Minor 1-5 がすべて landed した時点で新規 Minor を出さない判断をした。著者の Round-3 agenda 3 項目も独立評価で polish 水準と判定。
- §4 で observation 3 件を **NOT-Minor として記録** することで、reviewer が見落とした論点ではなく、見た上で manuscript-side action 不要と判定した audit trail を残す。

それでも本査読 report の信頼度を formal 化するには以下のいずれか必要 (Round 1 と同じ):

- (a) 独立 human reviewer による cross-check
- (b) 別 LLM family (GPT-4 / Gemini / Mistral) reviewer による cross-check
- (c) Anthropic API direct + Haiku 4.5 (vs subagent fallback) による cross-check
- (d) 同 family であっても session 完全分離 + raw JSON re-verification の strict re-run (= 本 round で実施した方法)

**本 round 2 review の特徴**: Round 1 で指摘した Major 1-2 + Minor 1-5 + Q1-4 がすべて Round 2 author response 通り landed したことを raw JSON + line-by-line で独立確認、新規内部矛盾なし、Round 1 false-positive (stale extract) 再発なし、Round 2 author 予測の Round-3 agenda 3 件は polish のみと判定。**判定 Accept は bias 下でも raw evidence に basis する判定**。別 reviewer は (i) Accept (本 reviewer と同じ評価)、(ii) Minor Revision (V-042-tri / V-042-quad comp_mean back-fill を camera-ready 前に要請する場合) のいずれかに収束する可能性が高い。Major Revision / Reject に至る path は raw evidence 上 considered unlikely。
