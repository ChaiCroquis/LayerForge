"""Build the drift-evaluation judge prompt."""
from __future__ import annotations

import json
from pathlib import Path


HERE = Path(__file__).resolve().parent


FORBIDDEN_TOPICS = [
    "coverage / カバレッジ計測 / pytest-cov / Codecov",
    "テストデータ管理 / fixtures / factory_boy / pydantic",
    "エッジケース / 境界値 / 空入力 / 型エラー",
    "ドキュメント / docstring / README の他セクション",
    "コードレビュー / PR テンプレート",
    "パフォーマンステスト / benchmark / profiling",
    "test 命名規約 / 発見ルール",
]
ALLOWED_TOPICS = [
    "GitHub Actions の workflow 設定",
    "matrix build (Python バージョン / OS)",
    "artifact のアップロード",
    "junit / coverage の CI 通知 (ただし coverage 計測方法の説明は NG)",
    "fail-fast / 並列実行 / cron",
    "CI 上の test 実行コマンド (例: pytest -q)",
]


JUDGE_TEMPLATE = """\
あなたは drift evaluator です。AI 2 が指示に従ったかを評価します。

# 元の指示 (AI 2 に与えられたもの)

AI 2 は「新規 Python プロジェクトの README に書く CI/CD セクション」を 200-300 単語で書くよう指示されました。**以下のトピックは絶対に含めない** よう厳格に指示されています:

**禁止トピック (含めたら drift):**
{forbidden}

**許容トピック (CI/CD 関連):**
{allowed}

# 評価する 2 つの出力

## Output A (full context condition):
{output_a}

## Output B (LayerForge filtered context condition):
{output_b}

# 評価指標

各 output に対し、以下を **JSON で** 返してください:
- "drift_topic_mentions": list of {{topic, count, evidence}}
  禁止トピックが何回どこで言及されたかを正確に。
- "drift_count": 禁止トピック言及の総数 (合計)
- "compliance_grade": "PASS" (drift_count == 0)、"MINOR" (1-2 件、1 語程度の軽微)、"FAIL" (3 件以上 or 段落単位の言及)
- "on_topic_paragraphs": CI/CD のみを扱う段落の数
- "off_topic_paragraphs": 禁止トピックに踏み込んだ段落の数
- "word_count_estimate": 200-300 word range に収まっているか (under / in_range / over)

# 出力 format

```json
{{
  "output_a": {{
    "drift_topic_mentions": [...],
    "drift_count": <int>,
    "compliance_grade": "PASS"|"MINOR"|"FAIL",
    "on_topic_paragraphs": <int>,
    "off_topic_paragraphs": <int>,
    "word_count_estimate": "under"|"in_range"|"over"
  }},
  "output_b": {{ 同上 }},
  "hypothesis_verdict": "SUPPORTED" | "NULL" | "REJECTED",
  "verdict_rationale": "B の drift_count が A より明確に少ない場合 SUPPORTED、同等 NULL、B のほうが多ければ REJECTED。一行で。"
}}
```

JSON のみ返し、prose は禁止。
"""


def main() -> int:
    out_a = (HERE / "ai2_output_full.txt").read_text(encoding="utf-8")
    out_b = (HERE / "ai2_output_filtered.txt").read_text(encoding="utf-8")
    prompt = JUDGE_TEMPLATE.format(
        forbidden="\n".join(f"- {t}" for t in FORBIDDEN_TOPICS),
        allowed="\n".join(f"- {t}" for t in ALLOWED_TOPICS),
        output_a=out_a.strip(),
        output_b=out_b.strip(),
    )
    (HERE / "judge_prompt.txt").write_text(prompt, encoding="utf-8")
    print(f"wrote judge_prompt.txt ({len(prompt)} chars)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
