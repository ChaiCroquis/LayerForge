# LayerForge — project-local Claude Code configuration

This directory contains **project-local** Claude Code config. It activates
the LayerForge skill **only when Claude Code is run inside this repository**.
Nothing here touches your global `~/.claude/`.

## Layout

```
.claude/
├── README.md                       # this file
├── settings.json                   # project-local hooks (PostToolUse validate_output)
└── skills/
    └── layerforge/
        └── SKILL.md                # the skill that drives Mode A / Mode B
```

## What runs when

- **Skill discovery**: Claude Code auto-discovers `.claude/skills/layerforge/SKILL.md` whenever a session is opened from this repository. The skill becomes available as `/layerforge` (and is also triggered by the description-matching heuristic on user prompts).
- **Hook `PostToolUse:Bash`**: after every Bash invocation, `python -m layerforge.cli.validate_output` reads the hook envelope from stdin. It validates the payload **only** if the command actually invoked `layerforge.cli` and the stdout looks like a LayerForge CoreResult; otherwise it exits 0 silently. Non-LayerForge Bash calls (`ls`, `git`, `gh`, …) are unaffected.

## Smoke check

From the repo root:

```bash
# 1. Skill file is well-formed
head -5 .claude/skills/layerforge/SKILL.md

# 2. CLI runs without install (PYTHONPATH=. via -m)
python -c "import json; print(json.dumps({'nodes': [{'id': f'n{i}', 'text': p+'_a '+p+'_b '+p+'_c '+p+'_d'} for i, p in enumerate(['a','a','a','a','b','b','b','b','c','c','c','c','d','d','d','d'])]}))" > /tmp/lf_in.json
python -m layerforge.cli.decompose /tmp/lf_in.json --pretty | head -20

# 3. Hook companion is benign on unrelated stdin
echo '{"unrelated": true}' | python -m layerforge.cli.validate_output && echo OK

# 4. Hook fails on bad LayerForge payload (intended)
echo '{"status": "ok", "layers": []}' | python -m layerforge.cli.validate_output ; echo "exit=$?"
```

## Deploying globally (later)

When the skill is ready for daily use across all projects, copy the
skill folder to your user-level Claude Code config:

```bash
cp -r .claude/skills/layerforge ~/.claude/skills/
# (optional) merge .claude/settings.json hooks into ~/.claude/settings.json
```

That step is **not done now** — current scope is project-local test
verification only.
