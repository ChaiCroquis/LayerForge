"""Phase 2a — Anthropic-backed LLM client tests.

Offline tests verify the client contract and pydantic schema. The live test
is gated by ``ANTHROPIC_API_KEY`` so CI does not spend money or fail without
network.
"""
from __future__ import annotations

import os

import pytest

from layerforge.inference.llm_client import (
    AnthropicLLMClient,
    DEFAULT_MODEL,
    MockFailingLLM,
    MockLLMClient,
)
from layerforge.schema.llm_schemas import NodeProposal


# ----- schema contract -----


def test_node_proposal_accepts_nodes_only():
    p = NodeProposal(nodes=["a", "b"])
    assert p.nodes == ["a", "b"]
    assert p.error is None


def test_node_proposal_accepts_error_only():
    p = NodeProposal(error="decomposition_failed", reason="too short")
    assert p.error == "decomposition_failed"
    assert p.nodes == []


# ----- AnthropicLLMClient: offline interface tests -----


def test_anthropic_client_construction_requires_sdk():
    """If anthropic SDK is missing, constructor raises LLMError. Otherwise OK."""
    try:
        import anthropic  # noqa: F401
    except ImportError:
        from layerforge.exceptions import LLMError

        with pytest.raises(LLMError):
            AnthropicLLMClient(api_key="sk-fake")
        return

    client = AnthropicLLMClient(api_key="sk-fake")
    assert client.model == DEFAULT_MODEL
    assert hasattr(client, "propose_nodes")
    assert hasattr(client, "render")


def test_anthropic_client_default_model_is_opus_4_7():
    assert DEFAULT_MODEL == "claude-opus-4-7"


# ----- Mocks still work end-to-end -----


def test_mock_llm_propose_nodes_basic():
    nodes = MockLLMClient().propose_nodes("alpha. beta. gamma.")
    assert nodes == ["alpha", "beta", "gamma"]


def test_mock_failing_llm_raises():
    from layerforge.exceptions import LLMError

    with pytest.raises(LLMError):
        MockFailingLLM().propose_nodes("anything")


# ----- Live test (skipped unless ANTHROPIC_API_KEY is set) -----


@pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set",
)
def test_anthropic_client_live_parse_smoke():
    """Live smoke test for Boundary 1. Requires API key."""
    client = AnthropicLLMClient()
    text = (
        "Cats nap in sunbeams. Trains glide on rails. Pianos echo in halls. "
        "Volcanoes shape coastlines. Rivers carve canyons over millennia."
    )
    nodes = client.propose_nodes(text)
    assert isinstance(nodes, list)
    assert all(isinstance(n, str) and n for n in nodes)
    assert 3 <= len(nodes) <= 20


@pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set",
)
def test_anthropic_client_live_render_smoke():
    """Live smoke test for Boundary 2."""
    client = AnthropicLLMClient()
    template_data = {
        "layers": [
            {
                "layer_id": 0,
                "layer_name": "Layer 0",
                "n_members": 2,
                "member_texts": ["alpha", "beta"],
                "tokens": [["alpha", "beta"]],
                "n_components": 1,
                "is_converged": True,
            }
        ],
        "relations": [],
        "quality": {
            "modularity": 0.7,
            "layer_count": 1,
            "scale_coefficient": 0.5,
            "is_within_4_plus_minus_1": False,
            "quality_class": "good",
        },
    }
    text = client.render(template_data)
    assert isinstance(text, str)
    assert text.strip()
