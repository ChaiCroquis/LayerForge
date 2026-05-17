**LayerForge v9: Phase 2b Verification Update**

*Two-Layer Fidelity Structure and Hybrid Ensemble Path*

chai · 2026-05-17

*(Main paper. Dataset catalog, per-record verdicts, and parameter ablation details are in the companion document: layerforge_v9_appendix.pdf)*

**Abstract**

LayerForge is a deterministic text-decomposition tool that extracts 4 plus or minus 1 hierarchical themes via CPM community detection on sentence-transformer embeddings. The v8.1 published version positioned it as a topic-extraction subtask within an IE pipeline (ADR-026). This v9 update reports Phase 2b: 46 verifications and 14 parameter ablations across 14 datasets (EN/JA, multi-turn dialogue, multi-hop QA, news, long-form). We articulate (1) a two-layer fidelity structure: theme-level semantic preservation passes across multiple metric families on two datasets (hotpotqa EN / livedoor JA), and fact-level lexical preservation fails across multiple metric families on the same two datasets, (2) a statistically significant Hybrid ensemble path (LayerForge plus K-means; ensemble vs LayerForge alone: hotpotqa N=100 p=2.7e-05, livedoor N=27 p=5.1e-08; see Table 1 for vs K-means comparisons), (3) baseline parameter values frozen under bounded ablation budget --- no parameter change reached the IMPROVEMENT-LARGE threshold (\>0.30 delta) across 14 ablations under tested N (5-30); this is a freeze decision, not an optimality claim (see Section 4.5), and (4) explicit extrapolation boundaries per pattern coverage. The fact-level structural limitation is articulated as a constitutive design property (ADR-026), with hybrid pipeline as the operational remedy.

**1. Introduction**

LayerForge v8.1 produces 4 plus or minus 1 hierarchical themes from arbitrary input text via four components: (i) sentence-transformer embeddings (paraphrase-multilingual-mpnet-base-v2), (ii) CPM-Louvain community detection (Traag 2011, Blondel 2008), (iii) scale_finder with K=4 plus or minus 1 cognitive constraint (Miller 1956, Cowan 2001), (iv) ctfidf-based representation extraction (Grootendorst 2022). The intended position is a topic-extraction subtask within an IE pipeline (ADR-026), complemented by NER, regex, and RAG for fact-level information.

This v9 update articulates what LayerForge can and cannot do, where structural limitations lie, and which improvement paths are evidence-grounded. Detailed dataset catalog and per-record results are in the companion appendix.

What is new in v9 (relative to v8.1):

- Direct fact-level fidelity measurement (V-021 substring, V-022 ROUGE-L, V-023 attribute breakdown, V-024/024-bis downstream LLM accuracy) --- v8.1 reported only theme-level evidence.

- Two-layer fidelity formalization (Section 2) and the Pareto plot set (V-040) consolidating 38 evidence points into 5 visualizations.

- Hybrid ensemble path (LayerForge + K-means) with cross-corpus statistical significance (V-042-tri N=100 hotpotqa, V-042-quad N=27 livedoor), establishing an evidence-grounded improvement direction without modifying v8.1 core.

- Explicit extrapolation boundaries per pattern coverage, and a decoupled \'freeze under bounded ablation budget\' framing for the 14-ablation result (Section 4.5).

**2. Theoretical Framework: Two-Layer Fidelity**

We articulate fidelity as a two-layer structure rather than a single aggregate metric. Each layer carries internally consistent but oppositely-signed evidence:

- Theme-level semantic: response cosine, BERTScore F1, topic coherence (UMass/NPMI). Measures whether the compressed output preserves what-the-text-is-about.

- Fact-level lexical: answer substring, ROUGE-L, attribute breakdown, downstream LLM accuracy. Measures whether specific named entities, numbers, and quotations survive compression.

These layers are independent dimensions. LayerForge is structurally PASS at theme-level and structurally FAIL at fact-level. The theme-level PASS is corroborated by multiple metric families (response cosine, BERTScore F1, topic coherence UMass/NPMI) on two datasets (hotpotqa EN, livedoor JA). The fact-level FAIL is corroborated by four metric families (answer substring, ROUGE-L, attribute breakdown, downstream LLM accuracy) on the same two datasets. The fact-level FAIL is constitutive (ADR-026 design), not a defect; the remedy is hybrid pipeline (LayerForge plus NER/regex/RAG), not LayerForge internal modification. Figure 1 visualizes this positioning.

Disclaimer (metric multiplicity vs corpus multiplicity). The above evidence is metric-multiple but corpus-dual. Distinct metric families applied to the same corpus are statistically correlated and do not constitute independent observations in the sense of independent draws from disjoint populations. Per-dataset hotpotqa records dominate the fact-level evidence count (see Appendix B); livedoor provides the only out-of-corpus replication for both theme-level and fact-level. We therefore refrain from any ordinal \'n-tuple evidence\' labeling and emphasize that broader corpus coverage (V-102 cross-domain extension, see Section 7) is required before generalization beyond the two-corpus span.

Constitutive vs boundary-layer interventions. The fact-level FAIL is constitutive at the LayerForge core: it is a property of what LayerForge produces (theme-level representations via CPM-Louvain on sentence embeddings, ctfidf representation). It is not removed by any modification at the consumer boundary. The future-work items I-101 (probe API) and I-103 (output interpretation layer) are explicitly boundary-layer interventions: they help downstream consumers detect when a query requires fact-level routing (i.e., NER / regex / RAG rather than trusting LayerForge output as-is), but they do not change the internal constitutive property. The operational implication (\'fact-level use cases require the hybrid pipeline\') therefore remains unchanged by I-101 / I-103.

![Figure 1. Two-layer fidelity structure (V-040 Plot 3). LayerForge variants cluster in the lower-right quadrant: theme-level high (cosine/BERTScore \>= 0.8) but fact-level low (substring \<= 0.1). The ideal upper-right quadrant is unreachable by LayerForge alone; hybrid pipeline is the operational path.](media/209cd4677d0bed46686787b46c8ca357c0222c4c.png "Figure 1. Two-layer fidelity structure (V-040 Plot 3). LayerForge variants cluster in the lower-right quadrant: theme-level high (cosine/BERTScore >= 0.8) but fact-level low (substring <= 0.1). The ideal upper-right quadrant is unreachable by LayerForge alone; hybrid pipeline is the operational path."){width="5.0in" height="3.5in"}

*Figure 1. Two-layer fidelity structure (V-040 Plot 3). LayerForge variants cluster in the lower-right quadrant: theme-level high (cosine/BERTScore \>= 0.8) but fact-level low (substring \<= 0.1). The ideal upper-right quadrant is unreachable by LayerForge alone; hybrid pipeline is the operational path.*

**3. Method**

All verifications follow ADR-022 Section 3: pre-register Sections 1-5 (claim, dataset, method, pre-commit interpretations) with immutability, then execute and append Sections 6-8 (run record, outcome, impact). This prevents post-hoc threshold drift. Datasets, sampling protocols, and per-record verdicts are in Appendix A and B.

Self-preference bias disclosure: LLM-as-judge evaluations used Claude Code subagent (Sonnet/Opus) as evaluator on Claude-compressed context. This bias affects only the LLM-judged subset of verifications and not the metric-only subset; the differentiated scope (which verifications are bias-affected vs bias-independent) and the cross-confirmation status are articulated in Section 6 Limitations.

**4. Key Results**

**4.1 Reduction Landscape (14 Datasets)**

Reduction across 14 datasets confirms language-independent ceiling (Aozora 99.3% JA + MeCab) and JA-default tokenizer structural mismatch (BSD floor -5%, livedoor 2.5%). See Appendix A for dataset catalog. Figure 2 visualizes the reduction landscape colored by language and tokenization.

![Figure 2. Reduction landscape across 14 datasets (V-040 Plot 4). Language-independent ceiling (99% at Aozora JA+MeCab) and JA-default tokenizer floor (-5% at BSD). EN: 77-99%, JA+MeCab: 57-99%, JA-default: structural mismatch.](media/7a4b2c5bd3b11cae79f73f75ebfbb2176d19d4ec.png "Figure 2. Reduction landscape across 14 datasets (V-040 Plot 4). Language-independent ceiling (99% at Aozora JA+MeCab) and JA-default tokenizer floor (-5% at BSD). EN: 77-99%, JA+MeCab: 57-99%, JA-default: structural mismatch."){width="5.625in" height="3.28125in"}

*Figure 2. Reduction landscape across 14 datasets (V-040 Plot 4). Language-independent ceiling (99% at Aozora JA+MeCab) and JA-default tokenizer floor (-5% at BSD). EN: 77-99%, JA+MeCab: 57-99%, JA-default: structural mismatch.*

**4.2 Theme-level Fidelity (Pareto Frontier)**

On the reduction-by-theme-fidelity plane, F4 hybrid format (V-007/V-025) occupies the Pareto frontier with reduction around 0.85 and BERTScore F1 \>= 0.83 (Figure 3). The trade-off between reduction and theme-level fidelity is summarized by the visual heuristic fidelity ≈ 0.94 × (1 − reduction × 0.15), obtained as a two-point interpolation between the V-007 and V-025 Pareto endpoints (V-040 Pareto analysis). This is a heuristic approximation for reader orientation, not a regression fit; no R² or confidence interval is reported, and the expression should not be used for extrapolation outside the measured reduction range (approximately 0.77-0.99). Detailed verdicts and N for each point are in Appendix B.

![Figure 3. Reduction vs theme-level fidelity Pareto frontier (V-040 Plot 1). F4 hybrid format (V-007/V-025) is current Pareto-optimal at reduction around 0.85, BERTScore F1 0.83-0.94. ADR-022 Claim 2 threshold (0.80) marked in red.](media/86c466badf6d99dba93ab791bc1edb0644739b5b.png "Figure 3. Reduction vs theme-level fidelity Pareto frontier (V-040 Plot 1). F4 hybrid format (V-007/V-025) is current Pareto-optimal at reduction around 0.85, BERTScore F1 0.83-0.94. ADR-022 Claim 2 threshold (0.80) marked in red."){width="5.625in" height="3.9375in"}

*Figure 3. Reduction vs theme-level fidelity Pareto frontier (V-040 Plot 1). F4 hybrid format (V-007/V-025) is current Pareto-optimal at reduction around 0.85, BERTScore F1 0.83-0.94. ADR-022 Claim 2 threshold (0.80) marked in red.*

**4.3 Hybrid Ensemble Path (Statistical Significance)**

V-036 observed K-means baseline tok_recall 2x superior to LayerForge alone on hotpotqa N=5. We pursued Path 2 (LayerForge plus K-means ensemble) as the v8.1-integrity-preserving improvement direction. N progression confirms statistical significance and cross-corpus consistency:

  ------------------------------------------------------------------------------------------------------------------------
  **V-ID**     **Dataset**     **N**   **Ens vs LF (p)**   **Ens vs K-means (p)**   **comp_mean LF**   **comp_mean Ens**
  ------------ --------------- ------- ------------------- ------------------------ ------------------ -------------------
  V-042        hotpotqa        5       +0.067 (n.s.)       +0.000 (n.s.)            174.6              264.0

  V-042-bis    hotpotqa        30      +0.098              +0.042                   188.5              272.6

  V-042-tri    hotpotqa        100     +0.113 (2.7e-05)    +0.033 (2.4e-03)         n/a\*              n/a\*

  V-042-quad   livedoor (JA)   27      +0.140 (5.1e-08)    +0.260 (1.3e-10)         n/a\*              n/a\*
  ------------------------------------------------------------------------------------------------------------------------

*Table 1. Hybrid ensemble N progression and cross-corpus statistical significance, with decomposition output cost (comp_mean, characters per query). Both datasets confirm ensemble \> both baselines (paired t-test); ensemble incurs a consistent positive comp_mean overhead vs LayerForge alone on the rows where it was measured. (\*) V-042-tri / V-042-quad did not dump summary.\*.comp_mean in the raw JSON (the tri/quad evaluators recorded only tok_recall fields); the +44.6% overhead pattern measured at N=30 (V-042-bis) is taken as the representative estimate. Raw values from v042\*\_results.json.*

Computational overhead (cost-adjusted view). Table 1 reports both significance (p-values) and decomposition output cost (comp_mean, characters per query) for the rows where the latter is available. Ensemble incurs a consistent positive comp_mean overhead on both measured rows (V-042 hotpotqa N=5: 264.0 vs 174.6, +51.2%; V-042-bis hotpotqa N=30: 272.6 vs 188.5, +44.6%), before accounting for the additional K-means clustering step. The paired-t improvements must therefore be read against this overhead. The ensemble path is a per-deployment trade-off decision (recall gain vs output / latency cost), not a universal recommendation; formal downstream-LLM-token cost measurement, and back-filling comp_mean for V-042-tri / V-042-quad, are filed as E-101 in the future-work roadmap.

**4.4 Cost vs Accuracy Sweet Spot**

Figure 4 plots per-query input-token cost (log scale) versus downstream LLM accuracy on V-029-a (N=5 hotpotqa pilot). Full context averages 4.4k tokens/query at 60% accuracy (3/5; exact-binomial 95% CI \[14.7%, 94.7%\]); F4-hybrid alone averages 0.7k tokens/query at 0% accuracy (0/5; 95% CI \[0%, 52.2%\]). The two CIs overlap substantially, so this figure is reported as a pilot-scale indication rather than a significance claim. The hypothesized operational region (F4-hybrid + RAG retrieval at approximately 1-10k tokens/query and 30-70% accuracy) is drawn as a shaded uncertainty band; per-query verification of this region requires V-030 (Pending). Raw per-sample token counts are in v029a_cost_latency_results.json.

![Figure 4. Per-query input-token cost (log scale) vs downstream LLM accuracy, V-029-a hotpotqa N=5 pilot (V-040 Plot 5). Full baseline averages 4.4k tokens/query, accuracy 3/5 (60%, 95% CI \[14.7%, 94.7%\]). F4-hybrid alone averages 0.7k tokens/query, accuracy 0/5 (0%, 95% CI \[0%, 52.2%\]); CIs overlap. Shaded band: hypothesized F4-hybrid + RAG operational region, unverified, awaits V-030. N=5 pilot --- axis values are indicative, not significance claims.](media/6d30ceaaedb0106f16382c846757a78e6d3873b6.png "Figure 4. Per-query input-token cost (log scale) vs downstream LLM accuracy, V-029-a hotpotqa N=5 pilot (V-040 Plot 5). Full baseline averages 4.4k tokens/query, accuracy 3/5 (60%, 95% CI [14.7%, 94.7%]). F4-hybrid alone averages 0.7k tokens/query, accuracy 0/5 (0%, 95% CI [0%, 52.2%]); CIs overlap. Shaded band: hypothesized F4-hybrid + RAG operational region, unverified, awaits V-030. N=5 pilot — axis values are indicative, not significance claims."){width="5.625in" height="3.9375in"}

*Figure 4. Per-query input-token cost (log scale) vs downstream LLM accuracy, V-029-a hotpotqa N=5 pilot (V-040 Plot 5). Full baseline averages 4.4k tokens/query, accuracy 3/5 (60%, 95% CI \[14.7%, 94.7%\]). F4-hybrid alone averages 0.7k tokens/query, accuracy 0/5 (0%, 95% CI \[0%, 52.2%\]); CIs overlap. Shaded band: hypothesized F4-hybrid + RAG operational region, unverified, awaits V-030. N=5 pilot --- axis values are indicative, not significance claims.*

**4.5 Parameter Ablation Summary**

14 ablations did not find any parameter change yielding \>0.30 delta improvement under the tested N (5-30). This is an empirical statement about the ablation search budget, not a claim of global optimality: three parameters remain pending-refinement candidates (SNIPPET_CHARS PARTIAL-IMPROVEMENT 240/480, CPM gamma dataset-dependent best, ASCII tokenizer pattern core-spec future), and at least one ablation exhibited N-sensitive direction reversal (V-032-bis: mpnet \> MiniLM-L6 at N=30 reverses the N=5 direction). Baseline snapshot v1 is therefore preserved unchanged as a freeze decision under bounded ablation budget, not as an optimality assertion. Small-N ablation results should be read as direction-only. Notable individual findings: V-027 (digit preservation NEGATIVE leads to core-spec modification trigger), V-032-bis (the N=5→N=30 reversal motivating careful-strategy Rule 3). Full ablation table is in Appendix C.

**5. Discussion**

**5.1 Cross-corpus Direction Reversal**

V-042-tri (hotpotqa) shows K-means superior to LayerForge alone (+0.080). V-042-quad (livedoor) shows LayerForge superior to K-means (+0.121, direction reversed). Both datasets confirm ensemble superior to both baselines. As an empirical finding we report the reversal as dataset-dependent baseline behavior; we did not pre-register a hypothesis predicting this direction. A post-hoc interpretation --- \'K-means frequency tokens may favor multi-hop QA, LayerForge theme tokens may favor JA news\' --- is offered only as a candidate explanation pending V-103 (direction-reversal root cause, see Appendix E) and should not be read as a confirmed cause. The ensemble\'s headline property --- absorbing both regimes regardless of which baseline dominates --- does not depend on resolving the cause attribution.

**5.2 Why the Two-Layer Structure Matters**

Single aggregate fidelity metrics (e.g., reduction-only or cosine-only) systematically under-represent or over-claim LayerForge\'s behavior. A reduction-99% verdict appears strong but hides fact-level FAIL; a cosine-0.94 verdict appears strong but applies only at theme-level. The two-layer structure makes both true claims simultaneously articulable and prevents consumer-side misuse (e.g., expecting fact-extraction from LayerForge output).

**5.3 Driver-level vs Core-spec Modifications**

Driver-level parameter sweeps (TOP_MEMBERS, SNIPPET_CHARS, tokenizer matching) preserve v8.1 integrity. Core-spec modifications (ctfidf to tf hybrid, embedding swap, K=4 plus or minus 1 relaxation, scale_finder change) require v8.1 integrity reconsideration and paper update synchronization. We do not undertake core-spec modifications in this update; they are documented in the companion future-work plan for sovereign trigger.

**6. Limitations**

- Sample sizes N=5-100; formal population-scale not achieved.

- Self-preference bias (scope-specific): downstream-LLM-judged verifications V-024 (F3 refusal), V-024-bis (F4-hybrid accuracy), and V-025 (BERTScore via Claude-rendered evaluation) route through a Claude subagent acting as judge on Claude-compressed context and are therefore subject to LLM-as-judge self-preference bias (Anthropic acknowledged limitation). The V-042 family (paired t-test on tok_recall, including V-042-tri hotpotqa p=2.7e-05 and V-042-quad livedoor p=5.1e-08) computes its primary metric without an LLM judge and is therefore structurally independent of this bias. Formal Anthropic API plus Haiku 4.5 cross-confirmation remains pending for the LLM-judged subset.

- Coverage bias: EN long-form is dominated by hotpotqa (16/16 pure-hotpotqa-dataset rows in Appendix B Table B2; an additional 2 parameter-sweep rows V-024-tri/V-024-quad operate on hotpotqa data, and 2 mixed-corpus rows V-020/V-026 include hotpotqa alongside ShareGPT). JA mid-form is dominated by livedoor (V-022, V-029-b, V-029-d, V-042-quad, plus V-027/V-037/V-033 cross-corpus replication). Generalization beyond this two-corpus span requires V-102 (see Section 7) and is bounded by the metric-vs-corpus multiplicity caveat in the Section 2 disclaimer.

- Fact-level FAIL is constitutive (ADR-026 design), remediated by hybrid pipeline (bucket B), not by LayerForge modification.

- Path 1 (core-spec ctfidf to tf hybrid) is unevaluated; requires v8.1 integrity reconsideration.

- Ensemble cost overhead unquantified at the downstream-LLM-token level: V-042-bis shows +44.6% decomposition output volume for the ensemble vs LayerForge alone, but per-deployment cost / latency impact on the consuming LLM is unmeasured (E-101 pending).

- K=4±1 cognitive constraint robustness is only partially verified outside the constraint range. The only experiments probing ground-truth K outside K=4±1 are V-008 (polbooks, ground-truth K=3, LayerForge K=6 over-segmentation, ARI 0.6140 AMBIGUOUS) and V-009 (football, ground-truth K=12, K-FAIL with ARI 0.8549). These are graph-community benchmarks rather than text decomposition, and they indicate that the K=4±1 constraint produces partial agreement with out-of-range ground truth but is not validated for arbitrary K. Text decomposition with substantially different intrinsic K remains an extrapolation boundary.

**7. Future Work**

We articulate 15 future work items across 4 axes. Following the Section 2 constitutive vs boundary-layer distinction: I-101 (probe API) and I-103 (output interpretation layer) are boundary-layer interventions that do not modify the LayerForge core; V-101-104, G-101/G-103, and E-101/E-102 are observational / packaging items. None of these touch the v8.1 core spec. I-102 (routing logic) and I-104 (probe driver isolation), G-102/G-104 (framework / cross-tool integration), and E-103 (real deployment) are sovereign-trigger items because they either span v8.1 integrity or scope-expand beyond the personal-OS setting. AI-decidable items can proceed without architectural triggers; sovereign-trigger items await architectural and scope decisions. Full roadmap is in the companion appendix.

**8. Conclusion**

LayerForge v9 confirms a two-layer fidelity structure: theme-level semantic preservation is structurally PASS across multiple metric families on two datasets, and fact-level lexical preservation is structurally FAIL across multiple metric families on the same two datasets (hotpotqa EN, livedoor JA; see Section 2 disclaimer for the metric-vs-corpus multiplicity caveat). The Hybrid ensemble path is statistically significantly superior to both baselines on two datasets (hotpotqa p\<2.7e-05, livedoor p\<5.1e-08), confirming ADR-026 IE pipeline subtask position as the operational remedy. All 14 parameter ablations under tested N (5-30) produced no parameter change above the IMPROVEMENT-LARGE threshold; baseline snapshot v1 is frozen under bounded ablation budget (not an optimality claim). Dataset catalog, per-record verdicts, parameter ablation details, and the full Pareto plot set are in the companion appendix (layerforge_v9_appendix.pdf).

**References**

\[1\] Blei, D. M., Ng, A. Y., Jordan, M. I. (2003). Latent Dirichlet Allocation. JMLR.

\[2\] Blondel, V. D., et al. (2008). Fast unfolding of communities in large networks. J. Stat. Mech.

\[3\] Cowan, N. (2001). The magical number 4 in short-term memory. Behavioral and Brain Sciences.

\[4\] Grootendorst, M. (2022). BERTopic: Neural topic modeling with class-based TF-IDF.

\[5\] Lin, C.-Y. (2004). ROUGE: A Package for Automatic Evaluation of Summaries.

\[6\] Miller, G. A. (1956). The magical number seven, plus or minus two. Psychological Review.

\[7\] Reichardt, J., Bornholdt, S. (2006). Statistical mechanics of community detection. Phys. Rev. E.

\[8\] Reimers, N., Gurevych, I. (2019). Sentence-BERT. EMNLP-IJCNLP.

\[9\] Traag, V. A., Van Dooren, P., Nesterov, Y. (2011). Narrow scope for resolution-limit-free community detection. Phys. Rev. E.

\[10\] Zhang, T., et al. (2020). BERTScore: Evaluating Text Generation with BERT. ICLR.

*Repository access note for \[11\]-\[15\]: the repository https://github.com/ChaiCroquis/LayerForge-dev is currently private during pre-publication review. Peer reviewers may request read access from the corresponding author. A persistent archival deposit (Zenodo DOI) of the cited commits will be created for the camera-ready submission and will supersede the GitHub URLs below.*

\[11\] LayerForge v9 Supplementary (2026). docs/verification_index.md v6, commit a2e91a8. Resolvable at https://github.com/ChaiCroquis/LayerForge-dev/blob/a2e91a8/docs/verification_index.md (repository DOI deposit pending for camera-ready).

\[12\] LayerForge v9 Supplementary (2026). docs/parameter_baseline.md v8, commit 8d792fe. https://github.com/ChaiCroquis/LayerForge-dev/blob/8d792fe/docs/parameter_baseline.md

\[13\] LayerForge v9 Supplementary (2026). docs/capability_matrix.md, commit bce1e81. https://github.com/ChaiCroquis/LayerForge-dev/blob/bce1e81/docs/capability_matrix.md

\[14\] LayerForge v9 Supplementary (2026). docs/future_plan.md, commit c462618. https://github.com/ChaiCroquis/LayerForge-dev/blob/c462618/docs/future_plan.md

\[15\] LayerForge v9 Supplementary (2026). docs/06_decision_log.md, ADR-013 through ADR-026. Repository root: https://github.com/ChaiCroquis/LayerForge-dev (DOI deposit pending).
