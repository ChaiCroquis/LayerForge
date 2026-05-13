"""Mode C (compress) CLI tests."""
from __future__ import annotations

import json

import pytest

from layerforge.cli import compress


_SAMPLE_VERBOSE = """\
To write a unit test, first import the unittest module.
Then create a class inheriting from TestCase.

Define test methods with names starting with test_.
Use assertEqual to verify expected outputs.
Use assertRaises to verify exception behavior.

Beyond basic tests, consider edge cases like empty inputs.
Boundary conditions are particularly error-prone.
Always test the minimum and maximum allowed values.

For continuous integration, configure GitHub Actions.
A workflow YAML file goes in .github/workflows/.
Most projects use pytest as the test runner.
Coverage reports can be uploaded to Codecov.

Documentation should accompany tests.
Write a brief description in each test method's docstring.
A README section on how to run tests helps newcomers.
Examples of expected output are useful too.
"""


def test_compress_returns_passthrough_for_short_input():
    payload = {
        "question": "How do I test?",
        "response": "Short answer.\n\nOne sentence only.",
    }
    result = compress.run(payload)
    assert result["status"] == "passthrough"
    assert result["selected_text"] == payload["response"]
    assert result["compression"]["ratio"] == 1.0


def test_compress_returns_ok_for_multi_layer_input():
    payload = {
        "question": "How do I write a basic unit test?",
        "response": _SAMPLE_VERBOSE,
        "options": {"embedding_backend": "hash", "random_seed": 42},
    }
    result = compress.run(payload)
    assert result["status"] == "ok"
    assert "selected_layer_id" in result
    assert "selected_text" in result
    assert "deferred_layers" in result
    assert result["compression"]["ratio"] < 1.0
    assert result["compression"]["selected_chars"] < result["compression"]["input_chars"]


def test_compress_selected_is_subset_of_input():
    payload = {
        "question": "How do I write a basic unit test?",
        "response": _SAMPLE_VERBOSE,
        "options": {"embedding_backend": "hash"},
    }
    result = compress.run(payload)
    if result["status"] != "ok":
        pytest.skip(f"compress status={result['status']}")
    # Every selected paragraph must appear verbatim in the original.
    for para in result["selected_text"].split("\n\n"):
        assert para.strip() in _SAMPLE_VERBOSE


def test_compress_deferred_layers_cover_complement():
    payload = {
        "question": "How do I write a basic unit test?",
        "response": _SAMPLE_VERBOSE,
        "options": {"embedding_backend": "hash"},
    }
    result = compress.run(payload)
    if result["status"] != "ok":
        pytest.skip(f"compress status={result['status']}")
    # Sum of deferred n_items + selected layer's items == total node count
    selected_node_count = len([p for p in result["selected_text"].split("\n\n") if p.strip()])
    deferred_count = sum(d["n_items"] for d in result["deferred_layers"])
    # Re-split input to compare
    from layerforge.cli.compress import _split_into_nodes
    total = len(_split_into_nodes(_SAMPLE_VERBOSE))
    assert selected_node_count + deferred_count == total


def test_compress_deterministic():
    payload = {
        "question": "How do I write a basic unit test?",
        "response": _SAMPLE_VERBOSE,
        "options": {"embedding_backend": "hash", "random_seed": 42},
    }
    a = compress.run(payload)
    b = compress.run(payload)
    if a["status"] != "ok":
        pytest.skip(f"compress status={a['status']}")
    assert a["selected_layer_id"] == b["selected_layer_id"]
    assert a["selected_text"] == b["selected_text"]


def test_compress_main_writes_json(tmp_path, capsys):
    payload_path = tmp_path / "in.json"
    payload_path.write_text(json.dumps({
        "question": "How do I write tests?",
        "response": _SAMPLE_VERBOSE,
        "options": {"embedding_backend": "hash"},
    }), encoding="utf-8")
    rc = compress.main([str(payload_path), "--pretty"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["status"] in ("ok", "passthrough")


def test_compress_main_inline_question_flag(tmp_path, capsys):
    """--question + --response-file should construct payload without JSON input."""
    resp_path = tmp_path / "resp.txt"
    resp_path.write_text(_SAMPLE_VERBOSE, encoding="utf-8")
    rc = compress.main([
        "--question", "How do I write tests?",
        "--response-file", str(resp_path),
        "--embedding-backend", "hash",
        "--pretty",
    ])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["status"] in ("ok", "passthrough")


def test_compress_missing_question_errors():
    rc = compress.main(["--question", "", "--response-file", __file__])
    assert rc == 1


def test_compress_split_strategy_prefers_paragraphs():
    text = "para one.\n\npara two.\n\npara three.\n\npara four.\n\npara five.\n\npara six."
    from layerforge.cli.compress import _split_into_nodes
    nodes = _split_into_nodes(text)
    assert len(nodes) == 6
    assert nodes[0] == "para one."


def test_compress_split_falls_back_to_lines_for_bullet_lists():
    text = "- one\n- two\n- three\n- four\n- five\n- six\n- seven"
    from layerforge.cli.compress import _split_into_nodes
    nodes = _split_into_nodes(text)
    assert len(nodes) >= 6
