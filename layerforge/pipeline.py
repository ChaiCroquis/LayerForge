"""LayerForge pipeline entry point (docs/05 §統合フロー擬似コード)."""
from __future__ import annotations

from typing import Any

import numpy as np
import scipy.sparse as sp

from dataclasses import replace

from layerforge.constants import (
    DETERMINISTIC_SEED,
    LAYER_COUNT_MAX,
    LAYER_COUNT_MIN,
    MAX_RECURSION_DEPTH,
)
from layerforge.core.distillation import distill_layer
from layerforge.core.hierarchical import hierarchical_kmeans
from layerforge.core.modularity import (
    can_subdivide_layer,
    classify_separation_quality,
    compute_modularity,
)
from layerforge.core.relations import (
    extract_inter_layer_relations,
    hierarchy_to_layer_summaries,
)
from layerforge.core.scale_finder import find_valid_scale, is_layer_count_valid
from layerforge.exceptions import (
    LLMError,
    NoValidScaleError,
    SeparationQualityError,
)
from layerforge.inference.parse import parse_to_structure, parse_to_structure_mechanical
from layerforge.inference.render import render_to_natural
from layerforge.schema.input_schema import FormulationInput, RawInput
from layerforge.schema.output_schema import (
    CoreResult,
    NaturalLanguageOutput,
    QualityMetrics,
)


def layerforge_core(
    input_data: FormulationInput,
    seed: int = DETERMINISTIC_SEED,
    strict_quality: bool = False,
    target_range: tuple[int, int] = (LAYER_COUNT_MIN, LAYER_COUNT_MAX),
    community_method: str = "newman",
) -> CoreResult:
    """[DETERMINISTIC CORE] Same input → same output (F5).

    ``target_range`` defaults to Cowan's 4±1 = (3, 5). Override for
    sensitivity analysis — e.g., (1, 2) for very coarse, (10, 20) for
    fine-grained. This breaks the cognitive ergonomics guarantee but lets
    you study K's effect on compression / routing accuracy.

    ``community_method`` selects the community-detection backend:
      - ``"newman"`` (default): θ-threshold + KMeans on embeddings;
        Q (Newman modularity) used as quality metric. Subject to
        Fortunato-Barthélemy resolution limit (docs/08 §1.4).
      - ``"cpm"``: Leiden-CPM on the similarity graph (Traag 2011);
        resolution-limit-free via subgraph-invariance. Requires the
        optional ``cpm`` extra (``pip install layerforge[cpm]``).
        See docs/08 §1.6 and ADR-017 for the rationale.
    """
    if community_method not in ("newman", "cpm"):
        raise ValueError(
            f"community_method must be 'newman' or 'cpm', got {community_method!r}"
        )

    cpm_h_value: float | None = None

    if community_method == "cpm":
        from layerforge.core.community import detect_communities_cpm

        hierarchy, cpm_h_value, gamma = detect_communities_cpm(
            similarity=input_data.similarity_matrix,
            embeddings=input_data.embeddings,
            target_range=target_range,
            seed=seed,
        )
        n_layers = len(hierarchy.layers)
        theta = gamma  # scale_coefficient carries γ for CPM (vs θ for Newman)
    else:
        # 1. Find scale θ giving target K
        theta, n_layers = find_valid_scale(
            input_data.similarity_matrix,
            target_range=target_range,
        )

        # 2. Hierarchical clustering at K = n_layers
        hierarchy = hierarchical_kmeans(
            embeddings=input_data.embeddings,
            k=n_layers,
            use_resampling=True,
            random_state=seed,
        )

    # 3. Modularity quality check (Q on the threshold graph for both methods,
    #    so CPM and Newman results are cross-comparable).
    # For CPM we still use the original similarity but no θ was chosen — pass
    # 0.0 as the threshold (keeps all positive-weight edges).
    q_threshold = theta if community_method == "newman" else 0.0
    Q = compute_modularity(
        input_data.similarity_matrix,
        hierarchy.flat_labels,
        threshold=q_threshold,
    )
    quality_class = classify_separation_quality(Q)
    if quality_class == "poor" and strict_quality:
        raise SeparationQualityError(Q, threshold=0.3)

    # 4. Indivisibility flags per layer
    # Sparse path: skip the eigh-based indivisibility check (would densify
    # each per-layer subgraph). Flag conservatively as "not indivisible"
    # since we don't have evidence either way.
    indiv_flags: list[bool] = []
    sim = input_data.similarity_matrix
    is_sparse_sim = sp.issparse(sim)
    for layer in hierarchy.layers:
        idx = list(layer.member_indices)
        if len(idx) < 2:
            indiv_flags.append(True)
            continue
        if is_sparse_sim:
            indiv_flags.append(False)  # unknown; sparse spectral skipped
            continue
        sub = sim[np.ix_(idx, idx)]
        indiv_flags.append(not can_subdivide_layer(sub, threshold=theta))

    # 5. SCA distillation per layer
    distillations = []
    for layer in hierarchy.layers:
        idx = list(layer.member_indices)
        layer_nodes = tuple(input_data.nodes[i] for i in idx)
        layer_embeddings = input_data.embeddings[idx]
        # Adapt SCA min_cluster_size for small layers (paper default 100)
        adaptive_mcs = max(2, len(idx) // 4)
        adaptive_ms = max(1, adaptive_mcs // 2)
        distillation = distill_layer(
            layer_nodes=layer_nodes,
            embeddings=layer_embeddings,
            min_cluster_size=adaptive_mcs,
            min_samples=adaptive_ms,
            random_state=seed,
        )
        distillations.append(distillation)

    # 6. Pack layers + inter-layer relations
    layer_summaries = hierarchy_to_layer_summaries(
        hierarchy=hierarchy,
        nodes=input_data.nodes,
        distillations=tuple(distillations),
    )
    relations = extract_inter_layer_relations(layer_summaries)

    return CoreResult(
        layers=layer_summaries,
        inter_layer_relations=relations,
        quality_metrics=QualityMetrics(
            modularity=Q,
            layer_count=n_layers,
            scale_coefficient=theta,
            is_within_4_plus_minus_1=is_layer_count_valid(n_layers),
            quality_class=quality_class,
            indivisibility_flags=tuple(indiv_flags),
            community_method=community_method,
            cpm_h=cpm_h_value,
        ),
    )


DEFAULT_MIN_RECURSE_MEMBERS: int = 8


def _sub_formulation(
    parent: FormulationInput, member_indices: tuple[int, ...]
) -> FormulationInput:
    """Build a FormulationInput restricted to the given member indices."""
    from layerforge.core.scale_finder import compute_initial_scale
    from layerforge.schema.input_schema import ScaleParams

    idx = list(member_indices)
    sub_nodes = tuple(parent.nodes[i] for i in idx)
    sub_embeds = parent.embeddings[idx]
    if sp.issparse(parent.similarity_matrix):
        sub_sim = parent.similarity_matrix[idx, :][:, idx].tocsr()
    else:
        sub_sim = parent.similarity_matrix[np.ix_(idx, idx)]
    return FormulationInput(
        nodes=sub_nodes,
        embeddings=sub_embeds,
        similarity_matrix=sub_sim,
        initial_scale=ScaleParams(threshold=compute_initial_scale(sub_sim)),
    )


def layerforge_core_recursive(
    input_data: FormulationInput,
    seed: int = DETERMINISTIC_SEED,
    max_depth: int = 1,
    min_recurse_members: int = DEFAULT_MIN_RECURSE_MEMBERS,
    strict_quality: bool = False,
    target_range: tuple[int, int] = (LAYER_COUNT_MIN, LAYER_COUNT_MAX),
    community_method: str = "newman",
    _current_depth: int = 0,
) -> CoreResult:
    """Recursive F3.4 decomposition (4×4×4×4 = 256 nodes max).

    Decomposes each layer's members into sub-layers until any of:
      - depth reaches ``max_depth`` (1 = flat, current default behavior)
      - depth reaches the global hard limit ``MAX_RECURSION_DEPTH=4``
      - layer has fewer than ``min_recurse_members`` members
      - layer is Newman-indivisible (β₁ ≤ 0) — dense path only
      - sub-decomposition raises ``NoValidScaleError``

    Returns a ``CoreResult`` whose ``layers[i].children`` is recursively
    populated. ``layers[i].depth`` reflects the layer's level in the tree.
    """
    effective_max = min(max_depth, MAX_RECURSION_DEPTH)
    if effective_max < 1:
        raise ValueError(f"max_depth must be >= 1, got {max_depth}")

    base = layerforge_core(
        input_data,
        seed=seed,
        strict_quality=strict_quality,
        target_range=target_range,
        community_method=community_method,
    )
    base_layers = tuple(
        replace(layer, depth=_current_depth) for layer in base.layers
    )

    if _current_depth + 1 >= effective_max:
        return CoreResult(
            layers=base_layers,
            inter_layer_relations=base.inter_layer_relations,
            quality_metrics=base.quality_metrics,
        )

    # NOTE: we intentionally do NOT pre-check ``indivisibility_flags`` here.
    # Those flags are computed at the parent's θ threshold, which separates
    # super-clusters; sub-clusters within a super often look indivisible at
    # that threshold but become divisible when ``layerforge_core`` re-runs
    # its own binary-search θ on the sub-input. ``NoValidScaleError`` is the
    # authoritative stop signal — caught below.
    new_layers: list = []
    for layer in base_layers:
        n_members = len(layer.member_indices)
        if n_members < min_recurse_members:
            new_layers.append(layer)
            continue
        # Try to recurse.
        try:
            sub_input = _sub_formulation(input_data, layer.member_indices)
            sub_result = layerforge_core_recursive(
                sub_input,
                seed=seed,
                max_depth=max_depth,
                min_recurse_members=min_recurse_members,
                strict_quality=strict_quality,
                target_range=target_range,
                community_method=community_method,
                _current_depth=_current_depth + 1,
            )
            new_layers.append(replace(layer, children=sub_result.layers))
        except NoValidScaleError:
            # Sub-set can't be decomposed into 4±1; keep as leaf.
            new_layers.append(layer)

    return CoreResult(
        layers=tuple(new_layers),
        inter_layer_relations=base.inter_layer_relations,
        quality_metrics=base.quality_metrics,
    )


def layerforge_pipeline(
    raw_input: RawInput,
    llm_client: Any | None = None,
    embedding_client: Any | None = None,
    seed: int = DETERMINISTIC_SEED,
    strict_quality: bool = False,
) -> NaturalLanguageOutput:
    """End-to-end pipeline (entry point)."""
    try:
        formulation_input = parse_to_structure(
            raw_input,
            llm_client=llm_client,
            embedding_client=embedding_client,
        )
    except LLMError:
        formulation_input = parse_to_structure_mechanical(raw_input)

    try:
        core_result = layerforge_core(
            formulation_input, seed=seed, strict_quality=strict_quality
        )
    except NoValidScaleError as e:
        return _diagnostic_output(str(e))

    return render_to_natural(core_result, llm_client=llm_client)


def _diagnostic_output(message: str) -> NaturalLanguageOutput:
    return NaturalLanguageOutput(
        text=f"## Diagnostic\n\n{message}",
        layer_sections=("## Diagnostic",),
        metadata_summary=f"diagnostic: {message}",
    )
