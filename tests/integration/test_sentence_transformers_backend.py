"""Phase 2a integration test: sentence-transformers backend resolves
hash-embedding artifacts on the project's bundled Mode B fixture.

Skipped if sentence-transformers is unavailable (offline / no extras).
The model download is cached by HF after the first run.
"""
from __future__ import annotations

import json

import pytest

from layerforge.cli import decide


def _st_available() -> bool:
    try:
        import sentence_transformers  # noqa: F401

        return True
    except ImportError:
        return False


@pytest.mark.skipif(not _st_available(), reason="sentence-transformers not installed")
def test_sentence_transformers_resolves_mode_b_artifact():
    """Mode B sample_decisions.json: hash gives 3-layer mix, ST gives clean 4."""
    sample_path = ".claude/skills/layerforge/test_inputs/sample_decisions.json"
    payload = json.loads(open(sample_path, encoding="utf-8").read())
    payload["options"]["embedding_backend"] = "sentence_transformers"
    payload["options"]["embedding_model"] = "sentence-transformers/paraphrase-MiniLM-L3-v2"

    result = decide.run(payload)
    assert result["status"] == "ok"
    qm = result["quality_metrics"]
    # Hash baseline on this fixture: Q=0.593 acceptable, 3 layers.
    # Sentence-transformers should reach Q >= 0.7 (good) and 4 layers.
    assert qm["layer_count"] == 4, f"expected 4 layers, got {qm['layer_count']}"
    assert qm["modularity"] >= 0.70, f"Q={qm['modularity']:.3f} below 'good' threshold"
    assert qm["quality_class"] == "good"

    # Each theme (scope/place/struct/meta) should be a separate cluster:
    # decision IDs d00-d03, d04-d07, d08-d11, d12-d15.
    expected_themes = {
        frozenset({"d00", "d01", "d02", "d03"}),
        frozenset({"d04", "d05", "d06", "d07"}),
        frozenset({"d08", "d09", "d10", "d11"}),
        frozenset({"d12", "d13", "d14", "d15"}),
    }
    actual_themes = {frozenset(l["member_node_ids"]) for l in result["layers"]}
    assert actual_themes == expected_themes, (
        f"theme separation broken: expected {expected_themes}, got {actual_themes}"
    )


@pytest.mark.skipif(not _st_available(), reason="sentence-transformers not installed")
def test_sentence_transformers_no_backend_warning():
    """The hash-backend warning must NOT fire when sentence_transformers is used."""
    import io
    from layerforge.cli.decompose import maybe_warn_backend_quality

    sample_path = ".claude/skills/layerforge/test_inputs/sample_decisions.json"
    payload = json.loads(open(sample_path, encoding="utf-8").read())
    payload["options"]["embedding_backend"] = "sentence_transformers"
    payload["options"]["embedding_model"] = "sentence-transformers/paraphrase-MiniLM-L3-v2"

    result = decide.run(payload)
    buf = io.StringIO()
    maybe_warn_backend_quality(payload, result, stream=buf)
    assert buf.getvalue() == "", (
        f"sentence-transformers backend must not emit warning, got: {buf.getvalue()!r}"
    )
