---
name: layerforge
description: Decompose natural-language input into 4±1 hierarchical layers via deterministic core. Use when the user asks to "layerforge", "整理して" with LayerForge mention, or invokes /layerforge. For decision organization, use the decide mode.
allowed-tools: Read, Write, Bash
---

# LayerForge Skill

## Purpose
Decompose user input into 4±1 hierarchical layers using a deterministic Python core. Claude (this skill) handles the language boundaries (parsing input into nodes, rendering structured results into natural language); the deterministic core handles clustering, scale search, distillation, and modularity scoring.

## When to use
- The user mentions LayerForge, asks to decompose/organize text into layers, or invokes a slash command like `/layerforge`.
- The user asks to enumerate "what to decide now" for a task — use Mode B (decide).
- Skip for short or already-structured input (single sentence, bullet list under 5 items).

## Constraints
- Use ONLY information present in the user's input or the CLI output. Do not invent, extrapolate, or speculate.
- Quote node texts verbatim where they appear in the rendered output.
- Preserve numerical values from the CLI exactly. If a value is missing, write "data does not specify".
- Do NOT adopt any persona, voice, or rhetorical style. State facts directly.
- Number of nodes: 5 to 50 inclusive. Minimum node length: 10 characters.
- Nodes must be semantically independent and together cover the entire input.

## Workflow — Mode A: Natural Language Decomposition

### Step 1 — Node extraction
Read the input text. Identify semantically independent nodes (1-3 sentences each, no overlap, full coverage).

Write to a temp file (use the Bash tool with `mktemp` or write to `./tmp/layerforge_nodes_<short-id>.json`). Schema:

```json
{
  "nodes": [
    {"id": "n1", "text": "..."},
    {"id": "n2", "text": "..."}
  ],
  "options": {
    "embedding_backend": "hash",
    "random_seed": 42
  }
}
```

### Step 2 — Invoke deterministic core
```bash
python -m layerforge.cli.decompose <nodes.json> --pretty > <result.json>
```

The CLI handles: embedding → similarity → 4±1 scale search → HERCULES hierarchical clustering → Newman modularity check → SCA distillation per layer.

### Step 3 — Render
Read `result.json`. If `status == "error"`, jump to Step 4.

For each layer in `result.layers`:

```
## L{layer.id}: {layer.representation_summary}

**Members** ({len(layer.member_node_ids)}):
- {original node.text from input, quoted verbatim}
- ...

**Top tokens**: {layer.token_representations[0] joined by ", "}
**Purity**: {layer.purity:.2f}
{if layer.indivisible: "**Status**: indivisible (further split rejected by Newman β₁ ≤ 0)"}
```

After all layers:

```
## Inter-layer relations
{for each result.inter_layer_relations: "L{from} → L{to} ({type}, strength={strength:.3f})"}

## Quality
- Modularity Q: {result.quality_metrics.modularity:.3f} ({quality_class})
- Layer count: {result.quality_metrics.layer_count} (within 4±1: {is_within_4_plus_minus_1})
- Scale coefficient θ: {result.quality_metrics.scale_coefficient:.3f}
```

### Step 4 — On failure
If `result.status == "error"`:
- `NoValidScaleError`: report "4±1 に収まる構造が見つかりませんでした。入力範囲を絞るか、上位概念から再分解してください。"
- `SeparationQualityError`: report "modularity Q = {modularity} が分離品質基準を下回ります。入力ノード間の関係性が弱い可能性があります。"
- other: report `error_type` and `message` verbatim
DO NOT attempt to fill in missing layers.

---

## Workflow — Mode B: Decision Decomposition (Phase 2b)

### Step 1 — Decision enumeration
Read the user's task. Enumerate every decision needed to complete it (yes/no or choice points; both obvious and subtle). Output to JSON:

```json
{
  "nodes": [
    {"id": "d1", "text": "<decision phrased as a question or choice>"},
    {"id": "d2", "text": "..."}
  ],
  "options": {"random_seed": 42}
}
```

Note: Mode B uses `decide`, a thin wrapper around `decompose` that adds `status: "open"|"defer"` per layer based on the deterministic open-layer rule.

### Step 2 — Invoke core
```bash
python -m layerforge.cli.decide <decisions.json> --pretty > <layers.json>
```

The default rule is "open the first 2 layers (canonical id ascending), defer the rest". Override via `options.open_layer_count` (1–5) or `--open-layer-count N` if the user explicitly asks to widen / narrow scope.

**Persistence (re-opening deferred layers, ADR-013)**: pass `--task "<short task name>"` to enable state. The override list lives in `.layerforge_state/<task_hash>.json` (project-local, gitignored). Subsequent runs with the same `--task` load the saved overrides.

```bash
# First run — see what's open
python -m layerforge.cli.decide decisions.json --task "kdf-launch" --pretty

# Later: user says "actually let's also open L2"
python -m layerforge.cli.decide decisions.json --task "kdf-launch" --open 2 --pretty

# User changes mind, close L2 again
python -m layerforge.cli.decide decisions.json --task "kdf-launch" --close 2

# Mark a single decision as settled (decided / done)
python -m layerforge.cli.decide decisions.json --task "kdf-launch" --settle d05

# Undo a settle if user changes their mind
python -m layerforge.cli.decide decisions.json --task "kdf-launch" --unsettle d05

# Inspect persisted state without running
python -m layerforge.cli.decide --task "kdf-launch" --show-state --pretty
```

When `--task` is set, the output JSON includes:
- `manually_opened_layer_ids` — layers user pinned open (distinguish from auto-opened)
- `settled_decision_ids` — decisions user marked done across the whole run
- Per-layer `member_settled: [str, ...]` — settled members of that layer
- Per-layer `all_settled: bool` — true when every member of the layer is settled

**Render rule for settled items**: when a layer has `all_settled: true`, render its header with a ✓ marker and collapse the member list to a single line "all N decisions settled". For partially settled layers, render settled members with a `[x]` checkbox and unsettled with `[ ]`.

### Step 3 — Render
Read `layers.json`. The CLI has already tagged each layer with `status: "open"|"defer"` and exposes `open_layer_ids` / `deferred_layer_ids` for quick lookup. Render:

```
# Decision integration for: {user task}

## To decide now ({open_count} layers, {member_count} items):

### L{layer.id}: {layer.representation_summary}
- [ ] {decision.text} ({node_id})
…

## Deferred:
### L{layer.id}: {layer.representation_summary}
({len(layer.member_node_ids)} decisions — defer until open layers settle)
…

## Quality
{same as Mode A}
```

To "re-open" a deferred layer later, invoke decide again with `--open-layer-count` raised, or hand-pick decisions from a specific deferred layer.

---

## CLI reference

All CLI commands assume the **LayerForge project root** as the working directory (so `python -m layerforge.cli.*` can resolve the package). Before the first Bash call in a session, confirm this with `ls pyproject.toml layerforge/cli/decompose.py`; if either is missing, locate the LayerForge repo first (`find / -name "layerforge" -type d 2>/dev/null | head` or ask the user) and `cd` there.

### Embedding backend selection

`options.embedding_backend` controls how node texts become vectors. Pick by context:

| Backend | When to use | Trade-off |
|---|---|---|
| `"hash"` (default) | Project-local tests, offline / no-network, axiom verification | No external deps. Limited expressiveness — hash-bucket collisions can merge semantically distinct nodes; expect occasional `quality_class: "acceptable"` instead of `"good"`. |
| `"sentence_transformers"` | Real user input, production runs, decision integration on real tasks | Requires `pip install sentence-transformers` (in `[embeddings]` extra). Downloads model on first use (~400 MB). True semantic similarity. |

The CLI emits a stderr note when `hash` is used and Q < 0.7 — that is the signal to switch backend, not a LayerForge bug. For Mode B in particular (subtle decision similarity), prefer `sentence_transformers` once the user starts feeding real decisions.

Both `decompose` and `decide` accept `--embedding-backend {hash,sentence_transformers}` and `--embedding-model <hf_id>` as command-line overrides; they win over whatever is in `options.embedding_backend`. Empirical results:

| dataset | backend | Q | layers | ARI vs truth | notes |
|---|---|---|---|---|---|
| `sample_decisions.json` (synthetic) | hash | 0.593 (acceptable) | 3 | — | scope+meta mixed |
| `sample_decisions.json` (synthetic) | sentence_transformers | 0.750 (good) | 4 | — | 4 themes cleanly separated |
| **20 Newsgroups (real, 4 topics, 100 docs)** | sentence_transformers | 0.520 (acceptable) | 4 | **0.708** | each layer dominated by 1 topic, purity 83–96% |
| 20 Newsgroups (real, 200 docs) | sentence_transformers | 0.491 (acceptable) | 4 | 0.483 | noisier but structure preserved |

Run `python scripts/verify_real_data.py` to reproduce the 20NG numbers locally. Regression test: `tests/integration/test_real_data_20ng.py` (auto-skipped if sklearn/sentence-transformers cache miss + offline).

### Scaling: sparse top-K kNN similarity

For large inputs the O(n²) dense similarity matrix exceeds memory (~800 MB at n=10,000, ~80 GB at n=100,000). Use sparse top-K kNN instead:

```bash
# explicit k
python -m layerforge.cli.decompose nodes.json --sparse-top-k 50

# auto: dense for n < 5,000, sparse-top-50 for n >= 5,000
python -m layerforge.cli.decompose nodes.json --sparse-top-k auto
```

The same flag is accepted by `decide`. Two semantic differences in sparse mode:
- Per-layer **indivisibility flags are skipped** (would require sparse-eigh; flagged as `false` conservatively).
- Modularity Q is computed over the kNN graph rather than the full similarity matrix; the value is comparable but not identical to dense Q. Use `--sparse-top-k <large_K>` (e.g. 200) when you want the closest approximation to dense.

Suitable range: n ∈ [5,000 – 200,000]. Beyond that, use an approximate-kNN library (faiss / NMSLIB) — currently out of scope.

### Recursive depth (F3.4)

By default the CLI does **flat** 4±1 decomposition (one level). To recursively split each layer into 4±1 sub-layers, pass `--max-depth N` (1 ≤ N ≤ 4):

```bash
python -m layerforge.cli.decompose nodes.json --max-depth 2 --pretty
```

Each layer in the output JSON gains:
- `depth`: 0 for top-level, 1 for direct children, etc.
- `children`: array of sub-layer objects (recursive structure)

A sub-layer that cannot be 4±1 decomposed (members too few, or sub-distribution doesn't support it) remains a leaf without raising an error. Use `--min-recurse-members M` (default 8) to set the minimum-size guard for attempting recursion. Theoretical maximum: 4×4×4×4 = 256 leaf nodes at depth 4. Mode B (decide) inherits the same flag, but persistence (`--task`/`--open`/`--settle`) still operates only on top-level layer IDs.

### `python -m layerforge.cli.decompose [input.json] [--pretty]`
Mode A. Reads `input.json` (or stdin if `-` or omitted). Writes JSON to stdout. Exit 0 on success, non-zero on error (but the error payload is still emitted to stdout for the skill to read).

### `python -m layerforge.cli.decide [input.json] [--pretty] [--open-layer-count N]`
Mode B. Same I/O contract as decompose; adds `status` per layer plus top-level `open_layer_ids` / `deferred_layer_ids`.

### `python -m layerforge.cli.validate_output`
PostToolUse hook companion. Reads stdout of a previous Bash call from stdin; exits 0 if JSON is a valid LayerForge payload (or non-LayerForge / non-JSON, pass-through). See `docs/05b` §Hooks.

---

## DO NOT
- Add introductions, conclusions, or transitions not derived from `result.json`.
- Use evocative language unless the user's input contains it.
- Speculate about implications or context.
- Adopt any voice, persona, or rhetorical style.
- Retry indefinitely on `NoValidScaleError`/`SeparationQualityError`. Report once and ask the user to refine input.
