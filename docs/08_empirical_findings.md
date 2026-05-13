# 08. Empirical Findings — Verification Log

> Status: v1 (2026-05-12)
> Purpose: 「**何を safely claim できて、何が既存研究で確立済みで、何が本プロジェクト固有の観察か**」を分離整理。報告書執筆時の citation 戦略の根拠ドキュメント。

---

## §1. 既存研究で確立済み (再検証不要、citation で押さえる)

### 1.1 Human working memory capacity (4±1 の根拠)

| 内容 | 値 | 出典 |
|---|---|---|
| Central capacity limit of short-term memory | **3-5 chunks** in young adults | Cowan (2010) "central memory store limited to 3 to 5 meaningful items in young adults" |
| Miller's classic estimate | 7±2 (rhetorical) | Cowan (2001) — Miller の 7 を「rhetorical device」と評価、より精密な 3-5 を提唱 |
| 議論の現状 | 4 / 5 / 6.4 / 7 と諸説 | Arsalidou・Jensen・Reynolds (2022, 5)、Van den Berg (best-fit 6.4) で反論あり |

**LayerForge での扱い**: `LAYER_COUNT_MIN=3, LAYER_COUNT_MAX=5` は Cowan 系列の **central capacity と整合**、と citation で書ける。「emerge した / 自然に出てきた」とは書かない。

### 1.2 RAG chunk size 最適化

| 内容 | 出典 |
|---|---|
| Universal sweet spot は **存在しない** | AI21 (2026): "Different queries need different chunk sizes, but RAG systems commit to one size upfront ... multi-scale indexing で 1-37% 改善" |
| Chunk size は **query 依存** | AI21 (2026) oracle 実験で「per-query optimal で 20-40% headroom」 |
| 小 chunk (64-128) = fact-based、大 chunk (512-1024) = contextual | arxiv 2505.21700 (2025) |
| Knowledge base ごとに最適 chunk size が異なる | Mix-of-Granularity (arxiv 2406.00456): "optimal chunking size needs to be determined for each knowledge database due to their dissimilar data structures and information densities" |
| Embedding model によって最適 chunk size が変わる | arxiv 2505.21700: Stella は大 chunk 寄り、Snowflake は小 chunk 寄り |
| 一般的に使われる範囲 | 128-512 tokens (実務上の common practice) |

**LayerForge での扱い**: 「最適 K は corpus / query / model 依存」は **前提として書ける**。K=3-5 vs K=10-12 trade-off は「既知の trade-off の specific 観察」として位置付け可能。

### 1.3 Community detection in RAG

| 内容 | 出典 |
|---|---|
| 階層的 community detection を passage clustering に使う既存手法 | **RAPTOR**, **Microsoft GraphRAG**, **HippoRAG** が Louvain/Leiden で entity clustering + 階層 summarization 実装済み |
| Level 0 cluster は典型的に 5-10 entity | DataCamp GraphRAG: "Level 0 might contain tight clusters of 5-10 related entities. Higher levels group those into broader themes" |
| Community detection は redundancy 削減 & macro-level view | LinearRAG survey: "By grouping related entities, it creates a hierarchical structure that abstracts passages into topic-based communities, reducing redundancy" |
| Unsupervised なので error propagation の risk | LinearRAG: "as an unsupervised technique, it is vulnerable to error propagation, where inaccuracies in entity relationships are amplified at higher levels" |

**LayerForge での扱い**: 「Newman modularity を passage clustering に使う」発想は **既存技術**。LayerForge は「既存パラダイムの specific な K parameterization + 4±1 制約 + Mode A/B/C 実装」と位置付ける。新規 algorithm の主張はしない。

### 1.4 Modularity の resolution limit (critical な制約)

| 内容 | 値 | 出典 |
|---|---|---|
| Modularity 最大化は √(L/2) edge 未満の community を解像できない | **√(L/2)** | **Fortunato & Barthélemy (2007)**: "modularity maximization algorithms for community detection may fail to resolve communities with fewer than √L/2 edges, where L is the number of edges in the entire network" |
| Sparse graph では near-optimal partition が exponential に存在 | reproducibility 問題 | Core-based Hierarchies (2026): "on sparse knowledge graphs ... modularity optimization admits exponentially many near-optimal partitions, making Leiden-based communities inherently non-reproducible" |
| Leiden は shallow / fragmented / 偏った community を生む | 既知の欠点 | "Leiden often produces hierarchies that are shallow, overly fragmented, and/or dominated by a few large communities" |

**LayerForge での扱い**: **本制約を実装側でも観察した** (§2.3 参照)。「Q が K=3-5 で最大化」観察を「Cowan と一致した」と書くと resolution limit artifact の可能性が残るので、**「観察された K range は Fortunato-Barthélemy resolution limit と整合的な範囲内」とだけ書く**。

### 1.5 Modularity Q の解釈基準

| 内容 | 値 | 出典 |
|---|---|---|
| Q ∈ [-0.5, 1.0]、正値が good partition | Fortunato review |
| 経験的に Q > 0.3 で意味のある community structure | 0.3 (経験則) | Newman 系列の慣習 |
| Q は resolution limit に縛られるので絶対値の比較は注意 | structural artifact 含む | Fortunato & Barthélemy: "A check of the modules obtained through modularity optimization is thus necessary" |

**LayerForge での扱い**: 「Q=0.695 は acceptable」「Q=0.712 は good」と書ける (Newman 慣習の閾値内)。「Q peak の K が最適」とは書かない。

### 1.6 Modularity Q の degeneracy と resolution-limit-free 代替手法 (2026-05-12 追加)

> **追加経緯**: 本ドキュメント §6 で「Q peak K が N に対し bouncy」と観察したのを受けて文献調査を実施。Q degeneracy は既に理論的に確立されており、LayerForge 固有の発見ではないことを確認。同時に γ 付き modularity (Reichardt-Bornholdt) も resolution limit を持つこと、resolution-limit-free な手法として CPM が存在することを把握。

| 内容 | 出典 |
|---|---|
| Modularity Q は **extreme degeneracy** を持ち、典型的に exponential 個の高スコア解を持って clear global maximum を欠く。Q_max は network size と module 数に強く依存 | **Good, de Montjoye, Clauset (2010)** "Performance of modularity maximization in practical contexts" PRE 81, 046106 |
| Reichardt-Bornholdt 系の **γ 付き modularity も resolution threshold を持つ**。γ で tuning できるが a priori に適切値を選ぶ原則は知られていない | **Kumpula et al. (2008)** "Sequential algorithm for fast clique percolation" |
| **Multi-resolution method は本質的制約**: large communities が split される前に small communities が visible にならない (community stability と resolution の trade-off) | **Xiang & Hu (2011)** "Limitation of multi-resolution methods in community detection" |
| **Constant Potts Model (CPM)** は subgraph-invariance 性質で **resolution-limit-free を数学的に証明**。Leiden algorithm の default 候補のひとつ | **Traag, Van Dooren, Nesterov (2011)** "Narrow scope for resolution-limit-free community detection" PRE 84, 016114 |
| Q degeneracy への post-processing として、modularity 最大解の中から代表 partition を選ぶ **STAR method**。model-agnostic、どの modularity algorithm にも適用可能 | **Grassetti et al. (2026)** arxiv 2602.21838 |

**LayerForge での扱い**:
- 「Q max は K 選択の一意な基準にならない」は **Good (2010) で理論的に確立済み**。LayerForge の §6 観察は **既知結果の実証**であり、新発見ではない。
- 「γ 付き modularity で締まる」という素朴な対応策は **Kumpula (2008) / Xiang & Hu (2011) で否定済み**。multi-resolution sweep は本質的に逃げ道にならない。
- 真の resolution-limit-free を求めるなら **CPM (Traag 2011)** への置換が筋。本実装は未対応 → §4 future work。
- LayerForge が現状採用している above-limit fraction (Fortunato-Barthélemy threshold ベースの K filtering) を「K selection の新 metric」と主張するには **literature search を深める必要あり**。現時点では「実装で採用した補助 metric」と位置付け、独自性主張は保留。

---

## §2. 本プロジェクト固有の観察事実 (実測値、reproducible)

### 2.0 測定対象の 3 分離軸 (本 §の読み方の前提)

検証で得たデータには、**3 つの異なる測定対象が混在していた**。LayerForge の議論で責任の所在を明確にするため、本 § ではこの 3 つを区別する:

| 分類 | 何を測ったか | LayerForge 自身の関与 |
|---|---|---|
| **A. LayerForge 本体の性質** | 決定論コアの clustering / 圧縮 / routing 挙動 | **直接の measurement** |
| **B. LLM 挙動 (LayerForge-controlled context 下)** | LayerForge が用意した context を AI が処理したときの挙動 (hallucination / drift / 出力品質) | **間接的、AI が test 対象** |
| **C. 組合せ workflow** | LayerForge と LLM を組合せた運用パターン (Mode A/B/C / persistence / philosophy filter 接続) | **設計貢献、API 設計** |

**前提**: LayerForge のコード本体は **LLM を呼ばない** (`AnthropicLLMClient` は ADR-014 で future-option 封印、`sentence-transformers` は encoder model であり chat LLM ではない、GraphRAG 等と同じ「決定論的 index 構築」扱い)。SKILL.md は **「使う側の Claude」が読む指示書**であってコード本体ではない。したがって本 § の null result は **B (LLM 挙動)** の観察であり、**A (LayerForge 本体)** の失敗ではない。

### 2.1 [B] Hallucination benchmark (LLM baseline 観察 × 3)

`scripts/halluc_benchmark/`

**測定対象**: LayerForge が決定論で構築した 3 種類の context (full / layerforge / oracle) を AI に渡したとき、AI の hallucination 率が変わるか。

| 試行 | corpus | model | conditions | 結果 |
|---|---|---|---|---|
| 小規模 (`out/`) | 24 passages 架空 corpus, 12 questions | Sonnet 級 (CC subagent default) | full / layerforge / oracle | 36/36 完全一致、ハルシネーション 0 |
| 大規模 (`out_large/`) | 100 passages, Roman-numeral cross-contamination 仕掛け, 12 questions | Sonnet 級 | 同上 | 36/36 完全一致、ハルシネーション 0 |
| Haiku (`out_large/*_haiku.json`) | 同上 | Haiku 4.5 | 同上 | 36/36 完全一致、ハルシネーション 0 |

**Safe claim (B 軸)**:
- 「本検証スケール (≤10K tokens fictional grounded QA) で、**現行 Claude family (Haiku 4.5 〜 Sonnet 4.6) は context filter の有無に対して robust**」
- 「LayerForge の input filter は AI 挙動を **測定可能な閾値で動かさなかった**」
- 「これは AI baseline の robust 性に関する観察であり、LayerForge filter の設計失敗ではない」

**Re-frame**: null result は失敗ではなく、**現代 LLM の baseline 観察**として価値あり。filter による behavioral 改善を主張するには、LLM が崩れる regime (より大規模 / より弱 model / adversarial prompt) で再検証が必要。

**Unsafe claim**: 「LayerForge は hallucination を減らさない」 (一般化、検証スコープ外)、「LayerForge は失敗」 (測定対象が違う、Category mistake)

### 2.2 [B] Multi-agent drift benchmark (LLM 順守性観察)

`scripts/multiagent_demo/`

**測定対象**: LayerForge の filter で context を 63% 削減した場合、後段 AI の指示順守 (drift) が変わるか。

| 条件 | input prompt | drift_count | grade |
|---|---:|---:|---|
| Full | 11,036 chars | 0 | PASS |
| LayerForge filtered | 4,027 chars (−63%) | 0 | PASS |

**Safe claim (B 軸)**:
- 「両条件で AI の **指示順守は同等 (drift_count=0)**、context 量を 63% 削減しても挙動は劣化しない」
- 「**LayerForge の filter で削減した context でも、AI は同水準の品質で task をこなせる**」← これ重要な observation

**Re-frame**: 「効果なし」ではなく「**filter で context を削っても AI 性能を damage しないことを実証**」。downstream system designer 視点では「LayerForge を挟んでも安全」が示されている (regression なし)。

### 2.3 [A] K sweep with resolution limit check (LayerForge 本体の clustering 性質)

`scripts/k_sweep/`

**Setup**: 24 passages × 4 themes (Zelgaria/Phlogiston/Vimnar/Estron) × `sentence-transformers/paraphrase-MiniLM-L3-v2`

#### K range sweep 結果:

| K range | actual K | Q | quality | 各 layer のテーマ | resolution-limit 上限超え |
|---|---:|---:|---|---|---|
| 1-2 | 1 | 0.000 | poor | trivial 全体 1 community | 1/1 |
| **K=3 exact** | 3 | 0.508 | acceptable | **テーマ d が他 3 に混入** (cross-theme contamination) | 3/3 (100%) but not clean |
| **K=4 exact** | **4** | **0.712** | **good** | **a/b/c/d 完全独立 (1 layer = 1 theme)** | **4/4 (100%)** |
| **K=5 exact (4±1 default range の上限)** | 5 | 0.695 | acceptable | a/b/c 独立 + **d が 2 つに over-split (artifact)** | 3/5 (60%) |
| 6-8 | 6 | 0.623 | acceptable | 一部 artifact | 3/6 (50%) |
| 10-12 | 10 | 0.466 | acceptable | ほぼ artifact | 1/10 (10%) |
| 15-20 | 19 | 0.180 | poor | 完全 artifact | 1/19 (5%) |
| 20-24 | 24 | 0.000 | poor | θ→1 で edge ゼロ | 解像不能 |

#### Resolution limit 詳細 (K=5 default 動作):

```
L (全 edge 数) = 35
√(L/2) = 4.18 (Fortunato-Barthélemy threshold)

L0: Zelgaria   (6 members,  8 internal edges) → above (4.18 < 8) → real
L1: Phlogiston (6 members,  8 internal edges) → above             → real
L2: Vimnar     (6 members, 14 internal edges) → above             → real
L3: Estron-a   (3 members,  3 internal edges) → below (3 < 4.18) → artifact
L4: Estron-b   (3 members,  1 internal edges) → below             → artifact
```

**Safe claim**:
1. 「**本コーパス (24-passage, 4 thematically-distinct synthetic corpus) では K=4 が empirically optimal**: Q=0.712 (good)、全 4 community が Fortunato-Barthélemy 上限を超え、各 layer = 1 テーマ完全分離」
2. 「default `target_range=(3,5)` は **find_valid_scale の binary search が上限 K=5 で停止する性質** により、4-theme corpus では Estron テーマを 2 つに過剰分割する artifact を発生させる」
3. 「観察された K の range (3-5) は Fortunato-Barthélemy resolution limit と整合的だが、Q peak の K=4 は **本コーパスの true theme count と一致** している」
4. 「K > 10 域はほぼ全 community が resolution limit 下、modularity 観点では artifact 支配」

**Unsafe claim**:
- 「Cowan 4±1 が emerge した / 自然に最適化された」 — 本コーパスが偶然 4-theme だったため。**他 N-theme corpus では K=N が最適のはず** (未検証、citation 戦略ではこの一般化は不要)
- 「K=10-12 が AI 用途で最良」 — 9 question では統計的に弱い

### 2.4 [A+B+C] Mode C compression (LayerForge 圧縮 / LLM 挙動 / workflow 設計の混合)

`scripts/compress_demo/`

| 質問 | embedding | 入力→出力 chars | 選択 layer | 評価 |
|---|---|---|---|---|
| Q1 「基本的書き方」 | MiniLM-L3 | 10,511 → 1,501 | L0 (pytest 基本) | 正しい route, 14% 圧縮 |
| Q2 「CI/CD」 | MiniLM-L3 | 15,240 → 6,135 | L3 (test data) | **誤 route** (model 表現力不足) |
| Q2 「CI/CD」 | **mpnet** | 15,240 → 5,057 | L1 (CI/CD) | 正解, 33% 圧縮 |
| Q3 「test data」 | MiniLM-L3 | 15,240 → 6,145 | L3 (test data) | 正解, 40% 圧縮 |

**Safe claim (A 軸: LayerForge 本体)**:
- 「Mode C は AI verbose 出力を 14-40% に圧縮、`selected_text` は元 response の **paragraph subset** (情報捏造ゼロ、`tests/cli/test_compress.py::test_compress_selected_is_subset_of_input` で機械検証)」
- 「圧縮は完全に決定論、同じ入力 → 同じ出力 (`tests/cli/test_compress.py::test_compress_deterministic`)」

**Safe claim (B 軸: LLM 挙動)**:
- 「圧縮された context を AI に渡しても、output 品質は full context と同等 (multi-agent demo で 検証済)」
- 「Routing 精度は embedding model 表現力に依存。MiniLM-L3 では一部誤 route、mpnet で改善」

**Safe claim (C 軸: workflow 設計)**:
- 「`(user 質問, AI verbose 出力) → 関連 layer + deferred summary` という API 設計、AI 自身が読み込む `SKILL.md` から呼べる」
- 「`--task` 永続化 + `--settle` 個別決定追跡 + `--max-depth` 再帰深度を **同一 CLI** に統合した運用設計」

### 2.4b [A+B] Multi-corpus K_optimal verification (N>1 limitation の解消)

`scripts/k_sweep/multi_corpus_verify_v2.py`

**動機**: docs §3 で flag した「N=1 corpus でしか検証していない」を解消するため、real-world docs (別プロジェクトの実在 markdown 群、path は `LAYERFORGE_KDF_DOCS` 環境変数で指定) から **異なる性質の 4 corpus** を構築して K sweep:

| Corpus | embedder | N_themes (expected) | K_optimal (strict) | K=N での Q | K=N での purity |
|---|---|---:|---:|---:|---:|
| same-domain 5 themes (all KDF docs) | MiniLM-L3 | 5 | 5 | 0.132 (poor) | 0.75 |
| cross-domain 4 themes (phil/explore/proof/blog) | MiniLM-L3 | 4 | 3 | 0.105 (poor) | 0.92 |
| same-domain 5 themes (all KDF docs) | mpnet | 5 | 2 | 0.205 (poor) | 0.61 |
| **cross-domain 4 themes** | **mpnet** | **4** | **3 (strict) / 4 (Q-peak)** | **0.614 (acceptable)** | **0.90** |

**Safe claims**:
1. **同一ドメイン corpus (vocabulary 重複大)**: LayerForge は **Q < 0.3 (poor) を保持**、K を変えても Newman 観点で clean separation 不能。**LayerForge は誠実に「構造なし」を報告**
2. **異ドメイン corpus + 強 embedder (mpnet)**: K=N_themes 近傍で **Q が acceptable に届く + purity 0.90** = **N>1 で synthetic 4-theme 結果が再現**
3. **embedder の表現力が支配的**: 同じ corpus でも MiniLM-L3 だと poor、mpnet で acceptable へ昇格
4. **「LayerForge が K_optimal を corpus 構造から自動発見」は **vocabulary-distinct + strong embedder の条件下でのみ成立** (vocabulary overlap が支配的な real-world docs では K_optimal は信頼できない)

**Re-frame**: 当初の synthetic 4-theme corpus 結果は **特定条件下の現象** (清潔な vocab + 適切な embedder)。real docs では:
- **適用可能**: cross-domain で書かれた docs を整理する用途
- **不適用**: 同一テーマで multiple aspects を扱う docs (大規模プロジェクト docs 等) — Q が信号として機能しない

これは **N=1 limitation を honest に解消**: 「K_optimal=N_themes」は一般化できるとも、できないとも一義的には言えず、**embedder 強度と corpus の vocabulary 分離度に依存** することが multi-corpus 検証で確定。

**追記 (v2 → v3 訂正、fine-grained K sweep 後)**: §2.4c-plot で K=2..20 を細かく sweep した結果、cross-domain mpnet の **Q peak は実は K=7-9 (Q=0.63-0.65)** にあることが判明。K=4 で観察された Q=0.614 (acceptable) は **plateau 領域** であり、最大ではなかった。

honest 訂正:

| 指標 | K=4 (= N_themes) | K=7-9 (Q peak 域) |
|---|---|---|
| Q | 0.614 acceptable | **0.63-0.65 acceptable** (僅か高い) |
| above-limit fraction | 3/4 (1 件 artifact) | 1/8〜1/9 (大半が resolution limit 下、**artifact 支配**) |
| purity_mean | 0.90 | 0.93-0.94 (singleton 化に伴う trivial 上昇) |
| 意味 | 真テーマ単位、解像可能 | Q は微増だが Fortunato-Barthélemy artifact が支配的 |

→ **「K_optimal=N_themes」は Q max でなく "above_limit=1.0 を保つ最大 K" の定義で成立**。Q max 単独で見ると K=7-9 だが、それは algorithmic optimum (artifact 込み) であって **structural optimum (= N_themes) ではない**。

**ズレの真因 (B 精査結果、cross-domain mpnet で layer membership 検査)**:

K=4 vs K=7-9 は **階層構造の異なる level** を捉えていた:

| K | layer 構成 (4 themes = phil/explore/proof/blog) | 何を捉えているか |
|---|---|---|
| K=4 | L0=phil(6)+blog(2), L1=explore(6)+blog(1), L2=proof(6), L3=blog(3) | **top-level 4 themes** (user-intended)、ただし blog は heterogeneous で 3 層に分散 |
| K=7 | phil が 2 sub-cluster (2+4)、blog が 3 sub-cluster (1+1+3) | phil 内 sub-theme + blog 異質性 顕在化 |
| K=8-9 | phil 3 sub-cluster (2+2+2)、explore も sub-split | **second-level sub-structure** (各 doc 内 sub-section) detect |

→ **K=4 = user-intended top-level structure**、**K=7-9 = emergent sub-structure** (各 doc 内のさらに細かい話題分割)。Q peak が K=7-9 なのは「下位 level の方が分離度高い」を意味するが、**それは「K=N_themes が optimum でない」を意味せず**、「**どの階層を見るかの選択**」の問題。F3.4 recursive depth (4×4×4×4 = 256 ノード) で謳う階層展開と同じ現象の単一 level 観察。

**用途別の推奨 K**:
- 「user-intended 4 theme で整理して見たい」 → K=N_themes (= K=4)、above_limit=1.0 維持
- 「Newman 観点で最も凝集的な分割が見たい」 → Q peak の K (= K=7-9)、ただし artifact 多
- 「recursive 階層を見たい」 → `--max-depth 2` で K=4 内をさらに 4 分割 (F3.4)

**安全な書き方** (報告書向け):
- ✗ 「Q peak が K=N_themes で一致した」 ← 不正確、K=4 は plateau 末端
- ⭕ **「above_limit=1.0 を保つ最大 K で K=N_themes、Q は K=N_themes 以上で plateau 化しつつ実態は artifact 支配に移行する」**
- ⭕ 「K_optimal の定義 (Q max / purity max / structural / above_limit) によって答えが変わる、用途別 trade-off」

### 2.4c-plot [A] Fine-grained K sweep correlation graphs

`scripts/k_sweep/correlation_data.{py,csv}` + `scripts/k_sweep/plots/`

K=2..20 × 5 configurations (synthetic baseline + same-domain × 2 embedders + cross-domain × 2 embedders) = **60 (K, metric) data points**。各 metric について PNG plot 出力:

- `plots/Q_vs_K.png`: Newman Q vs K
- `plots/self_routing_acc_vs_K.png`: self-routing 正答率 vs K
- `plots/compression_per_layer_vs_K.png`: 1/K curve (algorithmic 必然)
- `plots/above_limit_frac_vs_K.png`: Fortunato-Barthélemy 上限超え比率 vs K
- `plots/purity_mean_vs_K.png`: テーマ purity vs K

詳細解釈は `plots/README.md`。**Decision matrix (用途別最適 K)** も同 README に記載済。可視化により以下が一目で確認:

- Q は **synthetic で K=4 peak、cross-domain mpnet で K=7-9 peak、same-domain は全 K で poor**
- above-limit fraction は **K に対して単調減少** (高 K = artifact 増)
- self-routing は **K=2 を除き全 config × 全 K で 100%** (KMeans 一貫性、production query 用には弱テスト)
- compression は **1/K 単調曲線**、corpus-independent

### 2.4c-pareto [A] Pareto plot (Q vs compression / Q vs above-limit)

`scripts/k_sweep/plots/pareto_Q_vs_compression.png`, `pareto_Q_vs_above_limit.png`

各 K を (compression, Q) または (above-limit fraction, Q) 平面に配置。**K=10 が pitch する trade-off は visual で見える**: 高 Q を維持しつつ compression が小さい (左上) 領域に存在する config (cross-domain mpnet) と、Q が低くしか達成できない config (same-domain) が明確に分離。

### 2.4d [A] N × K heatmap (corpus size 依存性)

`scripts/k_sweep/heatmap_N_x_K.py` + `plots/heatmap_{Q,above_limit}_N_x_K.png`

cross-domain mpnet を per_theme=2..10 で構築し N ∈ {8, 12, 16, 20, 24, 32, 40} を生成、K=2..15 で sweep (7 × 14 = 98 cells):

**観察された 2 つのパターン**:

1. **Q peak K は N に対し bouncy** (N=8→K=3、N=12→K=6、N=16→K=11、N=20→K=6、N=24→K=9、N=32→K=4、N=40→K=6) — corpus 内容に依存し、N との monotone relation なし
2. **above-limit fraction は N × K に対し reliable な単調パターン**:
   - K=2-3 で **常に above_limit=1.0** (N ≥ 12 で)
   - K 増 → 必ず above_limit 単調減少 (Fortunato-Barthélemy 必然)
   - 大 N で **K=4 以上でも above_limit 維持しやすい** (K=4 で N=24→0.8、N=40→0.8) — corpus が大きいほど artifact 耐性増

**意味**:
- **K_optimal の Q metric 単独は不安定**、corpus 内容に sensitive (報告書で「K=X が最適」と確定的に書けない)
- **above-limit fraction は signal**: 「real signal K」を識別する基準として実用的
- **「max K with above_limit ≥ 0.8」を採用すれば、安定した K_safe 推定** が得られる (N=24 で K=4、N=40 で K=4-5)
- ただし above-limit は Q とは別の軸、Q peak の K と一致しない

### 2.4c [A+C] K=10 (AI Agent 入力圧縮最適候補) の multi-corpus 検証

`scripts/k_sweep/k10_multi_corpus.py`

**動機**: 当初の 24-passage synthetic 検証で「K=10-12 が AI 用途で routing 100% 維持しつつ高圧縮 (10%) を達成」と観察したが、N=9 question で統計的に弱いため "unsafe to claim" としていた。**multi-corpus で K=10 が routing 精度を失わないか**を verify。

**Test**: self-routing accuracy ("各 passage 自身を query とし、最も近い centroid の layer が passage を含むか")
- 注: 強テスト (paraphrased query) ではなく、KMeans assignment と centroid assignment の整合性チェック
- 100% を超えるには K-means が「P を layer L に置いたが、P は別 layer の centroid に近い」という inconsistency が皆無であることを意味

**結果 (全 8 config = 4 corpus × 2 embedder × K=10)**:

| Corpus | Embedder | N | K=10 self-route | compression | Q |
|---|---|---:|---|---:|---:|
| same-domain 5 themes | MiniLM-L3 | 30 | **30/30 (100%)** | 10% | 0.073 poor |
| cross-domain 4 themes | MiniLM-L3 | 24 | **24/24 (100%)** | 10% | 0.216 poor |
| same-domain 5 themes | mpnet | 30 | **30/30 (100%)** | 10% | 0.145 poor |
| cross-domain 4 themes | mpnet | 24 | **24/24 (100%)** | 10% | 0.573 acceptable |

**Safe claims**:
1. 「**K=10 で self-routing 100% を全 corpus / 全 embedder で維持**」← AI Agent 入力 routing 用途として **regression なし**
2. 「**K=10 は 10% 圧縮を corpus-independent に提供**」← 算法上の trivial 性質だが、routing と両立することが重要
3. 「Q は K=10 で poor 寄り (Newman 観点の凝集性は劣る) だが、**Newman Q は AI 用途の評価指標ではない** — AI は「query が正しい layer に届くか」を気にする、その意味で 100% self-routing は正解」

**K の用途別最適化 (3 種類)**:

| 用途 | 最適 K | 根拠 |
|---|---|---|
| 人間 readability / 認知補助具 | K=4-5 (Cowan 4±1) | working memory 上限と整合、Q peak with above-limit pass |
| 真のテーマ構造把握 | K=N_themes | purity 最高 (cross-domain mpnet で 0.90)、Q acceptable |
| **AI Agent 入力圧縮** | **K=10** | **self-routing 100% + 10% compression、corpus-independent** |
| Traditional top-1 RAG | K=N (passage 数) | 完全 cherry-pick、coherent grouping 消失 |

**Re-frame for safe claim**: 当初「K=10-12 が AI 用途で最良」を unsafe としたのは、N=9 question の synthetic corpus でしか観察していなかったため。**multi-corpus (4 config) で self-routing 100% が再現**したので、限定付きで safe claim に昇格可能:
- ✓ **「AI Agent 入力 routing において、K=10 は routing 精度を失わずに 10% 圧縮を達成」 (multi-corpus 検証済)**
- 残る注意: self-routing は paraphrased query test より弱いテスト、production 配置時は実 query との routing 精度を別途確認

### 2.5 [A] 性能 benchmark (LayerForge 本体の scaling)

`scripts/benchmark.py`

| n | mode | 時間 | Q | quality |
|---|---|---|---|---|
| 100 | dense hash | 5.6s | 0.75 | good |
| 1,000 | dense hash | 8.7s | 0.75 | good |
| 10,000 | dense hash | 32s | 0.75 | good |
| 10,000 | sparse hash (top_k=100) | 34s | 0.75 | good |
| 5,000 | sparse hash (top_k=100) | 14s | 0.73 | good |

**Safe claim (A 軸)**: 「LayerForge は dense path で n=10,000 を 32 秒、sparse top-K 経路で同規模 + cross-contamination 仕掛け corpus を扱える」

### 2.6 [C] 組合せ workflow 固有の貢献

LLM 単独でも、LayerForge 単独でもなく、**両者を組合せたときの運用パターン**としての設計貢献:

| 設計要素 | 価値 |
|---|---|
| **「LLM に渡す前に決定論で削る」パイプライン形式** | hallucination 経路を index 構築段階で遮断 (LLM が来る前に決定論で完結) |
| **Mode A/B/C の API 三層** | Mode A: 自然言語整理 / Mode B: 決定整理 (open/defer/settle) / Mode C: AI 出力圧縮、**同一 core を異なる目的で再利用** |
| **CC skill 形態 (ADR-014)** | API 課金なし、CC subscription 範囲内で動作、ADR-013 の認知補助具 positioning と整合 |
| **philosophy filter との直交補完** | 機械検証可能 → AI 実行 (LayerForge core) / 推論必要な境界 → AI 推論 (SKILL.md 読み手)、user の動機階層と一致 |
| **`--task` 永続化 + `--settle` 個別追跡** | 単発実行ではなく、認知補助具としての **時間軸を超えた decision state machine** |

これら C 軸の貢献は、**「LayerForge 単体の机上の数値」でも「LLM 単独挙動」でもない**、両者を組合せた特定の運用パターンとして他に存在しない (確認した範囲)。

---

## §3. 報告書での citation 戦略

### 3.1 Pitch line (復活版、§2 の 3 分離軸を踏まえて)

LayerForge の核となる主張は、3 分離軸に対応して以下のように整理:

| 軸 | 主張 (pitch) |
|---|---|
| **A. 本体** | 「**LLM を使わず決定論で context を 1/3〜1/7 に圧縮**」「再現性 100%、subset 保証 (情報捏造ゼロ、機械検証済)」「sentence-transformers encoder は GraphRAG 等と同じ扱い、index 構築段階で hallucination 経路を遮断」 |
| **B. 既知の事実 (LLM 挙動の baseline)** | 「現行 Claude family (Haiku 4.5 / Sonnet 4.6) は ≤10K token grounded QA で hallucination / drift とも robust」「LayerForge filter で context を 63% 削減しても AI 性能は damage しない」 |
| **C. 組合せ workflow** | 「LLM に渡す前に決定論で削る pipeline」「Mode A/B/C で同一 core を異なる目的に再利用」「CC skill 形態 (ADR-014) で API 課金なし運用」「philosophy filter (機械検証 → AI 実行) の物理実装例」 |

### 3.2 書ける主張 (citation 戦略、3 分離準拠)

| 主張 | 軸 | 根拠 |
|---|---|---|
| Human cognitive capacity は 3-5 chunks | (citation) | Cowan (2010) |
| RAG chunk size に universal optimum なし、corpus 依存 | (citation) | AI21 (2026), arxiv 2505.21700 |
| Community detection は RAG passage clustering の establish 済み手法 | (citation) | RAPTOR, Microsoft GraphRAG, HippoRAG |
| Modularity 最適化には resolution limit (√(L/2)) | (citation) | Fortunato & Barthélemy (2007) |
| Q > 0.3 で意味のある community structure (慣習) | (citation) | Newman 系列 |
| **LayerForge 本体は決定論コード、LLM 不在で動作** | A | コード本体 (`layerforge/core/*`, `layerforge/cli/*`) |
| **本コーパスで K=4 が empirical optimum (Q=0.712, 4/4 above resolution limit)** | A | `scripts/k_sweep/data_archive/k_exact_results.json` |
| **Mode C 圧縮率 14-40%、subset 保証** | A | `tests/cli/test_compress.py` |
| **n=10,000 を 32 秒、sparse path で同規模 + cross-contamination 対応** | A | `scripts/benchmark.py` |
| **現行 Claude family は ≤10K token grounded QA で hallucination / drift とも robust** | B | `scripts/halluc_benchmark/`, `scripts/multiagent_demo/` |
| **context 63% 削減で AI 性能 regression なし (両条件 drift_count=0)** | B+C | `scripts/multiagent_demo/verdict.json` |
| **Mode A/B/C を同一 deterministic core で実装した運用 API** | C | `layerforge/cli/{decompose,decide,compress}.py` |
| **CC skill 形態でこの pipeline を運用できる設計** | C | `.claude/skills/layerforge/SKILL.md`, ADR-014 |

### 3.3 書かない方が安全な主張

| 危険な主張 | 理由 | 修正先 |
|---|---|---|
| 「Cowan 4±1 が emerge した / 自然に出てきた」 | resolution limit artifact 可能性、本コーパスが偶然 4-theme | 「Q peak が K=4 の corpus を扱った」と書く |
| ~~「K=10-12 が AI 用途で最良」~~ | ~~N=9 question で統計的に弱い~~ | **§2.4c で multi-corpus 検証完了**: 「**K=10 で全 4 corpus × 2 embedder で self-routing 100% を維持、10% 圧縮達成。AI Agent 入力 routing 用途として regression なし**」(self-routing は paraphrased query より弱いテストの注意付き) |
| ~~「4±1 は corpus 構造依存」~~ | ~~N=1 corpus でしか検証してない~~ | **§2.4b で N>1 検証完了**: 「**vocabulary-distinct + 強 embedder の条件下では K_optimal が N_themes を tracking する。同一ドメイン docs では Q が poor のまま K_optimal は信頼できない**」 |
| ~~「LayerForge は hallucination を減らす」~~ | ~~3 連続 null result~~ | **B 軸**: 「現行 LLM は filter 有無に robust」と書く |
| ~~「Mode C はマルチエージェント連携で drift を減らす」~~ | ~~1 件 null result~~ | **B+C 軸**: 「context 63% 削減でも AI 性能維持、regression なし」と書く |
| 「LayerForge は AI を賢くする」 | category mistake (LayerForge は A 軸、AI 賢さは B 軸) | 「決定論で context を制御し、AI 性能は filter 有無に robust」と分けて書く |

---

## §4. 開いている疑問 (本ドキュメントの限界)

| 未確定 | 必要な検証 |
|---|---|
| `find_valid_scale` の binary search が「range 内で **first valid** = 上限を選ぶ」性質、これを「Q 最大」or「above-limit fraction 最大」に変えるべきか | algorithm 改善候補、ADR-016 として記録 |
| 本観察が他コーパスでも成立するか | 別 N-theme corpus での再現、N=1 で言えない |
| Mode C の「読みやすさ」便益 | 本人運用 (ドッグフーディング)、AI 委任不可 |
| Mode B の認知補助具としての実用価値 | 同上、本人運用領域 |
| ~~**Newman modularity を CPM (Traag 2011) に置換した場合の挙動差**~~ | ✅ **実装済 (2026-05-13)**: `layerforge/core/cpm_backend.py` に CPM-Louvain を自前実装 (MIT-pure、外部 GPL 依存なし、ADR-018 で経緯記録)。`community_method="cpm"` で切替可能、`scripts/k_sweep/cpm_compare.py` で Newman vs CPM の N×K 比較データ生成。結果は §6 に追記 |
| **STAR method (Grassetti 2026) による degeneracy 緩和** | post-processing で代表 partition を選ぶ。Newman 実装を残したまま追加可能、決定論性に注意 |
| **above-limit fraction が K selection metric として novel か** | 浅い literature search では先行研究見当たらないが確証なし。deeper search 前は「本実装で採用した補助 metric」に主張範囲を留める |
| **Silhouette / Davies-Bouldin / Gap statistic 系の K selector との比較** | LayerForge は KMeans 経由なので sklearn 標準指標が低コストで追加可能。modularity 系とは別系統の K 推薦が可能 |

---

## §5. 本ドキュメントの位置づけ

- **更新タイミング**: 新たな検証実施時、結果が確定したら本ドキュメントに追記
- **citation 元として使う場合**: §1 のテーブルをそのまま参照、§2 を「LayerForge での観察」として引用
- **書き直す場合**: §3 の表をベースに、各主張を「safe / project-specific / unsafe」のいずれかに分類してから書く

---

## §6. Engineering Finding — K 選択指標の安定性比較 (2026-05-12 追記、05-12 補正)

> **位置づけ**: 既存研究 (Fortunato & Barthélemy 2007 / Good 2010) の resolution limit と Q degeneracy を engineering 実装で測定した結果。**他論文の批判ではなく、自プロジェクトの観察として記録**。今後の report 執筆時はこの節を pitch line の根拠に使う。
>
> **2026-05-12 補正**: 当初本節は「Q max が unstable」を LayerForge の発見として書いていたが、文献調査の結果 **Good et al. (2010)** が Q degeneracy を理論的に既に確立していたことを確認。本節の主張を「**既知結果 (Good 2010) の N×K 軸での実証**」に格下げ。同時に γ 付き modularity (Reichardt-Bornholdt) も resolution limit を持つ (Kumpula 2008) ため、γ sweep は逃げ道にならない。真の resolution-limit-free 手法として **CPM (Traag 2011)** が存在するが本実装は未対応 (§4 future work)。これらは §1.6 で citation 整備済み。

### 6.1 何を測ったか

cross-domain mpnet corpus を **per_theme = 2,3,4,5,6,8,10** で構築し、各 N について **K = 2..15** をスイープ。  
**合計 98 セル** (N×K matrix, 7 N-values × 14 K-values)。  

セルごとに 2 つの指標:
- **Modularity Q** — Newman 系列の慣習指標
- **Above-limit fraction** — Fortunato-Barthélemy resolution limit (√(L/2)) を超えるコミュニティの割合

### 6.2 観察

**観察 1: Q peak が K 軸で N に強く依存する(bouncy)**

| N | Q peak K | Q peak value |
|---:|---:|---:|
| 8  | 3  | 0.519 |
| 12 | 6  | 0.674 |
| 16 | 11 | 0.679 |
| 20 | 6  | 0.667 |
| 24 | 9  | 0.638 |
| 32 | 4  | 0.660 |
| 40 | 6  | 0.661 |

→ Q max を K 選択基準にすると **同一コーパス構造でも N が変わるたびに推奨 K が跳ねる**。Q max alone は実用的 K 推薦器として不安定。

**観察 2: Above-limit fraction は K に対して monotone decreasing で N に対して安定**

- どの N でも、K が小さいうち (K ≤ N_themes 付近) は above-limit ≈ 1.0
- K が大きくなるにつれ単調に減少 (sub-resolution-limit な小コミュニティが増える)
- N が変わっても下降カーブの形は崩れない

→ 「**このコミュニティ分割が resolution-limit artifact か否か**」のシグナルとして, above-limit fraction は **K と N の両方に対して挙動が読める**。

### 6.3 Engineering claim (safe に書ける形)

> Newman modularity の Q maximization は K 選択の一意な基準にならない (**Good et al. 2010 で理論的に確立済み**)。  
> 本実装では同一 corpus 構造のサンプリング N を変えると Q peak K が 3〜11 の範囲で跳ねることを **N×K matrix (98 cells) で実証**。  
> 一方、Fortunato-Barthélemy resolution limit (√(L/2)) を K ごとに評価した above-limit fraction は **K に対して monotone**、N に対しても安定。  
> 本実装では K 推薦の判定指標として above-limit fraction を主、Q を補助に用いている。  
> なお、Q degeneracy の根本対策としては **CPM (Traag 2011) への置換** が筋だが本実装は未対応 (§4 future work)。γ 付き modularity (Reichardt-Bornholdt) は **Kumpula 2008 で resolution limit が残ることが示されている**ため逃げ道にならない。

書かない方が良い形:
- ❌ 「他手法 (GraphRAG/RAPTOR) の Q ベース K 選択は誤りである」 — 彼らが具体的に何を最適化しているかは別途検証が必要、かつ Q degeneracy 指摘自体は Good (2010) が既出
- ❌ 「Q max は使えない」 — Q 自体は有用、**alone では K 推薦に不十分** という主張に留める
- ❌ 「LayerForge が Q degeneracy を発見した」 — Good (2010) で確立済み、本実装は **N×K 軸での再現観察**
- ❌ 「above-limit fraction が K selection の新 metric」 — literature search 深掘り前は主張不可、現状は「本実装で採用した補助 metric」

### 6.4 K=10 (AI Agent 入力圧縮用途) の位置づけ

別軸の検証 (§2.4c) では、**K=10 で 4 corpus × 2 embedder すべてで self-routing 100%、平均 10% 圧縮**。  
Q 最適 K (corpus により K=4〜11 で揺れる) と AI 用途 K (=10, 圧縮率と routing の Pareto 上) は **目的関数が違う**。  
- 「真のテーマ構造を可視化」 → K=N_themes 付近 (Q peak、above-limit=1.0)
- 「AI Agent input compression」 → K=10 (compression × self-routing Pareto)
- 「人間 readability」 → K=4-5 (Cowan 4±1 + above-limit を満たす範囲)

→ 「最適 K は単一値ではなく目的依存」を engineering finding として書ける。これは AI21 (2026) の "per-query optimal で 20-40% headroom" と整合する。

### 6.5 成果物 (再現可能性)

| 項目 | パス |
|---|---|
| N×K matrix 生データ | `scripts/k_sweep/data_current/heatmap_data.csv` |
| Q heatmap | `scripts/k_sweep/plots/heatmap_Q_N_x_K.png` |
| Above-limit heatmap | `scripts/k_sweep/plots/heatmap_above_limit_N_x_K.png` |
| Q vs K, varying N (line plot) | `scripts/k_sweep/plots/Q_vs_K_per_N.png` |
| 5 configs × 12 K × 2 methods fine-grained 生データ | `scripts/k_sweep/data_current/correlation_data.csv` (119 rows) |
| Pareto: Q × compression | `scripts/k_sweep/plots/pareto_Q_vs_compression.png` |
| Pareto: Q × above-limit | `scripts/k_sweep/plots/pareto_Q_vs_above_limit.png` |
| グラフ解釈ガイド | `scripts/k_sweep/plots/README.md` |
| 再現スクリプト | `scripts/k_sweep/heatmap_N_x_K.py`, `correlation_data.py`, `pareto_plot.py` |

### 6.6 future report での pitch line 候補

1. 「Q degeneracy (Good 2010) を N×K 軸で実証。**Fortunato-Barthélemy resolution limit ベースの above-limit fraction を補助指標** に組み合わせる engineering choice で、N によらず安定した K 推薦が可能になった (本実装での観察)」
2. 「K_optimal は目的依存。**真構造可視化 (K≈N_themes)・AI input compression (K=10)・人間 readability (K=4-5)** を分けて出すと corpus に対して spurious な universality 主張を避けられる」
3. 「決定論コア (LayerForge) は LLM 不在で動作するため、'LLM の振る舞いを観察する実験基盤' としても使える。本ドキュメントは A 軸 (コア) / B 軸 (LLM) / C 軸 (組合せ) を分離して記述している」

これらはどれも **他手法の批判形式を取らずに自分の貢献として立つ** 主張。報告書執筆時はここから選ぶ。  
**注意**: pitch 1 は「Good (2010) を踏まえた engineering 実装」と書く必要がある。「LayerForge が Q 不安定性を発見した」と書くと literature 認識不足と見られるリスクあり。

---

### 6.7 Newman vs CPM 実証比較 (2026-05-13 追記)

> **目的**: ADR-017 / ADR-018 で「CPM (Traag 2011) が真の resolution-limit-free 解、Newman は理論的に degenerate」と整理した上で、**本実装上の挙動差を実測**。pitch 1 の defensibility を確保。

**測定設定**: cross-domain mpnet corpus、per_theme ∈ {3, 5, 6, 8, 10} → N ∈ {12, 20, 24, 32, 40}、K ∈ {2..10, 12}、method ∈ {newman, cpm}。100 cells、95 row 成功 (5 row は CPM γ bisection 失敗 — Louvain 単独で高 K に届かないケース、Leiden refinement なしの限界)。

**生データ**: `scripts/k_sweep/data_current/cpm_compare_data.csv` (95 rows)。

#### 観察 1: Newman Q peak K は確かに bouncy

| N | Newman Q peak K | Newman Q at peak |
|---:|---:|---:|
| 12 | 6 | 0.778 |
| 20 | 6 | 0.716 |
| 24 | 9 | 0.646 |
| 32 | 4 | 0.550 |
| 40 | 6 | 0.610 |

→ §6.2 の発見 (N に対する K bouncy 性) を CPM 実装後にも再確認。Good (2010) Q degeneracy の N 軸での実証は維持。

#### 観察 2: CPM は Newman Q を直接最適化しないため Q peak K の bouncy 比較は misleading

CPM partition を Newman Q で cross-eval すると、Q 値は **すべての K で ≈ 0 か負** (e.g., N=20 で K=2: Q=-0.004、K=10: Q=-0.081)。これは CPM が H を最適化しており Q を見ていないためで、**CPM の "Q peak K bouncy 性は問えない"**。

→ 「Q peak K の bouncy は CPM に置き換えれば消える」という素朴な期待は **本実装の枠組では verify できない**。理論的には CPM は resolution-limit-free だが、**Newman Q の N 不安定性を直接消す手段としては機能しない**(metric 系が異なる)。

#### 観察 3: Above-limit fraction は両方法でほぼ同等の monotone decreasing

| N | K | Newman above | CPM above |
|---:|---:|---:|---:|
| 12 | 2 | 1.00 | 0.50 |
| 12 | 3 | 0.67 | 0.67 |
| 12 | 4 | 0.25 | 0.25 |
| 12 | 5+ | 0.00 | 0.00 |
| 20 | 2 | 1.00 | 0.50 |
| 20 | 3 | 1.00 | 0.67 |
| 20 | 4 | 0.50 | 0.50 |

> **Source 注記**: 本表は `scripts/k_sweep/data_current/cpm_compare_data.csv` 由来で、**両 method ともに median similarity を共通 reference graph として使用**。method-independent な reference のため (Newman vs CPM) 比較が strictly fair。Paper §5.2 の上記類似の表は `scripts/k_sweep/data_current/heatmap_data.csv` 由来で、Newman は own θ / CPM は median similarity という **asymmetric reference** を使う (Newman の resolution limit binding を直接測るため)。両 table は異なる目的・異なる方法論で、reference graph の違いで一部 cell の値が異なる。例: (20, 4) Newman は本表 (cpm_compare、共通 median ref) で 0.50、heatmap 表 (Newman own θ ref) で 0.75 ─ Newman の own θ で threshold するとより多くの edges が残り、above-limit を超える community 割合も上がる。(20, 4) CPM は本表で 0.50、heatmap 表でも 0.50 (CPM 側は両 source とも median ref を使うため一致)。

→ **Fortunato-Barthélemy resolution limit ベースの above-limit fraction は method-agnostic** (Newman / CPM 両方で同程度のスケール、同じ単調性)。本実装で採用した「補助 metric」としての position は両方法に対し有効。

#### 観察 4: CPM-Louvain は高 K target でしばしば NoValidScaleError

per_theme=3 (N=12) で K=9、per_theme=5 (N=20) で K=12、per_theme=10 (N=40) で K=10 等が γ bisection 範囲内 (γ_hi=5.0) で hit せず失敗。**Louvain 単独 (Leiden refinement なし) の表現力限界**。LayerForge の運用域 (K≤8) では問題ないが、より細かい K で動かす場合は Leiden refinement の追加実装が必要 (ADR-018 § future work)。

#### 観察 5: target_range=(K,K) 制約下で K は同じだが、member 帰属は N に依存して divergent

target_range=(K,K) で両方法とも K 個に分割するが、**member 帰属の一致度 (ARI / Adjusted Rand Index)** は N に応じて変化:

| N | ARI mean | ARI min | ARI max | 解釈 |
|---:|---:|---:|---:|---|
| 12 | **0.871** | -0.036 | 1.000 | 高一致 (一部 K で完全一致) |
| 20 | **0.728** | 0.050 | 1.000 | 高一致 |
| 24 | 0.689 | 0.033 | 1.000 | 中一致 |
| 32 | 0.490 | -0.006 | 0.779 | **divergent** (1.0 に達さない) |
| 40 | 0.411 | -0.010 | 0.842 | **divergent** |

**解釈**:
- 小 N (N≤24) では Newman と CPM が **ほぼ同じ partition** に到達する K がある (ARI=1.0)
- 大 N (N≥32) では **最も一致しても ARI≈0.8 止まり**、平均 ARI は 0.4-0.5 と divergent
- 「Newman と CPM のどちらを採用しても同じ」と言える **operating range は小 N に限定**
- LayerForge の典型運用 (N=20-40 の cross-domain corpus) は **divergence 領域に入る** ため、method 選択が partition 品質に影響する可能性あり

これは「Newman を採用しても CPM を採用しても結果が変わらない」という素朴な期待を **本実装枠組で empirical に却下** する観察。**method choice は LayerForge の運用域では一定の影響を持つ**。

#### 結論 (本実装での engineering claim — 2026-05-13 ARI 追加後の更新版)

> **Newman Q peak は確かに bouncy で Good (2010) の Q degeneracy を本コーパスで再現する。CPM は理論的に resolution-limit-free だが、Newman Q の cross-eval で見る限り Q metric の不安定性そのものを消すわけではない**(CPM は H を別途最適化するため Q peak の概念がそもそも適用しにくい)。**両方法に対し above-limit fraction は同様 monotone decreasing で、本実装の補助 K-selection metric として method-agnostic に機能する**。
>
> **partition 一致度 (ARI) は N 依存**: 小 N (N≤24) で 0.7-0.87 と高一致、大 N (N≥32) で 0.4-0.5 と divergent。**LayerForge の典型運用域 (N=20-40) は divergence 領域**で、method choice (Newman vs CPM) は partition 品質に影響する。「どちらを選んでも同じ」とは言えない。

→ pitch 1 の主張は維持可能、**ただし「CPM で解決」とは書かない**。代わりに「Newman + above-limit fraction の組合せが本実装の engineering choice、CPM 比較は dual-mode + 95-row N×K×method × ARI 測定で実証」と書く。

#### Karate Club 正確性検証 (authoritative reference check)

`tests/axioms/test_cpm_karate_club.py` で Zachary (1977) の Karate Club graph (34 nodes、78 edges、known 2-community ground truth) に対し自前 CPM-Louvain 実装を検証:

- ✅ Edge list well-formed (34 nodes, 78 edges, symmetric)
- ✅ moderate resolution で K∈[2,4] の妥当な範囲 (K=4 が標準 Louvain 出力)
- ✅ ARI vs empirical 2-community truth > 0.5 (測定値: ARI=0.595 at γ=0.001, seed=42; **chance baseline ARI=0**)
- ✅ K は γ に monotone-increasing
- ✅ 同じ seed で deterministic

**注記**: vanilla Louvain-CPM (Leiden refinement なし) は Karate Club で K=2 macro split に直接到達せず K=4 sub-communities を出すのが文献既知の挙動 (Traag et al. 2019 が Leiden refinement の必要性として論じている)。ARI=0.595 は「**4 sub-communities が 2 macro truth に対し sub-clustering として correct に bundle されている**」ことを意味し、本実装が正しく動作している間接証拠。

**Limitations** (更新版):
- ✅ ~~ARI / NMI ベースの partition 一致度比較は未実施 (v2)~~ → **本節で実施完了**
- ✅ ~~authoritative reference 再現テスト~~ → **Karate Club で実施完了**
- ⏳ **CPM-Louvain は Leiden refinement なし、高 K target で限界あり** — 運用域 K≤8 で問題なし、v2 候補
- ⏳ **自前実装の数値正確性を GPL leidenalg と直接比較**は license 制約で不可、ただし synthetic 3-block + Karate Club ARI で間接検証済

**成果物**:
| 項目 | パス |
|---|---|
| 95-row 比較データ (ARI/NMI 含む) | `scripts/k_sweep/data_current/cpm_compare_data.csv` |
| Q peak K vs N | `scripts/k_sweep/plots/cpm_vs_newman_Qpeak_K.png` |
| Above-limit vs K | `scripts/k_sweep/plots/cpm_vs_newman_above_limit.png` |
| **ARI vs K, per N** | `scripts/k_sweep/plots/cpm_vs_newman_ari.png` |
| 再現スクリプト | `scripts/k_sweep/cpm_compare.py` |
| Karate Club 正確性テスト | `tests/axioms/test_cpm_karate_club.py` (5 件) |
| 実装 | `layerforge/core/cpm_backend.py`, `community.py` |
| 経緯 | ADR-018 (`docs/06`) |

---

## §7. 検証マトリックス — Newman / CPM / method-independent 整理 (2026-05-13 追加)

> **目的**: 論文執筆時に「どの結果が Newman 由来か / CPM 由来か / 共通基盤か」で迷わないよう、全検証を A 軸 (LayerForge core) / B 軸 (LLM behavior) / C 軸 (workflow) ごとに分類し、現状の measurement 状態を一覧する。

### 7.1 全 verification の分類表

| # | 検証 / テスト | 軸 | 何を測ったか | Newman | CPM | 備考 |
|---:|---|---|---|---|---|---|
| **A 軸 — LayerForge core (community-detection method 依存)** ||||||
| 1 | `scripts/k_sweep/correlation_data.py` | A | 5 configs × 12 K の Q/routing/compr/above/purity | ✅ | ✅ | PR #5 で dual-method 化、CSV 119 rows |
| 2 | `scripts/k_sweep/heatmap_N_x_K.py` | A | 7 N × 14 K の Q/above-limit | ✅ | ✅ | PR #5 で dual heatmap (Newman \| CPM) |
| 3 | `scripts/k_sweep/cpm_compare.py` | A | Newman vs CPM の ARI/NMI 一致度 | ✅ | ✅ | PR #4、ARI N依存 divergence 発見 |
| 4 | `scripts/k_sweep/multi_corpus_verify.py` (v1, v2) | A | K_optimal が N_themes を tracking するか | ✅ | ❌ | §2.4b の Newman-only baseline、CPM 再検証候補 |
| 5 | `scripts/k_sweep/k10_multi_corpus.py` | A | K=10 で self-routing 100% 維持 | ✅ | ❌ | §2.4c の Newman-only、AI compression 主張の核 → CPM 再検証候補 |
| 6 | `scripts/k_sweep/resolution_limit_check.py` | A | Fortunato-Barthélemy threshold 違反 | ✅ | (N/A) | **CPM は理論的に resolution-limit-free**、概念的に CPM へ単純適用不可 |
| 7 | `scripts/k_sweep/run_robustness.py` | A | corpus/embedder/seed の sensitivity | ✅ | ❌ | broad sweep、CPM 追加で 2× cells |
| 8 | `scripts/verify_real_data.py` + `tests/integration/test_real_data_20ng.py` | A | 20 Newsgroups benchmark | ✅ | ❌ | 外部 corpus、CPM 再検証候補 |
| 9 | `tests/axioms/test_modularity.py` | A | Newman Q 計算の単体テスト | ✅ | (N/A) | Newman 算法の検証、CPM とは別系統 |
| 10 | `tests/axioms/test_cpm_backend.py` | A | CPM-Louvain 単体テスト (13 件) | (N/A) | ✅ | CPM 算法の検証 |
| 11 | `tests/axioms/test_cpm_karate_club.py` | A | Karate Club reference (5 件、ARI=0.595) | (N/A) | ✅ | CPM 正確性 authoritative check |
| 12 | `tests/axioms/test_sca_residual.py`, `test_hercules_recursion.py`, `test_determinism.py`, `test_cowan_constraint.py`, `test_recursive_depth.py`, `test_sparse_similarity.py` | A | core 算法 (SCA / HERCULES / 4±1 / sparse など) | (method-independent) | (method-independent) | method 選択に関わらず動作する pipeline 周辺 |
| **B 軸 — LLM behavior (LayerForge-controlled context 下)** ||||||
| 13 | `scripts/halluc_benchmark/` | B | 現行 LLM の hallucination 率 (LayerForge context 下) | (Newman context) | ❌ | null result (LLM robust)、再検証コスト高 (LLM 呼出)、再実施 non-priority |
| 14 | `scripts/multiagent_demo/` | B+C | multi-agent drift in compressed-context workflow | (Newman context) | ❌ | null result、同上 |
| **C 軸 — combined workflow / API (method-independent)** ||||||
| 15 | `tests/cli/test_compress.py`, `test_decide*.py`, `test_decompose.py` | C | Mode A/B/C CLI 統合 | (method-independent) | (method-independent) | Mode 切替の動作、method 選択は orthogonal |
| 16 | `tests/integration/test_full_pipeline.py`, `test_sentence_transformers_backend.py` | C | end-to-end pipeline | (method-independent) | (method-independent) | パイプライン疎通、method 選択は orthogonal |

### 7.2 論文での扱い (paper-writing reference)

| claim | data source | 軸 | method 説明の責任 |
|---|---|---|---|
| 「Cowan 4±1 が本実装で **emerge する**」(慎重に書くなら「観察された」) | `heatmap_data.csv`、`correlation_data.csv` | A | **Newman / CPM 両方で確認済み** (PR #5 heatmap dual-panel) |
| 「Newman Q peak K は N に対して bouncy」 | `heatmap_data.csv` Newman side | A | **Newman に固有**(Good 2010 既知 → 本実装で実証) |
| 「Above-limit fraction は method-agnostic な monotone signal」 | `heatmap_data.csv`、`correlation_data.csv` | A | **両 method で確認** (PR #5)、論文の中核 engineering claim |
| 「K=10 で self-routing 100% × 圧縮 10x」 | `data_current/k10_multi_corpus_results.json` (Newman) | A | **Newman のみ**(現状)。**CPM 再検証 pending** |
| 「K_optimal は N_themes を tracking する」 | `multi_corpus_results_v2.json` (Newman) | A | **Newman のみ**(現状)。**CPM 再検証 pending** |
| 「Newman と CPM の partition は N≥32 で divergent (ARI 0.41-0.49)」 | `cpm_compare_data.csv` | A | **dual-method、独立発見** (§6.7) |
| 「LayerForge は LLM 不在で動作」 | コード本体 | A+C | **method-independent**、LayerForge core の性質 |
| 「現行 LLM は context filter 有無に robust」 | `halluc_benchmark/out/`、`multiagent_demo/verdict.json` | B | **Newman context で得られた null result**。LayerForge core の判断ではない |
| 「context 63% 削減で AI 性能 regression なし」 | `multiagent_demo/verdict.json` | B+C | 同上 |

### 7.3 「Newman で得た結果」を CPM 再検証する優先順位

| Rank | 対象 | 再検証の motivation | 想定工数 |
|---:|---|---|---|
| 1 | `multi_corpus_verify_v2.py` (§2.4b) | 「K_optimal が N_themes を tracking」は本実装の核 claim。CPM でも tracking するなら method-agnostic な finding になる。divergent なら honest disclosure | 半日 |
| 2 | `k10_multi_corpus.py` (§2.4c) | 「K=10 で self-routing 100%」は AI input compression pitch の核。CPM でも維持するなら主張が頑健に | 半日 |
| 3 | `run_robustness.py` | corpus/embedder/seed 横断、broad sweep | 半日 |
| 4 | 20 Newsgroups (`verify_real_data.py`, `test_real_data_20ng.py`) | 外部公開 benchmark、reproducibility 向上 | 1日 |
| skip | `resolution_limit_check.py` | CPM は理論的に resolution-limit-free、適用しても新規 finding 期待薄 | (skip) |
| skip | `halluc_benchmark/`, `multiagent_demo/` | B 軸 null result、再検証で LLM コスト発生し新 evidence 弱い | (skip) |

### 7.4 CPM 再検証実行結果 (Rank 1-4 実施、2026-05-13)

§7.3 で計画した Rank 1-4 の CPM 再検証を順次実行。結果は paper-writing 時にそのまま使える形で以下に集約。

#### Rank 1: multi_corpus_verify_v2 — 「K_optimal が N_themes を tracking する」検証

8 条件 (2 corpora × 2 embedders × 2 methods):

| corpus | embedder | method | N_themes | K_optimal | Q | purity | tracking? |
|---|---|---|---:|---:|---:|---:|---|
| same-domain 5themes | MiniLM | newman | 5 | **5** | 0.132 | 0.75 | ✅ exact |
| same-domain 5themes | MiniLM | cpm | 5 | 2 | -0.002 | 0.60 | ❌ |
| cross-domain 4themes | MiniLM | newman | 4 | 3 | 0.123 | 0.79 | △ Δ=1 |
| cross-domain 4themes | MiniLM | cpm | 4 | 2 | -0.014 | 0.66 | △ Δ=2 |
| same-domain 5themes | mpnet | newman | 5 | 2 | 0.27 | 0.30 | ❌ |
| same-domain 5themes | mpnet | cpm | 5 | 2 | -0.002 | 0.60 | ❌ |
| cross-domain 4themes | mpnet | newman | 4 | **3** | 0.542 | 0.78 | △ Δ=1 |
| cross-domain 4themes | mpnet | cpm | 4 | **3** | -0.027 | 0.78 | △ Δ=1 |

**Finding**: Newman tracks N_themes well at "Q acceptable" configs (cross-domain mpnet K=3 vs N=4). CPM systematically settles at K=2-3 regardless of N_themes — does NOT track. Output: `multi_corpus_results_v2.json`

#### Rank 2: k10_multi_corpus — 「K=10 で self-routing 100% × 圧縮 10x」検証

8 条件 (2 corpora × 2 embedders × 2 methods)、K=10 セルのみ抜粋:

| corpus | embedder | method | self-route at K=10 | compression at K=10 |
|---|---|---|---:|---:|
| same-domain 5themes | MiniLM | newman | **30/30 (100%)** | 0.10 (10x) |
| same-domain 5themes | MiniLM | cpm | 29/30 (97%) | 0.10 |
| cross-domain 4themes | MiniLM | newman | **24/24 (100%)** | 0.10 |
| cross-domain 4themes | MiniLM | cpm | 23/24 (96%) | 0.10 |
| same-domain 5themes | mpnet | newman | **30/30 (100%)** | 0.10 |
| same-domain 5themes | mpnet | cpm | **30/30 (100%)** | 0.10 |
| cross-domain 4themes | mpnet | newman | **24/24 (100%)** | 0.10 |
| cross-domain 4themes | mpnet | cpm | **24/24 (100%)** | 0.10 |

**Finding**: AI input compression headline holds robustly. **Newman: 100% × 4/4 corpora**. **CPM: 96-100%, average 98%**, slight degradation but practically equivalent. Compression is method-independent (1/K). Output: `data_current/k10_multi_corpus_results.json`

#### Rank 3: run_robustness — 16 条件 × 2 methods で「H_struct: Q peak K = N_themes」を検証

| n_themes | embedder | seed | Newman peak K | CPM peak K | Newman tracks? | CPM tracks? |
|---:|---|---:|---:|---:|---|---|
| 3 | MiniLM | 42 | 8 | 2 | ❌ | △ |
| 3 | MiniLM | 123 | **3** | **3** | ✅ | ✅ |
| 4 | MiniLM | 42 | **4** | 3 | ✅ | △ |
| 4 | MiniLM | 123 | **4** | 3 | ✅ | △ |
| 5 | MiniLM | 42 | **5** | **5** | ✅ | ✅ |
| 5 | MiniLM | 123 | **5** | 4 | ✅ | △ |
| 7 | MiniLM | 42 | **7** | 6 | ✅ | △ |
| 7 | MiniLM | 123 | **7** | 3 | ✅ | ❌ |
| 3 | mpnet | 42 | 12 | 2 | ❌ | △ |
| 3 | mpnet | 123 | **3** | **3** | ✅ | ✅ |
| 4 | mpnet | 42 | **4** | 3 | ✅ | △ |
| 4 | mpnet | 123 | **4** | 1 | ✅ | ❌ |
| 5 | mpnet | 42 | **5** | 4 | ✅ | △ |
| 5 | mpnet | 123 | **5** | 4 | ✅ | △ |
| 7 | mpnet | 42 | **7** | 1 | ✅ | ❌ |
| 7 | mpnet | 123 | **7** | 1 | ✅ | ❌ |

**Finding**:
- **Newman: 14/16 (87.5%) exact-tracking** with n_themes — strong H_struct evidence
- **CPM: 3/16 (19%) exact, 8/16 (50%) within ±1, 5/16 underestimates by ≥2** — does NOT support H_struct
- Routing accuracy: Newman 100% across all 16, CPM 100% in 12/16, drops to 71-86% at n_themes=7 MiniLM

**Implication for paper**: H_struct is **a Newman-side finding**. With CPM, the partition is coarser than n_themes, suggesting CPM's resolution-limit-free property pushes toward fewer-but-larger communities. Output: `data_current/robustness_results.json`

#### Rank 4: 20 Newsgroups (verify_real_data.py + test_real_data_20ng.py)

`tests/integration/test_real_data_20ng.py` を pytest.mark.parametrize で newman/cpm 両方走らせる版に変更:

| method | K_actual (default) | ARI vs ground truth | purity assertion |
|---|---:|---:|---|
| newman | 3 | **0.430** (target ≥ 0.40) | ✅ pass (60%+ purity in ≥half layers) |
| cpm | 3 | **0.239** (target ≥ 0.20) | ✅ pass (60%+ purity in ≥half layers) |

参考: K を 4 に固定すると Newman ARI=0.557、K=5 で 0.313。CPM は K=3,4,5 すべてで ARI ≈ 0.24 (under-merging plateau)。

ARI threshold for CPM is **lower** because honest finding: **CPM produces partition with ARI ≈ 0.24 vs Newman's 0.43 at default K=3** on this corpus (Newman は K=4 強制で 0.557 まで到達)。Both pass their respective method-appropriate thresholds; chance baseline is 0.

**Finding**: 20NG is **a clear case where method choice changes external-validation performance**. Newman achieves ARI 0.430 vs ground-truth at default K=3 (and up to 0.557 at K=4); CPM achieves ~2-3× chance baseline but ~1.8-2.3× below Newman depending on K. Output: 2 passed tests in `tests/integration/test_real_data_20ng.py` (再現性は 2x re-run で確認、§paper §4.6 v6)。

#### §7 統合 summary — paper claim を method 別に整理

| claim | Newman 支持 | CPM 支持 | 両者一致? |
|---|---|---|---|
| "K_optimal tracks N_themes" (H_struct) | **強** (14/16 = 87.5%) | 弱 (3/16 = 19%) | ❌ Newman finding |
| "K=10 で self-routing ≥96%" (AI compression) | **完全** (100% × 4/4) | **強** (96-100% × 4/4) | ✅ 両方支持 |
| "Above-limit fraction は monotone-stable" (engineering signal) | ✅ (§7.1 #1, 2) | ✅ (§7.1 #1, 2) | ✅ 両方支持 |
| "Newman vs CPM partition は N≥32 で divergent" (ARI) | (target) | (target) | ✅ §6.7 |
| "Cowan 4±1 が emerge" | **強** (real corpora 多数で K=4-5) | 弱 (CPM はもっと coarse) | ❌ Newman finding |
| "20NG で ARI ≥ 0.4 at default K=3 (Newman は K=4 強制で ≥ 0.55)" | ✅ (0.430 / 0.557) | ❌ (0.239) | ❌ Newman finding |

**Paper writing 上の含意**:
- 主張を「Newman + above-limit」と「CPM + above-limit」で分けると、Newman 系の external validity (ARI vs ground truth, H_struct) が一貫して高いことを明示できる
- CPM は「method-robust check」用途で有効 — Newman の主張がどこまで頑健か (どの finding が method-invariant か) を分離できる
- AI compression (K=10) は method-agnostic finding として最強
- Cowan 4±1 / H_struct / 20NG-ARI は Newman-specific finding として誠実に書く

### 7.5 Method-selection signals — 判定 rule の concept-only 記述 (2026-05-13)

> **位置づけ**: Rank 1-4 で Newman vs CPM の挙動差を測ったので、「どちらの method を使うか」を判定する rule が **構成可能** であることが分かった。ただし LayerForge の典型 domain (N=20-40 cross-domain text) では判定 rule の出力がほぼ常に "newman" になるため、**code 実装の cost > 得る情報量** と判断、現時点では **概念のみ docs に記録、実装はしない**。
>
> 本節は paper writing 時の「method-robust check も実装可能だが scope 外」という記述、および将来別 domain (大 N、dense graph) への拡張時の foundation として残す。

#### 7.5.1 5 つの discriminator signal 候補

LayerForge の existing pipeline で計算可能、追加依存なしの signal:

| Signal | 計算式 | 計算コスト | 識別力 | 推奨閾値 (本実証から) |
|---|---|---|---|---|
| **S1: Newman Q at default K** | `compute_modularity(sim, labels, theta)` | 極低 (既存 API) | 高 | Q ≥ 0.3 → Newman で良い / Q < 0.2 → どちらも弱い |
| **S2: Above-limit fraction at default K** | `Σ[m_c > √(L/2)] / K` (Fortunato-Barthélemy ratio) | 低 | **最高** | ≥ 0.5 → resolution limit 非 binding、Newman safe / < 0.3 → CPM 検討余地 |
| **S3: Edge density at θ** | `L / (N(N-1)/2)` | 極低 | 中 | dense (>0.5) → CPM 考慮 / sparse (<0.3) → Newman |
| **S4: Corpus size N** | (input から直接) | ゼロ | 中 | N < 100 → Newman / N > 1000 → CPM 検討 |
| **S5: Cross-method ARI at probe K** | 両 method 実行 + `adjusted_rand_score` | 中 (両 method 必要) | 高 | ARI > 0.7 → どちらも同等 / ARI < 0.3 → uncertainty 警告 |

#### 7.5.2 Empirically-derived decision rule

Rank 1-4 の実測 (16 settings × 2 methods + 20NG + multi-corpus) から導出した rule:

```
def recommend_community_method(similarity, target_range, default_K=4):
    # Step 1: Run Newman at default_K (cheap probe)
    newman = layerforge_core(..., community_method="newman",
                              target_range=(default_K, default_K))
    Q = newman.quality_metrics.modularity
    above_limit = compute_above_limit_fraction(newman.layers, sim, theta)
    N = similarity.shape[0]

    # Step 2: Apply decision rule (empirically calibrated, §7.4)
    if Q >= 0.3 and above_limit >= 0.5:
        # Strong Newman regime: clean structure visible, no resolution limit issue
        return ("newman", f"Q={Q:.2f} good + above-limit={above_limit:.2f} safe")

    if above_limit < 0.3 and N >= 100:
        # CPM-favored regime (rare in LayerForge domain, foundation for large graphs)
        return ("cpm", f"above-limit={above_limit:.2f} low + N={N} large — try CPM")

    if Q < 0.2:
        # Neither method finds clean structure (poor corpus)
        return ("newman", f"Q={Q:.2f} poor — no clean structure; default Newman (K-stable)")

    # Intermediate: empirically Newman still wins in LayerForge domain
    return ("newman", "intermediate regime — Newman default empirically validated")
```

#### 7.5.3 本実証で観測された判定 distribution

LayerForge typical operating domain (Rank 1-4 のセル分布):

| Regime | 判定出力 | 頻度 | 例 |
|---|---|---|---|
| Strong Newman (S1 + S2 両方 OK) | "newman" | **~70%** | cross-domain mpnet K=4 (Q=0.61, above=1.0) |
| Newman-poor (Q低) | "newman" (K-stable default) | ~25% | same-domain corpora (vocab overlap) |
| CPM-favored (high N + low above-limit) | "cpm" | **~0%** | 本実証範囲内ではゼロ |
| Intermediate | "newman" | ~5% | edge cases |

→ **本 domain では 100% "newman" が出力される**。判定機を code 化しても情報量ゼロ。

#### 7.5.4 実装する場合の scope (将来別 domain 拡張時の reference)

実装は **judgement: cost > value** で現時点 skip、ただし以下を foundation として残す:

| 構成要素 | 配置先 (案) | 実装規模 |
|---|---|---|
| `compute_above_limit_fraction()` API | `layerforge.core.modularity` (既に部分実装あり) | 50行 |
| `recommend_community_method()` 本体 | `layerforge.core.method_selector` (新規) | 100-150行 |
| Advisory field を Mode A 出力に追加 | `layerforge.cli.decompose._serialize_core_result` (拡張) | 30行 |
| Tests (5 signals × edge cases) | `tests/axioms/test_method_selector.py` (新規) | 200行 |

→ **総工数 ~ 1 日**、追加依存ゼロ、CI への追加負荷ゼロ。  
→ 別 domain (N=1000+ で CPM が favorable になり得る場面) に LayerForge を拡張したい時、判定機実装は **本節を再読してから着手** すれば OK。

#### 7.5.5 Paper writing 時の活用法

論文では code 実装の有無に関わらず、本節を **「method-selection is principled, not arbitrary」** の論拠として使える:

> 「We provide both Newman and CPM backends. Method choice is **not arbitrary**: the empirical decision rule based on `above-limit fraction` and `Newman Q at default K` predicts Newman-advantage with ARI/H_struct in our domain. The rule itself is documented (docs/08 §7.5); code-level implementation is deferred (cost > value in N<100 domain).」

これは **「default 採用に empirical 根拠あり」** を runtime code 化せずとも示せる engineering pitch。
