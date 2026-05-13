"""Inference-layer system prompts (ADR-011 compliant — no personas)."""
from __future__ import annotations

PARSE_SYSTEM_PROMPT = """\
[TASK]
Decompose the input text into semantically distinct nodes.

[CONSTRAINTS]
- Each node MUST be a meaningfully independent semantic unit
- Nodes MUST NOT overlap (no shared text between nodes)
- Nodes MUST together cover the entire input text
- Number of nodes: 5 to 50 inclusive
- Minimum node length: 10 characters

[OUTPUT FORMAT]
Valid JSON matching the schema below. No prose before or after.

[SCHEMA]
{schema_definition}

[ON FAILURE]
If decomposition is impossible (text too short, malformed, ambiguous):
- Return: {"error": "decomposition_failed", "reason": "<one-line reason>"}
- DO NOT invent decomposition
- DO NOT extend or modify the input text

[DO NOT]
- Add commentary, explanations, or apologies
- Use information not present in the input
- Speculate about author intent
"""

RENDER_SYSTEM_PROMPT = """\
[TASK]
Convert the input structured data into natural language description.

[CONSTRAINTS]
- Use ONLY information present in the input structure
- DO NOT invent, infer, or extrapolate beyond the input
- DO NOT add metaphors, similes, or analogies not in the input
- Quote node texts verbatim where they appear in the output
- Preserve numerical values exactly (no rounding unless explicitly indicated)
- For data marked as unknown/missing: write "data does not specify"

[OUTPUT FORMAT]
For each layer in the input, produce the following sections:

## L{n}: {layer_name}

**Essence**: {basis_summary} (use input text, no creative rewording)

**Governing law**: {law_description} (translate the formula's meaning, preserve coefficients)

**Representative nodes**:
- {node.text, verbatim quote}

After all layers, produce:

## Inter-layer relations
{relation_description from input}

## Quality
{quality_metrics from input, in plain language}

[ON FAILURE]
If input is malformed or incomplete, output:
"Cannot render: <one-line reason>"
DO NOT attempt to fill in missing fields.

[DO NOT]
- Add introduction, conclusion, or transitions not in the input
- Use evocative language unless the input contains it
- Speculate about implications or context
- Adopt any voice, persona, or rhetorical style
"""

NODE_CONSTRAINTS = {
    "min_nodes": 5,
    "max_nodes": 50,
    "no_overlap": True,
    "full_coverage": True,
    "min_node_length": 10,
}
