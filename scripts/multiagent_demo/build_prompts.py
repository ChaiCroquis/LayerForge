"""Build AI 2 prompts for multi-agent drift verification.

AI 1's verbose output is fixed; we build two parallel prompts for AI 2:
  - condition_a (Full):       full 15K AI 1 output + task
  - condition_b (LayerForge): only the CI/CD layer extracted by Mode C + task

The task explicitly forbids off-topic content. Drift = AI 2 violates the
restriction by including coverage / test-data / etc. content.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


# Same task text for both conditions — that's the controlled variable.
TASK_INSTRUCTION = """\
あなたは前述の「AI 1 の回答」を参考に、新規 Python プロジェクトの README に
書く **CI/CD セクション** を 200-300 単語で書いてください。

**厳格な制約**:
- CI/CD の話題だけを書く (GitHub Actions、workflow 設定、matrix build、
  artifact、その他 CI/CD インフラ関連)
- 以下のトピックは **別セクションで扱うので絶対に含めないこと**:
  - coverage 計測 / pytest-cov / Codecov
  - テストデータ管理 / fixtures / factories
  - エッジケース / 境界値テスト
  - ドキュメント / docstring / README の他セクション
  - コードレビュー / PR テンプレート
  - パフォーマンステスト / benchmark
- 「上記の制約に従い」のような meta-注記は書かないこと
- セクションタイトル "## CI/CD" を冒頭に置き、本文を続ける形式
"""


def main() -> int:
    out = Path(__file__).resolve().parent
    out.mkdir(exist_ok=True)

    full_response = (ROOT / "scripts/compress_demo/verbose_response.txt").read_text(encoding="utf-8")
    compressed = json.loads(
        (ROOT / "scripts/compress_demo/compressed_q2_mpnet.json").read_text(encoding="utf-8")
    )
    filtered_response = compressed["selected_text"]

    print(f"full       chars: {len(full_response):>6}")
    print(f"filtered   chars: {len(filtered_response):>6}")
    print(f"compression ratio: {len(filtered_response) / len(full_response):.3f}")

    # --- condition A: full ---
    prompt_a = f"""\
# AI 1 の回答 (verbose、複数トピック横断)

{full_response}

# 指示

{TASK_INSTRUCTION}
"""
    (out / "prompt_full.txt").write_text(prompt_a, encoding="utf-8")
    print(f"wrote prompt_full.txt ({len(prompt_a)} chars)")

    # --- condition B: LayerForge filtered ---
    prompt_b = f"""\
# AI 1 の回答 (LayerForge で CI/CD layer のみ抽出済)

{filtered_response}

# 指示

{TASK_INSTRUCTION}
"""
    (out / "prompt_filtered.txt").write_text(prompt_b, encoding="utf-8")
    print(f"wrote prompt_filtered.txt ({len(prompt_b)} chars)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
