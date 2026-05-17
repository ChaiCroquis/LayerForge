# LayerForge

> 4±1 layer decomposition with deterministic core and inference boundaries.
> A Claude Code skill + Python CLI for HERCULES + SCA + Newman modularity based
> structural layering of text passages.

## Status

Phase 2 (skill + CLI). 147 passing tests across `tests/axioms`, `tests/cli`,
`tests/integration`. Documented design and empirical findings live under
[`docs/`](docs/).

**Paper status**:
- **v8.1 published** (2025): core algorithm + design (this repository's
  Python package, unchanged in v9 — algorithm-level releases are independent
  of paper revisions)
- **v9 (2026-05): Phase 2b Verification Update** — two-layer fidelity
  structure (theme-level PASS / fact-level FAIL) + Hybrid ensemble path
  (LayerForge + K-means, hotpotqa N=100 p=2.7e-05, livedoor N=27 p=5.1e-08)
  + explicit extrapolation boundaries. See [`paper/v9/`](paper/v9/) for the
  full manuscript and review history. Core algorithm is unchanged from
  v8.1; v9 adds verification depth and an evidence-grounded improvement
  direction without modifying the v8.1 core spec.

## Install

```bash
pip install -e .
# Optional extras:
pip install -e .[embeddings]   # sentence-transformers backend
pip install -e .[sca]          # UMAP + HDBSCAN (full SCA distillation)
pip install -e .[dev]          # pytest + ruff + hypothesis
```

Python ≥ 3.10 required.

## Three operating modes

| Mode | CLI | Purpose |
|---|---|---|
| **A. decompose** | `layerforge-decompose` | Structural layering of N nodes into K layers (deterministic core) |
| **B. decide** | `layerforge-decide` | Cognitive aid with persistence state machine (`open` / `close` / `settle` / `unsettle`) |
| **C. compress** | `layerforge-compress` | AI verbose output compression with subset guarantee |

Hook validation: `layerforge-validate-output` (designed for Claude Code
`PostToolUse:Bash` integration).

## Skill form (Claude Code integration)

The primary integration path (per **ADR-014** in
[`docs/06_decision_log.md`](docs/06_decision_log.md)) is a Claude Code skill:

- Skill manifest: [`.claude/skills/layerforge/SKILL.md`](.claude/skills/layerforge/SKILL.md)
- Project-local hook: [`.claude/settings.json`](.claude/settings.json)

In skill form the deterministic core is invoked by Claude Code; no API key
is required (per ADR-014, `AnthropicLLMClient` is retained as a future option
but the skill path doesn't exercise it).

## Paper (v9 — Phase 2b Verification Update)

The v9 paper (PDF at [`paper/v9/layerforge_v9_main.pdf`](paper/v9/layerforge_v9_main.pdf)
+ companion appendix) reports the following over the v8.1 baseline:

1. **Two-layer fidelity structure** (theme-level semantic PASS / fact-level
   lexical FAIL) corroborated by multiple metric families on two datasets
   (hotpotqa EN, livedoor JA)
2. **Hybrid ensemble path** (LayerForge + K-means) with cross-corpus
   statistical significance — ensemble vs LayerForge alone:
   hotpotqa N=100 p=2.7e-05, livedoor N=27 p=5.1e-08 (paired t-test)
3. **Baseline parameter values frozen under bounded ablation budget** — 14
   ablations under tested N (5-30) produced no parameter change above the
   IMPROVEMENT-LARGE threshold; this is a freeze decision, not an optimality
   claim
4. **Explicit extrapolation boundaries** per pattern coverage

**The v8.1 core algorithm is unchanged in v9.** v9 adds verification depth
(46 verifications, 14 parameter ablations across 14 datasets) and an
evidence-grounded improvement direction (Hybrid ensemble) without modifying
the v8.1 spec.

### Verification artifact availability

| Layer | Public | Private (reviewer access on request) |
|---|---|---|
| Paper PDF + LaTeX-equivalent docx + figures | ✓ [`paper/v9/`](paper/v9/) | — |
| Peer review history (3-round Reviewer/Author Agent loop, Accept) | ✓ [`paper/v9/round{1,2,3}/`](paper/v9/) | — |
| Raw JSON output (22 files, sufficient for numeric re-verification) | ✓ [`verification_results/v9/`](verification_results/v9/) | — |
| Public verification index | ✓ [`docs/verifications_index_v9.md`](docs/verifications_index_v9.md) | — |
| Driver scripts that produced the raw JSON | — | author-maintained `LayerForge-dev` (private during pre-publication review) |
| Per-record verification narratives (ADR-022 §1-8 markdown, ~200-600 lines each) | — | author-maintained `LayerForge-dev` |

A persistent **Zenodo DOI deposit** of the full verification artifact set
(records + driver scripts + raw JSON) will be created at camera-ready
stage. Peer reviewers may request read access to the author-maintained
private repository from the corresponding author.

### Self-preference bias disclosure

The v9 paper was drafted with Claude Code assistance, and the peer review
loop was conducted by Claude Code subagents (same model family). Per
Anthropic's LLM-as-judge guidance, formal acceptance evidence requires
cross-check by either (a) a human reviewer, (b) a different LLM family
(GPT-4 / Gemini / Mistral), or (c) Anthropic API direct + Haiku 4.5. The
paper structurally separates the LLM-judged subset (V-024 / V-024-bis /
V-025 — bias-affected) from the metric-only subset (V-042 family — paired
t-test on tok_recall, bias-independent) — see paper §3 and §6 for the
articulated scope.

## Documentation index

| File | Content |
|---|---|
| [`docs/01_overview.md`](docs/01_overview.md) | Project overview, motivation, scope (v8.1 design; v9 paper does not change this) |
| [`docs/02_axiom_sources.md`](docs/02_axiom_sources.md) | Source papers and how each formula is grounded |
| [`docs/03_extracted_formulas.md`](docs/03_extracted_formulas.md) | Algorithmic specifications (F1–F4) |
| [`docs/04_test_cases.md`](docs/04_test_cases.md) | Axiom-level test cases (T-series) |
| [`docs/05b_skill_design.md`](docs/05b_skill_design.md) | Skill-form integration design |
| [`docs/06_decision_log.md`](docs/06_decision_log.md) | ADR-001 through ADR-017 |
| [`docs/07_authoring_log.md`](docs/07_authoring_log.md) | Authoring-time meta-notes |
| [`docs/08_empirical_findings.md`](docs/08_empirical_findings.md) | Reproducible measurements (K sweep / N×K heatmap / Pareto / 3-axis separation) |
| [`docs/REFERENCES.md`](docs/REFERENCES.md) | Primary literature citations (URL form, no PDFs) |
| [`docs/verifications_index_v9.md`](docs/verifications_index_v9.md) | **v9 verification index (public subset)** — V-001 through V-042-quad, with per-V-ID pointers to raw JSON output |
| [`paper/v9/layerforge_v9_main.pdf`](paper/v9/layerforge_v9_main.pdf) | **v9 main paper** (Phase 2b Verification Update) |
| [`paper/v9/layerforge_v9_appendix.pdf`](paper/v9/layerforge_v9_appendix.pdf) | **v9 appendix** — dataset catalog, per-record verdicts, parameter ablation full details, Pareto plots |
| [`paper/v9/round{1,2,3}/`](paper/v9/) | v9 paper review history (3-round Reviewer/Author loop, Accept) |
| [`verification_results/v9/`](verification_results/v9/) | **22 raw JSON output files** for v9 paper's numeric claims (p-values, comp_mean, accuracy) — sufficient for third-party independent re-verification |

## Key empirical results

- **Q peak K is N-dependent** (bouncy across sample size) — N×K matrix over
  98 cells reproduces Good et al. (2010) Q degeneracy on the N axis.
- **Above-limit fraction** (Fortunato-Barthélemy resolution-limit ratio) is
  monotone-stable across K and N; LayerForge uses it as an auxiliary
  K-selection metric.
- **K=10 self-routing 100%** across 4 corpora × 2 embedders → AI-input
  compression sweet spot, ~10% per-layer compression with no routing loss.
- **3-axis separation** [A LayerForge core / B LLM behavior / C combined
  workflow] keeps null results properly attributed (LayerForge core does not
  invoke an LLM internally).

See [`docs/08_empirical_findings.md`](docs/08_empirical_findings.md) §6 for
full details.

## Reproducing the K sweep

```bash
# Required: a directory of markdown files for the cross-domain corpus
export LAYERFORGE_KDF_DOCS=/path/to/your/corpus
python -X utf8 scripts/k_sweep/correlation_data.py
python -X utf8 scripts/k_sweep/heatmap_N_x_K.py
python -X utf8 scripts/k_sweep/pareto_plot.py
```

Output PNGs / CSVs land under `scripts/k_sweep/{plots,*.csv}`.

## Test

```bash
pytest -x
```

## Citation

For the v9 paper (Phase 2b Verification Update):

> chai (2026). LayerForge v9: Phase 2b Verification Update — Two-Layer
> Fidelity Structure and Hybrid Ensemble Path. Manuscript at
> [`paper/v9/layerforge_v9_main.pdf`](paper/v9/layerforge_v9_main.pdf).
> Zenodo DOI deposit pending for camera-ready.

For the v8.1 core (algorithm + design) and earlier work, see the prior
commits referenced as "Initial public release: LayerForge v8.1".

## License

MIT — see [`LICENSE`](LICENSE).

## References

Primary literature (Eichin et al. 2024 / Newman 2006 / Fortunato &
Barthélemy 2007 / Cowan 2010 / Good et al. 2010 / Traag et al. 2011 / etc.)
listed in [`docs/REFERENCES.md`](docs/REFERENCES.md). Reference
implementations consulted: `mainlp/semantic_components` (MIT) and
`bandeerun/pyhercules` (MIT).
