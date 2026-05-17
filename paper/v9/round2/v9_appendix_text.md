**LayerForge v9 --- Appendix**

*Dataset Catalog, Verification Records, Parameter Ablation, and Pareto Plots*

chai · 2026-05-17 · Companion to layerforge_v9_main.pdf

**Appendix A. Dataset Catalog**

All datasets used in v9 verifications, with language, domain, N range, source, and licensing notes. Datasets are read-only mounted at C:/work/dataset-vault/readonly/ for verification reproducibility.

  -----------------------------------------------------------------------------------------------------------------------------
  **Dataset**                   **Language**   **Domain**            **Length**       **N used**    **Source**
  ----------------------------- -------------- --------------------- ---------------- ------------- ---------------------------
  WildChat (allenai/WildChat)   EN             multi-turn dialogue   mid (1-5k)       3-100         HuggingFace

  ShareGPT                      EN             multi-turn dialogue   mid              3-10          ShareGPT_V3_unfiltered

  LongBench hotpotqa            EN             multi-hop QA          long (50-100k)   5-100         LongBench v1

  loogle                        EN             long single-doc       long (10k+)      5             loogle

  CNN/DailyMail v3              EN             news summary          mid              10            HuggingFace cnn_dailymail

  livedoor news                 JA             news 9 categories     mid (1-2k)       9-27          livedoor-news-corpus

  jmultiwoz                     JA             dialogue              short            10            jmultiwoz

  jawiki                        JA             wiki                  long (10k+)      5 synthetic   jawiki_singletongue

  Aozora                        JA             literature            long (10k+)      5             aozorabunko_clean

  BSD parallel                  EN/JA          dialogue parallel     short            5 each path   bsd_ja_en

  meetingbank                   EN             meeting transcript    mid-long         5             meetingbank

  mt_bench_101                  EN             dialogue              short            10            mt_bench_101

  polbooks (Newman)             graph          community K=3         105 nodes        1             newman_adjnoun benchmark

  football (Newman)             graph          community K=12        115 nodes        1             newman benchmark
  -----------------------------------------------------------------------------------------------------------------------------

*Table A1. Dataset catalog (14 entries).*

**A.1 Sampling Protocols**

Sampling protocols vary by verification: deterministic head (V-018, V-021-042 hotpotqa), stratified by category (V-013-014 livedoor 9 cat), random with seed (V-005 claim1 robustness), synthetic grouped (V-017 jawiki 200-sentence units due to sentence-level original structure). Sampling protocol is recorded per V-ID in Appendix B.

**Appendix B. Verification Record Summary**

Complete verification record list (46 entries: Table B1 V-001-V-020 = 20 rows, Table B2 V-021-V-042-quad + 1 cross-corpus = 26 rows). Each row shows V-ID, dataset, N, verdict, and commit hash for traceability. Full Sections 1-8 records are in docs/verifications/\*.md.

  ------------------------------------------------------------------------------------------------------------------------
  **V-ID**   **Dataset**                    **N**          **Verdict (key metric)**                           **Commit**
  ---------- ------------------------------ -------------- -------------------------------------------------- ------------
  V-001      WildChat (Phase 2b entry)      962/50K        PASS dataset feasibility                           (retro)

  V-002      WildChat                       10             PASS pipeline shape (F1 cosine 0.538)              (retro)

  V-003      WildChat (step_a)              10             format artifact confirmed (F4 0.823 \> F1 0.538)   (retro)

  V-004      WildChat (claim1)              100            formal PASS reduction 93.00% mean                  76a8bda

  V-005      WildChat (robustness)          100            3-axis PASS (random/survivorship/length)           a13ce3f

  V-006      WildChat (claim2 F3)           3              FAIL (refusal 33.3%, specific divergent)           36ced95

  V-007      WildChat (claim2 F4 hybrid)    6              strong PASS (refusal 0/6, cosine 0.939)            f95010f

  V-008      polbooks                       105 nodes      AMBIGUOUS (ARI 0.6140, K=6 over-seg)               d88804f

  V-009      football                       115 nodes      K-FAIL but ARI 0.8549 high                         991671e

  V-010      mt_bench_101 + jmultiwoz       10 each        MIXED (mt PASS 77% / jmulti FAIL 16%)              3e68346

  V-011      loogle                         5              scope-FIT extreme 99% + caveat                     13d01a9

  V-012      meetingbank                    5              intermediate + length sensitivity                  af98808

  V-013      livedoor (JA default)          9 stratified   near-zero 2.5% chars (JA + default mismatch)       bb976c7

  V-014      livedoor (JA + MeCab)          9 stratified   improvement-LARGE delta +83.89 pp (86.40%)         fb51faf

  V-015      jmultiwoz + MeCab              10             improvement-LARGE delta +59.46 pp (75.48%)         fb182fb

  V-016      14 dataset length regression   8 dataset      v7 partial confirm (R-sq=0.54, p=0.023)            79b5cce

  V-017      jawiki                         5 synthetic    v7-fit INTERMEDIATE 93.65% + sigmoid hint          ffb5597

  V-018      ShareGPT + LongBench           3+5            WildChat-confirm + loogle-confirm                  b341cc5

  V-019      Aozora + BSD parallel          5 + 5x3        ceiling 99.29% + MeCab\>EN asymmetry               547f7aa

  V-020      ShareGPT + hotpotqa            3+5            LayerForge-COMPETITIVE vs LDA/NMF                  1dee6cd
  ------------------------------------------------------------------------------------------------------------------------

*Table B1. Verification records V-001 through V-020 (Phase 2a + 2b base).*

  -------------------------------------------------------------------------------------------------------------------------------------------------------------
  **V-ID**                       **Dataset**                              **N**      **Verdict (key metric)**                                      **Commit**
  ------------------------------ ---------------------------------------- ---------- ------------------------------------------------------------- ------------
  V-021                          hotpotqa (factual recall)                10         PRESERVE-FAIL substring 10%, tok 18%                          09d44bc

  V-022                          livedoor (ROUGE-L)                       9          RETENTION-FAIL R-L 0.074, delta +0.113                        5e0f21a

  V-023                          hotpotqa attribute breakdown             10 retro   ATTR-TYPE-UNIFORM-FAIL + CONTEXT-DOMINANT                     e51a847

  V-024                          hotpotqa F3 downstream                   5          REFUSAL-CONSTITUTIVE 5/5 (V-006 N=5 stronger)                 c5a53d4

  V-024-bis                      hotpotqa F4 hybrid downstream            5          REFUSAL-AVOIDED + ACCURACY-WEAK 0/5                           ea86ac4

  V-025                          WildChat retro BERTScore                 6          roberta 0.927 HIGH / mbert 0.838 MID-HIGH                     d3c678b

  V-026                          ShareGPT+hotpotqa topic coherence        6          LF-COMPETITIVE NPMI + UMass best 5/6 (hotpot/4 NMF outlier)   79bff78

  V-027                          hotpotqa tokenizer ext ablation          10         NEGATIVE (driver-level fix fails)                             bbe1b89

  V-029-a                        hotpotqa cost+latency                    5          Cost PASS 99%/84%, Latency FAIL -3.6%                         59bb20a

  V-029-b                        livedoor cross-doc overlap               27         DISCRIMINATIVE-STRONG ratio 1.31x                             783327b

  V-029-c                        ShareGPT theme baton-pass                10         BATON-PASS-STRONG ratio 1.99x                                 7cebd7b

  V-029-d                        livedoor title BERTScore                 27         TRIAGE-PROXY-RELATIVE delta 0.046                             76e1752

  V-029-f                        CNN/DM ROUGE+BERTScore                   10         SEMANTIC-PASS + LEXICAL relative SUPERIOR                     0bf849d

  V-031                          polbooks+football gamma sweep (retro)    7 values   best gamma dataset-dependent                                  (retro)

  V-032                          hotpotqa embedding (N=5)                 5          marginal delta +0.067 MiniLM direction                        0200f91

  V-032-bis                      hotpotqa embedding (N=30)                30         MPNET-SUPERIOR (direction reversed)                           1cc5c90

  V-033                          hotpotqa multi-seed (5 seed)             5x5        ROBUST-STRONG stdev 0.0                                       43e2539

  V-034                          hotpotqa community method                5x2        fact metric invariant (newman vs cpm)                         0200f91

  V-035                          hotpotqa K=4 plus or minus 1 vs K_free   5x2        fact metric invariant                                         0200f91

  V-036                          hotpotqa K-means baseline                5          K-means SUPERIOR delta +0.067                                 0200f91

  V-037                          hotpotqa MAX_NODES sweep                 5x4        INVARIANT (25/50/100/200)                                     0200f91

  V-024-tri                      TOP_MEMBERS sweep (5-\>20)               2x4        NO-IMPROVEMENT                                                0200f91

  V-024-quad                     SNIPPET sweep (120-\>480)                2x4        PARTIAL-IMPROVEMENT                                           0200f91

  V-040                          Pareto plots (38 evidence)               ---        5 plots, 5 intersections                                      31c5f51

  V-041                          core spec post-process variation         5          redundant overlap + cost reduction                            0200f91

  V-042                          ensemble N=5                             5          ENSEMBLE-EQUAL-OR-MARGINAL                                    94527bb

  V-042-bis                      ensemble N=30 (hotpotqa)                 30         ENSEMBLE-PARTIAL-IMPROVEMENT                                  1cc5c90

  V-042-tri                      ensemble N=100 (hotpotqa)                100        ENSEMBLE-SIGNIFICANT (p=2.7e-05)                              d009367

  V-042-quad                     ensemble livedoor cross-corpus           27         ENSEMBLE-HIGHLY-SIGNIFICANT (p=1.3e-10)                       d009367

  cross-corpus (V-027/037/033)   livedoor                                 9          V-037/033 direction-consistent confirmed                      8d792fe
  -------------------------------------------------------------------------------------------------------------------------------------------------------------

*Table B2. Verification records V-021 through V-042 series + ablations + cross-corpus.*

**Appendix C. Parameter Ablation Full Details**

All 14 parameter ablations with verdict, current value preservation status, and improvement path. Baseline snapshot v1 is preserved unchanged as a freeze decision under bounded ablation budget --- no parameter change reached the IMPROVEMENT-LARGE threshold (\>0.30 delta) under the tested N (5-30). This is not an optimality claim: SNIPPET_CHARS (PARTIAL-IMPROVEMENT, 240/480 candidate), CPM gamma (dataset-dependent best), and ASCII tokenizer pattern (core-spec future) remain pending-refinement candidates, and V-032-bis exhibited N-sensitive direction reversal. See main Section 4.5.

  -------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  **Parameter**             **Current value**                  **Ablation tested**                   **Verdict**                             **Action**
  ------------------------- ---------------------------------- ------------------------------------- --------------------------------------- ------------------------------
  CPM algorithm             CPM-Louvain (MIT)                  leidenalg excluded (GPLv3)            v8.1 confirmed                          keep

  CPM gamma (resolution)    default                            Sweep 0.01-1.0 (V-031 retro)          dataset-dependent best                  keep default

  embedding model           mpnet (multilingual)               vs MiniLM-L6 (V-032/V-032-bis N=30)   MPNET SUPERIOR delta -0.058             keep mpnet

  MeCab tokenizer           fugashi + unidic-lite              vs Janome/Sudachi (literature)        JA standard                             keep MeCab

  ASCII tokenizer pattern   \[a-zA-Z\]+ 3+ chars               \+ \[0-9\]+ (V-027)                   NEGATIVE (digit drop internal)          keep + core-spec future

  random_seed               42                                 5 seeds variance (V-033)              ROBUST-STRONG stdev 0.0                 keep 42

  K cognitive constraint    4 plus or minus 1 (Miller/Cowan)   vs K_free (3,10) (V-035)              fact metric invariant                   keep 4 plus or minus 1

  scale_finder algorithm    LayerForge spec                    vs K-means baseline (V-036)           LF-INFERIOR direction                   Hybrid path 2 (V-042)

  F3/F4 hybrid render       F4 default (ADR-024)               V-003/006/007/024/024-bis             F4 production-viable                    keep F4 default

  TOP_MEMBERS_PER_LAYER     5                                  vs 20 (V-024-tri)                     NO-IMPROVEMENT redundant                keep 5

  SNIPPET_CHARS             120                                vs 480 (V-024-quad)                   PARTIAL-IMPROVEMENT (partial recover)   keep 120 (240/480 candidate)

  MAX_NODES                 50                                 25/100/200 (V-037)                    INVARIANT                               keep 50

  representation_summary    ctfidf top-K                       post-process truncation (V-041)       cost reduction OK, fact invariant       keep

  token_representations     LayerForge spec                    alone vs union (V-041)                redundant overlap with rep_summary      keep

  bridge_nodes selection    prepare_render_data path           decompose.run absence verified        spec consistent                         keep

  Phase 2 thresholds        ADR-019 spec                       V-024-tri/quad subset                 driver-level confirmed                  keep
  -------------------------------------------------------------------------------------------------------------------------------------------------------------------------

*Table C. Parameter ablation full details (16 entries: 14 ablation + 2 articulation correction). No parameter change reached the IMPROVEMENT-LARGE threshold (\>0.30 delta) under tested N (5-30); baseline snapshot v1 is frozen under bounded ablation budget (not an optimality claim; see main Section 4.5).*

**Appendix D. Full Pareto Plot Set (V-040)**

Complete set of 5 Pareto plots from V-040 (commit 31c5f51). Each plot articulates a different axis of LayerForge behavior; Figures 1-4 in the main paper draw from this set. Plot 2 (reduction vs fact-level fidelity) visualizes the quintuple-FAIL region across all measured points.

![Plot 1. Reduction vs theme-level fidelity Pareto frontier (= main paper Figure 3).](media/86c466badf6d99dba93ab791bc1edb0644739b5b.png "Plot 1. Reduction vs theme-level fidelity Pareto frontier (= main paper Figure 3)."){width="5.625in" height="3.9375in"}

*Plot 1. Reduction vs theme-level fidelity Pareto frontier (= main paper Figure 3).*

![Plot 2. Reduction vs fact-level fidelity. All measured points cluster in PRESERVE-FAIL region (\<=0.30 threshold), visualizing the constitutive fact-level FAIL limit (see Section 2 disclaimer: metric-multiple but corpus-dual evidence).](media/bf02bb49d86facc381fb62d8bfe268756e13d278.png "Plot 2. Reduction vs fact-level fidelity. All measured points cluster in PRESERVE-FAIL region (<=0.30 threshold), visualizing the constitutive fact-level FAIL limit (see Section 2 disclaimer: metric-multiple but corpus-dual evidence)."){width="5.625in" height="3.9375in"}

*Plot 2. Reduction vs fact-level fidelity. All measured points cluster in PRESERVE-FAIL region (\<=0.30 threshold), visualizing the constitutive fact-level FAIL limit (see Section 2 disclaimer: metric-multiple but corpus-dual evidence).*

![Plot 3. Theme vs fact two-layer structure (= main paper Figure 1). LayerForge variants in lower-right quadrant (theme PASS / fact FAIL).](media/209cd4677d0bed46686787b46c8ca357c0222c4c.png "Plot 3. Theme vs fact two-layer structure (= main paper Figure 1). LayerForge variants in lower-right quadrant (theme PASS / fact FAIL)."){width="5.625in" height="3.9375in"}

*Plot 3. Theme vs fact two-layer structure (= main paper Figure 1). LayerForge variants in lower-right quadrant (theme PASS / fact FAIL).*

![Plot 4. Reduction landscape across 14 datasets (= main paper Figure 2). Colored by language and tokenization.](media/7a4b2c5bd3b11cae79f73f75ebfbb2176d19d4ec.png "Plot 4. Reduction landscape across 14 datasets (= main paper Figure 2). Colored by language and tokenization."){width="5.625in" height="3.28125in"}

*Plot 4. Reduction landscape across 14 datasets (= main paper Figure 2). Colored by language and tokenization.*

![Plot 5. Per-query input-token cost vs downstream LLM accuracy (= main paper Figure 4; see main Figure 4 caption for full details). Raw data: v029a_cost_latency_results.json.](media/6d30ceaaedb0106f16382c846757a78e6d3873b6.png "Plot 5. Per-query input-token cost vs downstream LLM accuracy (= main paper Figure 4; see main Figure 4 caption for full details). Raw data: v029a_cost_latency_results.json."){width="5.625in" height="3.9375in"}

*Plot 5. Per-query input-token cost vs downstream LLM accuracy (= main paper Figure 4; see main Figure 4 caption for full details). Raw data: v029a_cost_latency_results.json.*

**Appendix E. Future Work --- Full 15-item Roadmap**

Items marked AI-decidable can proceed without architectural triggers. Sovereign-trigger items await architectural and scope decisions.

  ------------------------------------------------------------------------------------------------------------------------
  **Item**   **Axis**         **Scope**                                    **Cost**          **Decision**
  ---------- ---------------- -------------------------------------------- ----------------- -----------------------------
  V-101      Verification     Pattern-probe accuracy formal measurement    mid-high          AI-decidable

  V-102      Verification     Cross-domain generalization (law, medical)   mid               AI-decidable

  V-103      Verification     Direction reversal root cause                mid               AI-decidable

  V-104      Verification     Existing-record probe-perspective reframe    low               AI-decidable (top priority)

  I-101      Implementation   Probe API (layerforge.probe.profile)         mid               AI-decidable

  I-102      Implementation   Routing primitive (pattern -\> algorithm)    mid-high          sovereign (architectural)

  I-103      Implementation   Output interpretation layer                  mid               AI-decidable

  I-104      Implementation   Probe driver isolation from core             mid               sovereign (v8.1 integrity)

  G-101      Integration      Claude Code skill packaging                  low               AI-decidable

  G-102      Integration      LangChain / LlamaIndex plugin                mid               sovereign (footprint)

  G-103      Integration      LLM API wrapper (probe + routing)            mid               AI-decidable

  G-104      Integration      KDF + LayerForge integration                 mid-high          sovereign (two-tool)

  E-101      Effective        Cost / latency improvement measurement       mid               AI-decidable

  E-102      Effective        Accuracy preservation confirmation           mid               AI-decidable

  E-103      Effective        Real-world deployment pilot                  high, long-term   sovereign (deployment)
  ------------------------------------------------------------------------------------------------------------------------

*Table E. Future work 15 items with priority and decision boundary.*

**Items Not Pursued**

G-102 (LangChain plugin): personal-OS scope over-engineering, deferred until consulting trigger. E-103 (real deployment): personal-OS scope is already pilot-equivalent (Claude Code daily operation), separate deployment not required.
