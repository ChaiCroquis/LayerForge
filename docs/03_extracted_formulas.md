# 03. Extracted Formulas

採用論文（A1-A4）から抽出した具体的な数式、アルゴリズム、入出力仕様。
実装時はこの文書を参照し、テストケース（§04）で境界条件を確認する。

---

## F1. HERCULES (A1) — Hierarchical Recursive Clustering

### F1.1 階層構造の定義

```
Hierarchy = {L_0, L_1, ..., L_n}
where:
  L_0 = {individual input items (leaf nodes)}
  L_i (i ≥ 1) = {clusters formed from L_{i-1}}
```

### F1.2 Level 0 初期化

```python
def initialize_level_0(D: Dataset, repr_mode: Literal["direct", "description"]) -> list[Cluster]:
    """
    Input: 
      D = list of data items (text/image/numeric)
      repr_mode = representation mode
    
    Output:
      C_0 = list of L0 Cluster objects
    
    Each cluster c ∈ C_0 has:
      - level = 0
      - children = [d_i]  (single item)
      - description = (LLM-generated or snippet)
      - description_embedding = E_text(description)
      - representation_vector = (E_text(d_i) if direct else description_embedding)
    """
```

### F1.3 階層クラスタリングループ

```
input:
  C_0: initial clusters
  k_config: cluster count per level (list or "auto")
  repr_mode: "direct" | "description"

procedure HierarchicalLoop(C_0, k_config, repr_mode):
  C_current = C_0
  while |C_current| > min_clusters:
    I = collect_representation_vectors(C_current, repr_mode)
    k = determine_k(I, k_config)
    if k ≤ 1: break
    
    labels, centroids = KMeans(I, k)
    
    # Optional: iterative resampling refinement
    if use_resampling:
      for s in range(m):
        R = ∅
        for j in range(k):
          I_j = {v ∈ I | label(v) = j}
          R_j = {r_t closest points in I_j to centroids[j]}
          R = R ∪ R_j
        _, centroids = KMeans(R, k)
        labels = Assign(I, centroids)
    
    C_next = create_parent_clusters(C_current, labels, centroids)
    summarize_with_llm(C_next)
    C_current = C_next
  
  return C_current
```

### F1.4 K (クラスタ数) 決定

LayerForge では HERCULES の `determine_k` を以下に拡張する：

```python
def determine_k_with_layer_constraint(
    similarity_matrix: np.ndarray,
    target_range: tuple[int, int] = (3, 5)  # Cowan's 4±1
) -> int:
    """
    Goal: layer count after recursive application falls in [3, 5]
    Method: binary search over scale_coefficient θ
    """
    theta_low, theta_high = 0.0, 1.0
    for _ in range(MAX_ITER):
        theta_mid = (theta_low + theta_high) / 2
        n_clusters = count_clusters_at_threshold(similarity_matrix, theta_mid)
        if n_clusters > target_range[1]:
            theta_low = theta_mid  # 閾値を上げる → クラスタが減る
        elif n_clusters < target_range[0]:
            theta_high = theta_mid  # 閾値を下げる → クラスタが増える
        else:
            return n_clusters  # ∈ [3, 5]
    raise NoValidScaleError("4±1 に収まる θ が存在しない")
```

### F1.5 表現ベクトルの上昇

Direct mode (i ≥ 1):
```
rep_vector(c_parent) = centroid({rep_vector(c) for c in c_parent.children})
```

Description mode (i ≥ 1):
```
desc_embedding(c_parent) = E_text(LLM_summarize(c_parent.children))
rep_vector(c_parent) = desc_embedding(c_parent)
```

### F1.6 評価指標

```
Internal metrics:
  - Silhouette Score
  - Davies-Bouldin Index
  - Calinski-Harabasz Index

External metrics (ground truth available):
  - Adjusted Rand Index (ARI)
  - Normalized Mutual Information (NMI)
  - Homogeneity, Completeness, V-measure

LayerForge specific:
  - Topic Alignment Score = cos_sim(topic_seed_embedding, cluster_desc_embedding)
```

---

## F2. SCA (A2) — Semantic Component Analysis

論文出典: Eichin, Schuster, Groh, Hedderich (2024) arXiv:2410.21054v3
精読状況: full text 精読済み (★★★★★)
重要な訂正: 初版設計資料 (2026-05-11 早朝) では検索抜粋から再構成しており、
            ハイパーパラメータの対応関係と推奨値に誤りがあった。本版で訂正済み。

### F2.1 SCA の6ステップパイプライン (Methodology §3)

SCAは BERTopic の拡張で、以下の6ステップで構成される：

```
Step 0: Embed input sequences (e.g., SBERT)
Step 1: Reduce and Cluster the embeddings
        - UMAP (5次元へ圧縮、cosine距離)
        - HDBSCAN (Euclidean距離でクラスタリング)
Step 2: Represent each component as normalized centroid v_i
Step 3: Decompose each embedding into linear components
Step 4: Repeat Steps 1-3 on residual embeddings
Step 5: Represent components by c-TF-IDF tokens
Step 6: Merge topics whose token representations overlap > θ
```

### F2.2 Semantic Component の定義 (原論文 Eq. 1)

各クラスタ C_i に対する semantic component:

```
v_i = v'_i / ||v'_i||

where:
  v'_i = (1 / |C_i|) · Σ_{x_j ∈ C_i} x_j    (centroid)
  v_i ∈ R^D                                  (unit vector)
```

### F2.3 Decomposition (原論文 Eq. 2)

embedding x_j を component v_i 方向に分解（条件付き）：

```
x'_j = x_j - μ · 1_{α_{i,j} > α} · ⟨x_j, v_i⟩ · v_i

where:
  α_{i,j} = ⟨x_j, v_i⟩ / ||x_j||    : activation score (cos類似度)
  μ ∈ [0, 1]                          : decomposition の強度 (hyperparameter)
  α ∈ [0, 1]                          : activation threshold (hyperparameter)
  1_{condition} = 1 if condition else 0  : indicator function
```

**3つのハイパーパラメータの役割** (原論文 §A.1):

| Parameter | 範囲 | 役割 |
|---|---|---|
| `μ` | [0, 1] | 1つの decomposition step で activation の何割を引くか。μ=1 で完全除去、μ<1 で superposition を許可 |
| `α` | [0, 1] | activation がこの閾値を超えたら decompose する。α=0 で全 component に分解、α>0 で条件付き分解（superposition を許可） |
| `θ` | [0, 1] | merging step で「同じ topic とみなす token overlap 比」 |

**原論文 §C.1 の推奨値（Trump dataset）**:
- α = 0.20
- μ = 0.95
- θ = 0.5
- min_cluster_size = 100
- min_samples = 50

### F2.4 反復手続き

```python
def run_sca(
    X: np.ndarray,
    mu: float = 0.95,
    alpha: float = 0.20,
    theta: float = 0.5,
    max_iter: int = 10,
    nc_s: int = 2,        # NC-S 停止条件用
    nc_threshold: int = 5, # 同上
    rn_threshold: float = 0.01,  # RN 停止条件用
) -> tuple[list[np.ndarray], np.ndarray]:
    """
    SCA 反復本体
    
    停止条件 (原論文 §A.3):
    - F:    max_iter 到達
    - NC-S: 直近 nc_s イテレーションでの新規 component が nc_threshold 未満
    - RN:   residual 行列の2-norm が rn_threshold 未満
    """
    components = []
    new_components_per_iter = []
    embeddings = X.copy()
    
    for iteration in range(max_iter):
        # Step 1: UMAP + HDBSCAN
        reduced = umap_reduce(embeddings, dim=5, metric='cosine')
        cluster_labels = hdbscan_cluster(
            reduced,
            min_cluster_size=100,
            min_samples=50,
        )
        
        # Step 2: 各クラスタの normalized centroid を component に
        new_in_this_iter = 0
        for cluster_id in np.unique(cluster_labels):
            if cluster_id == -1:  # noise cluster
                continue
            members = embeddings[cluster_labels == cluster_id]
            v_prime = members.mean(axis=0)
            v_i = v_prime / np.linalg.norm(v_prime)
            components.append(v_i)
            new_in_this_iter += 1
        
        new_components_per_iter.append(new_in_this_iter)
        
        # Step 3: Decomposition (条件付き)
        for j in range(len(X)):
            x_j = embeddings[j]
            norm_x_j = np.linalg.norm(x_j)
            if norm_x_j < 1e-12:
                continue
            
            # 最新イテレーションで追加された component に対してのみ分解
            for v_i in components[-new_in_this_iter:]:
                alpha_ij = np.dot(x_j, v_i) / norm_x_j
                if alpha_ij > alpha:
                    inner = np.dot(x_j, v_i)
                    embeddings[j] = x_j - mu * inner * v_i
                    x_j = embeddings[j]
        
        # 停止条件チェック
        # RN: 残差ノルム
        residual_norm = np.linalg.norm(embeddings)
        if residual_norm < rn_threshold:
            break
        
        # NC-S: 直近 nc_s イテレーションでの新規追加数
        if len(new_components_per_iter) >= nc_s:
            recent_total = sum(new_components_per_iter[-nc_s:])
            if recent_total < nc_threshold:
                break
    
    return components, embeddings


def merge_overlapping_components(
    components: list[np.ndarray],
    token_representations: list[set[str]],  # c-TF-IDF top-10 tokens
    theta: float = 0.5,
) -> tuple[list[np.ndarray], list[set[str]]]:
    """
    Step 6: token overlap > θ の component を merge
    
    Overlap definition (原論文 §3.6):
        O(R1, R2) = (1/10) · |R1 ∩ R2|
    
    O > θ なら同じ topic ID にまとめ、最初の topic の表現を保持
    """
    merged_components = []
    merged_tokens = []
    
    for v_new, tokens_new in zip(components, token_representations):
        merged = False
        for i, tokens_existing in enumerate(merged_tokens):
            overlap = len(tokens_new & tokens_existing) / 10
            if overlap > theta:
                # 既存にマージ、新しい方は捨てる
                merged = True
                break
        if not merged:
            merged_components.append(v_new)
            merged_tokens.append(tokens_new)
    
    return merged_components, merged_tokens
```

### F2.5 SCA を線形変換として見る (原論文 §A.2)

decomposition は embedding 空間から component 空間への線形変換と解釈できる：

```
帰納的定義:
  x'_0 = x
  x'_{i+1} = x'_i - μ · 1_{α_{i,i} > α} · ⟨x'_i, v_i⟩ · v_i

サンプル x の j 番目 component へのアクティベーション:
  a_j = μ · 1_{α_{i,i} > α} · ⟨x'_j, v_j⟩

ここで α_{i,i} = ⟨x'_i, v_i⟩ / ||x'_i||
```

複数 component への所属はこのアクティベーションに threshold を適用して判定。

### F2.6 LayerForge への適用（蒸留式）

```python
@dataclass(frozen=True)
class DistillationResult:
    """単一レイヤーの蒸留結果"""
    components: tuple[np.ndarray, ...]      # basis
    activations: np.ndarray                  # shape: (n_nodes, n_components)
                                             # activations[j, i] = a_i for sample j
    residuals: np.ndarray                    # shape: (n_nodes, embedding_dim)
                                             # 最終 residual embedding
    residual_norms: np.ndarray               # shape: (n_nodes,)
    token_representations: tuple[frozenset[str], ...]
    is_converged: bool


def distill_layer(
    layer_nodes: tuple[Node, ...],
    embeddings: np.ndarray,
    mu: float = 0.95,
    alpha: float = 0.20,
    theta: float = 0.5,
    max_iter: int = 10,
) -> DistillationResult:
    """
    各レイヤーで SCA を実行して蒸留
    
    Note: ハイパーパラメータの選択は原論文 §A.1 + §C.1 に基づく
    LayerForge では Trump dataset の値を default として採用
    """
    # 1. SCA 本体
    components, final_residuals = run_sca(
        X=embeddings,
        mu=mu,
        alpha=alpha,
        max_iter=max_iter,
    )
    
    # 2. token 表現 (c-TF-IDF)
    token_reps = compute_ctfidf_per_cluster(layer_nodes, components)
    
    # 3. Merging step
    components, token_reps = merge_overlapping_components(
        components, token_reps, theta=theta
    )
    
    # 4. activations 計算 (F2.5 の a_j 式)
    activations = compute_activations(embeddings, components, mu=mu, alpha=alpha)
    
    # 5. residual norms
    residual_norms = np.linalg.norm(final_residuals, axis=1)
    
    # 6. 収束フラグ
    is_converged = np.linalg.norm(final_residuals) < 0.01  # RN 停止条件
    
    return DistillationResult(
        components=tuple(components),
        activations=activations,
        residuals=final_residuals,
        residual_norms=residual_norms,
        token_representations=tuple(frozenset(t) for t in token_reps),
        is_converged=is_converged,
    )
```

### F2.7 残差による品質判定

```python
def compute_layer_purity(distillation: DistillationResult, embeddings: np.ndarray) -> float:
    """
    purity ∈ [0, 1]
    - 1.0 = 残差ゼロ = component で完全に説明できる = レイヤーが純粋
    - 0.0 = 残差が embedding と同等 = 分解失敗
    """
    if len(distillation.residual_norms) == 0:
        return 0.0
    
    max_residual = np.max(distillation.residual_norms)
    max_embedding_norm = np.max(np.linalg.norm(embeddings, axis=1))
    
    if max_embedding_norm == 0:
        return 0.0
    
    return 1.0 - (max_residual / max_embedding_norm)


PURITY_THRESHOLD_GOOD = 0.7
PURITY_THRESHOLD_ACCEPTABLE = 0.5
```

### F2.8 SCA の限界と LayerForge での対処

原論文の明示的限界（§Limitations + §C.1 error analysis）:

1. **線形分解前提** (linear representation hypothesis, Park et al. 2024)
   - 非線形・多次元コンポーネントは1イテレーションで捕捉不可
   - 緩和策: μ < 1 と α > 0 で superposition を許容
2. **クラスタリングモジュールの依存性**
   - HDBSCAN の min_cluster_size に強く依存
   - dense な部分で「巨大な generic cluster」が形成されやすい
   - error analysis では impeachment topic が誤って全サンプルに割当られる例を報告
3. **token表現の解釈性限界**
   - 巨大 cluster の representation は generic で解釈困難

LayerForge での対処:
- **巨大generic cluster検出**: 単一 component が全サンプルの 30% 以上にアクティブな場合 warning
- **min_cluster_size 自動調整**: 4±1 制約と組み合わせて、過度な細分化/統合を避ける
- **ハイパーパラメータの問題依存性**: 原論文 §C.1 のグリッドサーチ表を参考に、データセット特性に応じて調整可能なAPIを提供

### F2.9 既知の暫定値 (LayerForge default)

| Parameter | LayerForge default | 出典 | 備考 |
|---|---|---|---|
| `mu` (μ) | 0.95 | 原論文 §C.1 Trump dataset | 短いテキスト向け |
| `alpha` (α) | 0.20 | 原論文 §C.1 Trump dataset | 〃 |
| `theta` (θ) | 0.5 | 原論文 §C.1 Trump dataset | 〃 |
| `min_cluster_size` | 100 | 原論文 §C.1 | 大規模データ向け、小規模では下げる |
| `min_samples` | 50 | 原論文 §C.1 | 〃 |
| `max_iter` | 10 | 原論文 §A.3 (I) | 全データセット共通 |
| `nc_s` | 2 | 原論文 §A.3 (S) | 〃 |
| `nc_threshold` | 5 | 原論文 §A.3 (T) | 〃 |
| `rn_threshold` | 0.01 | 原論文 §A.3 (M) | 〃 |

これらは LayerForge の `core/distillation.py` の default として採用する。

---

## F3. Cowan's 4±1 (A3) — Cognitive Constraint

### F3.1 制約定数

```python
# Cowan (2001) magical number 4
LAYER_COUNT_MIN = 3
LAYER_COUNT_MAX = 5
LAYER_COUNT_OPTIMAL = 4
```

### F3.2 制約適用条件

レイヤー数が制約範囲を満たすかの判定：

```python
def is_layer_count_valid(n_layers: int) -> bool:
    return LAYER_COUNT_MIN <= n_layers <= LAYER_COUNT_MAX
```

### F3.3 制約違反時の動作

```
if n_layers > LAYER_COUNT_MAX:
    → "粒度が細かすぎる"
    → relation threshold を強める (上げる)
    → クラスタが統合され、レイヤー数が減る

if n_layers < LAYER_COUNT_MIN:
    → "粒度が粗すぎる"
    → relation threshold を弱める (下げる)
    → クラスタが分裂し、レイヤー数が増える

if 範囲内に収まる θ が存在しない:
    → 問題設定が壊れている
    → 上位に NoValidScaleError を返す
```

### F3.4 再帰深度の制約

レイヤー内をさらに分解する場合の最大深度：

```python
MAX_RECURSION_DEPTH = 4  # 4±1 を再帰的に適用、最大4段

def can_recurse(current_depth: int) -> bool:
    return current_depth < MAX_RECURSION_DEPTH
```

理論最大: 4 × 4 × 4 × 4 = 256 ノードまで分解可能。実用上は十分。

---

## F4. Newman Modularity (A4) — Separation Quality

論文出典: Newman (2006) PNAS 103(23):8577-8582
精読状況: full text 精読済み (★★★★★)
重要な訂正: 初版設計資料では多コミュニティ版の標準形 (1/2m factor) を
            提示していたが、Newman 2006 原論文の Eq. 1 は 2-community 用で
            factor が 1/4m である。本版で両方の定式化を併記して訂正済み。

### F4.1 Modularity Q の定義 (原論文 Eq. 1, 2-community case)

ネットワークを2つのグループに分割した場合のmodularity：

```
Q = (1/4m) Σ_{i,j} [A_ij - (k_i k_j) / (2m)] · s_i s_j

where:
  A_ij  : adjacency matrix entry (i-j 間のエッジ数、通常 0 or 1)
  k_i   : degree of vertex i = Σ_j A_ij
  m     : total edge count = (1/2) Σ_i k_i
  s_i   : group indicator, s_i ∈ {+1, -1}
  
  s_i = +1 if vertex i in group 1
  s_i = -1 if vertex i in group 2
```

行列形式 (原論文 Eq. 2, 3):
```
Q = (1/4m) · s^T · B · s

B_ij = A_ij - (k_i k_j) / (2m)    : modularity matrix
```

### F4.2 多コミュニティへの一般化 (Newman & Girvan 2004; Newman 2006 §"Dividing networks into more than two communities")

k 個のコミュニティへの分割の場合 (Newman 2006 Eq. 5-6 で定義される):

```
Q = (1/2m) Σ_{i,j} [A_ij - (k_i k_j) / (2m)] · δ(c_i, c_j)

where:
  c_i        : community label of vertex i
  δ(x, y) = 1 if x = y else 0    : Kronecker delta
```

これは標準的な「多コミュニティ modularity」の形式で、LayerForge で採用する。

**Note**: 2-community 版 (Eq. 1) と多コミュニティ版で factor が異なる (1/4m vs 1/2m)。
これは 2-community の s_i s_j = 2·δ - 1 の関係から来ている：
```
Σ A_ij s_i s_j = Σ A_ij (2δ(c_i, c_j) - 1) = 2 Σ A_ij δ - 2m
```
の項を整理すると factor の違いが現れる。

### F4.3 Spectral Algorithm (原論文 §"Method of optimal modularity")

Newman の主要貢献は modularity matrix B の固有値分解による最適化：

```
Algorithm: Spectral modularity maximization (2-community)
  1. Compute modularity matrix B
  2. Find leading eigenvector u_1 of B (largest eigenvalue β_1)
  3. Set s_i = +1 if u_1[i] > 0, else s_i = -1
  4. Return the partition
```

**Indivisibility condition (原論文 重要な発見)**:
```
If β_1 ≤ 0 (no positive eigenvalue):
    → ネットワークは indivisible
    → これ以上分割しても modularity は増えない
```

LayerForge では分割の停止判定にこの性質を利用する。

### F4.4 Generalized Modularity Matrix (原論文 Eq. 6)

サブグラフ g をさらに分割する場合の修正された modularity matrix:

```
B^(g)_ij = B_ij - δ_ij · Σ_{k ∈ g} B_ik

ここで i, j はサブグラフ g 内の頂点のラベル
δ_ij は Kronecker delta
```

これにより階層的分割が可能になる：
- 全ネットワーク → 2分割（B を使用）
- 各サブグラフ → さらに2分割（B^(g) を使用）
- subgraph が indivisible になるまで繰り返し

LayerForge の階層クラスタリングと相性が良い。

### F4.5 Efficient Implementation (原論文 §"Implementation")

modularity matrix の dense 構造を避ける高速化：

```
B · x = A · x - (k · (k^T · x)) / (2m)

where:
  A · x   : sparse matrix multiplication, O(m + n)
  k^T · x : inner product, O(n)
  Total   : O(m + n) per iteration
```

Power iteration で leading eigenvector を求める：
- 通常 O(n) 回の反復で収束
- 全体: O((m+n)·n) = sparse graph では O(n²)
- 階層分割全体: O(n² log n) (典型的な dendrogram depth が log n)

### F4.6 LayerForge での実装

```python
import numpy as np

def compute_modularity(
    similarity_matrix: np.ndarray,
    cluster_labels: np.ndarray,
    threshold: float = 0.0,
) -> float:
    """
    多コミュニティ版 modularity Q を計算 (F4.2)
    
    Args:
        similarity_matrix: S where S[i,j] ∈ [-1, 1]
        cluster_labels: cluster ID for each node, shape (n,)
        threshold: edge threshold (S[i,j] > threshold をエッジとする)
    
    Returns:
        Q ∈ [-0.5, 1.0]
    """
    # Adjacency matrix
    A = (similarity_matrix > threshold).astype(float)
    np.fill_diagonal(A, 0)
    
    k = A.sum(axis=1)  # degrees
    m_total = A.sum() / 2  # total edges
    
    if m_total == 0:
        return 0.0
    
    # 効率的計算 (vectorized)
    # Q = (1/2m) Σ_ij [A_ij - k_i k_j / (2m)] δ(c_i, c_j)
    Q = 0.0
    unique_labels = np.unique(cluster_labels)
    for label in unique_labels:
        members = np.where(cluster_labels == label)[0]
        for i in members:
            for j in members:
                Q += A[i, j] - (k[i] * k[j]) / (2 * m_total)
    
    return Q / (2 * m_total)


def compute_modularity_spectral(
    similarity_matrix: np.ndarray,
    threshold: float = 0.0,
) -> tuple[np.ndarray, float, bool]:
    """
    Spectral algorithm で最適2分割を求める (F4.3)
    
    Returns:
        labels: shape (n,), values in {0, 1}
        Q: resulting modularity
        is_indivisible: True if β_1 ≤ 0
    """
    A = (similarity_matrix > threshold).astype(float)
    np.fill_diagonal(A, 0)
    
    k = A.sum(axis=1)
    m_total = A.sum() / 2
    
    if m_total == 0:
        return np.zeros(len(A), dtype=int), 0.0, True
    
    # Modularity matrix B
    B = A - np.outer(k, k) / (2 * m_total)
    
    # Leading eigenvalue & eigenvector
    eigenvalues, eigenvectors = np.linalg.eigh(B)
    # eigh returns ascending order, take the last
    beta_1 = eigenvalues[-1]
    u_1 = eigenvectors[:, -1]
    
    if beta_1 <= 0:
        # Indivisible: 全頂点を1グループに
        return np.zeros(len(A), dtype=int), 0.0, True
    
    # Partition by sign
    labels = (u_1 > 0).astype(int)
    
    Q = compute_modularity(similarity_matrix, labels, threshold)
    
    return labels, Q, False
```

### F4.7 品質判定基準

```python
MODULARITY_THRESHOLD_GOOD = 0.7
MODULARITY_THRESHOLD_ACCEPTABLE = 0.3


def classify_separation_quality(Q: float) -> str:
    """
    Newman 原論文 Table 1 の実験結果に基づく経験則:
    - 良いコミュニティ構造: Q ≈ 0.4 - 0.7
    - 強いコミュニティ構造: Q > 0.7
    - ランダム: Q ≈ 0
    
    LayerForge では「決定論的に処理可能なレイヤー分離」の閾値として
    高めに設定:
    """
    if Q >= MODULARITY_THRESHOLD_GOOD:
        return "good"        # 採用OK、断熱近似が成立
    elif Q >= MODULARITY_THRESHOLD_ACCEPTABLE:
        return "acceptable"  # 警告付きで採用
    else:
        return "poor"        # 再調整必要
```

Newman 原論文 Table 1 (karate club, jazz musicians, metabolic 等) では Q が 0.4-0.85 程度で、
構造を持つネットワークの典型的な範囲を示している。

### F4.8 断熱近似の成立条件

ADR-002「境界で推論、内部で決定論」の前提：

```
adiabatic_approximation_holds(layers) ⇔ Q(layers) >= MODULARITY_THRESHOLD_GOOD
```

これが成立しない場合、各レイヤーを独立に処理する仮定が崩れる。

### F4.9 LayerForge での Indivisibility 検出の活用

Newman の indivisibility 判定 (F4.3) を、LayerForge の停止条件として活用：

```python
def can_subdivide_layer(layer_similarity: np.ndarray) -> bool:
    """
    Newman 原論文 §"Indivisible subgraphs"の判定：
    B^(g) の leading eigenvalue が ≤ 0 ならこれ以上分割すべきでない
    """
    _, _, is_indivisible = compute_modularity_spectral(layer_similarity)
    return not is_indivisible
```

これは「**4±1 制約とは独立の停止条件**」として機能する。両方を組み合わせる：

```
分割継続条件 = (現レイヤー数 < 5) AND (can_subdivide_layer(...) is True)
```

---

## F5. 合成数式: LayerForge の決定論コア

採用論文 4 本を統合した、LayerForge の中核アルゴリズム：

```python
def layerforge_core(
    nodes: tuple[Node, ...],
    embeddings: np.ndarray,
) -> CoreResult:
    """
    完全に決定論的なコア処理。
    入力同じ → 出力同じ (frozen dataclass + numpy seed固定)
    """
    # Step 1: 類似度行列構築
    S = build_similarity_matrix(embeddings)
    
    # Step 2: 4±1 に収まる scale 係数を探索 [F1.4 + F3.2]
    theta, n_layers = find_valid_scale(
        S, target_range=(LAYER_COUNT_MIN, LAYER_COUNT_MAX)
    )
    
    # Step 3: HERCULES 階層クラスタリング [F1.3]
    hierarchy = hierarchical_kmeans(
        embeddings=embeddings,
        k=n_layers,
        use_resampling=True,
        random_state=DETERMINISTIC_SEED,
    )
    
    # Step 4: Newman modularity で分離品質測定 [F4.6, F4.7]
    Q = compute_modularity(S, hierarchy.flat_labels, threshold=theta)
    
    if classify_separation_quality(Q) == "poor":
        raise SeparationQualityError(
            f"modularity Q={Q:.3f} below threshold"
        )
    
    # Step 4b: Newman の indivisibility チェック [F4.9]
    # 各レイヤーがさらに分割可能かを判定（今回は分割しないが情報として保持）
    indivisibility_flags = [
        not can_subdivide_layer(extract_sub_similarity(S, layer))
        for layer in hierarchy.layers
    ]
    
    # Step 5: 各レイヤーで SCA 蒸留 [F2.6]
    distillations = []
    for layer_idx, layer in enumerate(hierarchy.layers):
        layer_embeddings = embeddings[layer.member_indices]
        layer_nodes = tuple(nodes[i] for i in layer.member_indices)
        
        result = distill_layer(
            layer_nodes=layer_nodes,
            embeddings=layer_embeddings,
            mu=0.95,      # F2.9 default
            alpha=0.20,   # F2.9 default
            theta=0.5,    # F2.9 default
        )
        
        # Step 5b: 純度チェック [F2.7]
        purity = compute_layer_purity(result, layer_embeddings)
        if purity < PURITY_THRESHOLD_ACCEPTABLE:
            # 警告 or 再分離（運用方針による）
            pass
        
        distillations.append(result)
    
    # Step 6: レイヤー間関係の抽出
    inter_layer_relations = extract_inter_layer_relations(hierarchy)
    
    return CoreResult(
        hierarchy=hierarchy,
        distillations=tuple(distillations),
        inter_layer_relations=inter_layer_relations,
        quality_metrics=QualityMetrics(
            modularity=Q,
            layer_count=n_layers,
            scale_coefficient=theta,
            is_within_4_plus_minus_1=is_layer_count_valid(n_layers),
            quality_class=classify_separation_quality(Q),
            indivisibility_flags=tuple(indivisibility_flags),
        ),
    )
```

この `layerforge_core` 関数の出力に対して、§04 のテストで境界条件を検証する。

---

## 数式の決定論性保証

各数式の決定論性が保たれる条件:

| 数式 | 決定論条件 |
|---|---|
| F1.3 KMeans | `random_state` 固定 |
| F1.3 Resampling | サンプル選択を index sort で安定化 |
| F1.4 二分探索 | 上限 iteration 数で停止保証 |
| F2.4 SCA iterative | max_iter, NC-S, RN 全停止条件で停止保証、UMAP の random_state 固定、HDBSCAN は本質的決定論 |
| F2.6 distill_layer | 上記の合成、merging step も決定論 |
| F2.7 purity計算 | numpy norm、純粋関数 |
| F4.3 spectral algorithm | numpy.linalg.eigh は決定論 (但し eigenvalue 縮退時に注意) |
| F4.6 modularity | 純粋関数、決定論 |
| F5 core | 上記すべての合成、決定論 |

**注意点 (Newman spectral algorithm)**: 
B 行列の eigenvalue が縮退している (重複している) 場合、対応する eigenvector の選択に
任意性がある。実用上はほぼ起きないが、決定論性を厳密に保つには
np.linalg.eigh の出力を eigenvalue 降順で安定ソートする必要がある。

これらの条件を §04 で `test_determinism_*` として検証する。
