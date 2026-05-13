# Hallucination benchmark — large corpus + Haiku comparison

## Setup

- **Corpus**: 100 fictional passages (4 themes × 25 entities each)
  - Naming patterns chosen to induce cross-contamination:
    `King-{roman}-Zelgar`, `luminoxide-{roman}`, `Vimnarus-{roman}`, `Codex-{roman}-Estronus`
    where roman ∈ {I..XXV}
- **Questions**: 12 (9 answerable + 3 unanswerable)
  - 3 unanswerable questions target nonexistent variants (`luminoxide-LV`, `Codex-XXVII-Estronus`)
  - 1 unanswerable asks for a property never modeled (king's favorite color)
- **Conditions**: full / layerforge / oracle (same as the small-corpus benchmark)
- **Routing**: LayerForge decomposed 100 passages into 4 clean theme-layers (Q = 0.750, "good"). 9/9 answerable questions routed to the correct theme layer.

## Results

### Sonnet-level subagents

| condition  | correct | refused | wrong | accuracy |
|------------|--------:|--------:|------:|---------:|
| full       |       9 |       3 |     0 |   100.0% |
| layerforge |       9 |       3 |     0 |   100.0% |
| oracle     |       9 |       3 |     0 |   100.0% |

### Haiku 4.5 subagents (`model: "haiku"`)

| condition  | correct | refused | wrong | accuracy |
|------------|--------:|--------:|------:|---------:|
| full       |       9 |       3 |     0 |   100.0% |
| layerforge |       9 |       3 |     0 |   100.0% |
| oracle     |       9 |       3 |     0 |   100.0% |

## Verdict

**Null result, both scales × both model tiers.**

- Baseline (full 100-passage corpus, no filtering) achieves 100% accuracy even on Haiku.
- LayerForge filter and oracle filter produce identical output to baseline.
- No hallucination ever occurred, including on cross-contamination traps (XXV-named entities, nonexistent variants).

## What this means

The hypothesis "LayerForge filtering reduces hallucination" cannot be tested with:
- Modern Claude models (Haiku 4.5 inclusive), AND
- ~10K-token fictional corpora with single-fact lookup questions.

Baseline is already too strong. To produce a measurable effect, one would need either:
- A much larger corpus (probably > 50K tokens with denser cross-contamination)
- A genuinely weak model (e.g. open-weight 7B-class)
- Multi-hop reasoning questions where context filtering changes what reasoning paths are available

ADR-012's "minimum context → reduced hallucination" remains a sensible design principle for older or smaller models, but **no positive evidence** for it has been gathered in the LayerForge project to date. ADR-012 has been amended to reflect this honestly (`docs/06_decision_log.md` ADR-012 補遺 v6).
