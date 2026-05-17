# LayerForge v9 Peer Review Report

Reviewer: Claude Code subagent (= self-preference bias disclosure: see §6)
Date: 2026-05-17
Paper: layerforge_v9_main.pdf + layerforge_v9_appendix.pdf
Cross-checked against: `docs/verification_index.md` v6, `docs/parameter_baseline.md` v8, `docs/06_decision_log.md`, `docs/verifications/*.md`, `scripts/fidelity_recall/*.json`.

## 1. 総合評価 (Overview & Recommendation)

- **判定（暫定）**: **Major Revision**
- **要約**: 本論文は「two-layer fidelity 構造」「Hybrid ensemble の統計的優位性」「14 ablations にわたる baseline 最適性」の三本柱を提示する v9 update である。主結果のうち V-042-tri / V-042-quad の p-value は raw JSON で再現確認できた一方、(a) §4.4 「Cost vs Accuracy Sweet Spot」の数値表現が読者を強く誤導する形になっており(N=5 累積トークン数を per-query 軸として figure 上に提示)、(b) §2 / §8 で繰り返される「quintuple-evidence PASS / FAIL」というラベルが evidence の独立性検証なしに使われており、(c) ADR-026 ベース fact-level FAIL の「constitutive design」articulate と §7 で提示される future work I-101/I-103 (probe API) との論理的緊張が解消されていない。修正は主に表現・図の再構築・claim の弱化で吸収可能で、reject 水準ではない。

## 2. 主な強み (Major Strengths)

- **§2 の two-layer fidelity 概念は構造的に価値が高い**: theme-level (semantic) vs fact-level (lexical) を独立次元として明示し、single-metric 評価の under-claim / over-claim 失敗 mode を明確に articulate している。V-026 の UMass/NPMI 結果 (per-sample raw 確認済) と V-021/V-022 の substring/ROUGE 結果が同一 input に対して反対符号の evidence を出していること自体は事実として強い。
- **Pre-register/post-run 分離 (§3) と immutability 規律**: ADR-022 §3 ベースの「§1-§5 改竄禁止下で §6-§8 を append」運用は post-hoc threshold drift を構造的に防いでおり、verification record (`docs/verifications/2026-05-16_v026_topic_coherence.md` §9 correction が append-only で landed されているのは具体例) としてこの規律が機能していることが確認できる。
- **V-042-tri / V-042-quad の cross-corpus 統計的検証は raw 再現可能**: `v042_tri_n100_stat_results.json` の `ensemble_vs_lf.p_t = 2.694e-05` と `v042_quad_livedoor_results.json` の `ensemble_vs_lf.p = 5.130e-08` を独立に確認、Table 1 の p 値報告と一致。Hybrid ensemble 主張は両 dataset で統計的に直接の裏付けがある。
- **§5.1 の cross-corpus direction reversal の honest 開示**: hotpotqa では K-means 優位、livedoor では LayerForge 優位という反転を隠蔽せず提示し、ensemble の効用を「両 regime を吸収する」として framing している点は科学的に誠実。

## 3. 重大な欠陥・懸念事項 (Major Concerns)

> ※論文の採否に直結する論理的破綻、前提の誤り、または決定的な説明不足。

### 【指摘 1】 §4.4 Figure 4 (Cost vs Accuracy) の axis 単位誤認 — high severity

- **問題点**: §4.4 本文と Figure 4 caption は「Full context achieves 60% accuracy at 22k tokens; F4 hybrid alone reaches 0% accuracy at 3.5k tokens」と articulate するが、raw 確認の結果これらの数値は **N=5 全 sample 合計** のトークン数 (22,006 = 5 query 累計、平均 ~4,400 tokens/query) と N=5 上の F4 hybrid `contains` 率 (0/5 = 0%) である。`docs/verifications/2026-05-17_v029a_cost_latency.md` line 49 で「Total N=5: full=22,006、F3=222、F4hyb=3,561」と明示されており、22k は per-query cost ではない。Figure 4 を log-scale の x-axis で「コスト」として読む読者は、1 クエリあたり 22k tokens 投入で 60% という比率を頭に描くが、これは 4,400 tokens 投入で 60% (N=5) の誤認となる。「accuracy 0%」も N=5 (V-024-bis `contains=0.0`) の数値で、論文 Abstract 級の図に出すには CI もなく N が極端に小さい。
- **理由・背景**: 「コスト vs 精度」プロットは本論文 §4.4 の operational implication 主張の核であり、F4 hybrid + RAG の hypothesized sweet spot (8k × 50%) を visually 正当化する根拠図である。x 軸が log scale + 累積カウントの混淆である以上、読者の判断を実質的に bias する。
- **必要な修正アクション**:
  1. x 軸を **per-query mean input tokens** に統一し、22k → ~4.4k に値変更 (V-029-a per-sample 平均から再描画)。
  2. y 軸 60% / 0% に **N=5、95% CI [exact binomial]** を併記。N=5 の `contains` 率 60% は 95% CI [14.7%, 94.7%]、0% は 95% CI [0%, 52.2%] でほぼ重なる。CI 重なりを図示するか、§4.4 を「N=5 pilot のため accuracy 軸は indicative のみ」と明示。
  3. Figure 4 caption と本文に「N=5 pilot、per-query mean」を必ず付記。
  4. 「hypothesized sweet spot 8k × 50%」は未検証 hypothesis であり、現状 figure 上に dot で示すと検証済と混同される。点ではなく **shaded region** として描き「V-030 未実施」を caption に再強調。

### 【指摘 2】 「quintuple-evidence PASS / FAIL」ラベルの independence 検証欠落 — high severity

- **問題点**: Abstract / §2 / §8 で「quintuple PASS at theme-level / quintuple FAIL at fact-level」が繰り返し articulate されるが、本文中で「これら 5 evidence がどの程度独立な情報源か」の議論が存在しない。`docs/verification_index.md` line 91 では fact-level FAIL を sextuple evidence と数えており、本論文の `quintuple` とそもそも数が合わない。さらに verification_index 自体が `V-021 (hotpotqa N=10) + V-022 (livedoor N=9) + V-023 (hotpotqa N=10 attribute) + V-024 (hotpotqa N=5 F3) + V-024-bis (hotpotqa N=5 F4) + V-042-tri (hotpotqa N=100)` を fact-level evidence として列挙しており、**6 件中 4 件が同一 dataset (hotpotqa) 上の異なる metric / N**、別 dataset は livedoor のみ。`quintuple` という ordinal claim は (a) 数が論文と index で不一致、(b) hotpotqa 偏在を mask する。
- **理由・背景**: 「quintuple-evidence」というラベルは reviewer / 読者に「5 個の独立な実験で同じ結論」という強い印象を与え、generalization claim を underwrite する効果を持つ。実際は同一 corpus 上の異なる metric は **independent ではなく correlated** であり、metric-multiplication と evidence-multiplication を区別する必要がある。論文 §6 Limitations の「Coverage bias: EN long-form dominated by hotpotqa (16/16 verifications)」と直接矛盾する。
- **必要な修正アクション**:
  1. Abstract / §2 / §8 の「quintuple」表現を **「(metric-multiple, dataset-limited): 2 datasets (hotpotqa / livedoor) × 4 metric families (substring / ROUGE / attribute / downstream accuracy)」** のように分解 articulate。
  2. verification_index v6 と数を合わせる (quintuple → sextuple)、もしくは数を出さず「multiple independent metrics on 2 datasets」表現に統一。
  3. §2 Theoretical Framework に「metric multiplicity ≠ corpus multiplicity」の disclaimer を 1 段落追加。

### 【指摘 3】 §4.5 「14 ablations confirm baseline parameter optimality」の inferential 飛躍 — medium-high severity

- **問題点**: §4.5 は「14 ablations confirm baseline parameter values are at or near improvement-LARGE threshold (no parameter shows >0.30 delta improvement)」と articulate するが、これは「改善が見つからなかった」(absence of evidence) を「現 baseline が最適」(evidence of optimality) と読み替える inferential 飛躍である。Appendix C の 16 行を確認すると、`CPM gamma` 行は「dataset-dependent best」、`SNIPPET_CHARS` 行は「PARTIAL-IMPROVEMENT, 240/480 candidate」、`ASCII tokenizer pattern` 行は「NEGATIVE (digit drop internal), core-spec future」と articulate されており、いずれも「baseline 最適」とは整合しない。`V-032-bis` も §4.5 本文で「mpnet > MiniLM-L6 in N=30 reverses N=5 direction」と direction reversal を認めており、ablation 結果が「safe」ではなく **「N に依存して reverse する」** 性質を持つことを著者自身も指摘している。
- **理由・背景**: 論文の operational implication (= 「現 baseline を凍結したまま hybrid path で改善せよ」) はこの「baseline 最適」claim に依拠する。もし baseline が "merely undisturbed by limited ablation budget" であれば、operational recommendation の論拠が大幅に弱くなる。
- **必要な修正アクション**:
  1. §4.5 一文を「14 ablations did not find any parameter change yielding >0.30 delta improvement under the tested N (5-30)」に弱化。
  2. SNIPPET_CHARS の PARTIAL-IMPROVEMENT、CPM gamma の dataset-dependent、tokenizer pattern の core-spec future の 3 件を「pending refinement candidates」として明示。
  3. V-032-bis の N=5 → N=30 direction reversal を §4.5 で 1 文追加し、「small-N ablation 結果は direction-only」と明示。

## 4. 軽微な指摘・修正要求 (Minor Points)

### 【指摘 1】 §4.2 trade-off curve `fidelity = 0.94 × (1 - reduction × 0.15)` の出自と統計的地位

`docs/verifications/2026-05-17_v040_pareto_analysis.md` line 63 と `scripts/analysis/eval_v040_pareto_analysis.py` line 426 に同一表現があるが、これは **regression fit ではなく approximation heuristic** として記述されている (「で近似」)。論文本文では「The trade-off curve is approximately fidelity = 0.94 × (1 − reduction × 0.15)」と書かれており、回帰式と誤読される。**「regression ではなく 2 点間 visual heuristic である」** ことを明示するか、R²/CI を付けるか、削除する。

### 【指摘 2】 V-026 UMass best 「6/6」 vs 「5/6」 の chain consistency

`docs/verifications/2026-05-16_v026_topic_coherence.md` §9 で 6/6 → 5/6 への correction が append されているが、論文 main 本文 §2 / §4 / §5 では UMass の具体数は引用されていない (これは正解)。一方 Appendix B Table B2 V-026 行は「LF-COMPETITIVE NPMI + UMass best 6/6」のまま記述されている可能性 (raw appendix では「LF-COMPETITIVE NPMI + UMass best 6/6」と書かれている、要確認)。実際の text 確認: `v9_appendix_text.md` line 156 の V-026 行は `"LF-COMPETITIVE NPMI + UMass best 6/6"` で **未訂正のまま**。**5/6 (hotpot/4 NMF outlier)** へ修正必要。

### 【指摘 3】 §6 Limitations の self-preference bias 開示は適切だが、影響範囲が曖昧

「Self-preference bias: subagent fallback (Claude evaluating Claude)」とだけ articulate されており、**どの結果がこの bias の影響を受けるか specific でない**。V-024 / V-024-bis / V-025 の downstream LLM accuracy / refusal / BERTScore はすべて Claude subagent 経由であるため、これら specific verification を bias 影響範囲として明示すべき。一方 V-042 系の paired t-test は metric ベース (tok_recall) であり LLM judge を経ていないため、bias から structurally 独立であることも明示すると claim の差別化ができる。

### 【指摘 4】 Abstract の「47+ verifications」の precise 数

Abstract は「47+ verifications and 14 parameter ablations across 14 datasets」と articulate するが、Appendix B Table B1/B2 で具体的に列挙されている V-ID を数えると 20 + 25 + cross-corpus 1 = 46 件で、「47+」とは合わない。**正確な数値 (例: 46 V-IDs)** に修正するか、後続検証を含む total count の根拠を明示。

### 【指摘 5】 §1 で v8.1 と v9 の差分が読者に伝わりにくい

§1 Introduction の最後段「This v9 update articulates what LayerForge can and cannot do...」は scope statement だが、**v8.1 から何が新しいのか (= V-021 以降の fidelity 直接測定、V-040 Pareto analysis、V-042 系の ensemble 統計的検証)** が箇条書きで明示されていない。読者が v8.1 を既読でないと差分が分からない。3-4 bullet で what's new in v9 を §1 末尾に追加推奨。

### 【指摘 6】 References の self-citation が `commit hash` 形式

Refs [11]-[15] が `commit a2e91a8` 等のコミットハッシュ形式で記載されているが、外部読者は本 repo へのアクセスがない場合 dereference できない。論文として self-contained にするには (a) repo の DOI / archived URL を付ける、(b) Appendix を独立 supplementary material として完結させる、いずれかが望ましい。

## 5. 著者への質問 (Questions for the Authors)

1. **§2 と §7 の論理的緊張**: §2 / §8 では fact-level FAIL を「constitutive design property (ADR-026)」 = LayerForge 単体では原理的に解決不可と articulate しているが、§7 で I-101 (probe API) / I-103 (output interpretation layer) を AI-decidable future work として挙げている。**probe API / interpretation layer の改善は fact-level FAIL の constitutive 性質を変えるのか、それとも別 dimension か**を明示してほしい。両者が「constitutive だが driver-level で改善可能」のような曖昧な status にあると、論文の operational implication (= 「fact 用途には hybrid pipeline 必須」) が弱まる。

2. **§5.1 cross-corpus direction reversal の root cause**: hotpotqa (K-means 優位) と livedoor (LayerForge 優位) の direction 反転を「multi-hop QA vs JA news」のタスク種別差として framing しているが、これは **post-hoc rationalization の risk** がある。事前に「multi-hop QA では token-frequency-based clustering が優位」と予測する根拠 (= 既存文献 / 理論) はあるか。なければ「dataset-dependent」のみに留め、cause attribution を弱める案を検討してほしい。

3. **§4.3 ensemble の computational overhead**: Table 1 は ensemble の p 値を報告するが、cost / latency の comparison がない。`v042_bis_n30_results.json` の `summary.ensemble.comp_mean = 272.57` vs `layerforge.comp_mean = 188.47` は ensemble が ~45% 長い decomposition output (および K-means の追加計算) を要することを示唆する。**ensemble が production で recommend されるためには cost-adjusted improvement** (例: 「+11.3% recall を +45% comp 増で達成」) の数値が必要ではないか。本論文 §4.3 / §5 / §8 で operational recommendation を出す前に、この trade-off を articulate すべき。

4. **V-008 polbooks の AMBIGUOUS 扱い**: Appendix B Table B1 で V-008 polbooks は「AMBIGUOUS (ARI 0.6140, K=6 over-seg)」と記載されているが、§4.2 〜 §4.5 本文では一切言及されない。LayerForge は K=4±1 cognitive constraint を core 仕様として持つが、polbooks の ground truth K=3 と football の ground truth K=12 はその範囲外であり、**K=4±1 制約が外挿境界の根拠データを持つ唯一の experiment** (V-008/V-009) が main paper 本文で扱われていない理由を説明してほしい。本来は §6 Limitations または §4 で「K 制約の robustness 検証は ARI 0.61/0.85 で partial」と articulate されるべきではないか。

## 6. Self-preference bias disclosure (本査読 limitation)

本査読は Claude Code subagent (Sonnet/Opus) によって実施された。著者 chai が Claude を用いて作成した paper を、別 Claude session が査読するため、構造的に positive direction に biased される可能性がある (= LLM-as-judge self-preference bias、Anthropic 公式 acknowledged limitation: [Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) で「we should use a different model for evaluation than the one used for generating the content」と明示)。

本査読では bias を構造的に counter するため以下を実施した:
- Major Concerns / Minor Points は **必ず raw JSON / verification record の具体行を cross-check した evidence ベース** で記述 (例: §4.4 Figure 4 の批判は `v029a_cost_latency_results.json` line 49 と `v029a` per-sample tokens の direct 確認、Major Concern 1)
- 「妥当」「特に問題なし」articulate は禁止、Strengths も具体的な file path / line / numeric evidence と共にのみ提示
- Appendix B Table B2 の「UMass best 6/6」が `2026-05-16_v026_topic_coherence.md` §9 correction (5/6) と inconsistent な点を bias を超えて指摘した (Minor 2)

それでも本査読 report の信頼度を formal 化するには以下のいずれか必要:
- (a) 独立 human reviewer による cross-check
- (b) 別 LLM family (GPT-4 / Gemini / Mistral) reviewer による cross-check
- (c) Anthropic API direct + Haiku 4.5 (vs subagent fallback) による cross-check
- (d) 同 family であっても session 完全分離 + raw JSON re-verification の strict re-run

特に Major Concern 1 (Figure 4 axis 単位誤認) と Major Concern 2 (quintuple-evidence ラベル) は実害が大きい論理的指摘であり、bias 下でも検出された点で robust 寄り。一方「総合評価 Major Revision」の severity 判定自体は subjective で、別 reviewer は Minor Revision / Reject の方向に divergent する可能性がある。
