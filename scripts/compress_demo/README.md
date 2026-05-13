# Mode C demonstration — AI verbose output compression

LayerForge `compress` 検証。AI に多面的質問を投げて verbose 回答を得て、
別の質問でその回答を圧縮 (出力を絞る) ことができるかを試す。

**目的**: ハルシネーション低減ではなく、**情報過多 (information overload) 対策**。
AI は聞かれた以上のことを返す傾向があり、認知負荷の原因になる。
LayerForge で出力を user 質問に対応する layer に絞ることで読み量を削減する。

## 実験

入力: AI による verbose 回答 (15,240 chars、~40 paragraphs、8 トピック横断)
- pytest 基本、coverage、CI/CD、test data 管理、edge cases 等を **混在** で記述
- 元質問: 「Python で 新規 プロジェクトに unit test を導入したい。 基本的な書き方を教えて。」

## 結果

### Q1 (基本的書き方) + paraphrase-MiniLM-L3-v2

```
入力: 10,511 chars
出力: 1,501 chars (ratio 0.143, 14%)
layer_count: 5
selected: L0 (pytest 基本 setup) - sim 0.86 ← 質問にぴったり
deferred:
  L1: 12 items (coverage)
  L2:  3 items (CI/CD)
  L3: 17 items (test data 管理)
  L4:  2 items (matrix build)
```

→ 「基本的書き方」質問に対し、coverage / CI/CD / test data / matrix を defer して
   pytest 基本 setup の部分のみを返した。**圧縮率 14%、内容も正しく絞れている**。

### Q2 (CI/CD 質問) + 小型モデル

```
selected: L3 (test data 管理) ← misroute!
sims: [0.69, 0.68, 0.60, 0.69, 0.62]
```

→ 小型モデル (MiniLM-L3) では「CI/CD」と「test data」を十分に区別できず、
   L3 (test data) が誤選択された。embedding 表現力不足が露呈。

### Q2 (CI/CD 質問) + 大型モデル (mpnet)

```
入力: 15,240 chars
出力: 5,057 chars (ratio 0.332, 33%)
layer_count: 3
selected: L1 (CI/CD) - sim 0.5522 ← 正解
deferred:
  L0: 22 items (基本書き方 + 他)
  L2:  4 items (test data)
selected の冒頭: "CI/CD への接続は、テストを「書いた」状態から「常に動いている」状態へ..."
```

→ mpnet (multilingual) で正しく L1 (CI/CD) を選択。圧縮率 33%。

### Q3 (test data 管理) + 小型モデル

```
selected: L3 (test data 管理) - sim 0.834 ← 正解
ratio: 0.403
```

→ 小型モデルでも単独で明確な layer なら正しく選べる。

## 観察された事実

| 観察 | 解釈 |
|---|---|
| 圧縮率 14-40% | 認知負荷削減として meaningful (元の 1/3 から 1/7 まで縮む) |
| selected_text は元の paragraph をそのまま含む (subset) | LayerForge は情報を捏造しない (機械検証済) |
| Defer 件数を可視化 | user は「N 件繰延された」と認知できる、必要なら expand 要求 |
| 大型モデルが route 精度向上 | embedding 品質が直接効く |

## わかること

- **Mode C は output を絞る目的を達成する**
- 圧縮の挙動は決定論で再現可能 (機械検証可)
- routing 精度は embedding モデルに依存 (小型では誤 route が観測される)
- production では `paraphrase-multilingual-mpnet-base-v2` 等の中-大型モデル推奨

## わからない / 言えない

- 「読みやすさ」自体は **本人主観**、本人運用が必要
- 圧縮した結果がタスクに十分か = 本人判断
- LayerForge を **使うべき場面 / 使わない場面の境界** = 本人の運用感覚

これは ADR-013 のドッグフーディング領域と同じく、AI 委任不可。

## 再現方法

```bash
# 1. verbose 回答を生成 (subagent や手動でも可)
#    → scripts/compress_demo/verbose_response.txt

# 2. compress 実行
python -X utf8 -m layerforge.cli.compress \
  --question "あなたの質問" \
  --response-file scripts/compress_demo/verbose_response.txt \
  --embedding-backend sentence_transformers \
  --embedding-model sentence-transformers/paraphrase-multilingual-mpnet-base-v2 \
  --pretty
```
