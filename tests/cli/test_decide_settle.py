"""Phase 2b settled-decision tracking tests."""
from __future__ import annotations

import json

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
def isolated(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return tmp_path


# ---------- state.py unit tests for settled ----------


def test_state_initial_settled_is_empty_list(isolated):
    s = state.load_state("t-settled")
    assert s["settled_decision_ids"] == []


def test_state_add_settled_dedups_and_sorts(isolated):
    s = state.load_state("t-settled-2")
    state.add_settled(s, "d005")
    state.add_settled(s, "d002")
    state.add_settled(s, "d005")  # dup
    assert s["settled_decision_ids"] == ["d002", "d005"]


def test_state_remove_settled(isolated):
    s = state.load_state("t-settled-3")
    state.add_settled(s, "d001")
    state.add_settled(s, "d009")
    state.remove_settled(s, "d001")
    assert s["settled_decision_ids"] == ["d009"]


def test_state_settled_roundtrip_through_save_load(isolated):
    s = state.load_state("t-settled-4")
    state.add_settled(s, "d011")
    state.add_settled(s, "d003")
    state.save_state(s, "t-settled-4", seed=42)
    reloaded = state.load_state("t-settled-4")
    assert reloaded["settled_decision_ids"] == ["d003", "d011"]


# ---------- decide.run() honors settled_decision_ids ----------


def test_run_annotates_member_settled():
    payload = _decisions_payload()
    out = decide.run(payload, settled_decision_ids=["d000", "d005"])
    assert out["settled_decision_ids"] == ["d000", "d005"]
    # Each layer must have member_settled and all_settled fields.
    for layer in out["layers"]:
        assert "member_settled" in layer
        assert "all_settled" in layer
        assert set(layer["member_settled"]) <= set(layer["member_node_ids"])
        # all_settled is true iff every member is in settled set.
        expected_all = bool(layer["member_node_ids"]) and set(layer["member_node_ids"]) <= {"d000", "d005"}
        assert layer["all_settled"] == expected_all


def test_run_all_settled_true_when_all_members_settled():
    payload = _decisions_payload()
    # First, run with no settled to discover which decisions are in L0.
    base = decide.run(payload)
    l0_members = next(l["member_node_ids"] for l in base["layers"] if l["id"] == 0)
    # Now settle every member of L0.
    out = decide.run(payload, settled_decision_ids=l0_members)
    l0 = next(l for l in out["layers"] if l["id"] == 0)
    assert l0["all_settled"] is True
    assert set(l0["member_settled"]) == set(l0_members)
    # Other layers stay all_settled=false.
    for layer in out["layers"]:
        if layer["id"] != 0:
            assert layer["all_settled"] is False


def test_run_settled_decision_ids_sanitized_against_existing_nodes():
    """Stale settled IDs from prior runs must be silently dropped."""
    payload = _decisions_payload()
    out = decide.run(payload, settled_decision_ids=["d000", "d_nonexistent", "d99999"])
    # Only d00 (which exists) survives.
    assert out["settled_decision_ids"] == ["d000"]


def test_run_without_settled_omits_field():
    payload = _decisions_payload()
    out = decide.run(payload)  # no settled arg
    # When settled_decision_ids is None, the top-level field is absent.
    assert "settled_decision_ids" not in out
    # Layers still carry member_settled/all_settled (empty / false).
    for layer in out["layers"]:
        assert layer["member_settled"] == []
        assert layer["all_settled"] is False


# ---------- decide.main() flow with --settle / --unsettle ----------


def test_main_settle_persists_id(isolated, capsys, tmp_path):
    inp = tmp_path / "decisions.json"
    inp.write_text(json.dumps(_decisions_payload()), encoding="utf-8")

    rc = decide.main([str(inp), "--task", "demo-settle", "--settle", "d005"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert "d005" in out["settled_decision_ids"]
    # Persisted.
    assert state.load_state("demo-settle")["settled_decision_ids"] == ["d005"]


def test_main_unsettle_removes_id(isolated, capsys, tmp_path):
    inp = tmp_path / "decisions.json"
    inp.write_text(json.dumps(_decisions_payload()), encoding="utf-8")

    decide.main([str(inp), "--task", "demo-unsettle", "--settle", "d005"])
    capsys.readouterr()
    decide.main([str(inp), "--task", "demo-unsettle", "--unsettle", "d005"])
    capsys.readouterr()
    assert state.load_state("demo-unsettle")["settled_decision_ids"] == []


def test_main_settle_without_task_is_invalid(capsys):
    rc = decide.main(["--settle", "d005"])
    assert rc == 1
    out = json.loads(capsys.readouterr().out)
    assert out["error_type"] == "InvalidUsageError"
    assert "settle" in out["message"]


def test_main_settled_propagates_across_invocations(isolated, capsys, tmp_path):
    inp = tmp_path / "decisions.json"
    inp.write_text(json.dumps(_decisions_payload()), encoding="utf-8")

    # Settle some decisions in one run.
    decide.main([str(inp), "--task", "demo-prop", "--settle", "d000"])
    capsys.readouterr()
    decide.main([str(inp), "--task", "demo-prop", "--settle", "d004"])
    capsys.readouterr()

    # Run without --settle: state still applies.
    rc = decide.main([str(inp), "--task", "demo-prop"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert sorted(out["settled_decision_ids"]) == ["d000", "d004"]


def test_main_show_state_includes_settled(isolated, capsys, tmp_path):
    inp = tmp_path / "decisions.json"
    inp.write_text(json.dumps(_decisions_payload()), encoding="utf-8")

    decide.main([str(inp), "--task", "demo-show", "--settle", "d007"])
    capsys.readouterr()

    rc = decide.main(["--task", "demo-show", "--show-state"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["settled_decision_ids"] == ["d007"]
