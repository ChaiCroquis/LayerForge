"""Stop/PostToolUse hook companion: validate LayerForge CoreResult JSON (L2 schema).

Reads from stdin. Two stdin shapes are supported:
1. A raw JSON CoreResult payload (legacy / direct piping).
2. A Claude Code PostToolUse hook envelope (recommended); we extract
   `tool_response.stdout` and only validate it when the originating
   `tool_input.command` actually invokes a `layerforge.cli` module.

For any other shape (non-JSON, non-LayerForge, unrelated Bash output) the
hook exits 0 (pass-through). It exits 1 *only* when the payload clearly
looks like LayerForge output but fails schema validation. This keeps the
hook from interfering with unrelated Bash calls in the project.

This is the docs/05b §Hooks integration L2 enforcement.
"""
from __future__ import annotations

import json
import sys


REQUIRED_TOP = {"status"}
REQUIRED_OK = {"status", "layers", "inter_layer_relations", "quality_metrics"}
REQUIRED_QM = {
    "modularity",
    "layer_count",
    "scale_coefficient",
    "is_within_4_plus_minus_1",
    "quality_class",
}
QUALITY_CLASSES = {"good", "acceptable", "poor"}


def _validate(payload: dict) -> tuple[bool, str]:
    if not isinstance(payload, dict):
        return False, "payload must be a JSON object"
    if not REQUIRED_TOP <= set(payload):
        return False, f"missing top-level keys: {REQUIRED_TOP - set(payload)}"
    status = payload.get("status")
    if status not in {"ok", "error"}:
        return False, f"status must be ok|error, got {status!r}"
    if status == "error":
        if "error_type" not in payload:
            return False, "error payload missing error_type"
        return True, "ok (error payload)"
    # status == ok
    missing = REQUIRED_OK - set(payload)
    if missing:
        return False, f"ok payload missing keys: {missing}"
    qm = payload.get("quality_metrics")
    if not isinstance(qm, dict):
        return False, "quality_metrics must be an object"
    qm_missing = REQUIRED_QM - set(qm)
    if qm_missing:
        return False, f"quality_metrics missing keys: {qm_missing}"
    if qm["quality_class"] not in QUALITY_CLASSES:
        return False, f"quality_class must be one of {QUALITY_CLASSES}"
    return True, "ok"


def _looks_like_layerforge(payload) -> bool:
    """Sniff: only treat as LayerForge if it has both shape sentinels."""
    if not isinstance(payload, dict):
        return False
    status = payload.get("status")
    if status not in {"ok", "error"}:
        return False
    if status == "ok" and "quality_metrics" not in payload:
        return False
    if status == "error" and "error_type" not in payload:
        return False
    return True


def _extract_candidate(raw: str):
    """Find the JSON payload to validate.

    Tries (a) raw stdin as a CoreResult, (b) a CC hook envelope from which
    we extract tool_response.stdout when the command invoked layerforge.cli.
    Returns the candidate dict, or None if nothing relevant.
    """
    raw = raw.strip()
    if not raw:
        return None
    try:
        outer = json.loads(raw)
    except json.JSONDecodeError:
        return None
    # (a) direct payload
    if _looks_like_layerforge(outer):
        return outer
    # (b) CC PostToolUse hook envelope
    if isinstance(outer, dict) and outer.get("tool_name") == "Bash":
        command = (outer.get("tool_input") or {}).get("command", "")
        if "layerforge.cli" not in command:
            return None
        stdout = (outer.get("tool_response") or {}).get("stdout", "")
        if not stdout.strip():
            return None
        try:
            inner = json.loads(stdout)
        except json.JSONDecodeError:
            return None
        return inner if _looks_like_layerforge(inner) else None
    return None


def main(argv: list[str] | None = None) -> int:
    raw = sys.stdin.read()
    payload = _extract_candidate(raw)
    if payload is None:
        # Either non-JSON, non-LayerForge, or unrelated Bash call.
        return 0
    ok, msg = _validate(payload)
    if not ok:
        sys.stderr.write(f"[layerforge.validate_output] FAIL: {msg}\n")
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
