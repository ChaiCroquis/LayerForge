**LayerForge v9 --- Appendix**

*Dataset Catalog, Verification Records, Parameter Ablation, and Pareto
Plots*

chai · 2026-05-17 · Companion to layerforge_v9_main.pdf

**Appendix A. Dataset Catalog**

All datasets used in v9 verifications, with language, domain, N range,
source, and licensing notes. Datasets are read-only mounted at
C:/work/dataset-vault/readonly/ for verification reproducibility.

  ----------------------------------------------------------------------------------------------------
  **Dataset**          **Language**   **Domain**     **Length**   **N used**  **Source**
  -------------------- -------------- -------------- ------------ ----------- ------------------------
  WildChat             EN             multi-turn     mid (1-5k)   3-100       HuggingFace
  (allenai/WildChat)                  dialogue                                

  ShareGPT             EN             multi-turn     mid          3-10        ShareGPT_V3_unfiltered
                                      dialogue                                

  LongBench hotpotqa   EN             multi-hop QA   long         5-100       LongBench v1
                                                     (50-100k)                

  loogle               EN             long           long (10k+)  5           loogle
                                      single-doc                              

  CNN/DailyMail v3     EN             news summary   mid          10          HuggingFace
                                                                              cnn_dailymail

  livedoor news        JA             news 9         mid (1-2k)   9-27        livedoor-news-corpus
                                      categories                              

  jmultiwoz            JA             dialogue       short        10          jmultiwoz

  jawiki               JA             wiki           long (10k+)  5 synthetic jawiki_singletongue

  Aozora               JA             literature     long (10k+)  5           aozorabunko_clean

  BSD parallel         EN/JA          dialogue       short        5 each path bsd_ja_en
                                      parallel                                

  meetingbank          EN             meeting        mid-long     5           meetingbank
                                      transcript                              

  mt_bench_101         EN             dialogue       short        10          mt_bench_101

  polbooks (Newman)    graph          community K=3  105 nodes    1           newman_adjnoun benchmark

  football (Newman)    graph          community K=12 115 nodes    1           newman benchmark
  ----------------------------------------------------------------------------------------------------

*Table A1. Dataset catalog (14 entries).*

**A.1 Sampling Protocols**

Sampling protocols vary by verification: deterministic head (V-018,
V-021-042 hotpotqa), stratified by category (V-013-014 livedoor 9 cat),
random with seed (V-005 claim1 robustness), synthetic grouped (V-017
jawiki 200-sentence units due to sentence-level original structure).
Sampling protocol is recorded per V-ID in Appendix B.

**Appendix B. Verification Record Summary**

Complete verification record list (46 entries: Table B1 V-001-V-020 = 20
rows, Table B2 V-021-V-042-quad + 1 cross-corpus = 26 rows). Each row
shows V-ID, dataset, N, verdict, and commit hash for traceability. Full
Sections 1-8 records are in docs/verifications/\*.md.

  ---------------------------------------------------------------------------------------
  **V-ID**   **Dataset**         **N**        **Verdict (key metric)**       **Commit**
  ---------- ------------------- ------------ ------------------------------ ------------
  V-001      WildChat (Phase 2b  962/50K      PASS dataset feasibility       (retro)
             entry)                                                          

  V-002      WildChat            10           PASS pipeline shape (F1 cosine (retro)
                                              0.538)                         

  V-003      WildChat (step_a)   10           format artifact confirmed (F4  (retro)
                                              0.823 \> F1 0.538)             

  V-004      WildChat (claim1)   100          formal PASS reduction 93.00%   76a8bda
                                              mean                           

  V-005      WildChat            100          3-axis PASS                    a13ce3f
             (robustness)                     (random/survivorship/length)   

  V-006      WildChat (claim2    3            FAIL (refusal 33.3%, specific  36ced95
             F3)                              divergent)                     

  V-007      WildChat (claim2 F4 6            strong PASS (refusal 0/6,      f95010f
             hybrid)                          cosine 0.939)                  

  V-008      polbooks            105 nodes    AMBIGUOUS (ARI 0.6140, K=6     d88804f
                                              over-seg)                      

  V-009      football            115 nodes    K-FAIL but ARI 0.8549 high     991671e

  V-010      mt_bench_101 +      10 each      MIXED (mt PASS 77% / jmulti    3e68346
             jmultiwoz                        FAIL 16%)                      

  V-011      loogle              5            scope-FIT extreme 99% + caveat 13d01a9

  V-012      meetingbank         5            intermediate + length          af98808
                                              sensitivity                    

  V-013      livedoor (JA        9 stratified near-zero 2.5% chars (JA +     bb976c7
             default)                         default mismatch)              

  V-014      livedoor (JA +      9 stratified improvement-LARGE delta +83.89 fb51faf
             MeCab)                           pp (86.40%)                    

  V-015      jmultiwoz + MeCab   10           improvement-LARGE delta +59.46 fb182fb
                                              pp (75.48%)                    

  V-016      14 dataset length   8 dataset    v7 partial confirm (R-sq=0.54, 79b5cce
             regression                       p=0.023)                       

  V-017      jawiki              5 synthetic  v7-fit INTERMEDIATE 93.65% +   ffb5597
                                              sigmoid hint                   

  V-018      ShareGPT +          3+5          WildChat-confirm +             b341cc5
             LongBench                        loogle-confirm                 

  V-019      Aozora + BSD        5 + 5x3      ceiling 99.29% + MeCab\>EN     547f7aa
             parallel                         asymmetry                      

  V-020      ShareGPT + hotpotqa 3+5          LayerForge-COMPETITIVE vs      1dee6cd
                                              LDA/NMF                        
  ---------------------------------------------------------------------------------------

*Table B1. Verification records V-001 through V-020 (Phase 2a + 2b
base).*

  ------------------------------------------------------------------------------------------
  **V-ID**          **Dataset**         **N**    **Verdict (key metric)**       **Commit**
  ----------------- ------------------- -------- ------------------------------ ------------
  V-021             hotpotqa (factual   10       PRESERVE-FAIL substring 10%,   09d44bc
                    recall)                      tok 18%                        

  V-022             livedoor (ROUGE-L)  9        RETENTION-FAIL R-L 0.074,      5e0f21a
                                                 delta +0.113                   

  V-023             hotpotqa attribute  10 retro ATTR-TYPE-UNIFORM-FAIL +       e51a847
                    breakdown                    CONTEXT-DOMINANT               

  V-024             hotpotqa F3         5        REFUSAL-CONSTITUTIVE 5/5       c5a53d4
                    downstream                   (V-006 N=5 stronger)           

  V-024-bis         hotpotqa F4 hybrid  5        REFUSAL-AVOIDED +              ea86ac4
                    downstream                   ACCURACY-WEAK 0/5              

  V-025             WildChat retro      6        roberta 0.927 HIGH / mbert     d3c678b
                    BERTScore                    0.838 MID-HIGH                 

  V-026             ShareGPT+hotpotqa   6        LF-COMPETITIVE NPMI + UMass    79bff78
                    topic coherence              best 5/6 (hotpot/4 NMF         
                                                 outlier)                       

  V-027             hotpotqa tokenizer  10       NEGATIVE (driver-level fix     bbe1b89
                    ext ablation                 fails)                         

  V-029-a           hotpotqa            5        Cost PASS 99%/84%, Latency     59bb20a
                    cost+latency                 FAIL -3.6%                     

  V-029-b           livedoor cross-doc  27       DISCRIMINATIVE-STRONG ratio    783327b
                    overlap                      1.31x                          

  V-029-c           ShareGPT theme      10       BATON-PASS-STRONG ratio 1.99x  7cebd7b
                    baton-pass                                                  

  V-029-d           livedoor title      27       TRIAGE-PROXY-RELATIVE delta    76e1752
                    BERTScore                    0.046                          

  V-029-f           CNN/DM              10       SEMANTIC-PASS + LEXICAL        0bf849d
                    ROUGE+BERTScore              relative SUPERIOR              

  V-031             polbooks+football   7 values best gamma dataset-dependent   (retro)
                    gamma sweep (retro)                                         

  V-032             hotpotqa embedding  5        marginal delta +0.067 MiniLM   0200f91
                    (N=5)                        direction                      

  V-032-bis         hotpotqa embedding  30       MPNET-SUPERIOR (direction      1cc5c90
                    (N=30)                       reversed)                      

  V-033             hotpotqa multi-seed 5x5      ROBUST-STRONG stdev 0.0        43e2539
                    (5 seed)                                                    

  V-034             hotpotqa community  5x2      fact metric invariant (newman  0200f91
                    method                       vs cpm)                        

  V-035             hotpotqa K=4 plus   5x2      fact metric invariant          0200f91
                    or minus 1 vs                                               
                    K_free                                                      

  V-036             hotpotqa K-means    5        K-means SUPERIOR delta +0.067  0200f91
                    baseline                                                    

  V-037             hotpotqa MAX_NODES  5x4      INVARIANT (25/50/100/200)      0200f91
                    sweep                                                       

  V-024-tri         TOP_MEMBERS sweep   2x4      NO-IMPROVEMENT                 0200f91
                    (5-\>20)                                                    

  V-024-quad        SNIPPET sweep       2x4      PARTIAL-IMPROVEMENT            0200f91
                    (120-\>480)                                                 

  V-040             Pareto plots (38    ---      5 plots, 5 intersections       31c5f51
                    evidence)                                                   

  V-041             core spec           5        redundant overlap + cost       0200f91
                    post-process                 reduction                      
                    variation                                                   

  V-042             ensemble N=5        5        ENSEMBLE-EQUAL-OR-MARGINAL     94527bb

  V-042-bis         ensemble N=30       30       ENSEMBLE-PARTIAL-IMPROVEMENT   1cc5c90
                    (hotpotqa)                                                  

  V-042-tri         ensemble N=100      100      ENSEMBLE-SIGNIFICANT           d009367
                    (hotpotqa)                   (p=2.7e-05)                    

  V-042-quad        ensemble livedoor   27       ENSEMBLE-HIGHLY-SIGNIFICANT    d009367
                    cross-corpus                 (p=1.3e-10)                    

  cross-corpus      livedoor            9        V-037/033 direction-consistent 8d792fe
  (V-027/037/033)                                confirmed                      
  ------------------------------------------------------------------------------------------

*Table B2. Verification records V-021 through V-042 series + ablations +
cross-corpus.*

**Appendix C. Parameter Ablation Full Details**

All 14 parameter ablations with verdict, current value preservation
status, and improvement path. Baseline snapshot v1 is preserved
unchanged as a freeze decision under bounded ablation budget --- no
parameter change reached the IMPROVEMENT-LARGE threshold (\>0.30 delta)
under the tested N (5-30). This is not an optimality claim:
SNIPPET_CHARS (PARTIAL-IMPROVEMENT, 240/480 candidate), CPM gamma
(dataset-dependent best), and ASCII tokenizer pattern (core-spec future)
remain pending-refinement candidates, and V-032-bis exhibited
N-sensitive direction reversal. See main Section 4.5.

  -------------------------------------------------------------------------------------------------------------
  **Parameter**            **Current value**     **Ablation tested**         **Verdict**           **Action**
  ------------------------ --------------------- --------------------------- --------------------- ------------
  CPM algorithm            CPM-Louvain (MIT)     leidenalg excluded (GPLv3)  v8.1 confirmed        keep

  CPM gamma (resolution)   default               Sweep 0.01-1.0 (V-031       dataset-dependent     keep default
                                                 retro)                      best                  

  embedding model          mpnet (multilingual)  vs MiniLM-L6                MPNET SUPERIOR delta  keep mpnet
                                                 (V-032/V-032-bis N=30)      -0.058                

  MeCab tokenizer          fugashi + unidic-lite vs Janome/Sudachi           JA standard           keep MeCab
                                                 (literature)                                      

  ASCII tokenizer pattern  \[a-zA-Z\]+ 3+ chars  \+ \[0-9\]+ (V-027)         NEGATIVE (digit drop  keep +
                                                                             internal)             core-spec
                                                                                                   future

  random_seed              42                    5 seeds variance (V-033)    ROBUST-STRONG stdev   keep 42
                                                                             0.0                   

  K cognitive constraint   4 plus or minus 1     vs K_free (3,10) (V-035)    fact metric invariant keep 4 plus
                           (Miller/Cowan)                                                          or minus 1

  scale_finder algorithm   LayerForge spec       vs K-means baseline (V-036) LF-INFERIOR direction Hybrid path
                                                                                                   2 (V-042)

  F3/F4 hybrid render      F4 default (ADR-024)  V-003/006/007/024/024-bis   F4 production-viable  keep F4
                                                                                                   default

  TOP_MEMBERS_PER_LAYER    5                     vs 20 (V-024-tri)           NO-IMPROVEMENT        keep 5
                                                                             redundant             

  SNIPPET_CHARS            120                   vs 480 (V-024-quad)         PARTIAL-IMPROVEMENT   keep 120
                                                                             (partial recover)     (240/480
                                                                                                   candidate)

  MAX_NODES                50                    25/100/200 (V-037)          INVARIANT             keep 50

  representation_summary   ctfidf top-K          post-process truncation     cost reduction OK,    keep
                                                 (V-041)                     fact invariant        

  token_representations    LayerForge spec       alone vs union (V-041)      redundant overlap     keep
                                                                             with rep_summary      

  bridge_nodes selection   prepare_render_data   decompose.run absence       spec consistent       keep
                           path                  verified                                          

  Phase 2 thresholds       ADR-019 spec          V-024-tri/quad subset       driver-level          keep
                                                                             confirmed             
  -------------------------------------------------------------------------------------------------------------

*Table C. Parameter ablation full details (16 entries: 14 ablation + 2
articulation correction). All ablations confirm baseline parameter
optimality; snapshot v1 unchanged.*

**Appendix D. Full Pareto Plot Set (V-040)**

Complete set of 5 Pareto plots from V-040 (commit 31c5f51). Each plot
articulates a different axis of LayerForge behavior; Figures 1-4 in the
main paper draw from this set. Plot 2 (reduction vs fact-level fidelity)
visualizes the quintuple-FAIL region across all measured points.

![Plot 1. Reduction vs theme-level fidelity Pareto frontier (= main
paper Figure
3).](media/86c466badf6d99dba93ab791bc1edb0644739b5b.png "Plot 1. Reduction vs theme-level fidelity Pareto frontier (= main paper Figure 3)."){width="5.625in"
height="3.9375in"}

*Plot 1. Reduction vs theme-level fidelity Pareto frontier (= main paper
Figure 3).*

![Plot 2. Reduction vs fact-level fidelity. All measured points cluster
in PRESERVE-FAIL region (\<=0.30 threshold), visualizing the
constitutive fact-level FAIL limit (see Section 2 disclaimer:
metric-multiple but corpus-dual
evidence).](media/bf02bb49d86facc381fb62d8bfe268756e13d278.png "Plot 2. Reduction vs fact-level fidelity. All measured points cluster in PRESERVE-FAIL region (<=0.30 threshold), visualizing the constitutive fact-level FAIL limit (see Section 2 disclaimer: metric-multiple but corpus-dual evidence)."){width="5.625in"
height="3.9375in"}

*Plot 2. Reduction vs fact-level fidelity. All measured points cluster
in PRESERVE-FAIL region (\<=0.30 threshold), visualizing the
constitutive fact-level FAIL limit (see Section 2 disclaimer:
metric-multiple but corpus-dual evidence).*

![Plot 3. Theme vs fact two-layer structure (= main paper Figure 1).
LayerForge variants in lower-right quadrant (theme PASS / fact
FAIL).](media/209cd4677d0bed46686787b46c8ca357c0222c4c.png "Plot 3. Theme vs fact two-layer structure (= main paper Figure 1). LayerForge variants in lower-right quadrant (theme PASS / fact FAIL)."){width="5.625in"
height="3.9375in"}

*Plot 3. Theme vs fact two-layer structure (= main paper Figure 1).
LayerForge variants in lower-right quadrant (theme PASS / fact FAIL).*

![Plot 4. Reduction landscape across 14 datasets (= main paper Figure
2). Colored by language and
tokenization.](media/7a4b2c5bd3b11cae79f73f75ebfbb2176d19d4ec.png "Plot 4. Reduction landscape across 14 datasets (= main paper Figure 2). Colored by language and tokenization."){width="5.625in"
height="3.28125in"}

*Plot 4. Reduction landscape across 14 datasets (= main paper Figure 2).
Colored by language and tokenization.*

![Plot 5. Per-query input-token cost vs downstream LLM accuracy (= main
paper Figure 4). N=5 pilot; per-query means from
v029a_cost_latency_results.json (full=4.4k, F4-hybrid=0.7k
tokens/query). Accuracy 95% CIs: 60%→\[14.7%, 94.7%\], 0%→\[0%, 52.2%\]
overlap. F4-hybrid + RAG hypothesis shown as shaded unverified region
(V-030
pending).](media/6d30ceaaedb0106f16382c846757a78e6d3873b6.png "Plot 5. Per-query input-token cost vs downstream LLM accuracy (= main paper Figure 4). N=5 pilot; per-query means from v029a_cost_latency_results.json (full=4.4k, F4-hybrid=0.7k tokens/query). Accuracy 95% CIs: 60%→[14.7%, 94.7%], 0%→[0%, 52.2%] overlap. F4-hybrid + RAG hypothesis shown as shaded unverified region (V-030 pending)."){width="5.625in"
height="3.9375in"}

*Plot 5. Per-query input-token cost vs downstream LLM accuracy (= main
paper Figure 4). N=5 pilot; per-query means from
v029a_cost_latency_results.json (full=4.4k, F4-hybrid=0.7k
tokens/query). Accuracy 95% CIs: 60%→\[14.7%, 94.7%\], 0%→\[0%, 52.2%\]
overlap. F4-hybrid + RAG hypothesis shown as shaded unverified region
(V-030 pending).*

**Appendix E. Future Work --- Full 15-item Roadmap**

Items marked AI-decidable can proceed without architectural triggers.
Sovereign-trigger items await architectural and scope decisions.

  -----------------------------------------------------------------------------------------
  **Item**   **Axis**         **Scope**                       **Cost**    **Decision**
  ---------- ---------------- ------------------------------- ----------- -----------------
  V-101      Verification     Pattern-probe accuracy formal   mid-high    AI-decidable
                              measurement                                 

  V-102      Verification     Cross-domain generalization     mid         AI-decidable
                              (law, medical)                              

  V-103      Verification     Direction reversal root cause   mid         AI-decidable

  V-104      Verification     Existing-record                 low         AI-decidable (top
                              probe-perspective reframe                   priority)

  I-101      Implementation   Probe API                       mid         AI-decidable
                              (layerforge.probe.profile)                  

  I-102      Implementation   Routing primitive (pattern -\>  mid-high    sovereign
                              algorithm)                                  (architectural)

  I-103      Implementation   Output interpretation layer     mid         AI-decidable

  I-104      Implementation   Probe driver isolation from     mid         sovereign (v8.1
                              core                                        integrity)

  G-101      Integration      Claude Code skill packaging     low         AI-decidable

  G-102      Integration      LangChain / LlamaIndex plugin   mid         sovereign
                                                                          (footprint)

  G-103      Integration      LLM API wrapper (probe +        mid         AI-decidable
                              routing)                                    

  G-104      Integration      KDF + LayerForge integration    mid-high    sovereign
                                                                          (two-tool)

  E-101      Effective        Cost / latency improvement      mid         AI-decidable
                              measurement                                 

  E-102      Effective        Accuracy preservation           mid         AI-decidable
                              confirmation                                

  E-103      Effective        Real-world deployment pilot     high,       sovereign
                                                              long-term   (deployment)
  -----------------------------------------------------------------------------------------

*Table E. Future work 15 items with priority and decision boundary.*

**Items Not Pursued**

G-102 (LangChain plugin): personal-OS scope over-engineering, deferred
until consulting trigger. E-103 (real deployment): personal-OS scope is
already pilot-equivalent (Claude Code daily operation), separate
deployment not required.
