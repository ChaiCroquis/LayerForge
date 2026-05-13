"""CLI tests — `python -m layerforge.cli.decompose` skill entry (ADR-014, Phase 2a)."""
from __future__ import annotations

import io
import json

import pytest

import io

from layerforge.cli import decompose
from layerforge.cli.decompose import maybe_warn_backend_quality
from layerforge.cli.validate_output import (
    _extract_candidate,
    _looks_like_layerforge,
    _validate as validate_output_payload,
)


# ----------------------------------------------------------------------
# happy path
# ----------------------------------------------------------------------


def _well_separated_input() -> dict:
    """4 thematic blocks with disjoint vocabularies.

    Using a synthetic vocabulary (alpha_*/beta_*/gamma_*/delta_*) so the hash
    embedding's token-bucket similarities form 4 clean blocks. Real-text
    fixtures share generic tokens ("evening", "morning") that leak between
    themes; this version avoids that for hash-backend stability.
    """
    themes = [
        ["alpha_a alpha_b alpha_c alpha_d", "alpha_a alpha_b alpha_e alpha_f",
         "alpha_b alpha_c alpha_g alpha_h", "alpha_a alpha_d alpha_g alpha_i"],
        ["beta_a beta_b beta_c beta_d", "beta_a beta_b beta_e beta_f",
         "beta_b beta_c beta_g beta_h", "beta_a beta_d beta_g beta_i"],
        ["gamma_a gamma_b gamma_c gamma_d", "gamma_a gamma_b gamma_e gamma_f",
         "gamma_b gamma_c gamma_g gamma_h", "gamma_a gamma_d gamma_g gamma_i"],
        ["delta_a delta_b delta_c delta_d", "delta_a delta_b delta_e delta_f",
         "delta_b delta_c delta_g delta_h", "delta_a delta_d delta_g delta_i"],
    ]
    nodes = []
    idx = 0
    for theme in themes:
        for text in theme:
            nodes.append({"id": f"n{idx:03d}", "text": text})
            idx += 1
    return {"nodes": nodes, "options": {"embedding_backend": "hash", "random_seed": 42}}


def test_run_returns_ok_status_for_well_separated_input():
    out = decompose.run(_well_separated_input())
    assert out["status"] == "ok"
    qm = out["quality_metrics"]
    assert 3 <= qm["layer_count"] <= 5
    assert qm["quality_class"] in {"good", "acceptable", "poor"}
    assert isinstance(qm["modularity"], float)
    assert isinstance(qm["scale_coefficient"], float)


def test_run_output_layers_cover_all_nodes():
    payload = _well_separated_input()
    out = decompose.run(payload)
    seen: set[str] = set()
    for layer in out["layers"]:
        seen.update(layer["member_node_ids"])
    expected = {n["id"] for n in payload["nodes"]}
    assert seen == expected


def test_run_output_passes_validate_output_schema():
    out = decompose.run(_well_separated_input())
    ok, msg = validate_output_payload(out)
    assert ok, msg


def test_run_is_deterministic():
    payload = _well_separated_input()
    a = decompose.run(payload)
    b = decompose.run(payload)
    # Compare structurally — float equality holds because the pipeline is
    # fully deterministic when seed/backend are fixed.
    assert a["quality_metrics"] == b["quality_metrics"]
    assert [l["member_node_ids"] for l in a["layers"]] == [
        l["member_node_ids"] for l in b["layers"]
    ]


# ----------------------------------------------------------------------
# error path
# ----------------------------------------------------------------------


def test_run_with_too_few_nodes_returns_error_payload():
    """2-node input cannot yield 4±1 layers — NoValidScaleError surfaces as JSON."""
    payload = {"nodes": [{"id": "n1", "text": "alpha beta"}, {"id": "n2", "text": "gamma delta"}]}
    # main() catches and emits JSON; run() raises directly. Validate both.
    with pytest.raises(Exception):
        decompose.run(payload)


def test_main_emits_error_json_on_failure(capsys, tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text('{"nodes": [{"id": "n1", "text": "alpha"}, {"id": "n2", "text": "beta"}]}', encoding="utf-8")
    rc = decompose.main([str(bad)])
    assert rc != 0
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "error"
    assert "error_type" in out


def test_main_emits_error_for_invalid_input():
    rc = decompose.main(["-"])  # stdin will be empty under pytest


# ----------------------------------------------------------------------
# validate_output hook
# ----------------------------------------------------------------------


def test_validate_output_accepts_ok_payload():
    ok, _ = validate_output_payload({
        "status": "ok",
        "layers": [],
        "inter_layer_relations": [],
        "quality_metrics": {
            "modularity": 0.5,
            "layer_count": 4,
            "scale_coefficient": 0.3,
            "is_within_4_plus_minus_1": True,
            "quality_class": "good",
        },
    })
    assert ok


def test_validate_output_accepts_error_payload():
    ok, _ = validate_output_payload({"status": "error", "error_type": "NoValidScaleError", "message": "x"})
    assert ok


def test_validate_output_rejects_missing_quality_metrics_field():
    ok, msg = validate_output_payload({
        "status": "ok",
        "layers": [],
        "inter_layer_relations": [],
        "quality_metrics": {"modularity": 0.5},
    })
    assert not ok
    assert "quality_metrics" in msg


def test_looks_like_layerforge_sniff():
    """Sniff must accept LayerForge shapes and reject unrelated JSON."""
    assert _looks_like_layerforge({
        "status": "ok",
        "quality_metrics": {},
    })
    assert _looks_like_layerforge({"status": "error", "error_type": "NoValidScaleError"})
    # Unrelated payloads — must be False so the hook passes them through.
    assert not _looks_like_layerforge({"unrelated": True})
    assert not _looks_like_layerforge({"status": "success"})  # wrong status enum
    assert not _looks_like_layerforge({"status": "ok"})  # missing quality_metrics
    assert not _looks_like_layerforge({"status": "error"})  # missing error_type
    assert not _looks_like_layerforge("not a dict")
    assert not _looks_like_layerforge([1, 2, 3])


def test_extract_candidate_pass_through_for_unrelated_bash():
    """Hook envelope from a non-LayerForge Bash call → no candidate."""
    envelope = json.dumps({
        "tool_name": "Bash",
        "tool_input": {"command": "ls -la"},
        "tool_response": {"stdout": "total 4\n-rw-r-- README\n", "stderr": "", "exit_code": 0},
    })
    assert _extract_candidate(envelope) is None


def test_extract_candidate_finds_layerforge_in_envelope():
    """Hook envelope wrapping a LayerForge CLI stdout → extracts inner payload."""
    inner = {
        "status": "ok",
        "layers": [],
        "inter_layer_relations": [],
        "quality_metrics": {
            "modularity": 0.5,
            "layer_count": 4,
            "scale_coefficient": 0.3,
            "is_within_4_plus_minus_1": True,
            "quality_class": "good",
        },
    }
    envelope = json.dumps({
        "tool_name": "Bash",
        "tool_input": {"command": "python -m layerforge.cli.decompose nodes.json"},
        "tool_response": {"stdout": json.dumps(inner), "stderr": "", "exit_code": 0},
    })
    candidate = _extract_candidate(envelope)
    assert candidate is not None
    assert candidate["status"] == "ok"


def test_extract_candidate_ignores_non_bash_tool():
    """Hook envelope for a non-Bash tool → no candidate."""
    envelope = json.dumps({
        "tool_name": "Read",
        "tool_input": {"file_path": "/tmp/x.json"},
        "tool_response": {"content": '{"status": "ok"}'},
    })
    assert _extract_candidate(envelope) is None


def test_extract_candidate_accepts_direct_payload():
    """Direct piping of a CoreResult (no envelope) still works."""
    direct = json.dumps({
        "status": "ok",
        "layers": [],
        "inter_layer_relations": [],
        "quality_metrics": {
            "modularity": 0.5,
            "layer_count": 4,
            "scale_coefficient": 0.3,
            "is_within_4_plus_minus_1": True,
            "quality_class": "good",
        },
    })
    candidate = _extract_candidate(direct)
    assert candidate is not None
    assert candidate["status"] == "ok"


def test_extract_candidate_returns_none_for_non_json():
    assert _extract_candidate("not json at all") is None
    assert _extract_candidate("") is None
    assert _extract_candidate("   \n  ") is None


def _result_with_q(q: float, status: str = "ok") -> dict:
    base = {
        "status": status,
        "layers": [],
        "inter_layer_relations": [],
        "quality_metrics": {
            "modularity": q,
            "layer_count": 4,
            "scale_coefficient": 0.3,
            "is_within_4_plus_minus_1": True,
            "quality_class": "acceptable",
        },
    }
    if status == "error":
        base = {"status": "error", "error_type": "NoValidScaleError", "message": "x"}
    return base


def test_warn_emitted_when_hash_backend_and_low_Q():
    """hash backend + Q < 0.7 → stderr note."""
    buf = io.StringIO()
    payload = {"nodes": [], "options": {"embedding_backend": "hash"}}
    maybe_warn_backend_quality(payload, _result_with_q(0.5), stream=buf)
    msg = buf.getvalue()
    assert "modularity Q=0.500" in msg
    assert "sentence_transformers" in msg


def test_warn_silent_when_Q_meets_good_threshold():
    """hash backend + Q ≥ 0.7 → no note (clustering already 'good')."""
    buf = io.StringIO()
    payload = {"nodes": [], "options": {"embedding_backend": "hash"}}
    maybe_warn_backend_quality(payload, _result_with_q(0.75), stream=buf)
    assert buf.getvalue() == ""


def test_warn_silent_for_non_hash_backend():
    """sentence_transformers backend never triggers the note."""
    buf = io.StringIO()
    payload = {"nodes": [], "options": {"embedding_backend": "sentence_transformers"}}
    maybe_warn_backend_quality(payload, _result_with_q(0.3), stream=buf)
    assert buf.getvalue() == ""


def test_warn_silent_for_error_result():
    """Error payloads do not trigger the note."""
    buf = io.StringIO()
    payload = {"nodes": [], "options": {"embedding_backend": "hash"}}
    maybe_warn_backend_quality(payload, _result_with_q(0.0, status="error"), stream=buf)
    assert buf.getvalue() == ""


def test_warn_silent_when_options_missing_defaults_to_hash():
    """Default backend is hash, so missing options still triggers on low Q."""
    buf = io.StringIO()
    maybe_warn_backend_quality({"nodes": []}, _result_with_q(0.4), stream=buf)
    assert "sentence_transformers" in buf.getvalue()


def test_validate_output_rejects_unknown_quality_class():
    ok, _ = validate_output_payload({
        "status": "ok",
        "layers": [],
        "inter_layer_relations": [],
        "quality_metrics": {
            "modularity": 0.5,
            "layer_count": 4,
            "scale_coefficient": 0.3,
            "is_within_4_plus_minus_1": True,
            "quality_class": "excellent",  # invalid
        },
    })
    assert not ok
