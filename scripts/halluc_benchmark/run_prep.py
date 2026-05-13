"""Build all answer prompts (3 conditions) + report routing summary.

Outputs:
    scripts/halluc_benchmark/out/answer_prompt_full.txt
    scripts/halluc_benchmark/out/answer_prompt_layerforge.txt
    scripts/halluc_benchmark/out/answer_prompt_oracle.txt
    scripts/halluc_benchmark/out/routing.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.halluc_benchmark.build_prompts import build_answer_prompt
from scripts.halluc_benchmark.router import route_all


def main() -> int:
    out_dir = Path(__file__).resolve().parent / "out"
    out_dir.mkdir(exist_ok=True)

    print("[1/2] Routing corpus through LayerForge...")
    routing = route_all()
    print(f"  layer_count: {routing.quality_metrics['layer_count']}")
    print(f"  Q          : {routing.quality_metrics['modularity']:.3f} ({routing.quality_metrics['quality_class']})")
    for layer in routing.layers:
        member_themes = {pid[0] for pid in layer.passage_ids}
        print(f"  L{layer.layer_id}: {len(layer.passage_ids)} passages, themes={sorted(member_themes)}, ids={list(layer.passage_ids)}")

    print("\n  Question routes (q -> layer):")
    for qid, lid in routing.question_routes.items():
        print(f"    {qid} -> L{lid}")

    routing_data = {
        "quality_metrics": routing.quality_metrics,
        "layers": [
            {"layer_id": layer.layer_id, "passage_ids": list(layer.passage_ids)}
            for layer in routing.layers
        ],
        "question_routes": routing.question_routes,
    }
    (out_dir / "routing.json").write_text(
        json.dumps(routing_data, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print("\n[2/2] Building answer prompts for 3 conditions...")
    for condition in ("full", "layerforge", "oracle"):
        prompt = build_answer_prompt(condition, routing)
        path = out_dir / f"answer_prompt_{condition}.txt"
        path.write_text(prompt, encoding="utf-8")
        print(f"  wrote {path} ({len(prompt)} chars)")

    print("\nReady. Next: feed each prompt to an Agent subagent, collect JSON answers.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
