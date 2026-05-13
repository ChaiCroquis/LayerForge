"""Integration tests (docs/05 §統合テスト戦略)."""
from __future__ import annotations

import numpy as np

from layerforge.inference.llm_client import MockFailingLLM, MockLLMClient
from layerforge.pipeline import layerforge_core, layerforge_pipeline
from layerforge.schema.input_schema import RawInput


def test_end_to_end_with_layered_text():
    """Decomposition of a text composed of 4 thematic blocks."""
    blocks = [
        "Cats purr softly on warm windowsills. Cats chase laser pointers in the kitchen. Cats nap in sunbeams every afternoon. Cats groom their whiskers each morning",
        "Trains glide across rusted rails at dawn. Trains carry passengers between cities. Trains whistle through long tunnels. Trains rumble past quiet stations",
        "Pianos resonate in concert halls. Pianos accompany jazz singers in clubs. Pianos teach children patience and rhythm. Pianos echo in empty cathedrals",
        "Volcanoes erupt with molten fury. Volcanoes shape the ocean floor. Volcanoes feed thermal springs nearby. Volcanoes record ancient climate shifts",
    ]
    raw = RawInput(source_type="text", content="\n".join(blocks))
    out = layerforge_pipeline(raw)
    assert out is not None
    assert "Quality" in out.text or "Diagnostic" in out.text


def test_inference_boundary_isolation(synthetic_layered_formulation):
    """Same FormulationInput → identical CoreResult (determinism)."""
    r1 = layerforge_core(synthetic_layered_formulation, seed=42)
    r2 = layerforge_core(synthetic_layered_formulation, seed=42)
    assert r1.quality_metrics.layer_count == r2.quality_metrics.layer_count
    for l1, l2 in zip(r1.layers, r2.layers):
        assert l1.member_indices == l2.member_indices


def test_full_fallback_chain():
    """LLM が完全失敗してもパイプラインは止まらない (template fallback)."""
    text_blocks = "\n".join(
        f"topic{k} alpha beta gamma word{k}" for k in range(20)
    )
    raw = RawInput(source_type="text", content=text_blocks)
    out = layerforge_pipeline(raw, llm_client=MockFailingLLM())
    assert out is not None
    assert isinstance(out.text, str)


def test_mock_llm_runs_end_to_end():
    text_blocks = "\n".join(
        f"topic{k} alpha beta gamma word{k}" for k in range(20)
    )
    raw = RawInput(source_type="text", content=text_blocks)
    out = layerforge_pipeline(raw, llm_client=MockLLMClient())
    assert out is not None
