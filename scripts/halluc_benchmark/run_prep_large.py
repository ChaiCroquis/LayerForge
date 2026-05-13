"""Build routing + 3-condition prompts for the LARGE (100-passage) corpus.

Outputs into scripts/halluc_benchmark/out_large/ to avoid clobbering the
small-corpus results.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np

from layerforge.cli.decompose import run as decompose_run
from layerforge.inference.embedding import SentenceTransformersEmbedding

from scripts.halluc_benchmark.corpus_large import (
    PASSAGES_LARGE,
    PASSAGE_BY_ID_LARGE,
    QUESTIONS_LARGE,
    QUESTION_BY_ID_LARGE,
)


EMBED_MODEL = "sentence-transformers/paraphrase-MiniLM-L3-v2"


def _normalize(vecs: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    safe = np.where(norms == 0, 1.0, norms)
    return vecs / safe


def _decompose_and_route():
    payload = {
        "nodes": [{"id": p.id, "text": p.text} for p in PASSAGES_LARGE],
        "options": {
            "embedding_backend": "sentence_transformers",
            "embedding_model": EMBED_MODEL,
            "random_seed": 42,
        },
    }
    result = decompose_run(payload)
    if result.get("status") != "ok":
        raise RuntimeError(f"decompose failed: {result}")

    embedder = SentenceTransformersEmbedding(model_name=EMBED_MODEL)
    passage_ids = [p.id for p in PASSAGES_LARGE]
    pid_to_idx = {pid: i for i, pid in enumerate(passage_ids)}
    passage_embeds = embedder.embed([p.text for p in PASSAGES_LARGE])

    centroids = []
    layer_ids = []
    layer_passages = {}
    for layer in result["layers"]:
        member_ids = list(layer["member_node_ids"])
        layer_passages[layer["id"]] = member_ids
        layer_ids.append(layer["id"])
        member_idx = [pid_to_idx[pid] for pid in member_ids]
        centroids.append(passage_embeds[member_idx].mean(axis=0))
    centroid_matrix = _normalize(np.stack(centroids))

    q_embeds = _normalize(embedder.embed([q.text for q in QUESTIONS_LARGE]))
    sims = q_embeds @ centroid_matrix.T
    chosen = np.argmax(sims, axis=1)

    routes = {QUESTIONS_LARGE[i].id: layer_ids[chosen[i]] for i in range(len(QUESTIONS_LARGE))}
    return result, layer_passages, routes


def _passages_block(pids: list[str]) -> str:
    if not pids:
        return "(no passages provided for this question.)"
    return "\n\n".join(f"[{p.id}] {p.text}" for p in (PASSAGE_BY_ID_LARGE[pid] for pid in pids))


def _build_answer_prompt(condition: str, routes: dict, layer_passages: dict) -> str:
    if condition == "full":
        return f"""\
You will answer {len(QUESTIONS_LARGE)} questions using ONLY the passages provided below.

# RULES
- Use ONLY information present in the passages. Do NOT use prior knowledge.
- If a question's answer is NOT in the passages, respond exactly: "Not in provided passages."
- Brief answer + cite passage ID.
- Do not invent details. The corpus is entirely fictional.
- Be especially careful with similar-looking entity names (e.g., luminoxide-XV vs luminoxide-XVI).

# PASSAGES
{_passages_block([p.id for p in PASSAGES_LARGE])}

# QUESTIONS
{chr(10).join(f"{q.id}: {q.text}" for q in QUESTIONS_LARGE)}

# OUTPUT FORMAT
JSON array; one object per question in order:
  "q": <id>, "answer": <text or "Not in provided passages.">, "source_passage_id": <id or null>
Return ONLY the JSON array. No prose.
"""

    # layerforge / oracle: per-question subset
    blocks = []
    for q in QUESTIONS_LARGE:
        if condition == "layerforge":
            pids = layer_passages[routes[q.id]]
        elif condition == "oracle":
            pids = [q.source_passage_id] if q.source_passage_id else []
        else:
            raise ValueError(condition)
        blocks.append(
            f"=== {q.id} ===\n"
            f"PASSAGES FOR THIS QUESTION:\n{_passages_block(pids)}\n\n"
            f"QUESTION: {q.text}"
        )
    return f"""\
You will answer {len(QUESTIONS_LARGE)} questions. Each has its OWN passage subset.

# RULES
- Use ONLY information from THAT question's passage subset. Not other questions' subsets.
- "Not in provided passages." when absent.
- Brief answer + cite passage ID.
- Corpus is fictional; do NOT use prior knowledge.

{chr(10).join(blocks)}

# OUTPUT FORMAT
JSON array, one object per question in order:
  "q": <id>, "answer": <text>, "source_passage_id": <id or null>
Return ONLY the JSON array. No prose.
"""


def main() -> int:
    out_dir = Path(__file__).resolve().parent / "out_large"
    out_dir.mkdir(exist_ok=True)

    print(f"# Large corpus: {len(PASSAGES_LARGE)} passages, {len(QUESTIONS_LARGE)} questions")
    print(f"# Total corpus char count: {sum(len(p.text) for p in PASSAGES_LARGE)} chars")

    print("\n[1/2] Routing via LayerForge...")
    result, layer_passages, routes = _decompose_and_route()
    qm = result["quality_metrics"]
    print(f"  layer_count: {qm['layer_count']}")
    print(f"  Q          : {qm['modularity']:.3f} ({qm['quality_class']})")
    for lid, pids in layer_passages.items():
        themes = {pid.split('-')[0] for pid in pids}
        print(f"  L{lid}: {len(pids)} passages, themes={sorted(themes)}")

    print("\n  Question routes (q -> layer, source-theme):")
    for q in QUESTIONS_LARGE:
        src_pid = q.source_passage_id
        src_theme = src_pid.split('-')[0] if src_pid else '-'
        print(f"    {q.id} -> L{routes[q.id]}  (source theme: {src_theme})")

    (out_dir / "routing.json").write_text(
        json.dumps({
            "quality_metrics": qm,
            "layer_passages": layer_passages,
            "question_routes": routes,
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("\n[2/2] Building answer prompts...")
    for condition in ("full", "layerforge", "oracle"):
        prompt = _build_answer_prompt(condition, routes, layer_passages)
        p = out_dir / f"answer_prompt_{condition}.txt"
        p.write_text(prompt, encoding="utf-8")
        print(f"  wrote {p} ({len(prompt)} chars)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
