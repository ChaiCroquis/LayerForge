# 04. Test Cases

採用論文の数式を **境界条件として** テストケース化したもの。
これらが pass することが、LayerForge の正しさを保証する。

テスト分類:
- `axioms/` : 採用論文の数式そのものの検証（このファイルの主内容）
- `integration/` : §05 統合フローのテスト
- `boundary/` : エッジケース・反証実験

---

## 共通フィクスチャ

```python
# tests/conftest.py
import numpy as np
import pytest
from dataclasses import dataclass

@pytest.fixture
def fixed_seed():
    """全テスト共通のseed固定"""
    np.random.seed(42)
    return 42

@pytest.fixture
def synthetic_layered_data():
    """
    既知のレイヤー構造を持つ合成データ
    - 4 layers (Cowan optimal)
    - each layer has 10 nodes
    - clear separation in embedding space
    """
    np.random.seed(42)
    layers = []
    for layer_id in range(4):
        center = np.random.randn(768) * 10
        nodes = center + np.random.randn(10, 768) * 0.5
        layers.append({"id": layer_id, "embeddings": nodes})
    return layers

@pytest.fixture
def synthetic_flat_data():
    """構造を持たないフラットデータ（反証実験用）"""
    np.random.seed(42)
    return np.random.randn(40, 768)
```

---

## A1: HERCULES Axioms

### test_hercules_recursion.py

#### T1.1 階層構造の整合性

```python
def test_hierarchy_levels_are_monotonic(synthetic_layered_data):
    """
    Axiom: |L_{i+1}| < |L_i| for all i
    各レベルのクラスタ数は単調減少
    """
    result = layerforge_core(synthetic_layered_data)
    sizes = [len(layer) for layer in result.hierarchy.layers]
    assert all(sizes[i] > sizes[i+1] for i in range(len(sizes)-1))
```

#### T1.2 L0 ノードの完全性

```python
def test_l0_nodes_fully_covered(synthetic_layered_data):
    """
    Axiom: 全 L0 ノードがいずれかの上位クラスタに所属
    """
    total_input = sum(len(layer["embeddings"]) for layer in synthetic_layered_data)
    result = layerforge_core(synthetic_layered_data)
    
    l0_count = sum(c.l0_descendants_count for c in result.hierarchy.top_clusters)
    assert l0_count == total_input
```

#### T1.3 representation_vector の継承

```python
def test_parent_centroid_equals_children_mean(synthetic_layered_data):
    """
    Axiom F1.5: rep_vector(parent) = mean(rep_vector(children))
    Direct mode のみ
    """
    result = layerforge_core(synthetic_layered_data, mode="direct")
    for cluster in result.hierarchy.all_clusters:
        if cluster.children:
            expected = np.mean([c.representation_vector for c in cluster.children], axis=0)
            np.testing.assert_allclose(
                cluster.representation_vector, 
                expected, 
                rtol=1e-5
            )
```

#### T1.4 K-Means の決定性

```python
def test_kmeans_deterministic(synthetic_layered_data, fixed_seed):
    """
    Axiom: random_state 固定で出力が完全再現
    """
    result1 = layerforge_core(synthetic_layered_data, seed=fixed_seed)
    result2 = layerforge_core(synthetic_layered_data, seed=fixed_seed)
    
    for c1, c2 in zip(result1.hierarchy.all_clusters, result2.hierarchy.all_clusters):
        np.testing.assert_array_equal(c1.member_indices, c2.member_indices)
```

#### T1.5 Resampling 後の安定性

```python
def test_resampling_improves_stability(synthetic_layered_data):
    """
    Axiom: resampling 後の centroid は外れ値の影響を受けにくい
    """
    # 外れ値を追加
    contaminated = add_outliers(synthetic_layered_data, n_outliers=5)
    
    result_with = layerforge_core(contaminated, use_resampling=True)
    result_without = layerforge_core(contaminated, use_resampling=False)
    
    # resampling ありの方が真の中心に近い
    true_centers = compute_true_centers(synthetic_layered_data)
    assert centroid_distance(result_with, true_centers) < centroid_distance(result_without, true_centers)
```

---

## A2: SCA Axioms

### test_sca_residual.py

注: SCAは PCA と異なる以下の性質を持つ。テストはこれに合わせる:
- component は cluster centroid を unit vector 化したもの（厳密直交ではない）
- decomposition は **条件付き** (α threshold を超えた activation のみ)
- merging は **embedding の cos 類似度ではなく token 表現の overlap** (θ) で判定
- 3つのハイパーパラメータ (α, μ, θ) と3つの停止条件 (F, NC-S, RN) を持つ

#### T2.1 component の単位ベクトル性 (原論文 Eq. 1)

```python
def test_components_are_unit_vectors():
    """
    Axiom F2.2: ||v_i|| = 1 for all semantic components
    各 component は cluster centroid を ||・|| で正規化したもの
    """
    X = generate_test_data()
    components, _ = run_sca(X, mu=0.95, alpha=0.20)
    
    for v in components:
        assert abs(np.linalg.norm(v) - 1.0) < 1e-6
```

#### T2.2 token overlap による merging の正しさ

```python
def test_merging_by_token_overlap():
    """
    Axiom F2.4 / 原論文 §3.6:
    O(R1, R2) = (1/10) · |R1 ∩ R2|
    O > θ なら同じ topic ID にマージ、最初の topic の表現を保持
    
    注意: これは embedding の cos類似度 ではなく、token表現 (c-TF-IDF top-10) の overlap
    """
    components = [v_a, v_b, v_c]  # 適当な3つの component
    token_reps = [
        {"foo", "bar", "baz", "qux", "alpha", "beta", "gamma", "delta", "epsilon", "zeta"},
        {"foo", "bar", "baz", "qux", "alpha", "x1", "x2", "x3", "x4", "x5"},  # 5 overlap with #0
        {"y1", "y2", "y3", "y4", "y5", "y6", "y7", "y8", "y9", "y10"},  # no overlap
    ]
    
    merged_comp, merged_tokens = merge_overlapping_components(
        components, token_reps, theta=0.4
    )
    
    # #1 は #0 と overlap 5/10 = 0.5 > 0.4 → マージされる (消える)
    # #2 は overlap なし → 保持される
    assert len(merged_comp) == 2
    assert "foo" in merged_tokens[0]  # #0 の表現が保持
    assert "y1" in merged_tokens[1]   # #2 がそのまま


def test_merging_no_overlap_means_no_merge():
    """
    Axiom: token 表現の overlap が θ 以下なら、 embedding が類似していてもマージしない
    (これが PCA-based手法 との違い)
    """
    # 故意に embedding は近いが token は重ならない pair
    similar_embedding_components = [v1, v2]  # cos_sim(v1, v2) ≈ 0.95
    distinct_tokens = [
        {f"a{i}" for i in range(10)},
        {f"b{i}" for i in range(10)},  # 全く重ならない
    ]
    
    merged_comp, _ = merge_overlapping_components(
        similar_embedding_components, distinct_tokens, theta=0.5
    )
    
    # embedding は似ているがマージされない
    assert len(merged_comp) == 2
```

#### T2.3 conditional activation の正しさ (原論文 Eq. 2 + §A.2)

```python
def test_conditional_activation():
    """
    Axiom F2.3 / 原論文 Eq. 2:
    decomposition は α_{i,j} > α_threshold の場合のみ行われる
    
    a_j = μ · 1_{α_{i,i} > α} · ⟨x'_j, v_j⟩
    
    つまり activation 値が閾値以下なら activation は 0 になる
    """
    # cos類似度が α 以下になるよう設計したサンプル
    x_orthogonal = np.array([0.0, 1.0, 0.0])  # v_test と直交
    v_test = np.array([1.0, 0.0, 0.0])
    
    activations = compute_activations(
        embeddings=np.array([x_orthogonal]),
        components=[v_test],
        mu=0.95,
        alpha=0.20,
    )
    
    # ⟨x, v⟩ = 0 < α=0.20 なので activation も 0
    assert activations[0, 0] == 0.0


def test_activation_value_when_above_threshold():
    """
    Axiom F2.3:
    α_{i,i} > α の場合、activation = μ · ⟨x'_i, v_i⟩
    """
    x_aligned = np.array([0.8, 0.6, 0.0])
    v_test = np.array([1.0, 0.0, 0.0])
    
    # α_{i,i} = ⟨x, v⟩ / ||x|| = 0.8 / 1.0 = 0.8 > 0.20 (= α)
    
    activations = compute_activations(
        embeddings=np.array([x_aligned]),
        components=[v_test],
        mu=0.95,
        alpha=0.20,
    )
    
    expected = 0.95 * np.dot(x_aligned, v_test)  # μ · ⟨x, v⟩
    assert abs(activations[0, 0] - expected) < 1e-6
```

#### T2.4 residual と decomposition の関係 (原論文 Eq. 2)

```python
def test_residual_after_decomposition():
    """
    Axiom F2.3 / 原論文 Eq. 2:
    x'_j = x_j - μ · 1_{α_{i,j} > α} · ⟨x_j, v_i⟩ · v_i
    
    decomposition 後の residual は元の embedding から
    activation 方向を引いたもの
    """
    np.random.seed(42)
    x = np.random.randn(768)
    v = np.random.randn(768)
    v = v / np.linalg.norm(v)  # unit vector
    
    mu = 0.95
    alpha_threshold = 0.20
    alpha_ij = np.dot(x, v) / np.linalg.norm(x)
    
    # 1回の decomposition step
    if alpha_ij > alpha_threshold:
        expected_residual = x - mu * np.dot(x, v) * v
    else:
        expected_residual = x  # 変化なし
    
    result = single_decomposition_step(x, v, mu=mu, alpha=alpha_threshold)
    
    np.testing.assert_allclose(result, expected_residual, atol=1e-6)


def test_decomposition_reduces_alignment_with_component():
    """
    Axiom: μ=1 で decomposition 後の residual は v に直交する
    """
    x = np.random.randn(768)
    v = np.random.randn(768)
    v = v / np.linalg.norm(v)
    
    x_residual = single_decomposition_step(x, v, mu=1.0, alpha=0.0)
    
    # μ=1 で完全に v 方向の成分を除去 → residual ⊥ v
    inner = np.dot(x_residual, v)
    assert abs(inner) < 1e-5


def test_partial_decomposition_with_mu():
    """
    Axiom: μ < 1 では decomposition 後も v に部分的に残る (superposition 許容)
    """
    x = np.random.randn(768)
    v = np.random.randn(768) 
    v = v / np.linalg.norm(v)
    
    mu = 0.5
    x_residual = single_decomposition_step(x, v, mu=mu, alpha=0.0)
    
    # μ=0.5 では (1-μ)=0.5 分が残る
    original_alignment = np.dot(x, v)
    residual_alignment = np.dot(x_residual, v)
    
    expected_alignment = original_alignment * (1 - mu)
    assert abs(residual_alignment - expected_alignment) < 1e-5
```

#### T2.5 停止条件 F (max_iter) の動作

```python
def test_stopping_criterion_F_max_iter():
    """
    Axiom F2.4 / 原論文 §A.3:
    F: max_iter に到達したら停止
    """
    X = generate_complex_data(n=1000)  # 多数の component を持つ
    
    # max_iter = 3 で強制停止
    components, _ = run_sca(X, max_iter=3, mu=0.95, alpha=0.20)
    
    # 停止していること自体は例外を投げないことで確認
    # 加えて、3回の反復分だけ component が生成されている (上限)
    # 各反復で複数 component が出るので exact数は確定できないが、
    # 制限なしで動かした場合より少ないはず
    components_unlimited, _ = run_sca(X, max_iter=100, mu=0.95, alpha=0.20)
    
    assert len(components) <= len(components_unlimited)
```

#### T2.6 停止条件 NC-S (新規 component 不足) の動作

```python
def test_stopping_criterion_NC_S():
    """
    Axiom F2.4 / 原論文 §A.3:
    NC-S: 直近 nc_s イテレーションでの新規 component 数 < nc_threshold で停止
    
    LayerForge default: nc_s=2, nc_threshold=5
    """
    # 簡単なデータ (新規 component がすぐ枯渇)
    X = generate_simple_data(n=100, n_true_components=3)
    
    components, _ = run_sca(
        X,
        max_iter=100,
        nc_s=2,
        nc_threshold=5,
    )
    
    # 真の component 数 (3) 程度で停止しているはず
    # max_iter までは行かない
    assert len(components) < 20  # 経験的上限
```

#### T2.7 停止条件 RN (residual norm) の動作

```python
def test_stopping_criterion_RN_residual_norm():
    """
    Axiom F2.4 / 原論文 §A.3:
    RN: residual の行列 2-norm が rn_threshold 未満で停止
    
    LayerForge default: rn_threshold=0.01
    """
    # decomposition が完全に成功するよう設計したデータ
    X = generate_linearly_decomposable_data(n=100, n_components=3)
    
    components, final_residuals = run_sca(
        X,
        max_iter=100,
        rn_threshold=0.01,
        mu=1.0,  # 完全に分解
    )
    
    final_norm = np.linalg.norm(final_residuals)
    assert final_norm < 0.01  # RN 条件を満たして停止
```

#### T2.8 ハイパーパラメータ default 値 (原論文 §C.1)

```python
def test_hyperparameter_defaults():
    """
    Axiom F2.9: LayerForge default は原論文 §C.1 Trump dataset の値
    """
    from layerforge.constants import (
        SCA_DEFAULT_MU,
        SCA_DEFAULT_ALPHA,
        SCA_DEFAULT_THETA,
        SCA_DEFAULT_MIN_CLUSTER_SIZE,
        SCA_DEFAULT_MIN_SAMPLES,
        SCA_DEFAULT_MAX_ITER,
        SCA_DEFAULT_NC_S,
        SCA_DEFAULT_NC_THRESHOLD,
        SCA_DEFAULT_RN_THRESHOLD,
    )
    
    assert SCA_DEFAULT_MU == 0.95
    assert SCA_DEFAULT_ALPHA == 0.20
    assert SCA_DEFAULT_THETA == 0.5
    assert SCA_DEFAULT_MIN_CLUSTER_SIZE == 100
    assert SCA_DEFAULT_MIN_SAMPLES == 50
    assert SCA_DEFAULT_MAX_ITER == 10
    assert SCA_DEFAULT_NC_S == 2
    assert SCA_DEFAULT_NC_THRESHOLD == 5
    assert SCA_DEFAULT_RN_THRESHOLD == 0.01
```

#### T2.9 UMAP + HDBSCAN の決定論性

```python
def test_clustering_determinism():
    """
    Axiom: SCA の Step 1 (UMAP + HDBSCAN) は random_state 固定で決定論的
    
    注意 (原論文 §B.1):
    cuML の GPU 実装は CPU 版と結果が一致しない場合がある。
    LayerForge は umap-learn (CPU) を使用して決定論性を担保する。
    """
    X = generate_test_data()
    
    components_1, _ = run_sca(X, random_state=42)
    components_2, _ = run_sca(X, random_state=42)
    
    assert len(components_1) == len(components_2)
    for v1, v2 in zip(components_1, components_2):
        np.testing.assert_allclose(v1, v2, atol=1e-8)
```

#### T2.10 LayerForge schema (DistillationResult) の整合性

```python
def test_distillation_result_schema():
    """
    Axiom F2.6: distill_layer の出力 schema 正しさ
    """
    X = generate_test_data()
    nodes = make_nodes(X)
    
    distillation = distill_layer(
        layer_nodes=nodes,
        embeddings=X,
        mu=0.95,
        alpha=0.20,
        theta=0.5,
    )
    
    # schema 充足
    assert isinstance(distillation.components, tuple)
    assert all(v.shape[0] == X.shape[1] for v in distillation.components)  # 各 unit vector
    
    n_components = len(distillation.components)
    assert distillation.activations.shape == (len(X), n_components)
    
    assert distillation.residuals.shape == X.shape
    assert distillation.residual_norms.shape == (len(X),)
    
    assert isinstance(distillation.token_representations, tuple)
    assert len(distillation.token_representations) == n_components
    assert all(isinstance(t, frozenset) for t in distillation.token_representations)
    
    assert isinstance(distillation.is_converged, bool)


def test_distillation_result_is_frozen():
    """
    Axiom ADR-007: DistillationResult は frozen
    """
    X = generate_test_data()
    distillation = distill_layer(make_nodes(X), X)
    
    with pytest.raises(Exception):  # FrozenInstanceError or AttributeError
        distillation.components = ()
```

#### T2.11 純度 (purity) と残差の関係 (F2.7)

```python
def test_purity_inverse_of_residual():
    """
    Axiom F2.7: purity が高い ⇔ 最大残差が小さい
    purity = 1 - max(residual_norms) / max(embedding_norms)
    """
    clean_data = generate_clean_data()      # 同一クラスタ性が高い
    noisy_data = generate_noisy_data()      # ばらつきが大きい
    
    p_clean = compute_layer_purity(
        distill_layer(make_nodes(clean_data), clean_data),
        clean_data,
    )
    p_noisy = compute_layer_purity(
        distill_layer(make_nodes(noisy_data), noisy_data),
        noisy_data,
    )
    
    assert p_clean > p_noisy
    assert p_clean > PURITY_THRESHOLD_GOOD


def test_purity_threshold_constants():
    """
    Axiom F2.7: 閾値定数の値
    """
    from layerforge.constants import (
        PURITY_THRESHOLD_GOOD, PURITY_THRESHOLD_ACCEPTABLE
    )
    assert PURITY_THRESHOLD_GOOD == 0.7
    assert PURITY_THRESHOLD_ACCEPTABLE == 0.5
    assert PURITY_THRESHOLD_GOOD > PURITY_THRESHOLD_ACCEPTABLE


def test_purity_bounds():
    """
    Axiom F2.7: purity ∈ [0, 1]
    """
    X = generate_test_data()
    distillation = distill_layer(make_nodes(X), X)
    purity = compute_layer_purity(distillation, X)
    
    assert 0.0 <= purity <= 1.0
```

#### T2.12 multi-topic assignment (F2.5)

```python
def test_multi_topic_assignment_via_activations():
    """
    Axiom F2.5: activations[i, k] > activation_threshold のサンプルは
    component k に属する。1サンプルが複数 component に属しうる。
    """
    # 複数 component にまたがるよう設計したデータ
    X = generate_multi_topic_data()
    distillation = distill_layer(
        layer_nodes=make_nodes(X),
        embeddings=X,
    )
    
    activation_threshold = 0.3
    
    # 全サンプル中、複数アサインされる比率
    multi_assigned = sum(
        1 for i in range(len(X))
        if (distillation.activations[i] > activation_threshold).sum() > 1
    )
    
    # 設計上、複数 topic にまたがるサンプルが存在するはず
    assert multi_assigned > 0
```

#### T2.13 巨大 generic cluster の検出 (F2.8 LayerForge 拡張)

```python
def test_giant_cluster_warning():
    """
    Axiom F2.8 (LayerForge 拡張):
    単一 component が全サンプルの 30% 以上にアクティブな場合は warning
    (原論文 §C.1 error analysis で報告された問題)
    """
    # 故意に1つの巨大トピックを持つデータ
    X_with_giant = generate_data_with_giant_topic(
        n=1000,
        giant_ratio=0.5,  # 全体の50%が同じ topic
    )
    
    distillation = distill_layer(make_nodes(X_with_giant), X_with_giant)
    
    # 検出関数が warning を発するか
    warnings_list = detect_giant_clusters(
        distillation,
        threshold_ratio=0.3,
    )
    
    assert len(warnings_list) >= 1  # 少なくとも1つの巨大 cluster
```

#### T2.14 SCA Step1 = BERTopic との等価性 (原論文の主張検証)

```python
def test_first_iteration_equals_bertopic():
    """
    Axiom (原論文 §3 末尾):
    SCA の 1回目イテレーション = BERTopic と同じ結果
    
    LayerForge では BERTopic を参考実装として置き、
    回帰テストとして使う
    """
    X = generate_test_data()
    
    # SCA 1イテレーションのみ
    sca_components, _ = run_sca(X, max_iter=1, mu=0.95, alpha=0.20)
    
    # BERTopic 参考実装
    bertopic_components = run_bertopic_reference(X)
    
    # 同じ数のトピック (SCA の Step 1 は BERTopic と同じ UMAP+HDBSCAN)
    assert len(sca_components) == len(bertopic_components)
    
    # 各 component が対応する (順序は異なるかもしれない)
    for v_sca in sca_components:
        # 最も近い BERTopic component との類似度
        max_sim = max(
            abs(np.dot(v_sca, v_bt)) 
            for v_bt in bertopic_components
        )
        assert max_sim > 0.95  # ほぼ同一
```

---

## A3: Cowan Constraint Axioms

### test_cowan_constraint.py

#### T3.1 制約定数の固定

```python
def test_layer_count_constants():
    """
    Axiom F3.1: 4±1 = [3, 5], optimal = 4
    """
    from layerforge.constants import (
        LAYER_COUNT_MIN, LAYER_COUNT_MAX, LAYER_COUNT_OPTIMAL
    )
    assert LAYER_COUNT_MIN == 3
    assert LAYER_COUNT_MAX == 5
    assert LAYER_COUNT_OPTIMAL == 4
```

#### T3.2 範囲内判定

```python
@pytest.mark.parametrize("n,expected", [
    (2, False),  # too coarse
    (3, True),
    (4, True),
    (5, True),
    (6, False),  # too granular
    (10, False),
])
def test_is_layer_count_valid(n, expected):
    """
    Axiom F3.2: [3, 5] のみ valid
    """
    assert is_layer_count_valid(n) == expected
```

#### T3.3 4±1 への収束

```python
def test_scale_search_converges_to_4_plus_minus_1(synthetic_layered_data):
    """
    Axiom F3.3: 適切な scale_coefficient が存在し、binary search で見つかる
    """
    embeddings = np.concatenate([l["embeddings"] for l in synthetic_layered_data])
    S = build_similarity_matrix(embeddings)
    
    theta, n_layers = find_valid_scale(S, target_range=(3, 5))
    
    assert 3 <= n_layers <= 5
    assert 0.0 <= theta <= 1.0
```

#### T3.4 制約違反時の自動調整

```python
def test_too_many_clusters_triggers_threshold_increase(over_segmented_data):
    """
    Axiom F3.3: クラスタが多すぎる → threshold を上げて統合
    """
    initial_theta = 0.3
    final_theta, n_layers = adjust_scale(over_segmented_data, initial_theta)
    
    assert final_theta > initial_theta  # 閾値が上がっている
    assert n_layers <= LAYER_COUNT_MAX
```

#### T3.5 解なし問題の検出

```python
def test_unresolvable_problem_raises(unresolvable_data):
    """
    Axiom: 4±1 に収まらない問題 → NoValidScaleError
    これは「問題設定が壊れている」診断指標として機能する
    """
    with pytest.raises(NoValidScaleError):
        layerforge_core(unresolvable_data)
```

#### T3.6 再帰深度制約

```python
def test_max_recursion_depth(deep_hierarchy_data):
    """
    Axiom F3.4: 再帰深度は MAX_RECURSION_DEPTH を超えない
    """
    result = layerforge_core(deep_hierarchy_data, max_depth=4)
    
    def get_max_depth(cluster, current_depth=0):
        if not cluster.children:
            return current_depth
        return max(get_max_depth(c, current_depth+1) for c in cluster.children)
    
    for top_cluster in result.hierarchy.top_clusters:
        assert get_max_depth(top_cluster) <= 4
```

---

## A4: Modularity Axioms

### test_modularity.py

注: Newman 2006 原論文に従い、以下の側面をテストする:
- 多コミュニティ版 modularity Q (F4.2)
- Spectral algorithm (F4.3-F4.5)
- Indivisibility 判定 (F4.9)
- 重み付きグラフへの一般化

#### T4.1 modularity の値域 (原論文 §"Modularity range")

```python
def test_modularity_value_range(synthetic_layered_data):
    """
    Axiom F4.1: Q ∈ [-0.5, 1.0]
    """
    result = layerforge_core(synthetic_layered_data)
    assert -0.5 <= result.quality_metrics.modularity <= 1.0
```

#### T4.2 完全分離での最大値 (原論文 Table 1)

```python
def test_modularity_max_for_complete_separation():
    """
    Axiom: 完全に分離されたグラフでは Q → 1
    
    Newman 原論文 Table 1 では実データで 0.4-0.85 だが、
    人工的に完全分離したデータでは 0.7 以上が出るはず
    """
    perfectly_separated = generate_disconnected_clusters(n_clusters=4, n_per_cluster=10)
    
    result = layerforge_core(perfectly_separated)
    assert result.quality_metrics.modularity > 0.7
```

#### T4.3 ランダムグラフでのほぼゼロ

```python
def test_modularity_near_zero_for_random():
    """
    Axiom: ランダムグラフでは Q ≈ 0
    (原論文 §"Modularity": "the modularity is the number of edges falling 
    within groups minus the expected number in an equivalent network with 
    edges placed at random")
    """
    random_data = synthetic_flat_data()  # 構造なし
    
    try:
        result = layerforge_core(random_data)
        assert abs(result.quality_metrics.modularity) < 0.3
    except NoValidScaleError:
        # 4±1 に収まらず失敗するのも正解（構造がないため）
        pass
```

#### T4.4 重み付きグラフでの一般化 (LayerForge 拡張)

```python
def test_weighted_modularity_consistency():
    """
    Axiom F4.6: 重み付き類似度行列でも Q が定義される
    
    注: Newman 原論文は unweighted graph (A_ij ∈ {0,1}) が主だが、
    threshold で binary化することで重み付きへ拡張可能
    """
    similarity_matrix = generate_weighted_similarity()
    labels = generate_labels()
    
    Q = compute_modularity(similarity_matrix, labels, threshold=0.0)
    assert isinstance(Q, float)
    assert not np.isnan(Q)
    assert -0.5 <= Q <= 1.0
```

#### T4.5 Spectral Algorithm: leading eigenvalue による2分割 (F4.3)

```python
def test_spectral_partition_via_leading_eigenvector():
    """
    Axiom F4.3 / 原論文 §"Method of optimal modularity":
    1. B = A - kk^T / (2m) を計算
    2. B の leading eigenvector u_1 を求める
    3. s_i = +1 if u_1[i] > 0 else -1
    
    これでネットワークが2分割される
    """
    # 既知の2-community 構造を持つ karate club ライクなデータ
    similarity = generate_karate_club_like_data()
    
    labels, Q, is_indivisible = compute_modularity_spectral(similarity)
    
    # 2-community 検出
    assert len(np.unique(labels)) == 2
    assert not is_indivisible
    assert Q > 0  # 正のmodularity (分割が有意味)
```

#### T4.6 Indivisibility 判定 (F4.3, 原論文 §"Indivisible subgraphs")

```python
def test_indivisibility_when_no_positive_eigenvalue():
    """
    Axiom F4.9 / 原論文:
    Modularity matrix B の leading eigenvalue β_1 ≤ 0 なら
    そのネットワークは indivisible (これ以上分割しても Q は増えない)
    """
    # 完全グラフ (全頂点が均等に接続、構造なし)
    n = 10
    complete_similarity = np.ones((n, n)) - np.eye(n)
    
    labels, Q, is_indivisible = compute_modularity_spectral(complete_similarity)
    
    # 完全グラフは indivisible のはず
    assert is_indivisible
    assert Q == 0.0


def test_can_subdivide_layer_helper():
    """
    Axiom F4.9: can_subdivide_layer は indivisibility の逆
    """
    indivisible_data = generate_indivisible_graph()
    divisible_data = generate_clear_community_graph()
    
    assert can_subdivide_layer(indivisible_data) == False
    assert can_subdivide_layer(divisible_data) == True
```

#### T4.7 Spectral algorithm の karate club ケース (原論文 Fig. 2)

```python
def test_karate_club_known_partition():
    """
    Axiom (回帰テスト): 原論文 Fig. 2 の karate club ネットワークで
    Newman の spectral 算法が known partition を再現する
    
    これは Newman 原論文の最も有名な例であり、
    実装の正しさの強い証拠となる
    """
    # 標準的な karate club データ (公開データセット)
    A = load_zachary_karate_club()
    similarity = A.astype(float)  # adjacency をそのまま類似度として
    
    labels, Q, _ = compute_modularity_spectral(similarity)
    
    # 原論文の Q ≈ 0.393 (spectral のみ、fine-tuning 前)
    assert 0.35 < Q < 0.45
    
    # 既知の2派閥との一致率
    known_factions = load_zachary_known_factions()
    agreement = max(
        np.mean(labels == known_factions),
        np.mean(labels != known_factions),  # ラベルの順序が逆の場合
    )
    assert agreement > 0.9  # ほぼ完全一致を期待
```

#### T4.8 Generalized modularity matrix (F4.4, 原論文 Eq. 6)

```python
def test_generalized_modularity_matrix_for_subgraph():
    """
    Axiom F4.4 / 原論文 Eq. 6:
    B^(g)_ij = B_ij - δ_ij · Σ_{k∈g} B_ik
    
    サブグラフを再帰的に分割する際に使う
    """
    full_similarity = generate_test_similarity()
    subgraph_indices = [0, 1, 2, 3, 4]
    
    B_g = compute_generalized_modularity_matrix(full_similarity, subgraph_indices)
    
    # B^(g) の行和・列和が 0 (原論文の指摘)
    row_sums = B_g.sum(axis=1)
    assert np.allclose(row_sums, 0, atol=1e-8)


def test_recursive_subdivision_via_generalized_matrix():
    """
    Axiom F4.4: B^(g) を使った再帰的分割で複数コミュニティを発見可能
    """
    # 4コミュニティ構造のデータ
    multi_community_data = generate_n_community_graph(n_communities=4)
    
    # 再帰的分割
    final_labels = newman_recursive_subdivision(multi_community_data)
    
    # 4コミュニティが検出される
    assert len(np.unique(final_labels)) == 4
```

#### T4.9 断熱近似の判定 (F4.8)

```python
def test_adiabatic_approximation_detection(synthetic_layered_data):
    """
    Axiom F4.8: Q ≥ MODULARITY_THRESHOLD_GOOD ⇔ 断熱近似が有効
    """
    result = layerforge_core(synthetic_layered_data)
    
    if result.quality_metrics.modularity >= MODULARITY_THRESHOLD_GOOD:
        # 各レイヤーが独立に処理可能であるべき
        for layer in result.layers:
            layer_embeddings = extract_embeddings(layer)
            distillation = distill_layer(layer.member_nodes, layer_embeddings)
            assert distillation.is_converged
```

#### T4.10 Newman の効率的実装 (F4.5)

```python
def test_efficient_B_multiplication():
    """
    Axiom F4.5 / 原論文 Eq. 7:
    B · x = A · x - k · (k^T · x) / (2m)
    
    sparse な A を使うことで O(m + n) で計算可能
    """
    np.random.seed(42)
    n = 100
    A = generate_sparse_adjacency(n)
    k = A.sum(axis=1)
    m_total = A.sum() / 2
    
    x = np.random.randn(n)
    
    # 効率的計算
    Bx_efficient = A @ x - k * (k @ x) / (2 * m_total)
    
    # 直接計算
    B = A.astype(float) - np.outer(k, k) / (2 * m_total)
    Bx_direct = B @ x
    
    np.testing.assert_allclose(Bx_efficient, Bx_direct, atol=1e-10)
```

---

## Determinism Axioms

### test_determinism.py

#### TD.1 同一入力 → 同一出力

```python
def test_core_deterministic(synthetic_layered_data, fixed_seed):
    """
    ADR-002: 決定論層は同一入力で同一出力
    """
    np.random.seed(fixed_seed)
    result1 = layerforge_core(synthetic_layered_data)
    
    np.random.seed(fixed_seed)
    result2 = layerforge_core(synthetic_layered_data)
    
    assert result1 == result2  # frozen dataclass の __eq__
```

#### TD.2 部分入力の独立性

```python
def test_subsets_independent(synthetic_layered_data, fixed_seed):
    """
    Axiom: 入力の subset 処理が、subset外の影響を受けない
    """
    subset_a = synthetic_layered_data[:2]
    subset_b = synthetic_layered_data[2:]
    
    np.random.seed(fixed_seed)
    result_a = layerforge_core(subset_a)
    
    np.random.seed(fixed_seed)
    result_b = layerforge_core(subset_b)
    
    # それぞれ独立に処理されるべき
    assert result_a.hierarchy != result_b.hierarchy
```

---

## Property-Based Tests (内包確認)

### test_containment_properties.py

これらは採用しなかった論文 (B1-B3) の主張を、LayerForge が自動的に満たしているかの確認。

#### TP.1 スケール分離性 (RGMem 内包)

```python
from hypothesis import given, strategies as st

@given(scale_factor=st.floats(min_value=0.5, max_value=2.0))
def test_scale_invariance_property(scale_factor, synthetic_layered_data):
    """
    Property: scale_factor を変えても、レイヤー構造のトポロジーは保存される
    (RGMem の主張: スケール不変な構造の存在)
    """
    original = layerforge_core(synthetic_layered_data)
    scaled = layerforge_core(synthetic_layered_data, scale_multiplier=scale_factor)
    
    # トポロジー（接続関係）は同じ
    assert original.hierarchy.topology == scaled.hierarchy.topology
```

#### TP.2 層数と内在相関長 (RG-DL 内包)

```python
@given(correlation_length=st.floats(min_value=1.0, max_value=20.0))
def test_layer_count_logarithmic_in_correlation_length(correlation_length):
    """
    Property: 必要レイヤー数 ∝ log(intrinsic correlation length)
    (RG-DL Principles H2 の主張)
    """
    data = generate_data_with_correlation_length(correlation_length)
    result = layerforge_core(data)
    
    n_layers = len(result.hierarchy.layers)
    
    # log の比例関係を確認
    expected = int(np.log2(correlation_length)) + 1
    assert abs(n_layers - expected) <= 1
```

#### TP.3 階層的タスク分解 (HiAgent 内包)

```python
def test_hierarchical_task_decomposition_applicable():
    """
    Property: LayerForgeをタスク分解に適用可能
    (HiAgent の階層WM管理が実現可能)
    """
    tasks = generate_task_descriptions()  # natural language tasks
    result = layerforge_core(tasks)
    
    # 各レイヤーが意味的に独立したサブタスクを表す
    for layer in result.hierarchy.layers:
        assert layer.semantic_independence_score > 0.7
```

---

## Boundary Tests (エッジケース)

### test_boundaries.py

#### TB.1 単一ノード

```python
def test_single_node_input():
    """単一ノード入力は分解不要、そのまま返す"""
    result = layerforge_core([single_node])
    assert len(result.hierarchy.layers) == 1
    assert result.hierarchy.layers[0].nodes == [single_node]
```

#### TB.2 同一ノードの重複

```python
def test_identical_nodes():
    """同じノードが10個 → 1レイヤーに集約"""
    identical_nodes = [node] * 10
    result = layerforge_core(identical_nodes)
    # 4±1 に収まらないが、診断として valid な失敗
    # または、自動的に1クラスタとして処理
```

#### TB.3 完全直交ノード

```python
def test_orthogonal_nodes():
    """全ノードが完全直交 → 分解不可能"""
    orthogonal = np.eye(10)
    with pytest.raises(NoValidScaleError):
        layerforge_core(orthogonal)
```

#### TB.4 極端な不均衡

```python
def test_extreme_imbalance():
    """1つのクラスタが99%を占める → 警告付きで処理"""
    imbalanced = generate_imbalanced_data(majority_ratio=0.99)
    result = layerforge_core(imbalanced)
    assert result.warnings  # 不均衡警告
```

---

## Test Coverage Goals

| Category | Target Coverage | テスト数の目安 |
|---|---|---|
| axioms/ | 100% (全公理の境界条件) | ~50本 |
| integration/ | 90% (統合フロー) | ~30本 |
| boundary/ | 全エッジケース網羅 | ~20本 |
| determinism/ | 100% (再現性は絶対要件) | ~20本 |

各 axiom セクションのテスト数 (本ドキュメント現状):
- T1 (HERCULES): 5本
- T2 (SCA): **14本** (v2で大幅拡張)
- T3 (Cowan): 6本
- T4 (Newman modularity + spectral algorithm): **10本** (v2でspectral追加)
- TD (Determinism): 2本+α
- TP (Property-based, 内包確認): 3本
- TB (Boundary): 4本

合計目標: pytest **約160-180 本程度**。
Verification Forge (578本) の規模感より小さくて済むが、初版見積もり (100-150本) より増加。

---

## Test 実行の決定論保証

```python
# tests/conftest.py
import os
import random
import numpy as np

@pytest.fixture(autouse=True)
def deterministic_environment():
    """全テストで決定論的環境を保証"""
    os.environ['PYTHONHASHSEED'] = '0'
    random.seed(42)
    np.random.seed(42)
    # sklearn 等の内部 random_state も全て固定
```

これにより、CI/ローカル/別環境で同じテスト結果が得られる。
