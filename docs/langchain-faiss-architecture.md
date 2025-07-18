# LangChain & FAISS を使用した保険ドメイン知識の回答処理アーキテクチャ

## 概要
本システムは、LangChainとFAISSを活用して保険に関する質問に対して適切な回答を提供するRAG（Retrieval-Augmented Generation）システムです。

## アーキテクチャ図

```mermaid
graph TB
    subgraph "データ準備フェーズ"
        CSV[qa.csv<br/>保険Q&Aデータ] --> SETUP[setup_index.py]
        SETUP --> |Q文書をベクトル化| EMBED1[OpenAI Embeddings<br/>text-embedding-3-large]
        EMBED1 --> FAISS_INDEX[(FAISS Index<br/>index.faiss)]
        SETUP --> |A文書を保存| A_CSV[(a.csv<br/>回答データ)]
    end

    subgraph "ユーザークエリ処理フェーズ"
        USER[ユーザー<br/>LINE] --> |質問| MAIN[main.py]
        MAIN --> IC[IndexController]
        IC --> |クエリをベクトル化| EMBED2[OpenAI Embeddings<br/>text-embedding-3-large]
        EMBED2 --> |類似度検索| FAISS_INDEX
        FAISS_INDEX --> |上位K件取得| TOP_K[類似Q&A<br/>top_k=3]
        TOP_K --> |メタデータから<br/>識別番号取得| A_CSV
        A_CSV --> |回答テキスト取得| QA_LIST[Q&Aリスト]
    end

    subgraph "回答選択フェーズ"
        QA_LIST --> PROMPT[GetPrompt<br/>最適Q&A選択プロンプト]
        USER_Q[ユーザー質問] --> PROMPT
        PROMPT --> GPT[OpenAI GPT<br/>gpt-4o-mini]
        GPT --> |最も関連性の高い<br/>Q&Aを選択| SELECTED[選択されたQ&A]
        SELECTED --> |回答をユーザーに返す| USER
    end

    style CSV fill:#e1f5e1
    style FAISS_INDEX fill:#e1e5f5
    style A_CSV fill:#e1e5f5
    style USER fill:#f5e1e1
    style GPT fill:#f5f5e1
```

## 処理フローの詳細

### 1. データ準備フェーズ（setup_index.py）
- **入力**: qa.csv（質問、回答、内容、URLを含む保険Q&Aデータ）
- **処理**:
  1. 各Q&Aレコードを読み込み
  2. 質問文をOpenAI Embeddings（text-embedding-3-large）でベクトル化
  3. FAISSインデックスに保存（メタデータに識別番号とURLを含む）
  4. 回答文と内容を結合してa.csvに保存

### 2. ユーザークエリ処理フェーズ（IndexController.search_index）
- **入力**: ユーザーからの質問
- **処理**:
  1. 質問をOpenAI Embeddingsでベクトル化
  2. FAISSで類似度検索（L2距離）を実行
  3. 上位K件（デフォルト3件）の類似Q&Aを取得
  4. メタデータの識別番号から対応する回答をa.csvから取得

### 3. 回答選択フェーズ（IndexController.assist_ai）
- **入力**: ユーザー質問と上位K件のQ&Aリスト
- **処理**:
  1. GetPromptで選択用プロンプトを生成
  2. GPT-4o-miniに最も関連性の高いQ&Aを選択させる
  3. 選択されたQ&Aの回答をユーザーに返す

## 主要コンポーネント

- **FAISS**: 高速ベクトル類似検索
- **LangChain**: ベクトルストア管理とドキュメント処理
- **OpenAI Embeddings**: テキストのベクトル化
- **OpenAI GPT**: 最適なQ&A選択の判断
- **Firestore**: ユーザーデータと会話履歴の管理（図では省略）