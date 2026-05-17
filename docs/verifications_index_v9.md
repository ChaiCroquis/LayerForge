# LayerForge v9 — Verification Index (Public)

> Public-facing subset of the full verification index. This document is referenced by **LayerForge v9: Phase 2b Verification Update** (paper at `paper/v9/`) as References [11].

## Scope

This index summarizes the **46 verifications and 14 parameter ablations** cited in the v9 paper, with pointers to the raw JSON output files in `verification_results/v9/` and to the paper sections where each verification's outcome is articulated.

## Verification record format (ADR-022 §3)

Each verification follows a pre-register / post-run protocol with immutable Sections 1-5 (claim, dataset, method, pre-commit interpretations) and append-only Sections 6-8 (run record, outcome, impact). The **full per-record narratives** (markdown files of approximately 200-600 lines each, organized as `docs/verifications/YYYY-MM-DD_<topic>.md` in the author's working repository) are maintained in a separate author-maintained repository, currently private during pre-publication review. **Peer reviewers may request read access** from the corresponding author. A persistent Zenodo DOI deposit of the full verification artifact set (records + driver scripts + raw JSON) will be created at camera-ready stage.

This public subset deliberately includes (a) the raw JSON output that lets a third party independently re-verify the numeric claims of the paper, plus (b) a summary table of V-IDs / verdicts. It deliberately omits (a) the driver scripts that produced these JSON files, and (b) the per-record `docs/verifications/*.md` narratives, both of which are in the author-maintained private repository.

## Phase 2a + 2b base (V-001 through V-020)

See paper Appendix B Table B1 for the full row-by-row articulation. Highlights:

- **V-004 / V-005**: WildChat reduction 93%, 3-axis robustness PASS
- **V-007**: F4 hybrid format PASS, cosine 0.939
- **V-013 / V-014**: livedoor (JA) tokenizer mismatch → MeCab fix, delta +83.89 pp
- **V-016**: 14-dataset length regression v7 partial confirm, R²=0.54

JSON files for V-001 through V-020 are part of the prior verification cycle and not included in `verification_results/v9/`; they correspond to **LayerForge v8.1** (already public in the parent repository, see `scripts/` for v8.1 demos).

## Phase 2b fact-level + ensemble (V-021 through V-042-quad)

| V-ID | JSON file in `verification_results/v9/` | Paper section |
|---|---|---|
| V-021 hotpotqa factual recall (substring/tok) | `v021_factual_recall_results.json` | Appendix B Table B2 |
| V-022 livedoor ROUGE-L | `v022_rouge_livedoor_results.json` | Appendix B Table B2 |
| V-023 hotpotqa attribute breakdown | `v023_attribute_breakdown_results.json` | Appendix B Table B2 |
| V-024 hotpotqa F3 downstream LLM | (subagent input/output JSON, not in public subset — see paper §6 LLM-judge bias scope) | Appendix B Table B2 |
| V-024-bis hotpotqa F4-hybrid downstream LLM | (subagent input/output JSON, not in public subset) | Appendix B Table B2 |
| V-025 WildChat retro BERTScore | `v025_bertscore_retro_results.json` | Appendix B Table B2 |
| V-026 ShareGPT+hotpotqa topic coherence | `v026_topic_coherence_results.json` | Appendix B Table B2 (5/6 UMass best, hotpot/4 NMF outlier) |
| V-027 hotpotqa tokenizer ext ablation | `v027_tokenizer_ext_results.json` | Appendix B Table B2; §4.5 |
| V-029-a hotpotqa cost+latency | `v029a_cost_latency_results.json` | **Figure 4 / §4.4** |
| V-029-b livedoor cross-doc overlap | `v029b_cross_doc_overlap_results.json` | Appendix B Table B2 |
| V-029-c ShareGPT theme baton-pass | `v029c_theme_baton_pass_results.json` | Appendix B Table B2 |
| V-029-d livedoor title BERTScore | `v029d_livedoor_title_bertscore_results.json` | Appendix B Table B2 |
| V-029-f CNN/DM ROUGE+BERTScore | `v029f_cnndm_rouge_bertscore_results.json` | Appendix B Table B2 |
| V-032 hotpotqa embedding N=5 | `v032_embedding_compare_results.json` | Appendix B Table B2; §4.5 |
| V-032-bis hotpotqa embedding N=30 (direction reversal) | `v032_bis_n30_results.json` | Appendix B Table B2; §4.5 (motivates careful-strategy Rule 3) |
| V-033 hotpotqa multi-seed | `v033_multi_seed_results.json` | Appendix B Table B2 |
| V-034 / V-035 community method / K=4±1 | `v034_v035_combined_results.json` | Appendix B Table B2; §4.5 |
| V-036 hotpotqa K-means baseline | `v036_baseline_clustering_results.json` | Appendix B Table B2; §4.3 (motivated Path 2 ensemble) |
| V-037 hotpotqa MAX_NODES sweep | `v037_max_nodes_results.json` | Appendix B Table B2; §4.5 |
| V-041 core spec post-process | `v041_core_spec_ablation_results.json` | Appendix B Table B2 |
| **V-042 ensemble N=5** | `v042_ensemble_hybrid_results.json` | **§4.3 Table 1 row 1** |
| **V-042-bis ensemble N=30 (hotpotqa)** | `v042_bis_n30_results.json` | **§4.3 Table 1 row 2** |
| **V-042-tri ensemble N=100 (hotpotqa)** | `v042_tri_n100_stat_results.json` | **§4.3 Table 1 row 3; Abstract p=2.7e-05** |
| **V-042-quad ensemble livedoor cross-corpus** | `v042_quad_livedoor_results.json` | **§4.3 Table 1 row 4; Abstract p=5.1e-08** |

## V-IDs without public JSON (LLM-judged subset, scope-specific bias)

Per paper §6 Limitations, these verifications used Claude Code subagent as LLM-as-judge on Claude-compressed context. Their subagent input / output JSON files are not included in this public subset because their interpretation is bounded by the self-preference bias disclosed in §6. The raw output files exist in the author's private repository and are available to reviewers on request.

- V-024 (F3 refusal downstream)
- V-024-bis (F4-hybrid accuracy downstream)
- V-024-tri (TOP_MEMBERS sweep)
- V-024-quad (SNIPPET sweep)
- V-031 (CPM gamma sweep, retro)

## V-040 Pareto plots and cross-corpus V-IDs

- **V-040**: 5 Pareto plots consolidating 38 evidence points. PNG sources at `paper/v9/figures/v040_plot{1..5}_*_en.png`, referenced by paper Figures 1-4 and Appendix D.
- **cross-corpus (V-027 / V-037 / V-033) on livedoor**: replication results, summarized in paper Appendix B Table B2 last row; raw aggregates folded into the parent V-IDs' JSON output files.

## Self-preference bias disclosure (Anthropic LLM-as-judge guidance)

The v9 paper was drafted with Claude Code assistance, and the peer review loop was conducted by Claude Code subagents (same model family). Per Anthropic's LLM-as-judge guidance, formal acceptance evidence requires cross-check by either (a) a human reviewer, (b) a different LLM family (GPT-4 / Gemini / Mistral), or (c) Anthropic API direct + Haiku 4.5. This index, the public JSON output files, and the structural articulation of bias scope (LLM-judged subset vs metric-only subset, paper §3 + §6) are designed so that an independent cross-checker can verify the metric-only claims without the bias-affected channel.

## Citation

If you cite the verification artifacts in this directory, please cite the paper:

> chai (2026). LayerForge v9: Phase 2b Verification Update. Manuscript at `paper/v9/layerforge_v9_main.pdf`.

The Zenodo DOI for the camera-ready verification artifact deposit will be appended here when issued.
