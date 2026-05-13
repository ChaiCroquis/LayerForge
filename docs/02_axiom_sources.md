# 02. Axiom Sources

LayerForge が公理として採用する論文と、その採用範囲の宣言。

採用方針（ADR-005 参照）:
- 代表論文の数式とテスト結果が一致すれば、それが内包する派生研究は採用不要
- 採用論文の数式は **境界条件としてテストケース化** する（ADR-006）

---

## 採用論文一覧（公理として扱う）

### A1: HERCULES (Petnehazi & Aradi, 2025)

**Citation**: Petnehazi, G., & Aradi, B. (2025). HERCULES: Hierarchical Embedding-based Recursive Clustering Using LLMs for Efficient Summarization. arXiv:2506.19992v2.

**Adoption scope**:
- ✓ 再帰的階層クラスタリングのアルゴリズム骨格 (Algorithm 1, 2, 3)
- ✓ Direct Mode / Description Mode の二モード設計
- ✓ Iterative resampling による centroid refinement
- ✓ K-Means を各レベルで適用するメカニズム
- ✗ K の決定方法（HERCULESは手動 or 内部指標、LayerForgeでは 4±1 制約で自動化）
- ✗ LLM プロンプト戦略（独自実装）

**Reason for adoption**: 縦軸（レイヤー再帰分解）の最も成熟した既存実装。MIT/Apache相当のオープン実装（pyhercules）が存在。

**Tests required**: §04 test_hercules_recursion.py 参照

---

### A2: SCA - Semantic Component Analysis (Friedrich et al., 2024)

**Citation**: Friedrich, F. et al. (2024). Semantic Component Analysis: Introducing Multi-Topic Distributions to Clustering-Based Topic Modeling. arXiv:2410.21054v3.

**Adoption scope**:
- ✓ basis + residual の線形分解構造
- ✓ 残差クラスタリングの反復手続き
- ✓ 「basis で説明されない部分」を次のレイヤーの入力にする発想
- ✗ 線形性の制約（LayerForgeでは非線形 law も許容）
- ✗ topic modeling 特化部分

**Reason for adoption**: 横軸（同レイヤー内蒸留）の `distill(layer) = (basis, law, residuals)` 構造の直接的先行研究。

**Tests required**: §04 test_sca_residual.py 参照

---

### A3: Cowan's Magical Number 4 (Cowan, 2001)

**Citation**: Cowan, N. (2001). The magical number 4 in short-term memory: A reconsideration of mental storage capacity. Behavioral and Brain Sciences, 24(1), 87-114.

**Adoption scope**:
- ✓ ワーキングメモリ容量 = 4±1 chunks（3〜5の範囲）
- ✓ chunking が「単純要素」ではなく「意味的単位」として機能する性質
- ✗ 認知発達や個人差の議論（実装には不要）

**Reason for adoption**: 4±1 を観測指標として使う理論的根拠。実装上は「レイヤー数の正常範囲」として定数化。

**Constants**:
```python
LAYER_COUNT_MIN = 3
LAYER_COUNT_MAX = 5
LAYER_COUNT_OPTIMAL = 4
```

**Tests required**: §04 test_cowan_constraint.py 参照

---

### A4: Newman Modularity (Newman, 2006)

**Citation**: Newman, M. E. J. (2006). Modularity and community structure in networks. PNAS, 103(23), 8577-8582.

**Adoption scope**:
- ✓ modularity Q の定義式
- ✓ Q を「レイヤー分離品質」の測定に使用
- ✓ Q が高い ⇔ 同レイヤー内が密、レイヤー間が疎、の同値性
- ✗ コミュニティ検出アルゴリズム自体（HERCULESのk-meansで代替）

**Reason for adoption**: ADR-002の「断熱近似」が成立する条件を定量化するため。

**Formula**:
```
Q = (1/2m) Σ_ij [A_ij - (k_i k_j / 2m)] δ(c_i, c_j)
where:
  A = adjacency matrix
  k_i = degree of node i
  m = total edges
  c_i = community of node i
  δ = Kronecker delta
```

**Tests required**: §04 test_modularity.py 参照

---

## 内包確認のみの論文（直接採用しない）

### B1: RGMem (2026) — RG-inspired Memory Evolution

**Citation**: Anokhin et al. (2026). RGMem: Renormalization Group–inspired Memory Evolution for Language Agents. arXiv:2510.16392.

**Why not directly adopted**:
- 構想的にはLayerForgeのスケール係数調整と同じ発想だが、適用先（長期会話メモリ）が異なる
- 採用すべき具体的数式が、HERCULES + Cowan の組合せで実現可能

**Test of containment**:
- LayerForgeが「異なるスケールで異なるレイヤーを抽出できる」性質を持てば、RGMemの主張を自動的に満たす
- → `test_scale_separation_property` で property-based test

---

### B2: RG Principles for Deep Neural Architectures (2026)

**Citation**: arXiv preprint 2026, RG Principles for Deep Neural Architectures, rs.21203/rs-9005595/v1.

**Why not directly adopted**:
- 深層学習アーキテクチャへの適用で、LayerForgeのスコープ外
- ただし「層数が固有相関長に対数比例」(H2) という主張は LayerForge の検証材料になる

**Test of containment**:
- データセットの内在的相関長 ξ と最適レイヤー数の関係を測定
- → `test_layer_count_vs_correlation_length` で実証実験

---

### B3: HiAgent (ACL 2025) — Hierarchical Working Memory Management

**Citation**: HiAgent, ACL 2025 Long Paper 1575.

**Why not directly adopted**:
- LLMエージェントのタスク分解で、領域が異なる
- 4±1 制約を明示的に使っていない

**Test of containment**:
- LayerForgeが階層的タスク分解にも適用できれば、HiAgent的なエージェント設計の基盤になる
- 将来の統合候補（ADR-009）

---

## 採用しない既存研究（明示的に範囲外）

以下は構想の議論で言及されたが、実装には組み込まない。

| Source | Reason for exclusion |
|---|---|
| Marr's Three Levels (1982) | 哲学的背景、実装に直接影響しない |
| Polya "How to Solve It" | 問題解決の一般論、形式化されていない |
| HTN Planning | プランニング領域、LayerForgeのスコープ外 |
| Hyperbolic Embedding (Nickel & Kiela 2017) | 階層構造の埋め込み方法の一つ、LayerForgeは Euclidean前提で十分 |
| Persistent Homology / TDA | 計算コスト過大、4±1 制約のシンプル化と整合しない |
| Miller's 7±2 (1956) | Cowan 2001 で更新済み、4±1 を採用 |
| Baddeley's WM model | Cowan に内包 |

---

## 数式の依存関係グラフ

```
A3 (Cowan 4±1)
  └→ LAYER_COUNT_MIN/MAX 定数
       └→ scale_coefficient 二分探索 [ADR-003]
            └→ A1 (HERCULES) の K_config に渡される

A1 (HERCULES) hierarchical clustering
  └→ each layer's clustering result
       └→ A4 (Newman) modularity Q で品質測定
            └→ Q が閾値以下なら scale_coefficient 再調整

A1 (HERCULES) cluster representation
  └→ A2 (SCA) basis + residual に分解
       └→ residual がしきい値以下なら蒸留完了
            → 越えれば再帰的に下位レイヤー分解
```

この依存関係は §05 統合設計で詳細化する。

---

## 公理の独立性検証

採用 4 論文（A1-A4）が相互独立であることの確認：

- A1 ⊥ A2: HERCULES は分解の縦構造、SCA は同レイヤー内の横構造 → 直交
- A1 ⊥ A3: HERCULES は K の決定方法を抽象化、Cowan は K の範囲を制約 → 補完関係
- A1 ⊥ A4: HERCULES は分解手続き、Newman は分解品質測定 → 別軸
- A2 ⊥ A3: SCA はノード集合内処理、Cowan はレイヤー数制約 → 別軸
- A2 ⊥ A4: SCA は basis 分解、Newman はグラフ構造 → 別軸
- A3 ⊥ A4: Cowan は層数の制約、Newman は分離度の測定 → 別軸

→ 全てのペアで独立性が確認できる。冗長な公理は採用していない。
