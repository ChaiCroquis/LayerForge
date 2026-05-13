"""CLI entry: 自然言語ノード群 → CoreResult JSON (Phase 2a Mode A).

Invoked by the LayerForge Claude Code skill (SKILL.md Mode A).
The skill writes nodes.json, calls this CLI, reads result.json.

Schema (input):
    {
      "nodes": [{"id": "n1", "text": "..."}, ...],
      "options": {
        "target_layer_count_min": 3,        # optional, default 3
        "target_layer_count_max": 5,        # optional, default 5
        "embedding_backend": "hash" | "sentence_transformers",  # default "hash"
        "embedding_model": "<hf model id>", # optional
        "random_seed": 42                   # optional, default 42
      }
    }

Schema (output, stdout):
    Success:
      {
        "status": "ok",
        "layers": [
          {
            "id": int,
            "member_node_ids": [str, ...],
            "representation_summary": str,
            "token_representations": [[str, ...], ...],
            "purity": float,
            "indivisible": bool
          }
        ],
        "inter_layer_relations": [{"from": int, "to": int, "type": str, "strength": float}],
        "quality_metrics": {
          "modularity": float,
          "layer_count": int,
          "scale_coefficient": float,
          "is_within_4_plus_minus_1": bool,
          "quality_class": "good" | "acceptable" | "poor"
        }
      }
    Failure:
      {"status": "error", "error_type": "NoValidScaleError"|..., "message": str,
       "diagnostic": {...}}
"""
from __future__ import annotations

import argparse
import json
import sys
import traceback
from typing import Any

from layerforge.constants import (
    DETERMINISTIC_SEED,
    LAYER_COUNT_MAX,
    LAYER_COUNT_MIN,
    MODULARITY_THRESHOLD_GOOD,
)
from layerforge.core.distillation import compute_layer_purity
from layerforge.core.modularity import (
    build_similarity_matrix,
    build_sparse_similarity_matrix,
)
from layerforge.core.scale_finder import compute_initial_scale
from layerforge.exceptions import LayerForgeError, NoValidScaleError, SeparationQualityError
from layerforge.pipeline import (
    DEFAULT_MIN_RECURSE_MEMBERS,
    layerforge_core,
    layerforge_core_recursive,
)
from layerforge.schema.input_schema import FormulationInput, Node, ScaleParams


def _load_input(path: str | None) -> dict:
    if path is None or path == "-":
        return json.loads(sys.stdin.read())
    with open(path, encoding="utf-8") as f:
        return json.load(f)


AUTO_SPARSE_N: int = 5000
DEFAULT_SPARSE_TOP_K: int = 50


def _resolve_sparse(sparse_top_k_raw, n: int) -> tuple[bool, int]:
    """Decide whether to use sparse and what top_k to use.

    Returns (use_sparse, top_k). For dense path, top_k is irrelevant.
    """
    if sparse_top_k_raw is None or sparse_top_k_raw == 0:
        return False, 0
    if isinstance(sparse_top_k_raw, str) and sparse_top_k_raw.lower() == "auto":
        if n >= AUTO_SPARSE_N:
            return True, DEFAULT_SPARSE_TOP_K
        return False, 0
    try:
        k = int(sparse_top_k_raw)
    except (TypeError, ValueError) as e:
        raise ValueError(
            f"sparse_top_k must be int, 'auto', or None; got {sparse_top_k_raw!r}"
        ) from e
    if k <= 0:
        return False, 0
    return True, k


def _build_embeddings(texts: list[str], backend: str, model: str | None, hash_dim: int = 1024):
    if backend == "sentence_transformers":
        from layerforge.inference.embedding import SentenceTransformersEmbedding

        client = SentenceTransformersEmbedding(
            model_name=model or "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
        )
        return client.embed(texts)
    # Default: deterministic hash embedding (no network, no extra deps).
    # 1024-dim default keeps token-bucket collision low enough that
    # thematic separation survives without real embeddings.
    from layerforge.inference.embedding import HashEmbedding

    return HashEmbedding(dim=hash_dim).embed(texts)


def _serialize_layer(layer, node_id_map: dict[int, str], embeddings, indiv_flags) -> dict:
    member_ids = [node_id_map[i] for i in layer.member_indices]
    layer_embeds = embeddings[list(layer.member_indices)] if len(layer.member_indices) else embeddings[:0]
    purity = compute_layer_purity(layer.distillation, layer_embeds)
    token_reps = [sorted(t) for t in layer.distillation.token_representations]
    rep_summary = (
        ", ".join(token_reps[0]) if token_reps and token_reps[0] else f"layer {layer.layer_id}"
    )
    out = {
        "id": layer.layer_id,
        "depth": getattr(layer, "depth", 0),
        "member_node_ids": member_ids,
        "representation_summary": rep_summary,
        "token_representations": token_reps,
        "purity": float(purity),
        "indivisible": bool(indiv_flags[layer.layer_id])
        if layer.layer_id < len(indiv_flags)
        else False,
    }
    children = getattr(layer, "children", ())
    if children:
        # Children's indivisibility flags are baked into the sub-CoreResult,
        # but at serialization time we only have the top-level flags here.
        # For children, default to False (unknown at this level); the sub-
        # decomposition's own flags are captured in the recursion's
        # ``children[...].children`` chain implicitly when populated.
        out["children"] = [
            _serialize_layer(c, node_id_map, embeddings, indiv_flags=())
            for c in children
        ]
    return out


def _serialize_core_result(core_result, node_id_map: dict[int, str], embeddings) -> dict:
    indiv_flags = core_result.quality_metrics.indivisibility_flags
    layers_out: list[dict[str, Any]] = [
        _serialize_layer(layer, node_id_map, embeddings, indiv_flags)
        for layer in core_result.layers
    ]
    return {
        "status": "ok",
        "layers": layers_out,
        "inter_layer_relations": [
            {
                "from": r.from_layer_id,
                "to": r.to_layer_id,
                "type": r.relation_type,
                "strength": float(r.strength),
            }
            for r in core_result.inter_layer_relations
        ],
        "quality_metrics": {
            "modularity": float(core_result.quality_metrics.modularity),
            "layer_count": int(core_result.quality_metrics.layer_count),
            "scale_coefficient": float(core_result.quality_metrics.scale_coefficient),
            "is_within_4_plus_minus_1": bool(
                core_result.quality_metrics.is_within_4_plus_minus_1
            ),
            "quality_class": core_result.quality_metrics.quality_class,
            "community_method": core_result.quality_metrics.community_method,
            "cpm_h": (
                None
                if core_result.quality_metrics.cpm_h is None
                else float(core_result.quality_metrics.cpm_h)
            ),
        },
    }


def run(payload: dict) -> dict:
    if not isinstance(payload, dict):
        raise ValueError("input must be a JSON object")
    raw_nodes = payload.get("nodes")
    if not isinstance(raw_nodes, list) or not raw_nodes:
        raise ValueError("nodes must be a non-empty list")

    options = payload.get("options") or {}
    seed = int(options.get("random_seed", DETERMINISTIC_SEED))
    target_min = int(options.get("target_layer_count_min", LAYER_COUNT_MIN))
    target_max = int(options.get("target_layer_count_max", LAYER_COUNT_MAX))
    backend = str(options.get("embedding_backend", "hash"))
    model = options.get("embedding_model")
    hash_dim = int(options.get("hash_dim", 1024))
    # Sparse kNN similarity for large n. Three resolutions:
    #   options.sparse_top_k=<int>     → use sparse with this top_k
    #   options.sparse_top_k="auto"     → auto-enable when n >= AUTO_SPARSE_N
    #   options.sparse_top_k=None / 0   → force dense (back-compat default)
    sparse_top_k_raw = options.get("sparse_top_k", None)
    # F3.4 recursive depth. max_depth=1 (default) = current flat behavior.
    max_depth = int(options.get("max_depth", 1))
    min_recurse_members = int(
        options.get("min_recurse_members", DEFAULT_MIN_RECURSE_MEMBERS)
    )
    # Community detection backend: "newman" (default, Q + threshold + KMeans)
    # or "cpm" (Leiden-CPM, resolution-limit-free, requires layerforge[cpm]).
    community_method = str(options.get("community_method", "newman")).lower()
    if community_method not in ("newman", "cpm"):
        raise ValueError(
            f"community_method must be 'newman' or 'cpm'; got {community_method!r}"
        )

    node_objs: list[Node] = []
    node_id_map: dict[int, str] = {}
    for i, n in enumerate(raw_nodes):
        nid = str(n.get("id") or f"n{i:04d}")
        text = str(n.get("text") or "").strip()
        if not text:
            raise ValueError(f"node {nid} has empty text")
        node_objs.append(Node(id=nid, text=text, metadata={"source": "cli"}))
        node_id_map[i] = nid

    embeddings = _build_embeddings(
        [n.text for n in node_objs], backend=backend, model=model, hash_dim=hash_dim
    )
    use_sparse, sparse_top_k = _resolve_sparse(sparse_top_k_raw, n=len(node_objs))
    if use_sparse:
        similarity = build_sparse_similarity_matrix(embeddings, top_k=sparse_top_k)
    else:
        similarity = build_similarity_matrix(embeddings)
    initial = compute_initial_scale(similarity)
    formulation = FormulationInput(
        nodes=tuple(node_objs),
        embeddings=embeddings,
        similarity_matrix=similarity,
        initial_scale=ScaleParams(threshold=initial),
    )

    if not (1 <= target_min <= target_max):
        raise ValueError(
            f"target_layer_count: must have 1 <= min <= max; got ({target_min}, {target_max})"
        )

    if max_depth > 1:
        core_result = layerforge_core_recursive(
            formulation,
            seed=seed,
            max_depth=max_depth,
            min_recurse_members=min_recurse_members,
            target_range=(target_min, target_max),
            community_method=community_method,
        )
    else:
        core_result = layerforge_core(
            formulation,
            seed=seed,
            target_range=(target_min, target_max),
            community_method=community_method,
        )
    return _serialize_core_result(core_result, node_id_map, embeddings)


def maybe_warn_backend_quality(payload: dict, result: dict, stream=None) -> None:
    """Emit a stderr note if hash backend was used and Q is below 'good'.

    The hash backend is a deterministic stand-in for testing without
    network deps; when modularity Q is below MODULARITY_THRESHOLD_GOOD it
    is usually the embedding's expressiveness, not the user's input.
    sentence-transformers fixes most such cases.
    """
    if result.get("status") != "ok":
        return
    backend = (payload.get("options") or {}).get("embedding_backend", "hash")
    if backend != "hash":
        return
    qm = result.get("quality_metrics") or {}
    Q = qm.get("modularity")
    if Q is None or Q >= MODULARITY_THRESHOLD_GOOD:
        return
    out = stream if stream is not None else sys.stderr
    out.write(
        f"[layerforge] note: modularity Q={Q:.3f} below 'good' threshold "
        f"({MODULARITY_THRESHOLD_GOOD}). The hash embedding backend has limited "
        f"expressiveness; retry with options.embedding_backend=\"sentence_transformers\" "
        f"for production-quality clustering.\n"
    )


def _error_payload(exc: BaseException) -> dict:
    if isinstance(exc, NoValidScaleError):
        return {
            "status": "error",
            "error_type": "NoValidScaleError",
            "message": str(exc),
            "diagnostic": {"similarity_stats": getattr(exc, "similarity_stats", {})},
        }
    if isinstance(exc, SeparationQualityError):
        return {
            "status": "error",
            "error_type": "SeparationQualityError",
            "message": str(exc),
            "diagnostic": {
                "modularity": getattr(exc, "modularity", None),
                "threshold": getattr(exc, "threshold", None),
            },
        }
    if isinstance(exc, LayerForgeError):
        return {"status": "error", "error_type": type(exc).__name__, "message": str(exc)}
    return {
        "status": "error",
        "error_type": "UnexpectedError",
        "message": f"{type(exc).__name__}: {exc}",
        "diagnostic": {"traceback": traceback.format_exc()},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="layerforge.cli.decompose",
        description="Decompose nodes into 4±1 layers (skill CLI entry).",
    )
    parser.add_argument(
        "input", nargs="?", default="-",
        help="Path to nodes.json, or '-' for stdin (default).",
    )
    parser.add_argument(
        "--pretty", action="store_true", help="Pretty-print JSON output."
    )
    parser.add_argument(
        "--embedding-backend", type=str, default=None,
        choices=["hash", "sentence_transformers"],
        help="Override options.embedding_backend. 'hash' (default) is offline/fast; "
             "'sentence_transformers' is production-quality but requires the [embeddings] extra.",
    )
    parser.add_argument(
        "--embedding-model", type=str, default=None,
        help="Override options.embedding_model (sentence-transformers HF model id).",
    )
    parser.add_argument(
        "--sparse-top-k", default=None, metavar="K_or_AUTO",
        help=f"Use sparse top-K kNN similarity for large n. Pass an integer "
             f"(default {DEFAULT_SPARSE_TOP_K} via 'auto'), 'auto' to enable "
             f"only when n >= {AUTO_SPARSE_N}, or omit for dense.",
    )
    parser.add_argument(
        "--max-depth", type=int, default=None, metavar="D",
        help="F3.4 recursive depth. 1 (default) = flat decomposition (current "
             "behaviour). Higher values recursively decompose each layer into "
             "sub-layers up to D (hard cap: MAX_RECURSION_DEPTH=4). Each layer "
             "in output gains 'children' + 'depth' fields.",
    )
    parser.add_argument(
        "--min-recurse-members", type=int, default=None, metavar="M",
        help=f"Skip recursion for layers with fewer than M members. "
             f"Default {DEFAULT_MIN_RECURSE_MEMBERS}.",
    )
    parser.add_argument(
        "--target-layer-min", type=int, default=None, metavar="MIN",
        help=f"Override Cowan's 4±1 lower bound (default {LAYER_COUNT_MIN}). "
             f"Use for sensitivity analysis only.",
    )
    parser.add_argument(
        "--target-layer-max", type=int, default=None, metavar="MAX",
        help=f"Override Cowan's 4±1 upper bound (default {LAYER_COUNT_MAX}).",
    )
    parser.add_argument(
        "--community-method", type=str, default=None,
        choices=["newman", "cpm"],
        help="Community detection backend. 'newman' (default) = θ + KMeans + Q "
             "(Fortunato-Barthélemy resolution limit applies). 'cpm' = Leiden-CPM "
             "(Traag 2011) on similarity graph, resolution-limit-free. Requires "
             "the [cpm] extra (pip install layerforge[cpm]).",
    )
    args = parser.parse_args(argv)

    try:
        payload = _load_input(args.input)
        if args.embedding_backend is not None:
            payload.setdefault("options", {})["embedding_backend"] = args.embedding_backend
        if args.embedding_model is not None:
            payload.setdefault("options", {})["embedding_model"] = args.embedding_model
        if args.sparse_top_k is not None:
            payload.setdefault("options", {})["sparse_top_k"] = args.sparse_top_k
        if args.max_depth is not None:
            payload.setdefault("options", {})["max_depth"] = args.max_depth
        if args.min_recurse_members is not None:
            payload.setdefault("options", {})["min_recurse_members"] = args.min_recurse_members
        if args.target_layer_min is not None:
            payload.setdefault("options", {})["target_layer_count_min"] = args.target_layer_min
        if args.target_layer_max is not None:
            payload.setdefault("options", {})["target_layer_count_max"] = args.target_layer_max
        if args.community_method is not None:
            payload.setdefault("options", {})["community_method"] = args.community_method
        result = run(payload)
        maybe_warn_backend_quality(payload, result)
        out = json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None)
        sys.stdout.write(out + "\n")
        return 0
    except Exception as e:  # noqa: BLE001  — CLI surface, must not crash
        out = json.dumps(_error_payload(e), ensure_ascii=False, indent=2 if args.pretty else None)
        sys.stdout.write(out + "\n")
        return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
