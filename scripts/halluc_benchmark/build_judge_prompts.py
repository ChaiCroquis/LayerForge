"""Build judge prompts from the answer files."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.halluc_benchmark.build_prompts import build_judge_prompt


def main() -> int:
    out_dir = Path(__file__).resolve().parent / "out"
    for condition in ("full", "layerforge", "oracle"):
        answers = json.loads((out_dir / f"answers_{condition}.json").read_text(encoding="utf-8"))
        prompt = build_judge_prompt(answers)
        (out_dir / f"judge_prompt_{condition}.txt").write_text(prompt, encoding="utf-8")
        print(f"wrote judge_prompt_{condition}.txt ({len(prompt)} chars)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
