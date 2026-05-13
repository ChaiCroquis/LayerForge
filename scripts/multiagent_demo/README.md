# Multi-agent drift verification (H2)

LayerForge を multi-agent pipeline の中間 filter として配置し、下流 AI の
drift (指示外 topic への膨らみ) を抑制できるかを検証。

## 仮説 H2

**「AI 2 に full context を渡すと off-topic に drift する。LayerForge filter で渡すと、AI 2 は指定 topic に focused で出力する」**

## Setup

| 役割 | 内容 |
|---|---|
| AI 1 (既存) | `scripts/compress_demo/verbose_response.txt` — 8 トピック横断 verbose 回答 (10,512 chars) |
| LayerForge Mode C | mpnet model で CI/CD layer のみ抽出 → filtered (3,489 chars、ratio 0.33) |
| AI 2 (今回検証) | 「CI/CD セクションを 200-300 単語で。coverage/test data/edge cases 等は **絶対に含めるな**」 |

## Conditions

| 条件 | AI 2 への入力 |
|---|---|
| **A. Full** | AI 1 の全 10,512 chars + 指示 (prompt 11,036 chars) |
| **B. LayerForge filtered** | CI/CD layer のみ 3,489 chars + 指示 (prompt 4,027 chars) |

## Judge metric

LLM-as-judge subagent が両 output を評価:
- `drift_count`: 禁止トピックの言及回数
- `compliance_grade`: PASS / MINOR / FAIL
- `on_topic_paragraphs` / `off_topic_paragraphs`
- `word_count_estimate`: range 内か

## 結果

```json
{
  "output_a": {drift_count: 0, PASS, 5 on-topic / 0 off-topic, in_range},
  "output_b": {drift_count: 0, PASS, 5 on-topic / 0 off-topic, in_range},
  "hypothesis_verdict": "NULL",
  "rationale": "両 output とも禁止トピック言及 0 で同等、drift 差は観測されない。"
}
```

**両条件で完全 PASS、drift 差は無し**。

## 解釈

仮説 H2 は **null result**:
- AI 2 (subagent default = Sonnet 級) は、明示的な「含めるな」指示を full context でも遵守する
- LayerForge filter による behavioral 改善は **このセットアップでは観測不可**

ただし以下は事実として残る:
- ✓ token 削減: prompt が 11,036 → 4,027 chars (63% 削減) — **客観的に効く**
- ✓ AI 2 output 品質: 両者ほぼ同等 (filter で **劣化しない**)
- ✓ AI 2 latency: 入力小さい → 推論速い (subagent run 時間で観測可能)

つまり Mode C は AI 2 の **挙動を変えない** が **コストは下げる**。「behavioral guardrail」ではなく「cost optimizer」としての positioning が誠実。

## 3 つの実験の系列

| 実験 | 仮説 | 結果 |
|---|---|---|
| H1a 小規模 ハルシネーション | filter で AI 自己ハルシネーション減 | null (12/12 完全一致) |
| H1b 大規模 + Haiku | corpus 規模・モデルでも null | null (Haiku でも 12/12) |
| H2 multi-agent drift | filter で下流 AI drift 減 | **null (両 PASS, drift_count=0)** |

3 連続の null。

## 結論

**LayerForge の検証可能な客観的価値は以下に集約**:

| 価値主張 | 検証可能性 | 結果 |
|---|---|---|
| 算法実装の正しさ | 客観 (pytest) | ✓ 147 件 PASS |
| token / context 削減 | 客観 (chars) | ✓ 14-40% 圧縮 |
| 情報捏造ゼロ (subset 保証) | 客観 (subset test) | ✓ 機械検証済 |
| 質問→layer routing 精度 | 客観 (sim score) | ✓ 大型 model で正確 |
| ハルシネーション減 | 客観 (LLM-as-judge) | ✗ null × 3 |
| マルチエージェント drift 減 | 客観 (drift judge) | ✗ null |
| **human 認知負荷削減** | **主観 (本人運用)** | **未検証、ドッグフーディング待ち** |

「修正された LayerForge の核」:
- **AI を better にする tool ではない** (modern Claude が既に十分強い)
- **AI 出力の量を制御する tool** (cost reduction、認知負荷削減仮説)
- 後者の主観便益は本人運用でしか測れない
