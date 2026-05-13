"""Boundary 1: parse natural language → FormulationInput."""
from __future__ import annotations

import hashlib
from typing import Any

import numpy as np

from layerforge.constants import MAX_RETRIES
from layerforge.core.modularity import build_similarity_matrix
from layerforge.core.scale_finder import compute_initial_scale
from layerforge.exceptions import LLMError, SchemaViolation
from layerforge.schema.input_schema import (
    FormulationInput,
    Node,
    RawInput,
    ScaleParams,
)


def _normalize(text: str) -> str:
    return " ".join(text.strip().split())


def _node_id(text: str, idx: int) -> str:
    h = hashlib.sha1(text.encode("utf-8")).hexdigest()[:10]
    return f"n{idx:04d}_{h}"


def mechanical_split(text: str | list[str]) -> list[str]:
    """Deterministic fallback: split on punctuation/newlines."""
    if isinstance(text, list):
        items = [s for s in (t.strip() for t in text) if s]
    else:
        items: list[str] = []
        for chunk in text.replace("\n", ".").split("."):
            s = chunk.strip()
            if s:
                items.append(s)
    return items or [str(text).strip() or "empty"]


def validate_node_proposal(proposal: list[str], original_text: str | list[str]) -> bool:
    """Minimal validation: non-empty, min length, count bounds."""
    if not proposal:
        return False
    if len(proposal) < 1 or len(proposal) > 200:
        return False
    return all(len(n.strip()) >= 1 for n in proposal)


def _hash_embed(texts: list[str], dim: int = 64) -> np.ndarray:
    """Deterministic hash-based pseudo-embedding for tests / no-LLM mode."""
    out = np.zeros((len(texts), dim), dtype=float)
    for i, t in enumerate(texts):
        for j, tok in enumerate(t.lower().split()):
            h = int(hashlib.sha1(tok.encode("utf-8")).hexdigest(), 16)
            out[i, h % dim] += 1.0
    # L2 normalize for cosine-friendly behaviour
    norms = np.linalg.norm(out, axis=1, keepdims=True)
    safe = np.where(norms == 0, 1.0, norms)
    return out / safe


def parse_to_structure(
    raw_input: RawInput,
    llm_client: Any | None = None,
    embedding_client: Any | None = None,
) -> FormulationInput:
    """[INFERENCE BOUNDARY 1] schema-enforced, retry → mechanical fallback."""
    text = (
        raw_input.content
        if isinstance(raw_input.content, list)
        else str(raw_input.content)
    )

    proposal: list[str] | None = None
    if llm_client is not None:
        for _ in range(MAX_RETRIES):
            try:
                candidate = llm_client.propose_nodes(text if isinstance(text, str) else "\n".join(text), None, None)
                if validate_node_proposal(candidate, text):
                    proposal = candidate
                    break
            except (SchemaViolation, LLMError):
                continue

    if proposal is None:
        proposal = mechanical_split(text)

    normalized = [_normalize(s) for s in proposal if _normalize(s)]
    nodes = tuple(
        Node(id=_node_id(t, i), text=t, metadata={"source": "parse"})
        for i, t in enumerate(normalized)
    )

    if embedding_client is not None:
        embeddings = embedding_client.embed([n.text for n in nodes])
    else:
        embeddings = _hash_embed([n.text for n in nodes])

    similarity_matrix = build_similarity_matrix(embeddings)
    initial_threshold = compute_initial_scale(similarity_matrix)

    return FormulationInput(
        nodes=nodes,
        embeddings=embeddings,
        similarity_matrix=similarity_matrix,
        initial_scale=ScaleParams(threshold=initial_threshold),
    )


def parse_to_structure_mechanical(raw_input: RawInput) -> FormulationInput:
    """Pure deterministic path (no LLM)."""
    return parse_to_structure(raw_input, llm_client=None, embedding_client=None)
