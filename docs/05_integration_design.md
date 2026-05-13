# 05. Integration Design

採用した公理（§02, §03）を統合した LayerForge 全体アーキテクチャ。

設計原則: **境界で推論、内部で決定論** (ADR-002)

---

## システム全体図

```
┌──────────────────────────────────────────────────────────────────┐
│                         LayerForge System                          │
│                                                                    │
│  ┌─────────────────┐                                              │
│  │ Natural Language │ (User input / KDF nodes / docs)             │
│  └────────┬────────┘                                              │
│           ▼                                                        │
│  ┌──────────────────────┐                                         │
│  │ [INFERENCE BOUNDARY 1]│ AI推論層                                │
│  │   parse_to_structure  │ schema強制 + retry/fallback             │
│  └────────┬─────────────┘                                         │
│           ▼                                                        │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                    DETERMINISTIC CORE                       │  │
│  │                                                             │  │
│  │  ┌─────────────────┐    ┌────────────────────┐            │  │
│  │  │ scale_finder    │ →  │ hierarchical_kmeans │            │  │
│  │  │ (4±1 binary     │    │ (HERCULES adapted)  │            │  │
│  │  │   search)       │    └─────────┬──────────┘            │  │
│  │  └─────────────────┘              ▼                        │  │
│  │           ▲              ┌─────────────────┐               │  │
│  │           │              │ modularity_check │               │  │
│  │           │              │ (Newman Q)       │               │  │
│  │           │              └─────────┬───────┘               │  │
│  │           │  retry if poor         │                        │  │
│  │           └────────────────────────┤                        │  │
│  │                                    ▼                        │  │
│  │                          ┌────────────────────┐             │  │
│  │                          │ sca_distillation    │             │  │
│  │                          │ (per layer)         │             │  │
│  │                          └─────────┬──────────┘             │  │
│  │                                    ▼                        │  │
│  │                          ┌────────────────────┐             │  │
│  │                          │ inter_layer_relations│            │  │
│  │                          └─────────┬──────────┘             │  │
│  └──────────────────────────────────┬─┘                        │  │
│                                     ▼                            │
│  ┌──────────────────────┐                                         │
│  │ [INFERENCE BOUNDARY 2]│ AI推論層                                │
│  │   render_to_natural   │ template + LLM, validation              │
│  └────────┬─────────────┘                                         │
│           ▼                                                        │
│  ┌─────────────────┐                                              │
│  │ Natural Language │ (Layered output for user)                   │
│  │     Output       │                                              │
│  └─────────────────┘                                              │
└──────────────────────────────────────────────────────────────────┘
```

---

## モジュール構成

```
layerforge/
├── __init__.py
├── constants.py              # Cowan 4±1 等の定数 (F3.1)
├── schema/
│   ├── __init__.py
│   ├── input_schema.py       # FormulationInput, Node 等
│   ├── output_schema.py      # LayerForgeResult, DistillationResult 等
│   └── intermediate.py       # 内部処理の中間データ構造
├── inference/
│   ├── __init__.py
│   ├── parse.py              # INFERENCE BOUNDARY 1
│   ├── render.py             # INFERENCE BOUNDARY 2
│   ├── llm_client.py         # Claude/OpenAI API ラッパー
│   └── validation.py         # schema validation
├── core/
│   ├── __init__.py
│   ├── scale_finder.py       # F1.4 binary search
│   ├── hierarchical.py       # F1.3 HERCULES adapted
│   ├── modularity.py         # F4.2 Newman Q
│   ├── distillation.py       # F2.3 SCA per layer
│   └── relations.py          # inter-layer extraction
├── pipeline.py               # F5 layerforge_core
└── exceptions.py             # NoValidScaleError, SeparationQualityError, etc.

tests/
├── conftest.py
├── axioms/                   # §04 公理テスト
│   ├── test_hercules_recursion.py
│   ├── test_sca_residual.py
│   ├── test_cowan_constraint.py
│   ├── test_modularity.py
│   └── test_determinism.py
├── integration/
│   ├── test_full_pipeline.py
│   ├── test_inference_boundaries.py
│   └── test_fallback.py
└── boundary/
    ├── test_edge_cases.py
    └── test_containment_properties.py
```

---

## データフロー詳細

### Stage 0: Retrieval (Optional)

KDF や知識ベースから関連ノードを抽出する場合：

```python
def retrieve(query: str, knowledge_base) -> tuple[Node, ...]:
    """Decision: 決定論。embed + top-k 検索"""
    query_embedding = embed_one(query)
    candidates = knowledge_base.search(query_embedding, top_k=K_RETRIEVAL)
    return tuple(candidates)
```

### Stage 1: Boundary 1 - Parse (Inference Layer)

自然言語 → schema 構造化:

```python
def parse_to_structure(
    raw_input: RawInput,
    llm_client: LLMClient,
) -> FormulationInput:
    """
    [INFERENCE BOUNDARY 1]
    
    AI推論を使うが、出力は schema 強制。
    失敗時 retry → fallback to mechanical split。
    """
    # 1. Raw input の境界確定
    text = load_input(raw_input)
    
    # 2. ノード化（推論層、schema 強制）
    for attempt in range(MAX_RETRIES):
        try:
            proposal = llm_client.propose_nodes(
                text,
                schema=NodeListSchema,
                constraints=NODE_CONSTRAINTS,
            )
            if validate_node_proposal(proposal, text):
                nodes = proposal
                break
        except (SchemaViolation, LLMError):
            continue
    else:
        # Fallback: 機械的分割
        nodes = mechanical_split(text)
    
    # 3. 正規化（決定論）
    normalized_nodes = tuple(normalize(n) for n in nodes)
    
    # 4. Embedding 化（決定論扱い）
    embeddings = embed_batch([n.text for n in normalized_nodes])
    
    # 5. 類似度行列（決定論）
    similarity_matrix = cosine_similarity_matrix(embeddings)
    
    # 6. 初期 scale 係数（決定論）
    initial_scale = compute_initial_scale(similarity_matrix)
    
    return FormulationInput(
        nodes=normalized_nodes,
        embeddings=embeddings,
        similarity_matrix=similarity_matrix,
        initial_scale=initial_scale,
    )
```

### Stage 2: Deterministic Core

完全に決定論的な処理（F5 参照）:

```python
def layerforge_core(input_data: FormulationInput) -> CoreResult:
    """
    [DETERMINISTIC CORE]
    
    入力同じ → 出力同じ。
    全公理テスト (§04) がここを対象とする。
    """
    # 2.1 scale 係数探索
    theta, n_layers = find_valid_scale(
        input_data.similarity_matrix,
        target_range=(LAYER_COUNT_MIN, LAYER_COUNT_MAX),
        initial_theta=input_data.initial_scale.threshold,
    )
    
    # 2.2 階層クラスタリング
    hierarchy = hierarchical_kmeans(
        embeddings=input_data.embeddings,
        k_per_level=[n_layers],
        use_resampling=True,
        random_state=DETERMINISTIC_SEED,
    )
    
    # 2.3 modularity 品質チェック
    Q = compute_modularity(
        input_data.similarity_matrix,
        hierarchy.flat_labels,
        threshold=theta,
    )
    
    quality = classify_separation_quality(Q)
    if quality == "poor":
        raise SeparationQualityError(
            f"Modularity Q={Q:.3f} below threshold. "
            f"Possible problem misformulation."
        )
    
    # 2.4 各レイヤーで SCA 蒸留
    distillations = []
    for layer in hierarchy.layers:
        layer_embeddings = input_data.embeddings[layer.member_indices]
        layer_nodes = tuple(input_data.nodes[i] for i in layer.member_indices)
        
        distillation = distill_layer(
            embeddings=layer_embeddings,
            nodes=layer_nodes,
        )
        distillations.append(distillation)
    
    # 2.5 レイヤー間関係抽出
    inter_layer_relations = extract_inter_layer_relations(
        hierarchy=hierarchy,
        distillations=distillations,
    )
    
    return CoreResult(
        hierarchy=hierarchy,
        distillations=tuple(distillations),
        inter_layer_relations=inter_layer_relations,
        quality_metrics=QualityMetrics(
            modularity=Q,
            layer_count=n_layers,
            scale_coefficient=theta,
            is_within_4_plus_minus_1=is_layer_count_valid(n_layers),
            quality_class=quality,
        ),
    )
```

### Stage 3: Boundary 2 - Render (Inference Layer)

構造化結果 → 自然言語:

```python
def render_to_natural(
    core_result: CoreResult,
    llm_client: LLMClient,
) -> NaturalLanguageOutput:
    """
    [INFERENCE BOUNDARY 2]
    
    AI推論で自然言語化するが、情報を歪めない。
    失敗時 retry → fallback to template-only render。
    """
    # 1. テンプレート用データ準備（決定論）
    template_data = prepare_render_data(core_result)
    
    # 2. AI推論で翻訳（schema 強制、創作禁止）
    for attempt in range(MAX_RETRIES):
        try:
            rendered = llm_client.render(
                template_data,
                system_prompt=STRICT_TRANSLATION_PROMPT,
                output_schema=NaturalTextSchema,
            )
            if validate_natural_output(rendered, core_result):
                return rendered
        except (SchemaViolation, LLMError, ValidationError):
            continue
    
    # 3. Fallback: テンプレートのみ
    return template_only_render(template_data)
```

---

## Schema 定義（境界の型）

### Input Schema

```python
# layerforge/schema/input_schema.py

from dataclasses import dataclass
from typing import Literal
import numpy as np

@dataclass(frozen=True)
class RawInput:
    """エントリーポイント。User input or document set."""
    source_type: Literal["text", "document_list", "kdf_query"]
    content: str | list[str]
    metadata: dict | None = None


@dataclass(frozen=True)
class Node:
    """単一の意味的単位 (ノード化後)"""
    id: str  # 一意ID (hash等)
    text: str  # 正規化済みテキスト
    metadata: dict
    
    def __post_init__(self):
        if not self.id:
            raise ValueError("Node id required")
        if not self.text:
            raise ValueError("Node text required")


@dataclass(frozen=True)
class ScaleParams:
    """スケール係数 (重力係数の中立用語: ADR-004)"""
    threshold: float  # θ: relation cutoff
    decay_exponent: float = 1.0  # α
    kernel_type: str = "cosine"


@dataclass(frozen=True)
class FormulationInput:
    """決定論コアへの入力 (Boundary 1 の出力)"""
    nodes: tuple[Node, ...]
    embeddings: np.ndarray  # shape: (n_nodes, embedding_dim)
    similarity_matrix: np.ndarray  # shape: (n_nodes, n_nodes)
    initial_scale: ScaleParams
    
    def __post_init__(self):
        n = len(self.nodes)
        assert self.embeddings.shape[0] == n
        assert self.similarity_matrix.shape == (n, n)
```

### Output Schema

```python
# layerforge/schema/output_schema.py

@dataclass(frozen=True)
class DistillationResult:
    """単一レイヤーの蒸留結果"""
    basis: np.ndarray  # shape: (n_components, embedding_dim)
    law_coefficients: np.ndarray  # shape: (n_nodes, n_components)
    residuals: np.ndarray  # shape: (n_nodes,) residual norms
    is_converged: bool


@dataclass(frozen=True)
class LayerSummary:
    """単一レイヤーのメタ情報"""
    layer_id: int
    member_indices: tuple[int, ...]
    member_nodes: tuple[Node, ...]
    representation_vector: np.ndarray
    distillation: DistillationResult
    layer_name: str | None = None  # Boundary 2 で埋める


@dataclass(frozen=True)
class InterLayerRelation:
    """レイヤー間の関係"""
    from_layer_id: int
    to_layer_id: int
    relation_type: Literal["contains", "constrains", "specializes"]
    strength: float


@dataclass(frozen=True)
class QualityMetrics:
    """分解品質指標"""
    modularity: float
    layer_count: int
    scale_coefficient: float
    is_within_4_plus_minus_1: bool
    quality_class: Literal["good", "acceptable", "poor"]


@dataclass(frozen=True)
class CoreResult:
    """決定論コアの出力"""
    layers: tuple[LayerSummary, ...]
    inter_layer_relations: tuple[InterLayerRelation, ...]
    quality_metrics: QualityMetrics


@dataclass(frozen=True)
class NaturalLanguageOutput:
    """最終出力 (Boundary 2 の出力)"""
    text: str  # full rendered text
    layer_sections: tuple[str, ...]  # 各レイヤーの文章
    metadata_summary: str  # quality metrics の人間化版
```

---

## 例外設計

```python
# layerforge/exceptions.py

class LayerForgeError(Exception):
    """全ての LayerForge 例外の基底"""

class NoValidScaleError(LayerForgeError):
    """4±1 に収まる scale 係数が見つからない"""
    def __init__(self, message: str, similarity_stats: dict):
        super().__init__(message)
        self.similarity_stats = similarity_stats

class SeparationQualityError(LayerForgeError):
    """modularity Q が threshold を下回る"""
    def __init__(self, modularity: float, threshold: float):
        super().__init__(
            f"Modularity {modularity:.3f} < threshold {threshold:.3f}"
        )
        self.modularity = modularity

class SchemaViolation(LayerForgeError):
    """推論層出力が schema に違反"""

class LLMError(LayerForgeError):
    """LLM API 呼び出し失敗"""

class ValidationError(LayerForgeError):
    """出力検証失敗"""
```

---

## 推論層プロンプト設計

### Boundary 1: Parse プロンプト (ADR-011 準拠)

ペルソナ定義 ("You are a...") は使用しない。目的 + 制約 + 出力形式 で記述する。

```python
# layerforge/inference/prompts.py

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

NODE_CONSTRAINTS = {
    "min_nodes": 5,
    "max_nodes": 50,
    "no_overlap": True,
    "full_coverage": True,
    "min_node_length": 10,  # characters
}
```

**設計上の意図** (ADR-011 参照):
- 「あなたは structural analyzer です」と書かない → 暗黙の前提が混入しない
- 「正確に答えてください」のような曖昧な指示を避け、具体的制約を列挙
- 「DO NOT」セクションで創作・補完を明示的に禁止
- 失敗時の挙動を schema として明示し、AI に「失敗していい」と伝える

### Boundary 2: Render プロンプト (ADR-011 準拠)

ペルソナ定義 ("You are a translator...") は使用しない。

```python
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
```

**設計上の意図** (ADR-011 参照):
- 「翻訳者」というペルソナを置かない → 「翻訳者らしい補足説明」を防ぐ
- 「creative rewording」を明示的に禁止 → 言い換えによる情報歪曲を防ぐ
- 「DO NOT adopt any voice, persona, or rhetorical style」で再帰的に防御
- 失敗時の挙動を schema として明示

---

## 統合フロー擬似コード

```python
# layerforge/pipeline.py

def layerforge_pipeline(
    raw_input: RawInput,
    llm_client: LLMClient,
    embedding_client: EmbeddingClient,
) -> NaturalLanguageOutput:
    """LayerForge full pipeline (entry point)"""
    
    # ===== Boundary 1: Inference =====
    try:
        formulation_input = parse_to_structure(
            raw_input=raw_input,
            llm_client=llm_client,
            embedding_client=embedding_client,
        )
    except LLMError as e:
        # 推論層失敗 → 機械的フォールバック
        formulation_input = parse_to_structure_mechanical(raw_input)
    
    # ===== Deterministic Core =====
    try:
        core_result = layerforge_core(formulation_input)
    except NoValidScaleError as e:
        # 問題設定が壊れている → 上位に診断情報を返す
        return create_diagnostic_output(e)
    except SeparationQualityError as e:
        # 品質不足 → 警告付きで処理続行 or 失敗
        if STRICT_MODE:
            raise
        core_result = create_low_quality_result(e)
    
    # ===== Boundary 2: Inference =====
    output = render_to_natural(
        core_result=core_result,
        llm_client=llm_client,
    )
    
    return output
```

---

## 統合テスト戦略

### Integration Test Targets

```python
# tests/integration/test_full_pipeline.py

def test_end_to_end_with_known_structure(synthetic_layered_data):
    """既知の4層構造のデータが、4±1 レイヤーに分解される"""
    raw_input = RawInput(
        source_type="document_list",
        content=synthetic_layered_data,
    )
    
    output = layerforge_pipeline(raw_input, mock_llm, mock_embedder)
    
    assert "## L0" in output.text
    assert "## L1" in output.text
    assert 3 <= len(output.layer_sections) <= 5

def test_inference_boundary_isolation():
    """推論層の出力を強制的に変えても、決定論層の出力は不変"""
    formulation_input = create_test_formulation_input()
    
    result1 = layerforge_core(formulation_input)
    # 同じ formulation_input なら何度呼んでも同じ
    result2 = layerforge_core(formulation_input)
    
    assert result1 == result2

def test_full_fallback_chain():
    """推論層が全失敗してもパイプラインは止まらない"""
    failing_llm = MockFailingLLM()
    raw_input = generate_test_input()
    
    output = layerforge_pipeline(raw_input, failing_llm, mock_embedder)
    
    assert output is not None  # template fallback で出力される
    assert output.metadata_summary  # 警告メッセージ
```

---

## 依存ライブラリ

```toml
# pyproject.toml

[project]
name = "layerforge"
version = "0.1.0"
dependencies = [
    "numpy>=1.26",
    "scikit-learn>=1.4",  # KMeans
    "scipy>=1.12",         # sparse matrix, linalg
    "pydantic>=2.0",       # schema validation (optional)
    "anthropic>=0.39",     # Claude API
    "sentence-transformers>=2.7",  # embedding
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-cov>=5.0",
    "hypothesis>=6.0",     # property-based testing
    "ruff>=0.4",
]
```

---

## パフォーマンス考慮

| 操作 | 計算量 | 想定上限 |
|---|---|---|
| Embedding (batch) | O(n × d) | n=10,000 nodes |
| Similarity matrix | O(n²) | n=10,000 → 100M entries |
| KMeans | O(n × k × d × iter) | k=5, iter=300 |
| Modularity | O(n²) (dense) | sparse化で O(m) where m=edges |
| SCA per layer | O(n × d²) | typically n << 1000 per layer |
| Binary search (scale) | O(log(1/eps) × n²) | eps=1e-6, ~20 iter |

n=10,000 の入力で、決定論コア全体は数分〜十数分で完了見込み。

実用上のボトルネックは Boundary 1 の LLM 呼び出し（バッチ処理で軽減）。

---

## 並行プロジェクトとの統合インターフェース

### KDF Integration

```python
# layerforge/integration/kdf.py

def from_kdf_query(query: str, kdf: KDF) -> RawInput:
    """KDFノードを LayerForge 入力に変換"""
    nodes = kdf.search(query, top_k=100)
    return RawInput(
        source_type="kdf_query",
        content=[node.content for node in nodes],
        metadata={"kdf_node_ids": [n.id for n in nodes]},
    )

def to_kdf_nodes(result: CoreResult) -> list[KDFNode]:
    """LayerForge の蒸留結果を KDF ノードとして書き戻し"""
    return [
        KDFNode(
            content=layer.distillation.basis_summary,
            metadata={"layer_id": layer.layer_id},
            parent_relations=extract_relations(result, layer),
        )
        for layer in result.layers
    ]
```

### Verification Forge Integration

```python
# layerforge/integration/verification_forge.py

def verify_invariants(result: CoreResult) -> VerificationReport:
    """LayerForge の不変性を Verification Forge で形式検証"""
    invariants = [
        f"layer_count_in_range_3_5({result.quality_metrics.layer_count})",
        f"modularity_above_threshold({result.quality_metrics.modularity})",
        # ...
    ]
    return verification_forge.verify(invariants)
```

これらの統合は Phase 3 で実装（ADR-010 参照）。
