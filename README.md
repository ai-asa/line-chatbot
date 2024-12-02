# line chatbot

多機能LINEチャットボットの開発

## 概要
一般的なチャット、firestore、RAG、動画検索に加えて、サブスクリプション機能の試験導入など。web apiとして使用

## 主な機能
- 保険知識の提供（Knowledge Mode）
- Q&Aデータベースの検索（QA Mode）
- YouTube動画の検索と推奨（YouTube Mode）
- 営業提案のサポート（General Support Mode）
- サブスクリプション管理（Stripe連携）

## 技術スタック
- Python 3.x
- OpenAI API (GPT-4)
- LINE Messaging API
- YouTube Data API
- Firebase (Firestore)
- Stripe API
- FAISS (Facebook AI Similarity Search)
- LangChain

## セットアップ
1. 必要なパッケージのインストール:
    pip install -r requirements.txt

2. 環境変数の設定:
`.env`ファイルを作成し、以下の環境変数を設定:

    OPENAI_API_KEY=your_openai_api_key
    LINE_ACCESS_TOKEN=your_line_access_token
    YOUTUBE_DATA_API_KEY=your_youtube_api_key

3. 設定ファイルの確認:
`config.ini`で各種設定を行います:

    [CONFIG]
    retry_limit = 5
    openai_model = gpt-4o

    [INDEX]
    qa_csv_path = ./data/qa/qa.csv
    a_csv_path = ./data/index/a.csv
    q_index_path = ./data/index/
    top_k = 5

## プロジェクト構造
    .
    ├── main.py                 # メインアプリケーション
    ├── requirements.txt        # 依存パッケージ
    ├── config.ini             # 設定ファイル
    ├── .env                   # 環境変数
    └── src/                   # ソースコード
        ├── firestore/        # Firestore関連
        ├── line/            # LINE Bot関連
        ├── openai/          # OpenAI API関連
        ├── rag/            # RAG (検索) 関連
        ├── stripe/         # Stripe決済関連
        └── youtube/        # YouTube API関連

## デプロイ
Google Cloud Functionsにデプロイして使用することを想定しています。

## 注意事項
- API使用量に応じて課金が発生する可能性があります
- 各APIの利用規約を遵守してください
- 本番環境では適切なエラーハンドリングを実装してください

## ライセンス
このプロジェクトは通常非公開です。無断での使用、複製、配布は禁止されています。