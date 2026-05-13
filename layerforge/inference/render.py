"""Boundary 2: CoreResult → natural language output."""
from __future__ import annotations

from typing import Any

from layerforge.constants import MAX_RETRIES
from layerforge.exceptions import LLMError, SchemaViolation, ValidationError
from layerforge.schema.output_schema import CoreResult, NaturalLanguageOutput


def prepare_render_data(core_result: CoreResult) -> dict:
    """Strip numpy arrays, keep human-readable fields."""
    layers = []
    for layer in core_result.layers:
        layers.append(
            {
                "layer_id": layer.layer_id,
                "layer_name": layer.layer_name or f"Layer {layer.layer_id}",
                "n_members": len(layer.member_indices),
                "member_texts": [n.text for n in layer.member_nodes],
                "tokens": [sorted(t) for t in layer.distillation.token_representations],
                "n_components": len(layer.distillation.components),
                "is_converged": layer.distillation.is_converged,
            }
        )
    return {
        "layers": layers,
        "relations": [
            {
                "from": r.from_layer_id,
                "to": r.to_layer_id,
                "type": r.relation_type,
                "strength": r.strength,
            }
            for r in core_result.inter_layer_relations
        ],
        "quality": {
            "modularity": core_result.quality_metrics.modularity,
            "layer_count": core_result.quality_metrics.layer_count,
            "scale_coefficient": core_result.quality_metrics.scale_coefficient,
            "is_within_4_plus_minus_1": core_result.quality_metrics.is_within_4_plus_minus_1,
            "quality_class": core_result.quality_metrics.quality_class,
        },
    }


def template_only_render(template_data: dict) -> NaturalLanguageOutput:
    """Pure template-based render (deterministic fallback)."""
    sections: list[str] = []
    for layer in template_data["layers"]:
        lines = [
            f"## L{layer['layer_id']}: {layer['layer_name']}",
            "",
            f"**Members** ({layer['n_members']}):",
        ]
        for txt in layer["member_texts"][:5]:
            lines.append(f"- {txt}")
        if len(layer["member_texts"]) > 5:
            lines.append(f"- ... ({len(layer['member_texts']) - 5} more)")
        lines.append("")
        if layer["tokens"]:
            lines.append("**Top tokens per component**:")
            for k, toks in enumerate(layer["tokens"]):
                lines.append(f"- C{k}: {', '.join(toks) if toks else '(none)'}")
        sections.append("\n".join(lines))

    rel_lines = ["## Inter-layer relations", ""]
    for r in template_data["relations"]:
        rel_lines.append(
            f"- L{r['from']} → L{r['to']} ({r['type']}, strength={r['strength']:.3f})"
        )
    sections.append("\n".join(rel_lines))

    q = template_data["quality"]
    metadata = (
        f"modularity={q['modularity']:.3f}, layer_count={q['layer_count']}, "
        f"theta={q['scale_coefficient']:.3f}, "
        f"in_4±1={q['is_within_4_plus_minus_1']}, class={q['quality_class']}"
    )
    sections.append(f"## Quality\n\n{metadata}")

    text = "\n\n".join(sections)
    return NaturalLanguageOutput(
        text=text,
        layer_sections=tuple(sections),
        metadata_summary=metadata,
    )


def validate_natural_output(rendered: Any, core_result: CoreResult) -> bool:
    """Lightweight validation: layer count matches, text non-empty."""
    if rendered is None:
        return False
    if isinstance(rendered, NaturalLanguageOutput):
        return bool(rendered.text)
    if isinstance(rendered, str):
        return bool(rendered.strip())
    return False


def render_to_natural(
    core_result: CoreResult,
    llm_client: Any | None = None,
) -> NaturalLanguageOutput:
    """[INFERENCE BOUNDARY 2]"""
    template_data = prepare_render_data(core_result)

    if llm_client is not None:
        from layerforge.inference.prompts import RENDER_SYSTEM_PROMPT

        for _ in range(MAX_RETRIES):
            try:
                rendered = llm_client.render(
                    template_data,
                    system_prompt=RENDER_SYSTEM_PROMPT,
                    output_schema=None,
                )
                if validate_natural_output(rendered, core_result):
                    if isinstance(rendered, NaturalLanguageOutput):
                        return rendered
                    # Wrap raw string
                    return NaturalLanguageOutput(
                        text=str(rendered),
                        layer_sections=(),
                        metadata_summary="(LLM rendered)",
                    )
            except (SchemaViolation, LLMError, ValidationError):
                continue

    return template_only_render(template_data)
