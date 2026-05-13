"""LLM clients — Phase 2a primary path is the Claude Code skill (ADR-014, v5).

This module is the **future-option library path** preserved per ADR-014
("現在の設計は将来の選択肢を縛らない"). The primary v5 implementation lives
in:
- `SKILL.md` at the repo root (Claude Code skill instructions, no Python LLM client)
- `layerforge/cli/decompose.py` (deterministic CLI invoked by the skill)

`AnthropicLLMClient` here is retained for the scenario where LayerForge is
distributed as a standalone library (see ADR-014 §Future option). It is not
exercised by the default skill flow and is not on the Phase 2a critical path.

Mocks remain useful for offline tests of the boundary contract.
"""
from __future__ import annotations

import os
from typing import Any, Protocol

from layerforge.constants import MAX_RETRIES
from layerforge.exceptions import LLMError, SchemaViolation
from layerforge.inference.prompts import (
    PARSE_SYSTEM_PROMPT,
    RENDER_SYSTEM_PROMPT,
)


# ----------------------------------------------------------------------
# Contracts
# ----------------------------------------------------------------------


class LLMClient(Protocol):
    """Inference-boundary client contract (Boundary 1 / Boundary 2)."""

    def propose_nodes(
        self, text: str, schema: Any = None, constraints: dict | None = None
    ) -> list[str]: ...

    def render(
        self, template_data: dict, system_prompt: str = "", output_schema: Any = None
    ) -> Any: ...


# ----------------------------------------------------------------------
# Mocks (deterministic, network-free)
# ----------------------------------------------------------------------


class MockLLMClient:
    """Deterministic mock for tests and offline runs."""

    def propose_nodes(
        self, text: str, schema: Any = None, constraints: dict | None = None
    ) -> list[str]:
        parts: list[str] = []
        for line in text.replace("\n", ".").split("."):
            s = line.strip()
            if s:
                parts.append(s)
        return parts

    def render(
        self, template_data: dict, system_prompt: str = "", output_schema: Any = None
    ):
        from layerforge.inference.render import template_only_render
        return template_only_render(template_data)


class MockFailingLLM:
    """Always raises LLMError — used to exercise fallback paths."""

    def propose_nodes(self, *_a, **_kw):
        raise LLMError("mock failure")

    def render(self, *_a, **_kw):
        raise LLMError("mock failure")


# ----------------------------------------------------------------------
# Anthropic-backed real client
# ----------------------------------------------------------------------


# Per CLAUDE.md global rules: default to the latest and most capable model.
DEFAULT_MODEL: str = "claude-opus-4-7"

# Token budgets (large enough to avoid truncation; streaming used for render).
PARSE_MAX_TOKENS: int = 8192
RENDER_MAX_TOKENS: int = 64000


class AnthropicLLMClient:
    """Real LLM client backed by the Anthropic SDK.

    - Parse (Boundary 1): structured output via `messages.parse()` with the
      `NodeProposal` pydantic model. Adaptive thinking disabled (mechanical
      decomposition is not reasoning-heavy).
    - Render (Boundary 2): free-form markdown via `messages.stream()`.
      Adaptive thinking enabled for quality-sensitive translation.

    Prompt-caching markers are placed on the system prompt; actual cache
    hits depend on the model's prefix-size minimum (Opus 4.7 = 4096 tokens).
    """

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        api_key: str | None = None,
        render_effort: str = "high",
    ) -> None:
        try:
            import anthropic  # type: ignore
        except ImportError as e:  # pragma: no cover
            raise LLMError(
                "anthropic SDK not installed. Install with: pip install layerforge[inference]"
            ) from e
        self._anthropic = anthropic
        self._client = anthropic.Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))
        self.model = model
        self.render_effort = render_effort

    # -- Boundary 1: parse --------------------------------------------------

    def propose_nodes(
        self,
        text: str,
        schema: Any = None,
        constraints: dict | None = None,
    ) -> list[str]:
        """Decompose `text` into a list of semantically distinct node strings."""
        from layerforge.schema.llm_schemas import NodeProposal

        system = [
            {
                "type": "text",
                "text": PARSE_SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ]
        messages = [{"role": "user", "content": text}]

        try:
            response = self._client.messages.parse(
                model=self.model,
                max_tokens=PARSE_MAX_TOKENS,
                system=system,
                messages=messages,
                output_format=NodeProposal,
            )
        except self._anthropic.APIStatusError as e:
            raise LLMError(f"parse APIStatusError {e.status_code}: {e.message}") from e
        except self._anthropic.APIConnectionError as e:
            raise LLMError(f"parse APIConnectionError: {e}") from e

        proposal = response.parsed_output
        if proposal is None:
            raise SchemaViolation("Boundary 1: parsed_output is None")
        if proposal.error:
            raise SchemaViolation(
                f"Boundary 1 reported failure: {proposal.error} ({proposal.reason or ''})"
            )
        if not proposal.nodes:
            raise SchemaViolation("Boundary 1: empty nodes list")
        return list(proposal.nodes)

    # -- Boundary 2: render -------------------------------------------------

    def render(
        self,
        template_data: dict,
        system_prompt: str = "",
        output_schema: Any = None,
    ) -> str:
        """Render structured `template_data` to natural-language markdown."""
        sys_text = system_prompt or RENDER_SYSTEM_PROMPT
        # Pack template_data as a single user text block. JSON is fine — the
        # render prompt instructs Claude to preserve values verbatim.
        import json

        user_payload = json.dumps(template_data, ensure_ascii=False, indent=2)
        system = [
            {
                "type": "text",
                "text": sys_text,
                "cache_control": {"type": "ephemeral"},
            }
        ]
        messages = [{"role": "user", "content": user_payload}]

        try:
            with self._client.messages.stream(
                model=self.model,
                max_tokens=RENDER_MAX_TOKENS,
                system=system,
                messages=messages,
                thinking={"type": "adaptive"},
                output_config={"effort": self.render_effort},
            ) as stream:
                final = stream.get_final_message()
        except self._anthropic.APIStatusError as e:
            raise LLMError(f"render APIStatusError {e.status_code}: {e.message}") from e
        except self._anthropic.APIConnectionError as e:
            raise LLMError(f"render APIConnectionError: {e}") from e

        text_parts = [b.text for b in final.content if getattr(b, "type", None) == "text"]
        if not text_parts:
            raise SchemaViolation("Boundary 2: empty text response")
        return "\n".join(text_parts)
