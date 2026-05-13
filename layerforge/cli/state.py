"""Persistent state for Phase 2b decide-mode re-opening (ADR-013).

A single `.layerforge_state/<task_hash>.json` file per *task* records the
user's manual layer-open overrides. The state is read by `decide`
*before* applying the default open/defer rule and merged on top of it.

State shape:
    {
      "task": "<human-readable task name>",
      "task_hash": "<sha1 prefix>",
      "manually_opened_layer_ids": [int, ...],
      "settled_decision_ids": [str, ...],
      "last_seed": <int>,
      "last_run_at": "<ISO8601 UTC>"
    }

The state is keyed by the task name (whatever string the user passes via
`--task`). Two different invocations with the same task name share state;
distinct task names are independent. State is project-local (lives under
the project root, not under `~/.claude/`), gitignored by default.
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STATE_DIR_NAME: str = ".layerforge_state"


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def task_hash(task: str) -> str:
    """Stable short hash for a task name. Used as the state file basename."""
    return hashlib.sha1(task.encode("utf-8")).hexdigest()[:12]


def state_dir(root: str | os.PathLike | None = None) -> Path:
    """Return the state directory (creating it if needed)."""
    base = Path(root) if root else Path.cwd()
    d = base / STATE_DIR_NAME
    d.mkdir(exist_ok=True, parents=True)
    return d


def state_path(task: str, root: str | os.PathLike | None = None) -> Path:
    return state_dir(root) / f"{task_hash(task)}.json"


def load_state(task: str, root: str | os.PathLike | None = None) -> dict[str, Any]:
    """Load state for ``task``; return an empty-shape dict if absent."""
    path = state_path(task, root)
    if not path.exists():
        return {
            "task": task,
            "task_hash": task_hash(task),
            "manually_opened_layer_ids": [],
            "settled_decision_ids": [],
            "last_seed": None,
            "last_run_at": None,
        }
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    # Defensive defaults — older state files may lack fields.
    data.setdefault("task", task)
    data.setdefault("task_hash", task_hash(task))
    data.setdefault("manually_opened_layer_ids", [])
    data.setdefault("settled_decision_ids", [])
    data.setdefault("last_seed", None)
    data.setdefault("last_run_at", None)
    return data


def save_state(
    state: dict[str, Any],
    task: str,
    root: str | os.PathLike | None = None,
    seed: int | None = None,
) -> Path:
    """Persist ``state`` for ``task``. Updates last_run_at / last_seed."""
    state["task"] = task
    state["task_hash"] = task_hash(task)
    state["last_run_at"] = _now_iso()
    if seed is not None:
        state["last_seed"] = seed
    # Canonicalize override + settled lists (sorted, deduped).
    state["manually_opened_layer_ids"] = sorted(set(state.get("manually_opened_layer_ids", [])))
    state["settled_decision_ids"] = sorted(set(state.get("settled_decision_ids", [])))
    path = state_path(task, root)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    return path


def add_open(state: dict[str, Any], layer_id: int) -> dict[str, Any]:
    state["manually_opened_layer_ids"] = sorted(
        set(state.get("manually_opened_layer_ids", [])) | {int(layer_id)}
    )
    return state


def remove_open(state: dict[str, Any], layer_id: int) -> dict[str, Any]:
    state["manually_opened_layer_ids"] = sorted(
        set(state.get("manually_opened_layer_ids", [])) - {int(layer_id)}
    )
    return state


def add_settled(state: dict[str, Any], decision_id: str) -> dict[str, Any]:
    state["settled_decision_ids"] = sorted(
        set(state.get("settled_decision_ids", [])) | {str(decision_id)}
    )
    return state


def remove_settled(state: dict[str, Any], decision_id: str) -> dict[str, Any]:
    state["settled_decision_ids"] = sorted(
        set(state.get("settled_decision_ids", [])) - {str(decision_id)}
    )
    return state
