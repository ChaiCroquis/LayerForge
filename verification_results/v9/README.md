# LayerForge v9 — Raw Verification Results

This directory contains the raw JSON output of the per-verification driver scripts cited in **LayerForge v9: Phase 2b Verification Update** (paper at `paper/v9/`).

## Purpose

Reviewers and readers of the v9 paper can **independently re-verify** the numeric claims (p-values, mean / std, comp_mean, accuracy, etc.) by decoding these JSON files and recomputing aggregates, without re-running the original experiments.

This satisfies the "verifiable numbers" portion of reproducibility. The driver scripts that produced these JSON files (and the per-record verification narratives in the ADR-022 Section 1-8 format) are maintained in a separate author repository (currently private during pre-publication review) and are available to peer reviewers on request — see `paper/v9/layerforge_v9_main.pdf` References [11]-[15] for access notes. A persistent Zenodo DOI deposit of the full verification artifact set will be created at camera-ready stage.

## File listing (22 files, 1 per cited verification)

| File | V-ID | Dataset | Sample size | Key numeric in paper |
|---|---|---|---|---|
| `v021_factual_recall_results.json` | V-021 | hotpotqa | 10 | PRESERVE-FAIL substring 10%, tok 18% |
| `v022_rouge_livedoor_results.json` | V-022 | livedoor | 9 | RETENTION-FAIL R-L 0.074, delta +0.113 |
| `v023_attribute_breakdown_results.json` | V-023 | hotpotqa | 10 retro | ATTR-TYPE-UNIFORM-FAIL + CONTEXT-DOMINANT |
| `v025_bertscore_retro_results.json` | V-025 | WildChat retro | 6 | roberta 0.927 HIGH / mbert 0.838 MID-HIGH |
| `v026_topic_coherence_results.json` | V-026 | ShareGPT+hotpotqa | 6 | UMass best 5/6 (hotpot/4 NMF outlier) |
| `v027_tokenizer_ext_results.json` | V-027 | hotpotqa tokenizer ablation | 10 | NEGATIVE (driver-level fix fails) |
| `v029a_cost_latency_results.json` | V-029-a | hotpotqa | 5 | Figure 4 source: full=4.4k, F4-hybrid=0.7k tokens/query, accuracy 3/5 vs 0/5 |
| `v029b_cross_doc_overlap_results.json` | V-029-b | livedoor cross-doc | 27 | DISCRIMINATIVE-STRONG ratio 1.31x |
| `v029c_theme_baton_pass_results.json` | V-029-c | ShareGPT theme baton-pass | 10 | BATON-PASS-STRONG ratio 1.99x |
| `v029d_livedoor_title_bertscore_results.json` | V-029-d | livedoor title BERTScore | 27 | TRIAGE-PROXY-RELATIVE delta 0.046 |
| `v029f_cnndm_rouge_bertscore_results.json` | V-029-f | CNN/DM ROUGE+BERTScore | 10 | SEMANTIC-PASS + LEXICAL relative SUPERIOR |
| `v032_embedding_compare_results.json` | V-032 | hotpotqa embedding N=5 | 5 | marginal delta +0.067 MiniLM direction |
| `v032_bis_n30_results.json` | V-032-bis | hotpotqa embedding N=30 | 30 | MPNET-SUPERIOR (direction reversed from V-032) |
| `v033_multi_seed_results.json` | V-033 | hotpotqa multi-seed | 5x5 | ROBUST-STRONG stdev 0.0 |
| `v034_v035_combined_results.json` | V-034 / V-035 | hotpotqa community method / K=4±1 | 5x2 / 5x2 | fact metric invariant |
| `v036_baseline_clustering_results.json` | V-036 | hotpotqa K-means baseline | 5 | K-means SUPERIOR delta +0.067 (motivated Path 2 ensemble) |
| `v037_max_nodes_results.json` | V-037 | hotpotqa MAX_NODES sweep | 5x4 | INVARIANT (25/50/100/200) |
| `v041_core_spec_ablation_results.json` | V-041 | core spec post-process | 5 | redundant overlap + cost reduction |
| `v042_ensemble_hybrid_results.json` | V-042 | hotpotqa N=5 | 5 | ENSEMBLE-EQUAL-OR-MARGINAL; comp_mean LF=174.6, Ens=264.0 (Table 1 row 1) |
| `v042_bis_n30_results.json` | V-042-bis | hotpotqa N=30 | 30 | ENSEMBLE-PARTIAL-IMPROVEMENT; comp_mean LF=188.5, Ens=272.6 (Table 1 row 2) |
| `v042_tri_n100_stat_results.json` | V-042-tri | hotpotqa N=100 | 100 | ENSEMBLE-SIGNIFICANT, ensemble_vs_lf p_t=**2.694e-05** (Abstract + Table 1 row 3) |
| `v042_quad_livedoor_results.json` | V-042-quad | livedoor cross-corpus | 27 | ENSEMBLE-HIGHLY-SIGNIFICANT, ensemble_vs_lf p=**5.130e-08**, ensemble_vs_km p=**1.326e-10** (Abstract + Table 1 row 4) |

## How to verify the paper's headline numbers

```python
import json

# Abstract: "hotpotqa N=100 p=2.7e-05" — ensemble vs LayerForge alone
with open("v042_tri_n100_stat_results.json") as f:
    d = json.load(f)
print(d["stat_tests"]["ensemble_vs_lf"]["p_t"])  # → 2.6941e-05

# Abstract: "livedoor N=27 p=5.1e-08"
with open("v042_quad_livedoor_results.json") as f:
    d = json.load(f)
print(d["stat_tests"]["ensemble_vs_lf"]["p"])    # → 5.1296e-08
print(d["stat_tests"]["ensemble_vs_km"]["p"])    # → 1.3260e-10  (the "see Table 1" pointer)

# Table 1 row 2: V-042-bis comp_mean LF=188.5, Ens=272.6
with open("v042_bis_n30_results.json") as f:
    d = json.load(f)
print(d["summary"]["layerforge"]["comp_mean"])   # → 188.47
print(d["summary"]["ensemble"]["comp_mean"])     # → 272.57
```

## Known gaps (= what's NOT here)

These files are honestly articulated in the paper as `n/a*` in Table 1:

- `v042_tri_n100_stat_results.json` and `v042_quad_livedoor_results.json` **do not contain** `summary.layerforge.comp_mean` / `summary.ensemble.comp_mean` fields — the V-042-tri / V-042-quad evaluator scripts recorded only `tok_recall` aggregates and `stat_tests`, not `comp_chars` per record. The +44.6% / +51.2% output-volume overhead reported in the paper's §4.3 Table 1 caption is derived from V-042 N=5 and V-042-bis N=30 only. Back-filling `comp_mean` for the larger-N runs is filed as future-work item E-101.

## Cross-reference

- Main paper: `paper/v9/layerforge_v9_main.pdf`
- Appendix (full per-record table): `paper/v9/layerforge_v9_appendix.pdf` Appendix B Table B2
- Verification index (subset): `docs/verifications_index_v9.md`

## Versioning

These JSON files correspond to the commit referenced in the paper's References [11]. They are not regenerated as the paper revises; if the paper is updated with new verification runs, this directory will be append-only updated and a new commit hash will be cited.

## License

Same as the parent repository (see `LICENSE` at the repo root). The data in these JSON files is derived from public benchmark datasets (hotpotqa, livedoor news corpus, ShareGPT, etc.) under their respective licenses — see paper Appendix A Table A1 for dataset provenance.
