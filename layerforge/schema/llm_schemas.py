"""Pydantic schemas for inference-boundary structured outputs (ADR-007).

These are the wire-format contracts at Boundary 1 (parse) and Boundary 2
(render). Keeping them in pydantic — not the frozen dataclasses — lets
`anthropic.messages.parse()` validate them server-side.
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class NodeProposal(BaseModel):
    """Boundary 1 output. Either ``nodes`` is non-empty OR ``error`` is set."""

    nodes: list[str] = Field(default_factory=list, max_length=200)
    error: Optional[str] = None
    reason: Optional[str] = None
