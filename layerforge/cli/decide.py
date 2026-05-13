"""CLI entry: 決定リスト → 「今開くレイヤー」を含む CoreResult (Phase 2b Mode B, ADR-013).

Thin wrapper around `decompose`. Runs the same deterministic core, then
tags each layer with `status: "open" | "defer"` using:

    open layers = first `open_layer_count` ids ∪ manually_opened (from state)

The canonical layer_id ordering is set in `core/hierarchical.py` by
first-member-index. State persistence (Phase 2b §Implementation
requirement 4) is project-local: `--task <name>` enables it, then
`--open N` and `--close N` adjust the manual override list.

Schema (input):
    Same as decompose, plus optional ``options.open_layer_count`` (int,
    default 2, must be in [1, 5]).

Schema (output):
    Same as decompose, plus per-layer ``status: "open"|"defer"``,
    top-level ``open_layer_ids: [int, ...]`` /
    ``deferred_layer_ids: [int, ...]``, and (when --task is given)
    ``manually_opened_layer_ids: [int, ...]``.
"""
from __future__ import annotations

import argparse
import json
import sys

from layerforge.cli import decompose as _decompose
from layerforge.cli import state as _state
from layerforge.constants import LAYER_COUNT_MAX


DEFAULT_OPEN_LAYER_COUNT: int = 2


def _annotate_open_defer(
    result: dict,
    open_layer_count: int,
    manually_opened: list[int] | None = None,
    settled_decision_ids: list[str] | None = None,
) -> dict:
    """Annotate each layer with status; honor manual overrides + settled set."""
    if result.get("status") != "ok":
        return result
    layers = result.get("layers") or []
    ordered_ids = sorted(l["id"] for l in layers)
    auto_open = set(ordered_ids[:open_layer_count])
    manual = set(manually_opened or [])
    # Manual overrides may reference a layer id that doesn't exist (e.g. state
    # from a prior run with a different K). Silently drop those.
    manual &= set(ordered_ids)
    open_ids = auto_open | manual

    settled = set(settled_decision_ids or [])
    all_member_ids: set[str] = set()
    for layer in layers:
        all_member_ids.update(layer.get("member_node_ids", []))
    # Sanitize: settled IDs may reference decisions removed in this run.
    effective_settled = settled & all_member_ids

    for layer in layers:
        layer["status"] = "open" if layer["id"] in open_ids else "defer"
        members = layer.get("member_node_ids", [])
        layer_settled = [mid for mid in members if mid in effective_settled]
        layer["member_settled"] = layer_settled
        layer["all_settled"] = bool(members) and len(layer_settled) == len(members)

    result["open_layer_ids"] = sorted(open_ids)
    result["deferred_layer_ids"] = sorted(set(ordered_ids) - open_ids)
    if manually_opened is not None:
        result["manually_opened_layer_ids"] = sorted(manual)
    if settled_decision_ids is not None:
        result["settled_decision_ids"] = sorted(effective_settled)
    return result


def run(
    payload: dict,
    manually_opened: list[int] | None = None,
    settled_decision_ids: list[str] | None = None,
) -> dict:
    """Run decompose, then add open/defer + settled annotations.

    ``manually_opened`` (when provided) is the persisted override list
    loaded from state. Overrides ∪ auto_open form the final open set.
    ``settled_decision_ids`` tags individual decisions as already-decided;
    layers where every member is settled get ``all_settled: true``.
    """
    options = payload.get("options") or {}
    raw_open = options.get("open_layer_count", DEFAULT_OPEN_LAYER_COUNT)
    try:
        open_layer_count = int(raw_open)
    except (TypeError, ValueError) as e:
        raise ValueError(f"open_layer_count must be int, got {raw_open!r}") from e
    if not (1 <= open_layer_count <= LAYER_COUNT_MAX):
        raise ValueError(
            f"open_layer_count must be in [1, {LAYER_COUNT_MAX}], got {open_layer_count}"
        )

    core_result = _decompose.run(payload)
    return _annotate_open_defer(
        core_result, open_layer_count, manually_opened, settled_decision_ids
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="layerforge.cli.decide",
        description="Decompose decisions into 4±1 layers with open/defer tags (Phase 2b).",
    )
    parser.add_argument(
        "input", nargs="?", default="-",
        help="Path to decisions.json, or '-' for stdin (default).",
    )
    parser.add_argument(
        "--pretty", action="store_true", help="Pretty-print JSON output."
    )
    parser.add_argument(
        "--open-layer-count", type=int, default=None,
        help=f"Number of layers to mark 'open' (default {DEFAULT_OPEN_LAYER_COUNT}). "
             f"Overrides options.open_layer_count if both are set.",
    )
    parser.add_argument(
        "--task", type=str, default=None,
        help="Task name. When set, persists/loads manual layer overrides "
             "in .layerforge_state/<task_hash>.json (project-local).",
    )
    parser.add_argument(
        "--open", type=int, default=None, metavar="LAYER_ID",
        help="Add LAYER_ID to the manually-opened set (requires --task).",
    )
    parser.add_argument(
        "--close", type=int, default=None, metavar="LAYER_ID",
        help="Remove LAYER_ID from the manually-opened set (requires --task).",
    )
    parser.add_argument(
        "--settle", type=str, default=None, metavar="DECISION_ID",
        help="Mark DECISION_ID as settled (decided / done). Requires --task.",
    )
    parser.add_argument(
        "--unsettle", type=str, default=None, metavar="DECISION_ID",
        help="Remove DECISION_ID from the settled set. Requires --task.",
    )
    parser.add_argument(
        "--show-state", action="store_true",
        help="Print the persisted state for --task and exit (no decompose run).",
    )
    parser.add_argument(
        "--embedding-backend", type=str, default=None,
        choices=["hash", "sentence_transformers"],
        help="Override options.embedding_backend (same flag as decompose).",
    )
    parser.add_argument(
        "--embedding-model", type=str, default=None,
        help="Override options.embedding_model (sentence-transformers HF model id).",
    )
    args = parser.parse_args(argv)

    state_required_flags = (
        args.open is not None
        or args.close is not None
        or args.settle is not None
        or args.unsettle is not None
        or args.show_state
    )
    if state_required_flags and not args.task:
        sys.stdout.write(json.dumps({
            "status": "error",
            "error_type": "InvalidUsageError",
            "message": "--open / --close / --settle / --unsettle / --show-state require --task",
        }, ensure_ascii=False) + "\n")
        return 1

    try:
        # --show-state short-circuit
        if args.show_state:
            state = _state.load_state(args.task)
            out = json.dumps(state, ensure_ascii=False, indent=2 if args.pretty else None)
            sys.stdout.write(out + "\n")
            return 0

        payload = _decompose._load_input(args.input)
        if args.open_layer_count is not None:
            payload.setdefault("options", {})["open_layer_count"] = args.open_layer_count
        if args.embedding_backend is not None:
            payload.setdefault("options", {})["embedding_backend"] = args.embedding_backend
        if args.embedding_model is not None:
            payload.setdefault("options", {})["embedding_model"] = args.embedding_model

        manually_opened: list[int] | None = None
        settled_ids: list[str] | None = None
        state: dict | None = None
        if args.task:
            state = _state.load_state(args.task)
            if args.open is not None:
                _state.add_open(state, args.open)
            if args.close is not None:
                _state.remove_open(state, args.close)
            if args.settle is not None:
                _state.add_settled(state, args.settle)
            if args.unsettle is not None:
                _state.remove_settled(state, args.unsettle)
            manually_opened = list(state["manually_opened_layer_ids"])
            settled_ids = list(state.get("settled_decision_ids", []))

        result = run(
            payload,
            manually_opened=manually_opened,
            settled_decision_ids=settled_ids,
        )
        _decompose.maybe_warn_backend_quality(payload, result)

        # Persist state *after* a successful run (so a failing run doesn't
        # commit half-applied overrides). On error the run() above raises and
        # we fall through to the except branch.
        if args.task and state is not None and result.get("status") == "ok":
            seed = int((payload.get("options") or {}).get("random_seed",
                                                          _decompose.DETERMINISTIC_SEED))
            _state.save_state(state, args.task, seed=seed)

        out = json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None)
        sys.stdout.write(out + "\n")
        return 0
    except Exception as e:  # noqa: BLE001
        out = json.dumps(_decompose._error_payload(e), ensure_ascii=False, indent=2 if args.pretty else None)
        sys.stdout.write(out + "\n")
        return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
