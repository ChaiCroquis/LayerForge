# 05b. Skill-based Integration Design

> Status: v5 で新設 (ADR-014 に基づく)
> 関連: 05_integration_design.md (旧スタンドアロン版、互換性のため残置)

ADR-014 に基づき、LayerForge を Claude Code skill として実装する場合の設計。
これが**第一の実装形態**であり、05 のスタンドアロン版は将来オプションとして留保。

---

## 構造の全体像

```
~/.claude/skills/layerforge/
├── SKILL.md                  # Claude への指示書（推論層相当）
├── core/                     # 決定論コア (Python パッケージ)
│   ├── __init__.py
│   ├── constants.py          # Cowan 4±1 等の定数
│   ├── scale_finder.py       # F1.4 二分探索
│   ├── hierarchical.py       # F1.3 HERCULES adapted
│   ├── distillation.py       # F2.6 SCA
│   ├── modularity.py         # F4.6 Newman + spectral
│   ├── schema.py             # frozen dataclass の境界 schema
│   └── pipeline.py           # F5 layerforge_core
├── tests/                    # pytest (決定論コアの検証)
│   ├── conftest.py
│   ├── axioms/               # §04 公理テスト
│   ├── integration/
│   └── boundary/
├── cli/                      # SKILL.md から呼び出される CLI
│   ├── decompose.py          # Phase 2a: 自然言語整理
│   └── decide.py             # Phase 2b: 認知補助具
└── templates/                # 出力テンプレート
    ├── layer_summary.md      # レイヤー要約のテンプレート
    └── decision_list.md      # 決定リストのテンプレート
```

---

## 動作モデル

### Phase 2a: 自然言語整理

```
[開発者] → Claude Code に「このテキストを LayerForge で整理して」
  ↓
[Claude (Claude Code 内)] が SKILL.md を読む
  ↓
SKILL.md の指示に従い:
  1. テキストを意味的ノードに分解
     → Claude が JSON 形式で nodes.json を一時ファイルに書き出す
  2. embedding 計算 + 決定論コア実行
     → bash: python -m layerforge.cli.decompose nodes.json > result.json
  3. result.json を読んで、テンプレートに従って自然な文章を組み立てる
  4. 開発者に整理結果を提示
```

### Phase 2b: 認知補助具

```
[開発者] → Claude Code に「LayerForge プロジェクトを立ち上げたい」
  ↓
[Claude (Claude Code 内)] が SKILL.md を読む
  ↓
SKILL.md の指示に従い:
  1. タスクから「関連する決定群」を Claude が列挙
     → decisions.json に書き出す
  2. 決定空間を embedding + 決定論コアで分解
     → bash: python -m layerforge.cli.decide decisions.json > layers.json
  3. layers.json を読んで、「今開くレイヤー」の決定リストを出力
     → 「これだけ決めればいい」を開発者に提示
```

両者とも、**Boundary 1, 2 は Claude が SKILL.md の指示に従って実行**する。Python コードによる API クライアントは不要。

---

## SKILL.md のドラフト

実装の中心成果物。以下は v5 時点のドラフト案。

```markdown
# LayerForge Skill

## Purpose
Decompose natural language input into 4±1 hierarchical layers
using deterministic core, with Claude handling the language boundaries.

## When to use
- User asks to "整理して" / "organize" / "decompose" with LayerForge mentioned
- User asks for "決定を整理" / "what to decide first" (Phase 2b mode)
- Slash command: /layerforge or /lf-decide

## Workflow

### Mode A: Natural Language Decomposition

[TASK]
Decompose the user's input text into semantically distinct nodes,
then pass through the deterministic core, then render the result.

[STEP 1: Node extraction]
Read the input text. Identify semantically independent nodes.

Constraints:
- Each node: a meaningfully independent unit (1-3 sentences typical)
- Nodes MUST NOT overlap
- Nodes together MUST cover the entire input text
- Number of nodes: 5 to 50
- Minimum node length: 10 characters

Output format: JSON to a temporary file
```json
{
  "nodes": [
    {"id": "n1", "text": "..."},
    {"id": "n2", "text": "..."},
    ...
  ]
}
```

[STEP 2: Invoke deterministic core]
Use bash tool:
$ python -m layerforge.cli.decompose <nodes.json> > <result.json>

The core handles:
- Embedding computation
- Similarity matrix
- 4±1 scale search
- HERCULES hierarchical clustering
- Newman modularity check
- SCA distillation per layer

[STEP 3: Render]
Read result.json. For each layer, write:

## L{n}: {layer_name_inferred_from_basis}

**Essence**: {basis nodes summarized in 1-2 sentences,
              using their text verbatim where possible}

**Representative nodes**:
- {node.text quoted verbatim}

After all layers:

## Inter-layer relations
{Relations described in plain language}

## Quality
- Modularity: {Q}
- Layer count: {n_layers} (within 4±1: {is_within})
- Scale coefficient: {theta}

[STEP 4: On failure]
If decomposition fails (NoValidScaleError):
- Report: "問題設定が4±1に収まらない構造を持っています"
- Suggest: "より絞った範囲を指定するか、上位概念から分解し直してください"

[CONSTRAINTS]
- Do NOT invent information not present in the input text
- Do NOT use evocative language not present in the original
- Quote node texts verbatim
- Preserve numerical values from result.json exactly
- If a value is missing in result.json, write "data does not specify"

[DO NOT]
- Adopt any persona ("As an expert...", "I am an analyst...")
- Add introductions or conclusions not derived from the data
- Speculate beyond what the deterministic core produced

---

### Mode B: Decision Decomposition (Phase 2b)

[TASK]
Given a high-level task, identify "decisions to make right now" 
in 4±1 layers, and mark deeper layers as "defer until needed".

[STEP 1: Decision enumeration]
Read the user's task description.
Enumerate all decisions that would be needed to complete the task.

Constraints:
- Each decision: a single yes/no or choice point
- 10 to 50 decisions typically
- Include both "obvious" and "subtle" decisions

Output to: decisions.json
```json
{
  "task": "...",
  "decisions": [
    {"id": "d1", "text": "..."},
    {"id": "d2", "text": "..."},
    ...
  ]
}
```

[STEP 2: Layer decomposition]
$ python -m layerforge.cli.decide <decisions.json> > <layers.json>

[STEP 3: Open/close judgment]
For each layer, judge:
- Open: decisions in this layer should be made now
- Defer: decisions in this layer can wait until upper layers are decided

Rule (deterministic, computed by core):
- L1 (highest abstraction): always open
- L2-L3: open if L1 decisions are unsettled
- L4+: defer

[STEP 4: Render]

# Decision integration for: {task}

## To decide now ({count} items, within 4±1):

### L1: {layer_name}
- [ ] {decision.text}

### L2: {layer_name}
- [ ] {decision.text}

## Deferred (will become relevant once above are settled):
- {layer_name}: {sample decisions, count}
- ...

To reopen later: invoke with --open <layer_name>
```

---

## ファイル受け渡し方式の選定

Claude Code が core/ を呼ぶ方法は2つ：

### 方式A: 一時ファイル経由 (推奨)
```
Claude → /tmp/layerforge_nodes_<uuid>.json (書き出し)
       → bash: python -m layerforge.cli.decompose <file> > <result>
       → /tmp/layerforge_result_<uuid>.json (読み込み)
       → Claude が render
```

メリット:
- バイナリ embedding を JSON で受け渡せる (base64 等)
- デバッグ時に中間ファイルを確認できる
- Claude Code のサンドボックスに馴染む

### 方式B: stdin/stdout 直接
```
Claude → echo '...' | python -m layerforge.cli.decompose > result.json
```

メリット:
- 中間ファイル不要、クリーン

デメリット:
- 大きな embedding データで標準入出力が詰まる可能性
- デバッグしにくい

→ 推奨: **方式A** (実用性と保守性)

---

## CLI インターフェース仕様

### `layerforge.cli.decompose`

```bash
$ python -m layerforge.cli.decompose <nodes.json>
```

入力 (`nodes.json`):
```json
{
  "nodes": [
    {"id": "n1", "text": "..."},
    ...
  ],
  "options": {
    "target_layer_count_min": 3,
    "target_layer_count_max": 5,
    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
    "random_seed": 42
  }
}
```

出力 (stdout、JSON):
```json
{
  "status": "ok",
  "layers": [
    {
      "id": 0,
      "member_node_ids": ["n1", "n5", ...],
      "basis_node_ids": ["n1"],
      "representation_summary": "...",
      "purity": 0.85
    },
    ...
  ],
  "inter_layer_relations": [...],
  "quality_metrics": {
    "modularity": 0.78,
    "layer_count": 4,
    "scale_coefficient": 0.42,
    "is_within_4_plus_minus_1": true,
    "quality_class": "good"
  }
}
```

エラー時:
```json
{
  "status": "error",
  "error_type": "NoValidScaleError",
  "message": "4±1 に収まる scale 係数が見つかりません",
  "diagnostic": {
    "similarity_stats": {...},
    "attempted_thresholds": [...]
  }
}
```

### `layerforge.cli.decide`

```bash
$ python -m layerforge.cli.decide <decisions.json>
```

入力フォーマット、出力フォーマットは decompose と類似 (詳細は Phase 2b 実装時)。

---

## エラーハンドリング戦略

skill 形態では、エラーハンドリングは **2段構え**:

### 段1: 決定論コア内部のエラー
- 例外を上げる: `NoValidScaleError`, `SeparationQualityError`
- JSON 出力では `status: "error"` で表現
- Claude が JSON を読んで、ユーザーに自然な言葉で報告

### 段2: Claude による解釈エラー
- SKILL.md の制約に違反した出力をしてしまった場合
- 例: ノード化で重複が出る、文字数違反 等
- Claude が自分で検知して retry する (Claude Code の自然な挙動)
- Claude 自身が retry しても解決しない場合は、開発者に質問する

スタンドアロン版で必要だった**明示的な retry/fallback ロジック**は不要 (ADR-008 の緩和)。

---

## テスト戦略 (skill 形態での pytest)

決定論コアは従来通り pytest で検証可能。skill 形態固有のテスト:

### CLI テスト
```python
def test_cli_decompose_with_synthetic_data():
    """CLI コマンドが期待通りの JSON を出力する"""
    input_json = '{"nodes": [...]}'
    result = subprocess.run(
        ["python", "-m", "layerforge.cli.decompose"],
        input=input_json,
        capture_output=True,
        text=True,
    )
    output = json.loads(result.stdout)
    assert output["status"] == "ok"
    assert 3 <= output["quality_metrics"]["layer_count"] <= 5
```

### JSON Schema 検証テスト
```python
def test_cli_output_schema():
    """CLI 出力が事前定義 schema に合致"""
    output = run_cli_with_test_data()
    jsonschema.validate(output, LAYERFORGE_OUTPUT_SCHEMA)
```

### SKILL.md 自体のテスト (オプション)
- SKILL.md を Claude (別セッション) に読ませて、動作を再現できるかを確認
- これは半自動テスト、CI 化は困難
- 手動回帰テストとして実施

---

## philosophy filter との並列構造

開発者の既存資産との配置:

```
~/.claude/
├── profile/
│   └── cognitive_load_principles.md     # 既存 (judgment 用)
├── skills/
│   ├── secretary/
│   │   └── SKILL.md (Rule 6 含む)        # 既存 (philosophy filter 実装)
│   └── layerforge/                      # 新規
│       ├── SKILL.md                     # 階層分解の指示
│       ├── core/                        # 決定論実装
│       ├── tests/
│       ├── cli/
│       └── templates/
└── decisions/
    ├── 2026-05-05_philosophy-as-judgment-filter.md  # 既存
    └── 2026-XX-XX_layerforge-skill.md   # 将来追加
```

**philosophy filter**: 判断の物理層実装 (やる/やらない/AI委譲/捨てる)
**LayerForge**: 階層分解の物理層実装 (4±1 レイヤーに自動分解)

両者は **直交かつ補完的**:
- philosophy filter は「個別の判断」を機械化
- LayerForge は「判断の集合」を階層化

組み合わせ例:
```
開発者のタスク (例: 「LayerForge を立ち上げる」)
  ↓
LayerForge (認知補助具) で 4±1 レイヤーに分解
  ↓ 各レイヤーで決定すべき決定群を得る
philosophy filter が各決定を分類
  ↓
- 機械検証可能 → AI実行
- 100%再現可能 → AI実行
- 業務領域 → user
- 認知負荷削減に効く → AI default
- 効かない → 捨てる
  ↓
開発者が判断するのは「残った user 案件」だけ
```

これが開発者の動機階層 (楽したい) を最も貫徹する運用形態。

---

## 旧 05 (スタンドアロン版) との比較

| 項目 | 05 (スタンドアロン) | 05b (skill, 本書) |
|---|---|---|
| 実装形態 | pip ライブラリ | Claude Code skill |
| LLM クライアント | anthropic SDK 実装 | 不要 (Claude が直接) |
| 配布性 | 高 (pip install で誰でも) | 低 (開発者個人) |
| 工数 | 大 (Boundary 実装が重い) | 小 (SKILL.md 主体) |
| API コスト | あり | なし (Claude Code 月額のみ) |
| データプライバシー | API 経由 | ローカル完結 |
| philosophy filter との整合 | 中 | 完全並列 |
| Phase 2a 工数 | 2-3週間 | 数日 |

**旧 05 はスタンドアロン需要が出た際のため保持**。
基本実装は本書 (05b) に従う。

---

## 開発フェーズへの影響

(ADR-010 から ADR-014 への移行による更新)

### Phase 1: 公理層実装 (変更なし)
- 4-6 週間
- 採用論文の数式を pytest 化
- core/ の決定論部分を全実装
- ※ 推論層 stub は不要 (Claude が直接担当するため)

### Phase 2a: SKILL.md ドラフト + Claude Code 統合 (大幅短縮)
- **数日** (旧 2-3 週間から短縮)
- SKILL.md の Mode A (自然言語整理) を書く
- CLI インターフェース (`layerforge.cli.decompose`) を実装
- 実環境でテスト

### Phase 2b: 認知補助具 (変更なし、2-3週間)
- SKILL.md の Mode B (決定整理) を書く
- CLI (`layerforge.cli.decide`) を実装
- ドッグフーディング開始

### Phase 3: 実証実験 (変更なし)
- ADR-013 の認知補助具ドッグフーディング結果を実証データに

**総工数**: 旧計画 (6-12週間) → 新計画 (約5-9週間) で短縮。

---

## Hooks integration (v5 追記)

SKILL.md が主役だが、Claude Code の **hooks** で運用フローを強化する。
hooks は `~/.claude/settings.json` の `hooks` フィールドに shell command として登録される CC ネイティブ機構。

### 採用する hooks

| Hook event | Command (概要) | 目的 |
|---|---|---|
| `UserPromptSubmit` | `python -m layerforge.cli.route_prompt` (stdin から prompt 受領、`layerforge:` プレフィックスや特定キーワードを検知) | skill 自動起動の補助 (CC slash command を補完) |
| `PostToolUse` (matcher: `Bash`) | `python -m layerforge.cli.validate_output` | layerforge CLI が出力した JSON が L2 schema を満たしているか機械検証 (universal CLAUDE.md 完了報告フォーマット準拠) |
| `Stop` | `python -m layerforge.cli.sha_seal --session` | セッション内で生成された CoreResult JSON の sha256 を `.layerforge_seal.json` に記録 (L1/L3 検証用) |

### settings.json での登録例

```jsonc
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python -m layerforge.cli.validate_output",
            "timeout": 5
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python -m layerforge.cli.sha_seal --session",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

### hook の責務分担原則 (CLAUDE.md 禁則 1 準拠)

- hooks は **検知 + 強制** 専用 (「気をつける」を Hook 化したもの)
- 判断・解釈・修正は SKILL.md (Claude) 側で行う
- hook が fail → Claude が修正 retry → 2回目以降の同種失敗で hook が Stop Gate

### 既存 hooks との非干渉

開発者既存の `stop_dispatcher.py` (秘書 sycophancy 検知等) と LayerForge hooks は **直列実行**で衝突しない。
両者は別 dispatcher として `settings.json` に並列登録する。

---

## Open questions (skill 形態固有)

1. **複数 Claude Code セッション間での persistence**: 認知補助具で「閉じたレイヤー」を別セッションで再オープンする場合の状態保持 → 簡単な json ファイルで足りるか?
2. **テンプレートの言語**: SKILL.md は日本語? 英語? Claude は両対応だが、保守性で選ぶ
3. **slash command の設計**: `/lf` `/layerforge` `/lf-decide` 等の命名規約
4. **既存 secretary skill との連携**: Rule 6 で LayerForge を呼ぶ場合の判定条件
