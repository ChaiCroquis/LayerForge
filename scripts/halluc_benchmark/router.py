"""LayerForge-based routing: corpus → 4 layers → route question to one layer.

Pipeline:
1. Embed all corpus passages (sentence-transformers backend).
2. Run layerforge_core to produce 4±1 layers.
3. For each question, embed the question and pick the layer whose
   centroid (mean of member embeddings) has highest cosine similarity.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from layerforge.cli.decompose import run as decompose_run
from layerforge.inference.embedding import SentenceTransformersEmbedding

from scripts.halluc_benchmark.corpus import (
    PASSAGES,
    PASSAGE_BY_ID,
    QUESTIONS,
)


DEFAULT_EMBED_MODEL = "sentence-transformers/paraphrase-MiniLM-L3-v2"


@dataclass(frozen=True)
class LayerAssignment:
    layer_id: int
    passage_ids: tuple[str, ...]


@dataclass(frozen=True)
class RoutingResult:
    layers: tuple[LayerAssignment, ...]
    quality_metrics: dict
    question_routes: dict[str, int]  # question_id -> chosen layer_id


def _decompose_corpus(embed_model: str) -> tuple[dict, np.ndarray, list[str]]:
    """Run LayerForge on the corpus. Returns (result dict, passage embeddings,
    list of passage IDs in payload order)."""
    payload = {
        "nodes": [{"id": p.id, "text": p.text} for p in PASSAGES],
        "options": {
            "embedding_backend": "sentence_transformers",
            "embedding_model": embed_model,
            "random_seed": 42,
        },
    }
    result = decompose_run(payload)
    if result.get("status") != "ok":
        raise RuntimeError(f"LayerForge decompose failed: {result}")

    # Recompute embeddings for the question-routing step.
    embedder = SentenceTransformersEmbedding(model_name=embed_model)
    passage_ids = [p.id for p in PASSAGES]
    embeddings = embedder.embed([p.text for p in PASSAGES])
    return result, embeddings, passage_ids


def _normalize(vecs: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    safe = np.where(norms == 0, 1.0, norms)
    return vecs / safe


def route_all(embed_model: str = DEFAULT_EMBED_MODEL) -> RoutingResult:
    result, passage_embeddings, passage_ids = _decompose_corpus(embed_model)

    pid_to_idx = {pid: i for i, pid in enumerate(passage_ids)}
    layers_out: list[LayerAssignment] = []
    centroids: list[np.ndarray] = []
    layer_ids: list[int] = []

    for layer in result["layers"]:
        member_ids = tuple(layer["member_node_ids"])
        layers_out.append(LayerAssignment(layer_id=layer["id"], passage_ids=member_ids))
        member_idx = [pid_to_idx[pid] for pid in member_ids]
        centroid = passage_embeddings[member_idx].mean(axis=0)
        centroids.append(centroid)
        layer_ids.append(layer["id"])

    centroid_matrix = _normalize(np.stack(centroids))

    # Embed questions and route each to the best-matching layer.
    embedder = SentenceTransformersEmbedding(model_name=embed_model)
    question_texts = [q.text for q in QUESTIONS]
    q_embeds = _normalize(embedder.embed(question_texts))
    sims = q_embeds @ centroid_matrix.T  # (n_q, n_layers)
    chosen = np.argmax(sims, axis=1)

    question_routes = {
        QUESTIONS[i].id: layer_ids[chosen[i]] for i in range(len(QUESTIONS))
    }

    return RoutingResult(
        layers=tuple(layers_out),
        quality_metrics=result["quality_metrics"],
        question_routes=question_routes,
    )


def passages_for_condition(
    routing: RoutingResult,
    condition: str,
    question_id: str,
) -> list[str]:
    """Return the list of passage IDs to include in the prompt for a
    given (condition, question).

    Conditions:
      - "full"     : all 24 passages (baseline)
      - "layerforge": only passages of the routed layer
      - "oracle"   : only the ground-truth source passage (or [] if unanswerable)
    """
    from scripts.halluc_benchmark.corpus import QUESTION_BY_ID

    if condition == "full":
        return [p.id for p in PASSAGES]

    if condition == "layerforge":
        layer_id = routing.question_routes[question_id]
        for layer in routing.layers:
            if layer.layer_id == layer_id:
                return list(layer.passage_ids)
        raise KeyError(f"layer {layer_id} not found")

    if condition == "oracle":
        q = QUESTION_BY_ID[question_id]
        if q.source_passage_id is None:
            return []
        return [q.source_passage_id]

    raise ValueError(f"unknown condition: {condition}")
