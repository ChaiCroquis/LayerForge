"""Phase 2b persistence tests — state file + --open/--close round-trip."""
from __future__ import annotations

import json
import os

import pytest

from layerforge.cli import decide, state


def _decisions_payload() -> dict:
    themes = [
        ["scope_a scope_b scope_c scope_d", "scope_a scope_b scope_e scope_f",
         "scope_b scope_c scope_g scope_h", "scope_a scope_d scope_g scope_i"],
        ["place_a place_b place_c place_d", "place_a place_b place_e place_f",
         "place_b place_c place_g place_h", "place_a place_d place_g place_i"],
        ["struct_a struct_b struct_c struct_d", "struct_a struct_b struct_e struct_f",
         "struct_b struct_c struct_g struct_h", "struct_a struct_d struct_g struct_i"],
        ["meta_a meta_b meta_c meta_d", "meta_a meta_b meta_e meta_f",
         "meta_b meta_c meta_g meta_h", "meta_a meta_d meta_g meta_i"],
    ]
    nodes = []
    idx = 0
    for theme in themes:
        for text in theme:
            nodes.append({"id": f"d{idx:03d}", "text": text})
            idx += 1
    return {"nodes": nodes, "options": {"embedding_backend": "hash", "random_seed": 42}}


@pytest.fixture
def isolated_state_root(tmp_path, monkeypatch):
    """Run decide in an isolated CWD so state files don't leak across tests."""
    monkeypatch.chdir(tmp_path)
    return tmp_path


# ---------- state.py unit tests ----------


def test_task_hash_is_stable():
    assert state.task_hash("foo") == state.task_hash("foo")
    assert state.task_hash("foo") != state.task_hash("bar")


def test_load_state_returns_empty_shape_when_absent(isolated_state_root):
    s = state.load_state("never-saved")
    assert s["manually_opened_layer_ids"] == []
    assert s["task"] == "never-saved"
    assert s["task_hash"] == state.task_hash("never-saved")


def test_save_then_load_roundtrip(isolated_state_root):
    s = state.load_state("t1")
    state.add_open(s, 3)
    state.add_open(s, 1)
    state.save_state(s, "t1", seed=42)

    reloaded = state.load_state("t1")
    assert reloaded["manually_opened_layer_ids"] == [1, 3]
    assert reloaded["last_seed"] == 42
    assert reloaded["last_run_at"]


def test_add_open_dedups_and_sorts(isolated_state_root):
    s = state.load_state("t2")
    state.add_open(s, 3)
    state.add_open(s, 1)
    state.add_open(s, 3)
    assert s["manually_opened_layer_ids"] == [1, 3]


def test_remove_open(isolated_state_root):
    s = state.load_state("t3")
    state.add_open(s, 2)
    state.add_open(s, 4)
    state.remove_open(s, 2)
    assert s["manually_opened_layer_ids"] == [4]


# ---------- decide.run() honors manually_opened ----------


def test_run_with_manual_open_extends_open_set():
    payload = _decisions_payload()
    # Default open = [0, 1]. Pin L2 → expect [0, 1, 2].
    out = decide.run(payload, manually_opened=[2])
    assert out["open_layer_ids"] == [0, 1, 2]
    assert 2 not in out["deferred_layer_ids"]
    assert out["manually_opened_layer_ids"] == [2]


def test_run_drops_manual_open_for_nonexistent_layer():
    payload = _decisions_payload()
    out = decide.run(payload, manually_opened=[999])
    # Default = [0, 1]; the 999 is dropped silently.
    assert out["open_layer_ids"] == [0, 1]
    assert out["manually_opened_layer_ids"] == []


# ---------- decide.main() --task / --open / --close flow ----------


def test_main_persists_state_after_open(isolated_state_root, capsys, tmp_path):
    inp = tmp_path / "decisions.json"
    inp.write_text(json.dumps(_decisions_payload()), encoding="utf-8")

    rc = decide.main([str(inp), "--task", "demo", "--open", "2"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "ok"
    assert 2 in out["open_layer_ids"]

    # State file exists with the override persisted.
    reloaded = state.load_state("demo")
    assert reloaded["manually_opened_layer_ids"] == [2]


def test_main_close_reverts_open(isolated_state_root, capsys, tmp_path):
    inp = tmp_path / "decisions.json"
    inp.write_text(json.dumps(_decisions_payload()), encoding="utf-8")

    decide.main([str(inp), "--task", "demo2", "--open", "2"])
    capsys.readouterr()  # discard
    decide.main([str(inp), "--task", "demo2", "--close", "2"])
    capsys.readouterr()
    assert state.load_state("demo2")["manually_opened_layer_ids"] == []


def test_main_show_state_short_circuits(isolated_state_root, capsys, tmp_path):
    inp = tmp_path / "decisions.json"
    inp.write_text(json.dumps(_decisions_payload()), encoding="utf-8")

    # Populate state.
    decide.main([str(inp), "--task", "demo3", "--open", "3"])
    capsys.readouterr()

    # --show-state must NOT need an input file.
    rc = decide.main(["--task", "demo3", "--show-state"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["task"] == "demo3"
    assert out["manually_opened_layer_ids"] == [3]


def test_main_open_without_task_is_invalid(capsys):
    rc = decide.main(["--open", "2"])
    assert rc == 1
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "error"
    assert out["error_type"] == "InvalidUsageError"


def test_main_show_state_without_task_is_invalid(capsys):
    rc = decide.main(["--show-state"])
    assert rc == 1
    out = json.loads(capsys.readouterr().out)
    assert out["error_type"] == "InvalidUsageError"


def test_persisted_override_propagates_across_invocations(isolated_state_root, capsys, tmp_path):
    inp = tmp_path / "decisions.json"
    inp.write_text(json.dumps(_decisions_payload()), encoding="utf-8")

    # First run: open L2.
    decide.main([str(inp), "--task", "demo4", "--open", "2"])
    capsys.readouterr()

    # Second run: no --open flag, but override should still apply.
    rc = decide.main([str(inp), "--task", "demo4"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert 2 in out["open_layer_ids"]
    assert out["manually_opened_layer_ids"] == [2]


def test_state_file_path_includes_task_hash(isolated_state_root):
    p = state.state_path("my-task")
    assert p.name == f"{state.task_hash('my-task')}.json"
    assert p.parent.name == ".layerforge_state"
