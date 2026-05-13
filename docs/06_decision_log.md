# 06. Decision Log

LayerForge設計における主要判断の記録。実装時に「なぜこうなっているか」を再現可能にするための ADR。

---

## ADR-001: プロジェクト命名

**Decision**: 仮称 `LayerForge`

**Context**:
- Verification Forge との命名整合性
- 「レイヤーを鍛造する」というメタファーが構想と一致
- KDF / TIVE / Verification Forge と並列のサブシステムとして配置

**Alternatives considered**:
- SLDF (Scale-Layered Distillation Framework): 機能説明的で長い
- HLD (Hierarchical Layer Distillation): 略号で意味が伝わりにくい
- ScaleDistill: 機能の一部しか表現していない

**Status**: 仮確定（開発者の最終判断待ち）

---

## ADR-002: 推論層と決定論層の分離原則

**Decision**: 全フローを「境界で推論、内部で決定論」の原則で設計する。

**Context**:
- 開発者動機階層の中位「AIと決定論で分ける」と直接対応
- 品質要件「機械検証可能・100%再現可能」を達成するための必須条件
- 失敗モードの分離可能性（推論失敗とロジック失敗を区別）

**Implementation**:
- 推論層は2箇所のみ: ノード化（Step 2）と自然文章化（Step 7'）
- 中間処理は全て決定論
- 推論層の出力は schema 強制 (Structured Output API or constrained decoding)
- 推論失敗時は retry → fallback to template

**Consequence**:
- pytestで決定論層を完全カバー可能
- LLMバージョン依存を境界に閉じ込められる
- 推論層の品質が変動しても、決定論層の出力は不変

---

## ADR-003: 4±1 をスケール検出指標として採用

**Decision**: レイヤー数が `[3, 5]` の範囲に収まるスケール係数を、二分探索で自動的に発見する。

**Context**:
- Cowan (2001) のmagical number 4 が認知科学的裏付け
- 既存研究（HERCULES等）はクラスタ数を手動設定 or 内部メトリクスで最適化するが、4±1を観測指標として使う先行研究は未確認
- 開発者独自貢献の核心部分

**Mathematical formulation**:
```
find θ* such that:
  3 ≤ |layers(S, θ*)| ≤ 5
where:
  S = similarity matrix
  θ = relation threshold (scale coefficient)
  layers(S, θ) = clustering result with threshold θ
```

**Rejection condition**:
- どんなθでも `[3, 5]` に収まらない場合 → 問題設定が壊れている可能性
- これを診断指標としても活用する（後段で詳述）

**Alternatives considered**:
- 7±2 (Miller 1956): 古い値、Cowan以降は4が主流
- 完全自動（Silhouette score 等）: 認知負荷との接続が失われる

**Status**: 確定。実証実験で「4±1への収束率」を測定して妥当性検証する。

---

## ADR-004: 「重力アナロジー」の数式化方針

**Decision**: 比喩としては「重力係数」「引力」を維持するが、実装では `scale_coefficient` `relation_threshold` `weight_decay_alpha` 等の中立用語を使う。

**Context**:
- 既存研究との接続：RG (繰り込み群)、カーネル法、類似度関数で全て表現可能
- 重力という命名は直感的だが、論文化時には冗長
- 実装API名としては誤解を招く可能性

**Implementation**:
```python
@dataclass(frozen=True)
class ScaleParams:
    threshold: float          # θ: relation cutoff
    decay_exponent: float     # α: distance decay rate
    kernel_type: str          # φ: similarity weighting function
```

**比喩と実装の対応表**:
| 比喩 | 実装用語 |
|---|---|
| 重力係数 | scale_coefficient / threshold |
| 引力 | weighted_similarity |
| 重力減衰 | decay_exponent |
| 同じ重力レイヤー | same_scale_cluster |

**Status**: 確定。

---

## ADR-005: 採用論文の絞り込み方針

**Decision**: 代表論文の数式とテスト結果が一致すれば、それが内包する派生研究は採用不要とする。

**Context**:
- 開発者要求「わかりきっているものは採用しない」
- テストによる内包確認: 公理（採用数式）を満たす実装は、その派生定理も自動的に満たす
- 設計資料の肥大化を防ぐ

**Selection criteria**:
1. 数式が独自で再利用可能
2. テスト可能な性質を持つ
3. 他の採用論文に内包されない

**採用論文（最終）**:
| Source | 役割 |
|---|---|
| HERCULES (2025) | 縦軸：階層クラスタリング骨格 |
| SCA (2024) | 横軸：basis + 残差分解 |
| Cowan (2001) | 4±1 制約の理論的根拠 |
| Newman (2006) modularity | レイヤー分離品質の測定 |

**採用しないが内包確認**:
- TopicForest, BERTopic等の派生クラスタリング → HERCULESに内包
- RGMem, RG-DL Architectures → 理論的整合性確認のみ、数式は採用しない
- Marr / Polya / HTN等 → 哲学的背景、実装には影響しない

**Status**: 確定。

---

## ADR-006: テストケースの位置づけ

**Decision**: 採用論文の数式は **境界条件として** テストケース化する。実装の正しさだけでなく、理論との一致を検証する。

**Context**:
- 開発者要求「各論文の採用数式と、その結果をテストケースとして定義しておいて、その理論通りかどうかの境界として使う」
- 通常のunit testより一段強い「公理テスト」として位置づける

**Test category structure**:
```
tests/
├── axioms/               # 採用論文の数式そのものの検証
│   ├── test_hercules_recursion.py
│   ├── test_sca_residual.py
│   ├── test_cowan_constraint.py
│   └── test_modularity.py
├── integration/          # 統合フローの検証
└── boundary/             # エッジケース・反証実験
```

**Property-based testing**:
- 不変性 (scale invariance, closure 等) は property-based test で検証
- hypothesis ライブラリを使用

**Status**: 確定。

---

## ADR-007: schema 駆動設計

**Decision**: 全ての境界（モジュール間、推論層との接点、外部API）で frozen dataclass による schema を定義する。

**Context**:
- 「境界で推論、内部で決定論」を実装する具体的手段
- pydantic でも可だが、依存削減のため dataclass 優先
- frozen=True で意図しない変更を防ぐ

**Implementation pattern**:
```python
@dataclass(frozen=True)
class FormulationInput:
    nodes: tuple[Node, ...]
    embeddings: np.ndarray  # immutable by convention
    similarity_matrix: np.ndarray
    initial_scale: ScaleParams
```

**Status**: 確定。

---

## ADR-008: 失敗時のフォールバック設計

**Decision**: 各境界で2段階のフォールバックを持つ。

**Pattern**:
```
推論呼び出し → schema validation失敗
  ↓
retry (最大3回) → 失敗
  ↓
fallback to deterministic alternative
  ↓
それも失敗 → 構造化エラーを返す（呼び出し元判断に委ねる）
```

**具体例**:
- ノード化: AI推論 → 失敗 → 機械的な文単位分割
- スケール検出: 二分探索 → 失敗 → 「問題設定エラー」として上位に返す
- 自然文章化: AI推論 → 失敗 → テンプレート埋め込み

**Status**: 確定。

---

## ADR-009: 並行プロジェクトとの統合方針

**Decision**: LayerForge は **独立サブシステム** として開発し、後段で KDF/AET-OS/TIVE と統合する。

**Context**:
- 現状の開発者の負荷: Verification Forge proof Layer 2.5 完了、Coq/Lean formal verification 残、paper §4.x formalization phase 1 残
- LayerForge を既存プロジェクトに混ぜると、責任範囲が曖昧化
- 独立リポジトリで pytest 完結させてから統合する方が安全

**Integration points (将来)**:
- KDF: knowledge node を `FormulationInput.nodes` として受け取る
- TIVE: 280原則を「公理テスト」として LayerForge に流用可能
- AET-OS: 思考の整理エージェントとして組み込み
- Verification Forge: 形式検証で LayerForge の不変性を証明

**Status**: 確定。

---

## ADR-010: 開発フェーズ計画

**Decision**: 3フェーズで進める。

**Phase 1: 公理層実装 (4-6週間想定)**
- 採用論文の数式を pytest 化
- 決定論部分の全実装
- 推論層は stub（mock LLM）で進める

**Phase 2: 推論層接続 (2-3週間想定)**
- Claude API / structured output で推論層を実装
- schema validation の安定性確認
- 失敗時フォールバックの動作確認

**Phase 3: 実証実験 (期間未定)**
- KDFノード等の実データで 4±1 収束率を測定
- 既存研究 (HERCULES等) との出力比較
- 論文化材料の収集

**Status**: 仮計画。Phase 1 完了後に再評価。

---

## ADR-011: 推論層プロンプトはペルソナ定義を使わない

**Decision**: 推論層 (Boundary 1, Boundary 2) のプロンプトはペルソナ定義 ("You are a..." 形式) を使わず、**目的＋制約＋出力形式** で記述する。

**Context**:
- LayerForge の中心原理「最小コンテキスト × ハルシネーション最小化」と整合させるため
- ペルソナ定義は暗黙のコンテキストを大量に追加し、AIの「自由度」を高めてハルシネーションを誘発する
- 特に「専門家として」「アナリストとして」等の指定は、AIに **「専門家なら自信を持って答える」「専門家は分野の常識を共有している」** といった暗黙の前提まで採用させる
- これは LayerForge の決定論層の責任範囲を侵食する

**Mechanism (なぜペルソナ定義がハルシネーションを増やすか)**:
```
プロンプトなし: P(出力 | 質問)
ペルソナあり:   P(出力 | 質問, "あなたは医者")
             → 出力分布が「医者の発話分布」に引き寄せられる
             → "医者は推測しない" という前提とは裏腹に、
               医者の口調で推測してしまう
             → confidence の高い間違いを生む
```

**Implementation**:

旧 (ペルソナベース):
```
PARSE_SYSTEM_PROMPT = """
You are a structural analyzer. Your task is to decompose ...
"""
```

新 (目的＋制約):
```
PARSE_SYSTEM_PROMPT = """
[Task] Decompose the given text into semantically distinct nodes.

[Output schema] (provided)

[Constraints]
- Each node MUST be semantically independent
- Nodes MUST NOT overlap
- Nodes MUST cover the entire input text
- Number of nodes: 5 to 50
- If decomposition is impossible: return error indicator

[Output format] Valid JSON matching the schema.
[On failure] Return error indicator, do not invent.
"""
```

**変換規則**: 「専門家として〜」と書きたくなったら、以下に分解する:
1. 欲しい用語水準 → 「専門用語を使用」と直接指定
2. 欲しい慎重さ → 「不確実な部分は『不明』と明示」と直接指定
3. 欲しい引用 → 「根拠を含めて回答」と直接指定
4. 欲しいフォーマット → 出力形式で直接指定

→ ペルソナを介さず、欲しい挙動だけを直接列挙する。

**Consequence**:
- 推論層の出力分布が「目的に対する直接的な応答」に近づく
- 暗黙の前提による創作（ハルシネーション）が減少
- プロンプトが decision_log でレビュー可能になる（「なぜこの制約か」が明示できる）

**例外**:
- LayerForge では使わないが、一般的に**創作・対話生成**ではペルソナ定義が有効な場合がある
- LayerForge のタスクは「事実の構造化」「翻訳」が中心なので、ペルソナ定義は不要

**Status**: 確定。§05 のプロンプト例を本ADRに従って書き直し済み。

---

## ADR-012: 最小コンテキスト原理を設計憲法に格上げ

**Decision**: 「最小コンテキスト × ハルシネーション最小化」を LayerForge の設計憲法レベルの原理として明示し、新規設計判断の評価基準として採用する。

**Context**:
- userMemories で「動機階層の中位＝AIと決定論で分ける」と整理されていたが、その**目的論**が明示されていなかった
- 実際の目的は「ハルシネーションを減らして AI 応答精度を上げる」
- そのための手段が「AI に渡すコンテキストを最小化する」
- これが ADR-002 (境界で推論、内部で決定論) の上位原理

**Hierarchy**:
```
目的: AI 応答の精度最大化
↓
手段: ハルシネーションの最小化
↓
方法: 最小コンテキストで AI を呼ぶ
↓
そのために: AI に渡す前に決定論で削れるものを削る
   = ADR-002 (境界で推論、内部で決定論)
   = ADR-007 (schema 駆動設計)
   = ADR-011 (ペルソナ定義を使わない)
```

**Implication for design reviews**:
新規設計判断時の評価チェックリストに以下を追加:

```
□ この設計は、AI に渡すコンテキストを増やすか減らすか?
□ 増やすなら、それは「決定論で削れない本質的な情報」か?
□ 暗黙の前提を AI に補完させているか? (補完されると危険)
□ 同じ目的を、より小さなコンテキストで達成できないか?
```

**過去ADRとの整合性確認**:
- ADR-002 (境界で推論、内部で決定論) → 本原理の主要実装、整合
- ADR-007 (schema 駆動) → コンテキストの形式を絞る装置、整合
- ADR-008 (フォールバック設計) → AI 失敗時に決定論コアに戻る、整合
- ADR-011 (ペルソナ定義禁止) → 本原理の直接適用、整合

全ADRがこの上位原理から導出可能であることを確認。

**Status**: 確定 (原理として)。実証は **限定的に null result** (下記参照)。

---

### ADR-012 補遺 (v6, 2026-05-12): 検証ログと honest status

**主張**: 「LayerForge で context を分解 → AI に絞った context だけ渡す → ハルシネーション減少」

**実施した検証** (`scripts/halluc_benchmark/`):

| 試行 | corpus 規模 | model | 結果 |
|---|---|---|---|
| 小規模 (`out/`) | 24 passages × ~30 words = ~3K tokens、4 themes | Sonnet 4.6 級 (Agent subagent default) | 3 condition (full/layerforge/oracle) すべて **12/12 完全一致**、ハルシネーション 0 |
| 大規模 (`out_large/`) | 100 passages × ~50 words = ~10K tokens、4 themes、cross-contamination 仕掛け (luminoxide-I..XXV 等 Roman-numeral 命名で混乱誘発) | Sonnet 4.6 級 | 同様に **12/12 完全一致**、ハルシネーション 0 |
| 大規模 + 弱モデル | 同上 | Haiku 4.5 | 同様に **12/12 完全一致**、ハルシネーション 0 |

**Honest conclusion**:
- 「現行 Claude 系モデルが本検証スケールで context 量に対し robust」という事実が観測された
- 即ち: **本原理「最小 context → 減ハルシネーション」は、現行モデル × ~10K token corpus では検証不能**
- LayerForge の filter が baseline より優れているという証拠は得られなかった
- ただし baseline より劣る証拠も無い (routing 100% 正確、output 完全同一)

**仮説が有効でありうる領域** (未検証):
- corpus > 50K tokens (本実験スケール超過、需要待ちで再検証)
- 旧型/小型モデル (GPT-3.5, Llama 7B 等、本フレームでは試行範囲外)
- 意図的に紛らわしい高密度 cross-contamination (近接 numeric / 同義表現)
- 多段 reasoning が必要な質問 (本実験は single-fact lookup のみ)

**Decision update**: ADR-012 の原理 (最小コンテキスト × ハルシネーション最小化) は **設計憲法として保持**。ただし「実証された便益」とは謳わない。「現行モデル + 中規模 corpus では filter による gain は観測されず、ただし regression も発生せず」と honest に記述する。LayerForge の価値は ADR-013 (認知補助具) + decomposition の文脈 (decision 整理 / 階層分解) に置く。

---

## ADR-013: LayerForge の最初の応用例を「決定整理（認知補助具）」とする

**Decision**: LayerForge の元々の用途（自然言語の情報構造化）に加えて、**「決定空間の構造化」=「認知補助具」** を Phase 2b として開発計画に組み込む。これを最初のドッグフーディング対象とする。

**Context**:
- LayerForge 開発の対話の中で、開発者自身の認知特性が明らかになった:
  - 「整理が苦手」ではなく「整理コストの ROI が合わない」(タイプC)
  - 整理時に「作業手順・どこに何を置くか」のマイクロ決定が積み上がり「もういいや」になる
  - これは決定疲労の典型パターン
- 開発者が提案: 「考えすぎ、今のレイヤーはここまで！とかが自動で脳内展開できるようになったら、整理できそう」
- これは LayerForge を **自然言語整理** ではなく **決定整理** に応用するアイデア
- 同じアルゴリズム (4±1 レイヤー分解) が両方の問題を解く

**The insight**:
- 決定空間も embedding 可能 (決定間の関連性が定義できる)
- 4±1 制約をそのまま適用可能
- 「閉じるレイヤー」= 「今は決めなくていい決定群」として運用可能
- philosophy filter の上位層として機能する:
  - LayerForge 認知補助具: 「今このレイヤーで考えるべきか」を判定 (メタ判定)
  - philosophy filter: 「考えると判定された決定」に対する判定 (実行判定)

**Architectural placement**:

```
ユーザーのタスク (自然言語)
  ↓
[L0: LayerForge 認知補助具] ← 新規
  ↓ 4±1 レイヤーに分解
  ↓ 「今開くレイヤー」と「閉じるレイヤー」を判定
  ↓
[今開くレイヤーの決定群] (4±1 個)
  ↓
[philosophy filter] (各決定に適用)
  ↓
  - 機械検証可能 → AI実行
  - 100%再現可能 → AI実行
  - 業務領域 → user
  - 認知負荷削減に効く → AI default
  - 効かない → 捨てる
  ↓
最小限の user 判断項目
```

**Use case**:

```bash
$ layerforge decide "LayerForge プロジェクトを立ち上げる"

L1 [プロジェクト存在]: 1個の決定
  - 立ち上げる/見送る → ?

L2 [物理配置]: 1個の決定
  - ~/projects/layerforge/ で良いか → ?

L3 [初期構造]: 1個の決定
  - design_docs/ だけ置いて始める → ?

[以下のレイヤーは「今は開かない」と判定されました]
  - 命名規則 (L4 推定)
  - CI/CD 設定 (L5 推定)
  - 依存管理 (L4 推定)
  - skill 作成 (L5 推定)
  → 必要になったら 'layerforge decide --open <topic>' で開く

決定すべき項目: 3個 (4±1 内)
```

**Implementation requirements (Phase 2b)**:

LayerForge core (Phase 1 で完成) を基盤として、新規実装:

1. **Boundary 1 specialization (DecisionParseLLM)**: 
   - 自然言語タスク → 関連決定群のリスト
   - 既存 Parse プロンプトの特化版
2. **Decision embedding**: 
   - 決定文を embedding 化 (既存 embedder 流用)
3. **Open/close 判定ロジック (決定論)**: 
   - 「今このレイヤーを開くべきか」の判定式
   - 候補基準: 「上位レイヤーが未決定なら下位は閉じる」「相互依存があれば一緒に開く」等
   - 詳細は Phase 2b 実装時に確定
4. **再オープン機能**: 
   - `layerforge decide --open <topic>` で閉じたレイヤーを後から開く
   - persistent storage 必要 (decision history)
5. **CLI interface**: 
   - Phase 2b では CLI 起点で良い
   - GUI 化は Phase 3 以降

**Consequence**:
- 開発者自身が日常的に LayerForge を使う → ドッグフーディングが完璧
- 「自分の課題を自分の道具で解く」という強い実証例ができる
- 論文化時の説得力が増す (実装者の認知特性を補助した実例)
- Phase 1 完了後に **すぐ実用価値が出る** (Phase 2a 経由で Phase 2b に到達)
- LayerForge の汎用性が証明される: 自然言語整理 + 決定整理の両方で動く同一エンジン

**Risk**:
- 決定空間の embedding 品質が、テキスト embedding ほど良くない可能性
  - 対応: 既存の embedding モデルでまず試す、性能不足なら decision-specific embedding を検討
- 「閉じる/開く」の判定基準が経験則的になりうる
  - 対応: 初期は user override 必須、運用しながら判定基準を洗練

**Alternatives considered**:
- (a) Phase 2 は元々の用途 (自然言語整理) のみに集中、認知補助具は Phase 3 以降
  - Rejected: ドッグフーディングを早く始めた方が設計の問題が早く見つかる
- (b) 認知補助具を別プロジェクトとして切り出す
  - Rejected: 同一エンジンで動くなら統合しておく方が保守性が高い
- (c) 認知補助具を LayerForge のメイン用途にする
  - Rejected: 自然言語整理の方が論文化・他者への展開でより一般的

**Status**: 確定。

**Phase 2b の予算**: Phase 2a 完了後 2-3 週間想定。Phase 1 完了時点で再評価。

---

## ADR-014: Claude Code skill としての実装を第一形態とする

**Decision**: LayerForge の**第一の実装形態**を Claude Code の skill (`~/.claude/skills/layerforge/`) として確定する。スタンドアロンライブラリ + API クライアント形式は採用しない (将来の選択肢としては残す)。

**Context**:
- v1〜v4 の設計資料は **暗黙にスタンドアロンライブラリ + Anthropic SDK 直接呼び出し** を前提としていた
- 実際の対話履歴を遡ると、開発者の当初の発想は「Claude Code の skill か hooks に組み込む」だった
- 設計資料作成時に、Claude (Opus 4.7) が暗黙に「公開可能なライブラリ」を前提化していたズレ
- v5 でこのズレを訂正

**The realization**:
- 開発者の philosophy filter ADR (2026-05-05) は既に同じパターンで物理層実装している:
  - `~/.claude/profile/cognitive_load_principles.md` (原則)
  - `~/.claude/skills/secretary/SKILL.md` (Rule 6)
  - `~/.claude/decisions/2026-05-05_philosophy-as-judgment-filter.md` (判断記録)
- LayerForge を同じパターンに乗せることで、philosophy filter と並列構造になる
- 「判断の物理層実装」(philosophy filter) と「階層分解の物理層実装」(LayerForge) という整理

**Architectural transition**:

```
旧 (スタンドアロン前提, v1-v4):
  pip install layerforge
    ↓
  Python から API呼び出し (anthropic SDK)
    ↓
  LLM Client + retry + fallback の実装が必要

新 (skill 前提, v5):
  ~/.claude/skills/layerforge/
    ├── SKILL.md          # Claude への指示 (推論層相当)
    ├── core/             # 決定論コア (Python)
    │   ├── scale_finder.py
    │   ├── hierarchical.py
    │   ├── distillation.py
    │   ├── modularity.py
    │   └── ...
    ├── tests/            # pytest (決定論コアの検証)
    └── templates/        # 出力テンプレート
```

**Why this is simpler**:

| 項目 | スタンドアロン前提 | skill 前提 |
|---|---|---|
| LLM クライアント実装 | 必要 (anthropic SDK 等) | 不要 |
| API キー管理 | 必要 | 不要 |
| structured output 設定 | 必要 | SKILL.md で指示するだけ |
| retry/fallback ロジック | 必要 | Claude が判断 |
| プロンプトのバージョン管理 | 必要 | SKILL.md の git 管理 |
| schema 検証コード | 必要 | Claude に "JSON で出して" と書くだけ |
| Phase 2a の工数 | 大規模 (2-3週間) | 数日 |

**Consequence**:
- Phase 2a が大幅短縮 (2-3週間 → 数日)
- 推論層の実装責任が Claude (Claude Code 内) に移譲される
- API コストゼロ (Claude Code の月額のみ)
- データプライバシー向上 (開発者の環境内で完結)
- 他者への配布は困難になる (許容、ADR-009 と整合)

**動作モデル**:

```
[開発者が Claude Code で何かを指示]
  ↓
[Claude Code (Claude) が SKILL.md を読む]
  ↓
[SKILL.md の指示に従って Claude が動く]:
  1. 入力テキストを Claude が読んでノード化 (Boundary 1相当)
  2. python core/ を呼んで決定論コア実行
  3. 結果を Claude が読んで自然な文章にする (Boundary 2相当)
  4. 開発者に報告
```

API 呼び出しコードは一切不要。Claude 自身が「Boundary 1, 2」を担当する。

**既存 ADR との関係**:

| ADR | 影響 |
|---|---|
| ADR-002 (境界で推論、内部で決定論) | **整合**: 推論層が Claude Code 内に移っただけ、原則は変わらず |
| ADR-007 (schema 駆動) | **整合**: schema は SKILL.md に記述、コードレベル schema は決定論コア境界で適用 |
| ADR-008 (フォールバック) | **緩和**: Claude が自然にフォールバック判断、専用コード不要 |
| ADR-009 (独立サブシステム) | **修正**: 物理的配置は ~/.claude/skills/ 内、独立性は SKILL.md と core/ の分離で実現 |
| ADR-010 (Phase 計画) | **更新**: Phase 2a を「SKILL.md ドラフト + Claude Code 統合」に変更、工数大幅減 |
| ADR-011 (ペルソナ禁止) | **整合**: SKILL.md でも「あなたは〜」ではなく目的+制約で書く |
| ADR-012 (最小コンテキスト) | **強化**: API 経由しないため、暗黙コンテキストが減り、原理がより貫徹される |
| ADR-013 (認知補助具) | **整合**: 認知補助具も `/layerforge decide` のような slash command として実装可能 |

**Future option (留保)**:
将来、以下の状況が発生したら**単体ライブラリ化を検討**：
- 他者に配布したくなった場合
- Claude Code 以外の環境 (例: VS Code 拡張、Web アプリ) で使いたくなった場合
- 決定論コアの性能を商用展開したい場合

この場合、決定論コア (`core/`) はそのまま流用可能。SKILL.md を API クライアント実装に置き換えるだけ。**現在の設計は将来の選択肢を縛らない**。

**新規必要となる成果物**:
- `SKILL.md` のドラフト (Phase 2a の中心成果物)
- これは Boundary 1, 2 のプロンプトを「Claude に対する指示」として書き直したもの
- ペルソナ定義禁止 (ADR-011) と最小コンテキスト原理 (ADR-012) を貫徹

**配置の最終形 (案)**:

```
~/.claude/
├── profile/
│   └── cognitive_load_principles.md         # 既存
├── skills/
│   ├── secretary/SKILL.md                   # 既存 (philosophy filter)
│   └── layerforge/                          # 新規
│       ├── SKILL.md
│       ├── core/                            # 決定論コア
│       ├── tests/
│       └── templates/
├── decisions/
│   ├── 2026-05-05_philosophy-as-judgment-filter.md  # 既存
│   └── 2026-XX-XX_layerforge-skill.md        # 新規 (将来)
```

**Status**: 確定 (v5)。

---

## ADR-015: ADR-012 honest 化と Mode A/B/C positioning 確定 (v6)

**Decision**: 検証フェーズ (`scripts/halluc_benchmark/`, `scripts/multiagent_demo/`) で得た 3 連続 null result + Mode C 実装による本来意図の発見を踏まえ、LayerForge の positioning を「behavioral guardrail (AI を賢くする)」から「**context filter / cost optimizer / 主観認知補助具**」に確定する。

**Context** (要点のみ、詳細は `docs/08_empirical_findings.md`):
- ADR-012 「ハルシネーション最小化」の検証は 3 連続 null
- 入力 filter による hallucination 減 effect は本検証スケールで観測不能
- ただし Mode C (AI 出力圧縮) は本来意図と合致、客観的に圧縮率 14-40% を達成
- 「動く」「正しい」「subset 保証」は機械検証済 (147 pytest)

**Re-positioning (3 分離軸、v6 改訂版)**:

| 軸 | 主張 |
|---|---|
| **A. LayerForge 本体 (決定論コード、LLM 不在で動作)** | **「LLM を使わず決定論で context を 1/3〜1/7 に圧縮」「再現性 100%、subset 保証で情報捏造ゼロ」「index 構築段階で hallucination 経路を遮断」** |
| **B. LLM 挙動 baseline (LayerForge-controlled context 下で観察)** | 「現行 Claude family は filter 有無に robust」「context 63% 削減でも AI 性能維持」 ← null result はここの「LLM が too good」観察 |
| **C. 組合せ workflow 設計** | 「Mode A/B/C で同一 core を異なる目的に再利用」「CC skill 形態で API 課金なし運用」「philosophy filter の物理実装例」 |

**Critical clarification**: LayerForge の **コード本体は LLM を呼ばない** (`AnthropicLLMClient` は ADR-014 で future-option 封印、`sentence-transformers` は encoder model であり chat LLM ではない、GraphRAG 等と同じ「決定論的 index 構築」扱い)。本セッション中盤で「LayerForge は LLM 使う」と誤認したが、これは category mistake。

**Null result の re-frame**:
- ~~「LayerForge は hallucination 減らさない、効果なし」~~ → category mistake
- ✓ 「現行 LLM が context noise に robust なため、LayerForge filter の behavioral effect は本検証 regime で検出不能」 (B 軸の観察、LayerForge 本体の失敗ではない)

**Implementation**: `docs/08` で 3 分離軸 + safe claim / unsafe claim 整理済、本書は要約のみ。

**Status**: 確定 (v6 改訂)。

---

## ADR-016: find_valid_scale の K 選択 algorithm 改善候補 (未実装、検討中)

**Context**:
- 現状の `find_valid_scale(similarity, target_range=(3,5))` は binary search で **range 内の first valid** (= 多くの場合上限 K=5) を返す
- §scripts/k_sweep/ の resolution-limit check で発覚: 4-theme corpus に対し K=5 を選ぶと 1 テーマを **過剰分割** (Fortunato-Barthélemy 上限下回りの artifact community を 2 件生成)
- 同コーパスで K=4 exact なら Q=0.712 (good) かつ 4/4 community が resolution limit 超え

**改善案 (3 候補)**:

| 案 | 算法 | trade-off |
|---|---|---|
| A. Q max 選択 | range 内で `layerforge_core` 全候補 K について Q 比較、最大を選ぶ | 計算コスト O(range_size × KMeans cost)、artifact 自動回避 |
| B. above-limit fraction max | range 内で「resolution limit 超え community 比率」最大の K を選ぶ | コスト同、より resolution-limit 直接対処 |
| C. Q が plateau 化する最小 K | range 内で Q 増加が <ε となる最小 K (Occam's razor) | 過剰分割を抑止しつつ計算コスト最小 |

**Status**: 未実装。本検証で「default K=5 でも routing は 100%」を確認済のため、緊急性なし。実装すると default 挙動が変わるため、ADR としては「課題認識」止まり、実装は別途判断。

**関連**: `docs/08_empirical_findings.md` §2.3、`scripts/k_sweep/`

---

## ADR-017: AI 推論の誤り訂正記録 — γ 付き modularity 推奨の撤回 (2026-05-12)

**目的**: AI (本セッションの私) が出した推奨の中に文献誤認に基づく誤りがあったため、撤回内容と検出経緯を ADR として残す。今後の **sycophancy 構造的検知** および **AI 推論の盲信防止** の材料とする。

**Context**:
- 2026-05-12 セッションで、私 (Claude) は §6 で観察した「Q peak K が N に対し bouncy」現象を受けて、改善策として **「Reichardt-Bornholdt 系の γ 付き modularity で締まる」** と推奨した
- 同時に「multi-resolution γ sweep」「stability-based consensus」「spectral approach」などを並列に提示
- user 側で独立に文献調査を実施した結果、以下の事実が判明:

| 私の推奨 | 実態 (user 調査) | 出典 |
|---|---|---|
| γ 付き modularity で締まる | ✗ γ も resolution limit 持つ | Kumpula et al. (2008) |
| multi-resolution γ sweep が解決策 | ✗ 本質的制約あり (community stability と resolution の trade-off 不可避) | Xiang & Hu (2011) |
| CPM が最強 (これだけは正しかった) | ✓ subgraph-invariance で resolution-limit-free を証明 | Traag, Van Dooren, Nesterov (2011) |
| stability-based (consensus) | △ STAR method として確立、決定論性に注意 | Grassetti et al. (2026) |
| Q max が unstable は LayerForge の発見 | ✗ 既に理論的に確立 (Good 2010) | Good, de Montjoye, Clauset (2010) |

**Decision**:
1. γ 付き modularity 推奨を **撤回**
2. CPM 置換を future work として §4 に明示 (実装は別 iteration)
3. §6 の framing を「Good (2010) の N×K 軸での実証」に格下げ (LayerForge 固有の発見ではない)
4. above-limit fraction の novelty 主張も保留 (literature search 深掘り前は「本実装で採用した補助 metric」)
5. 本 ADR で誤り経緯を残し、**「AI agent の文献推奨を物理層検証なしに採用しない」** という運用原則を明文化

**検出経緯の構造分析**:
- 私の誤りは「**γ で resolution 問題が解ける**」という素朴な対応策を、Kumpula (2008) / Xiang & Hu (2011) を踏まえずに出した点
- 「最新文献調査を怠った」というよりは、**「modularity の Q を tuning パラメータで広げれば自由度が上がるから resolution limit を超えられるはず」という直感的推論**を裏取りせず出した
- user が「方法論を 5 つ挙げたが実態確認する」と独立調査に動いたため検出された。**AI の推論を user 側で物理層検証する習慣がワークした事例**

**運用原則 (ADR-017 として確定)**:
- AI が文献ベースの推奨を出した場合、**citation 出典 (年・著者・誌) と要旨を明示**することを義務化
- 出典なしの「〜が有効」「〜で締まる」系の推奨は **採用前に user 側の独立検証**を経る
- 撤回が発生した場合、本 ADR のように **撤回内容と検出経緯を残す** (隠さない)
- 本原則は `~/.claude/CLAUDE.md` の「禁則 5: Agent の PASS 報告を鵜呑みにしない」と整合

**関連**: `docs/08_empirical_findings.md` §1.6, §6 補正、user CLAUDE.md 禁則 5

---

## ADR-018: CPM 実装方式の選択 — graspologic-native bug 発見と自前実装への switch (2026-05-13)

**Context**:
- ADR-017 で「CPM (Traag 2011) を future work として明示」、後続セッションで「公開前に CPM 比較を実施する」方針確定
- License 哲学として LayerForge は MIT を貫きたい → GPL leidenalg は採用不可
- 第一候補: graspologic (MIT, Microsoft) の Leiden(CPM) 機能
- 第二候補: graspologic-native (MIT, Rust core)
- 自前実装は最終手段とする方針で開始

**調査経緯**:

1. **graspologic 本体 (high-level Python wrapper)**:
   - License: MIT ✅
   - CPM 対応: Leiden(use_modularity=False) で対応 ✅
   - Python 3.13 install: **失敗** ❌ — 依存 gensim が build error (setuptools/numpy<2.0 互換性問題)

2. **graspologic-native (Rust 実装、PyPI install 可)**:
   - License: MIT ✅
   - Install: Python 3.13 で問題なし (v1.2.5) ✅
   - API: `leiden(use_modularity=False, resolution=γ, seed=42)` で CPM ✅ (表面上)
   - **実測時に crash 発覚**: `pyo3_runtime.PanicException: index out of bounds: the len is 3 but the index is 4` at `compact_network.rs:145`
   - 最小再現例 (6 nodes, 7 edges, γ=0.5, CPM mode) で確実に panic
   - **同じ入力に対して use_modularity=True (Newman mode) は正常動作**
   - version 1.2.4 / 1.2.5 とも同様 panic、1.2.2 は API 非互換で別エラー
   - graspologic-native GitHub: open issue #43 "Leiden not working" 等あり、CPM 専用の bug 報告は未確認

3. **leidenalg (Traag 本人実装の Python package)**:
   - License: **GPLv3** ❌ — MIT/GPL 混在問題発生
   - optional extra で逃げる scenario B は user の license 哲学 (MIT cleanliness 一貫) に反する

→ Scenario A (MIT external lib 採用) 実質不可。

**Decision**:

1. **CPM-Louvain を自前実装** (シナリオ D)
   - 配置: `layerforge/core/cpm_backend.py` (pure-Python + numpy/scipy のみ)
   - 算法: Traag 2011 の CPM 品質関数 `H = Σ_c [m_c - γ * (n_c choose 2)]` を Louvain greedy local moves で最大化
   - ΔH 計算: `(k_{v,c2} - k_{v,c1}) + γ * (n_{c1} - 1 - n_{c2})` (移動先既存コミュニティの場合)、singleton split も評価
   - K target_range は γ の log-scale bisection で hit
2. **外部依存追加なし** — pyproject.toml の `[cpm]` optional extra は撤回 (graspologic-native 試行時に追加していたものを削除)
3. **graspologic-native の bug 試行は本 ADR で trace を残す** (隠さない、ADR-017 と同じ精神)
4. **公開時の主張は「CPM-Louvain 自前実装、Leiden refinement step は v2 候補」** と限定的に書く

**実装 scope (現時点)**:
- ✅ `cpm_partition(similarity, resolution, seed)` — Louvain CPM 単一パス
- ✅ `find_cpm_resolution(similarity, target_range, seed)` — γ bisection で K target 化
- ✅ `community.py` dispatcher (newman / cpm 切替、共通 Hierarchy 出力)
- ✅ pipeline / CLI / schema 配線 (`community_method` option、`cpm_h` field 追加)
- ✅ 13 件の axiom test (determinism / K monotone in γ / format parity / 既存テスト regression なし)
- ⏳ Newman vs CPM 比較測定 (`scripts/k_sweep/cpm_compare.py`、本 ADR コミット時点で background 実行中)

**Status**: 実装完了、測定実行中。比較結果は docs/08 §6 に追記予定。

**未対応 / future work**:
- Leiden refinement step (Traag 2019) は未実装 — 大規模 N (>1000) で局所最適に陥る可能性。LayerForge の運用規模 (N=24-40) では Louvain で十分との判断
- 自前実装の数値検証: 公式 leidenalg (GPL) 出力との一致確認は **License 上できない** ため、Traag 2011 論文の Karate Club 例で間接検証可能
- graspologic-native の bug 修正後に再評価する value は薄い (自前実装で運用が安定すれば switch コスト > 利得)

**運用原則 (ADR-018 として確定)**:
- 「外部ライブラリの API が表面上正しくても、実測で確認するまで採用判断しない」(graspologic-native の docstring は CPM 対応を謳っていたが panic、実測で初めて発覚)
- 「license 哲学を貫くために自前実装を選ぶ場合、scope を限定して工数膨張を防ぐ」(Leiden refinement や hierarchical mode は v2)

**関連**: ADR-017 (γ-modularity 推奨撤回、CPM が真の解と認識した経緯)、`docs/08_empirical_findings.md` §1.6 / §6, `layerforge/core/cpm_backend.py`

---

## ADR の階層関係 (v5 で更新)

ADR-014 追加により、配置が明確化:

```
ADR-012 (最小コンテキスト原理: 設計憲法)
  ↓ 導出
ADR-002 (境界で推論、内部で決定論)
ADR-007 (schema 駆動設計)
ADR-008 (フォールバック設計)
ADR-011 (ペルソナ定義禁止)
  ↓ 適用
ADR-003 (4±1 制約)
ADR-006 (公理テスト)
  ↓ 応用 (用途)
ADR-013 (認知補助具 - 最初のドッグフーディング)
  ↓ 配置 (形態)
ADR-014 (Claude Code skill として実装)
```

ADR-014 は**実装形態の決定**であり、用途 (ADR-013) と直交する軸。
両方の用途 (Phase 2a 自然言語整理 / Phase 2b 認知補助具) が、同じ skill 形態で実装される。

---

## Open questions

以下、現時点で未決の事項：

1. **embedding model の選定**: sentence-transformers (ローカル) vs OpenAI/Voyage (API) → Phase 1中に決定
2. **言語処理範囲**: 日本語特化 vs 多言語対応 → 開発者の主用途次第
3. **最大レイヤー深度の絶対上限**: 4±1の再帰的適用で深さ何段まで許すか → 実証で決定
4. **論文化のタイミング**: Phase 2 完了後 or Phase 3 完了後 → 結果次第
5. ~~**SCA論文 (A2) のfull text 精読**~~ → ✓ **解決済 (2026-05-11, PDF取得)**
6. ~~**Newman modularity 原典 (A4) の精読**~~ → ✓ **解決済 (2026-05-11, PDF取得)**
7. **採用しなかった論文の追跡**: Phase 3 で論文化する際、TopicForest、Clio、LLooM 等の最新比較が必要
8. **SCA 公式 GitHub 実装の確認**: 数式と実装で差分がないか確認 (Phase 1 着手前推奨)
9. **04_test_cases.md (SCA関連テスト) の再点検**: F2 訂正に合わせて T2.x を更新する必要
10. **Cowan 原論文の取得**: Phase 3 (論文化) 時に大学図書館経由で取得 → 二次資料で十分なら不要
11. **Method selector (`recommend_community_method`) の code 実装**: Rank 1-4 で empirical decision rule は確立済 (`docs/08` §7.5)、ただし LayerForge typical domain (N=20-40) では出力がほぼ常に "newman" のため実装 cost > value、現状 docs 記述のみ。**別 domain (N=1000+, dense graph) への拡張時に §7.5 を foundation として実装着手** (想定工数 1 日、追加依存なし)
