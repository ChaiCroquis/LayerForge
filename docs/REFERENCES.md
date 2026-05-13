# References — primary literature

> 本リポジトリでは第三者論文 PDF を直接配布しない (著作権上の懸念回避)。  
> 採用論文は以下の永続的 URL から取得すること。

## Core algorithm references

| 内容 | 著者・年 | 入手先 |
|---|---|---|
| **SCA (Semantic Component Analysis)** — F2 distillation 算法の出典 | Eichin, Schuster, Groh, Hedderich (2024) | arxiv:2410.21054 — https://arxiv.org/abs/2410.21054 |
| **Modularity and community structure in networks** — Newman spectral 算法と modularity Q | Newman, M. E. J. (2006), PNAS 103(23):8577-8582 | DOI: 10.1073/pnas.0601602103 — https://www.pnas.org/doi/10.1073/pnas.0601602103 |
| **Resolution limit in community detection** — √(L/2) 制約 | Fortunato, S. & Barthélemy, M. (2007), PNAS 104(1):36-41 | DOI: 10.1073/pnas.0605965104 — https://www.pnas.org/doi/10.1073/pnas.0605965104 |
| **Cowan working memory capacity** — 4±1 / 3-5 chunks の出典 | Cowan, N. (2010), Current Directions in Psychological Science 19(1):51-57 | DOI: 10.1177/0963721409359277 |
| **Modularity Q degeneracy** | Good, B. H., de Montjoye, Y.-A., Clauset, A. (2010), Phys. Rev. E 81, 046106 | DOI: 10.1103/PhysRevE.81.046106 |
| **CPM (Constant Potts Model)** — resolution-limit-free community detection | Traag, V. A., Van Dooren, P., Nesterov, Y. (2011), Phys. Rev. E 84, 016114 | DOI: 10.1103/PhysRevE.84.016114 |
| **Leiden refinement** — Louvain → Leiden の well-connectedness 保証 | Traag, V. A., Waltman, L., van Eck, N. J. (2019), Scientific Reports 9, 5233 | DOI: 10.1038/s41598-019-41695-z |
| **Multi-resolution method の限界** | Kumpula, J. M. et al. (2008); Xiang, J. & Hu, K. (2011) | (各誌に掲載) |
| **STAR — modularity degeneracy への post-processing** | Grassetti, S. et al. (2026) | arxiv:2602.21838 |

## Community detection benchmarks and systematic comparisons (paper §1.2.4)

| 内容 | 著者・年 | 入手先 |
|---|---|---|
| **LFR benchmark** — community detection algorithm の標準 synthetic benchmark | Lancichinetti, A. & Fortunato, S. (2009), Phys. Rev. E 80, 016118 | DOI: 10.1103/PhysRevE.80.016118 |
| **Newman/CPM/RB/RN systematic 比較** — Surprise maximization の提案 | Aldecoa, R. & Marín, I. (2013), Scientific Reports 3, 2216 | DOI: 10.1038/srep02216 — https://www.nature.com/articles/srep02216 |
| **Zachary Karate Club** — community detection の canonical benchmark | Zachary, W. W. (1977), J. Anthropological Research 33(4):452-473 | (各誌) |
| **CPM as Hedonic Game** — CPM の game-theoretic 再定式化、robust partition criteria | Felipe, L. L., Avrachenkov, K., Menasche, D. S. (2025) | arxiv:2509.03834 — https://arxiv.org/abs/2509.03834 |

## Clustering-based topic modeling / graph-based text clustering (paper §1.2.1)

| 内容 | 著者・年 | 入手先 |
|---|---|---|
| **Top2Vec** — joint document/word embedding + HDBSCAN | Angelov, D. (2020) | arxiv:2008.09470 — https://arxiv.org/abs/2008.09470 |
| **Vec2GC** — graph-based clustering for text, hierarchical | Rao, R. N. & Chakraborty, M. (2021) | arxiv:2104.09439 — https://arxiv.org/abs/2104.09439 |
| **BERTopic** — transformer embedding + UMAP + HDBSCAN + class-based TF-IDF | Grootendorst, M. (2022) | arxiv:2203.05794 — https://arxiv.org/abs/2203.05794 |
| **CETopic** — SimCSE + UMAP + K-means + TFIDF variant (NAACL 2022) | Zhang, Z., Fang, M., Chen, L., Namazi-Rad, M.-R. (2022) | https://aclanthology.org/2022.naacl-main.285/ |
| **G2T (Graph2Topic)** — sentence embedding + community detection + TFIDF (本研究の最近接 substrate prior art) | Zhang, L., Liu, J., Yan, Q. (2023) | arxiv:2304.06653 — https://arxiv.org/abs/2304.06653 |
| **LLM-Assisted Topic Reduction for BERTopic** — BERTopic + LLM merge step | Janssens, W., Bogaert, M., Van den Poel, D. (2025) | arxiv:2509.19365 — https://arxiv.org/abs/2509.19365 |

## Hierarchical RAG and GraphRAG (paper §1.2.2)

| 内容 | 著者・年 | 入手先 |
|---|---|---|
| **RAPTOR** — recursive abstractive processing for tree-organized retrieval | Sarthi, P. et al. (2024, ICLR) | arxiv:2401.18059 — https://arxiv.org/abs/2401.18059 |
| **GraphRAG** — Leiden + LLM summarization で query-focused summarization | Edge, D. et al. (2024) | arxiv:2404.16130 — https://arxiv.org/abs/2404.16130 |
| **GraphRAG-Bench** — GraphRAG family の domain-specific reasoning benchmark | Xiao, Y. et al. (2025) | arxiv:2506.02404 — https://arxiv.org/abs/2506.02404 |
| **RAG vs. GraphRAG** — RAG / RAPTOR / HippoRAG2 / GraphRAG の統一評価 framework | Han, H. et al. (2026) | arxiv:2502.11371 — https://arxiv.org/abs/2502.11371 |
| **Core-based Hierarchies for Efficient GraphRAG** — Leiden を k-core decomposition に置換 (Q degeneracy 問題への別 angle) | Hossain, J. & Sarıyüce, A. E. (2026) | arxiv:2603.05207 — https://arxiv.org/abs/2603.05207 |

## Context and memory compression (paper §1.2.3)

| 内容 | 著者・年 | 入手先 |
|---|---|---|
| **Clustering-driven Memory Compression for On-device LLMs** — **本研究と framing が最も近い同時期 prior art (Samsung)** | Bohdal, O., Saha, P., Michieli, U., Ozay, M., Ceritli, T. (2026) | arxiv:2601.17443 — https://arxiv.org/abs/2601.17443 |
| **EDU-based Context Compressor** — Elementary Discourse Unit decomposition による structure-then-select 圧縮 | Zhou, Y. et al. (2025) | arxiv:2512.14244 — https://arxiv.org/abs/2512.14244 |

## Reference implementations (cloned externally, MIT-licensed)

| 内容 | repo | License | 帰属 |
|---|---|---|---|
| pyhercules — HERCULES 算法参考実装 | github.com/bandeerun/pyhercules | MIT (Copyright 2025 Bandee) | `layerforge/core/*` の hierarchical KMeans 設計で参照 |
| mainlp/semantic_components — SCA 公式実装 | github.com/mainlp/semantic_components | MIT (Copyright 2024 Florian Eichin) | `layerforge/core/distillation.py` で構造を踏襲、`semantic_components/decomposition.py:448` を line-level で参照 |

ソースコード内の citation はそれぞれ `layerforge/core/distillation.py:3,166` および `layerforge/constants.py:47` に明示。

## Related RAG / community-detection 系手法 (本実装では未採用、比較対象)

- RAPTOR — https://arxiv.org/abs/2401.18059
- Microsoft GraphRAG — https://arxiv.org/abs/2404.16130
- HippoRAG — https://arxiv.org/abs/2405.14831
- LinearRAG survey
- Mix-of-Granularity — arxiv:2406.00456
- AI21 multi-scale indexing (2026)
