"""Mode C: Compress AI verbose output to the layer closest to user's question.

Input: (user_question, ai_response). Output: only the layer-of-interest's
content + a one-line summary per deferred layer. Use case: AI returned a
500-line answer covering 4 different concerns; user only wants the one
matching their current task.

This is a post-process filter on AI output — orthogonal to Mode A (input
text decomposition) and Mode B (decision integration). The mechanism is
the same: LayerForge decompose + question-driven routing.

Output JSON shape:
    {
      "status": "ok" | "error" | "passthrough",
      "selected_layer_id": int,
      "selected_text": str,            # joined nodes of the chosen layer, in order
      "deferred_layers": [
        {"layer_id": int, "n_items": int, "preview": "first 80 chars..."}
      ],
      "compression": {
        "input_chars": int,
        "selected_chars": int,
        "ratio": float                 # selected / input
      },
      "routing": {
        "question_to_layer_sim": [float, ...],  # similarity per layer
        "layer_count": int,
        "modularity": float,
      }
    }

For trivially short input (< MIN_NODES nodes after split), returns
status="passthrough" with the original text and no compression — the
4±1 axiom cannot apply.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import traceback
from pathlib import Path
from typing import Any

import numpy as np

from layerforge.cli import decompose as _decompose
from layerforge.core.modularity import build_similarity_matrix
from layerforge.exceptions import LayerForgeError, NoValidScaleError


MIN_NODES_FOR_COMPRESSION: int = 6  # need at least n_min(=3) × 2 for sensible 4±1 split
DEFAULT_PREVIEW_CHARS: int = 80


def _split_into_nodes(text: str) -> list[str]:
    """Split AI response into atomic units.

    Strategy:
      1. Try blank-line-delimited paragraphs. If ≥ MIN_NODES_FOR_COMPRESSION, use those.
      2. Otherwise, fall back to single-newline-delimited lines (markdown list items).
      3. Otherwise, sentence split.

    Final step: drop empties, strip whitespace, deduplicate-by-text in order.
    """
    text = text.strip()
    if not text:
        return []

    candidates: list[list[str]] = []

    # 1. paragraphs (blank-line separated)
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    candidates.append(paragraphs)

    # 2. lines (single-newline) — useful when AI uses markdown bullets
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    candidates.append(lines)

    # 3. sentences
    sentences = re.split(r"(?<=[.!?。!?])\s+", text)
    sentences = [s.strip() for s in sentences if s.strip()]
    candidates.append(sentences)

    # Pick the finest granularity that gives at least MIN_NODES_FOR_COMPRESSION,
    # preferring paragraphs to preserve coherent units.
    for nodes in candidates:
        if len(nodes) >= MIN_NODES_FOR_COMPRESSION:
            return nodes
    # If nothing reaches the threshold, return the finest split available
    return candidates[-1] if candidates[-1] else [text]


def _route_question_to_layer(
    question: str,
    layers: list[dict],
    node_embeds: np.ndarray,
    node_id_to_index: dict[str, int],
    embedder,
) -> tuple[int, list[float]]:
    """Compute question→layer routing via cosine similarity to layer centroids.

    Returns (best_layer_id, sims_per_layer).
    """
    q_embed = embedder.embed([question])
    norms = np.linalg.norm(q_embed, axis=1, keepdims=True)
    safe = np.where(norms == 0, 1.0, norms)
    q_unit = (q_embed / safe)[0]

    sims = []
    layer_ids = []
    for layer in layers:
        member_idx = [node_id_to_index[mid] for mid in layer["member_node_ids"]]
        centroid = node_embeds[member_idx].mean(axis=0)
        c_norm = np.linalg.norm(centroid)
        if c_norm == 0:
            sims.append(0.0)
        else:
            sims.append(float(q_unit @ (centroid / c_norm)))
        layer_ids.append(layer["id"])

    best_idx = int(np.argmax(sims))
    return layer_ids[best_idx], sims


def _build_embedder(backend: str, model: str | None):
    if backend == "sentence_transformers":
        from layerforge.inference.embedding import SentenceTransformersEmbedding
        return SentenceTransformersEmbedding(
            model_name=model or "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
        )
    from layerforge.inference.embedding import HashEmbedding
    return HashEmbedding(dim=1024)


def run(payload: dict) -> dict:
    """Compress an AI response based on its similarity to a user question.

    Required keys:
      - "question": str
      - "response": str
    Optional ``options``:
      - "embedding_backend": "hash" | "sentence_transformers"  (default: hash)
      - "embedding_model": str
      - "preview_chars": int
      - "random_seed": int
    """
    if not isinstance(payload, dict):
        raise ValueError("payload must be a JSON object")
    question = str(payload.get("question") or "").strip()
    response = str(payload.get("response") or "").strip()
    if not question:
        raise ValueError("question is required")
    if not response:
        raise ValueError("response is required")
    options = payload.get("options") or {}
    backend = options.get("embedding_backend", "hash")
    model = options.get("embedding_model")
    preview_chars = int(options.get("preview_chars", DEFAULT_PREVIEW_CHARS))
    seed = int(options.get("random_seed", 42))

    nodes = _split_into_nodes(response)
    input_chars = len(response)

    # Passthrough for trivially short input.
    if len(nodes) < MIN_NODES_FOR_COMPRESSION:
        return {
            "status": "passthrough",
            "reason": f"only {len(nodes)} nodes (< {MIN_NODES_FOR_COMPRESSION}); "
                      f"4±1 decomposition not applicable",
            "selected_text": response,
            "compression": {
                "input_chars": input_chars,
                "selected_chars": input_chars,
                "ratio": 1.0,
            },
        }

    # Decompose.
    decompose_payload = {
        "nodes": [{"id": f"p{i:04d}", "text": n} for i, n in enumerate(nodes)],
        "options": {
            "embedding_backend": backend,
            "embedding_model": model,
            "random_seed": seed,
        },
    }
    try:
        d_result = _decompose.run(decompose_payload)
    except NoValidScaleError as e:
        return {
            "status": "error",
            "error_type": "NoValidScaleError",
            "message": str(e),
            "selected_text": response,
            "compression": {
                "input_chars": input_chars,
                "selected_chars": input_chars,
                "ratio": 1.0,
            },
        }

    if d_result.get("status") != "ok":
        return d_result  # propagate error payload from decompose

    # Embed nodes again to build centroids for routing (decompose discards them).
    embedder = _build_embedder(backend, model)
    node_embeds = embedder.embed(nodes)
    node_id_to_index = {f"p{i:04d}": i for i in range(len(nodes))}

    best_layer_id, sims = _route_question_to_layer(
        question, d_result["layers"], node_embeds, node_id_to_index, embedder
    )

    # Extract selected layer + build deferred summaries.
    selected_layer = next(l for l in d_result["layers"] if l["id"] == best_layer_id)
    selected_indices = [node_id_to_index[mid] for mid in selected_layer["member_node_ids"]]
    selected_indices.sort()  # preserve original document order
    selected_nodes = [nodes[i] for i in selected_indices]
    selected_text = "\n\n".join(selected_nodes)

    deferred = []
    for layer in d_result["layers"]:
        if layer["id"] == best_layer_id:
            continue
        idxs = sorted(node_id_to_index[mid] for mid in layer["member_node_ids"])
        first_node = nodes[idxs[0]] if idxs else ""
        preview = first_node[:preview_chars] + (
            "..." if len(first_node) > preview_chars else ""
        )
        deferred.append({
            "layer_id": layer["id"],
            "n_items": len(idxs),
            "preview": preview,
        })

    qm = d_result["quality_metrics"]
    return {
        "status": "ok",
        "selected_layer_id": best_layer_id,
        "selected_text": selected_text,
        "deferred_layers": deferred,
        "compression": {
            "input_chars": input_chars,
            "selected_chars": len(selected_text),
            "ratio": round(len(selected_text) / input_chars, 3) if input_chars else 0.0,
        },
        "routing": {
            "question_to_layer_sim": [round(s, 4) for s in sims],
            "layer_count": qm["layer_count"],
            "modularity": qm["modularity"],
        },
    }


# ----- CLI entry -----


def _load_input(path: str | None) -> dict:
    if path is None or path == "-":
        return json.loads(sys.stdin.read())
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="layerforge.cli.compress",
        description="Mode C: compress an AI verbose response to the layer "
                    "closest to the user's question.",
    )
    parser.add_argument(
        "input", nargs="?", default="-",
        help="Path to JSON containing 'question' and 'response' fields, or '-' for stdin.",
    )
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument(
        "--question", type=str, default=None,
        help="Inline question text (overrides payload.question).",
    )
    parser.add_argument(
        "--response-file", type=str, default=None,
        help="Read the AI response from a text file (overrides payload.response).",
    )
    parser.add_argument(
        "--embedding-backend", default=None,
        choices=["hash", "sentence_transformers"],
    )
    parser.add_argument("--embedding-model", default=None)

    args = parser.parse_args(argv)

    try:
        if args.input == "-" and (args.question or args.response_file):
            payload = {}
        else:
            payload = _load_input(args.input)
        if args.question is not None:
            payload["question"] = args.question
        if args.response_file is not None:
            payload["response"] = Path(args.response_file).read_text(encoding="utf-8")
        if args.embedding_backend is not None:
            payload.setdefault("options", {})["embedding_backend"] = args.embedding_backend
        if args.embedding_model is not None:
            payload.setdefault("options", {})["embedding_model"] = args.embedding_model

        result = run(payload)
        out = json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None)
        sys.stdout.write(out + "\n")
        return 0 if result.get("status") in ("ok", "passthrough") else 1
    except Exception as e:  # noqa: BLE001
        err = {
            "status": "error",
            "error_type": type(e).__name__ if not isinstance(e, LayerForgeError) else e.__class__.__name__,
            "message": str(e),
        }
        if not isinstance(e, (LayerForgeError, ValueError)):
            err["traceback"] = traceback.format_exc()
        sys.stdout.write(json.dumps(err, ensure_ascii=False, indent=2 if args.pretty else None) + "\n")
        return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
