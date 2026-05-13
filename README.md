# LayerForge

> 4±1 layer decomposition with deterministic core and inference boundaries.
> A Claude Code skill + Python CLI for HERCULES + SCA + Newman modularity based
> structural layering of text passages.

## Status

Phase 2 (skill + CLI). 147 passing tests across `tests/axioms`, `tests/cli`,
`tests/integration`. Documented design and empirical findings live under
[`docs/`](docs/).

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

## Documentation index

| File | Content |
|---|---|
| [`docs/01_overview.md`](docs/01_overview.md) | Project overview, motivation, scope |
| [`docs/02_axiom_sources.md`](docs/02_axiom_sources.md) | Source papers and how each formula is grounded |
| [`docs/03_extracted_formulas.md`](docs/03_extracted_formulas.md) | Algorithmic specifications (F1–F4) |
| [`docs/04_test_cases.md`](docs/04_test_cases.md) | Axiom-level test cases (T-series) |
| [`docs/05b_skill_design.md`](docs/05b_skill_design.md) | Skill-form integration design |
| [`docs/06_decision_log.md`](docs/06_decision_log.md) | ADR-001 through ADR-017 |
| [`docs/07_authoring_log.md`](docs/07_authoring_log.md) | Authoring-time meta-notes |
| [`docs/08_empirical_findings.md`](docs/08_empirical_findings.md) | Reproducible measurements (K sweep / N×K heatmap / Pareto / 3-axis separation) |
| [`docs/REFERENCES.md`](docs/REFERENCES.md) | Primary literature citations (URL form, no PDFs) |

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

## License

MIT — see [`LICENSE`](LICENSE).

## References

Primary literature (Eichin et al. 2024 / Newman 2006 / Fortunato &
Barthélemy 2007 / Cowan 2010 / Good et al. 2010 / Traag et al. 2011 / etc.)
listed in [`docs/REFERENCES.md`](docs/REFERENCES.md). Reference
implementations consulted: `mainlp/semantic_components` (MIT) and
`bandeerun/pyhercules` (MIT).
