"""CLI tests — `python -m layerforge.cli.decide` (Phase 2b Mode B)."""
from __future__ import annotations

import json

import pytest

from layerforge.cli import decide
from layerforge.cli.validate_output import _looks_like_layerforge


def _decisions_input(open_layer_count: int | None = None) -> dict:
    """4 well-separated 'decision groups' via disjoint synthetic vocab."""
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
    payload = {
        "nodes": nodes,
        "options": {"embedding_backend": "hash", "random_seed": 42},
    }
    if open_layer_count is not None:
        payload["options"]["open_layer_count"] = open_layer_count
    return payload


def test_decide_default_open_count_is_two():
    out = decide.run(_decisions_input())
    assert out["status"] == "ok"
    assert len(out["open_layer_ids"]) == 2
    assert out["open_layer_ids"] == [0, 1]
    # deferred = total - open
    assert set(out["open_layer_ids"]) | set(out["deferred_layer_ids"]) == {
        l["id"] for l in out["layers"]
    }


def test_decide_per_layer_status_tagged():
    out = decide.run(_decisions_input())
    for layer in out["layers"]:
        assert layer["status"] in {"open", "defer"}
        if layer["id"] in out["open_layer_ids"]:
            assert layer["status"] == "open"
        else:
            assert layer["status"] == "defer"


def test_decide_open_layer_count_override():
    out = decide.run(_decisions_input(open_layer_count=1))
    assert out["open_layer_ids"] == [0]
    out3 = decide.run(_decisions_input(open_layer_count=3))
    assert out3["open_layer_ids"] == [0, 1, 2]


def test_decide_open_layer_count_out_of_range_raises():
    with pytest.raises(ValueError):
        decide.run(_decisions_input(open_layer_count=0))
    with pytest.raises(ValueError):
        decide.run(_decisions_input(open_layer_count=99))


def test_decide_output_passes_validate_output_sniff():
    out = decide.run(_decisions_input())
    # decide adds extra fields but the LayerForge sentinel sniff still matches.
    assert _looks_like_layerforge(out)


def test_decide_is_deterministic():
    a = decide.run(_decisions_input())
    b = decide.run(_decisions_input())
    assert a["open_layer_ids"] == b["open_layer_ids"]
    assert [l["status"] for l in a["layers"]] == [l["status"] for l in b["layers"]]


def test_decide_main_writes_json(capsys, tmp_path):
    inp = tmp_path / "decisions.json"
    inp.write_text(json.dumps(_decisions_input()), encoding="utf-8")
    rc = decide.main([str(inp), "--pretty"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "ok"
    assert "open_layer_ids" in out
    assert "deferred_layer_ids" in out


def test_decide_main_open_count_flag_overrides_options(capsys, tmp_path):
    inp = tmp_path / "decisions.json"
    payload = _decisions_input(open_layer_count=3)
    inp.write_text(json.dumps(payload), encoding="utf-8")
    rc = decide.main([str(inp), "--open-layer-count", "1"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["open_layer_ids"] == [0]  # CLI flag wins
