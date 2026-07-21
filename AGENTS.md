# AGENTS.md

RAiCA 2.0で作業するコーディングエージェント向けのガイドです。人間の開発者はREADME.mdと`docs/`を参照してください。

## プロジェクト概要

RA（企業担当）とCA（候補者担当）が推薦・面談・成約・並行状況・次アクションを一つの業務画面で管理する人材紹介業務アプリのPoCです。

- `frontend/` — React + TypeScript + Vite
- `backend/app/` — FastAPI、SQLAlchemyモデル、業務API、外部連携アダプター
- `backend/migrations/` — Alembic DBマイグレーション
- `backend/tests/` — API・DB・Porters同期テスト
- `docs/` — アーキテクチャ、ロジック仕様書、未決事項（日本語）

## セットアップ

```bash
make install        # venv作成 + Python/npm依存のインストール
```

環境変数は`.env.example`を参照。ローカル開発はSQLite（`data/raica.sqlite3`）で動作し、外部連携（Porters/Gmail/Zalo/Asana）は未設定でも起動できます。

## 開発・テスト

```bash
make dev-api        # FastAPIを127.0.0.1:8000で起動（ホットリロード）
make dev-web        # Viteデブサーバーを127.0.0.1:5173で起動
make test           # pytest（backend/tests）+ フロントのビルド検証
```

変更を加えたら必ず`make test`を通してからコミットしてください。バックエンドのみの変更でも、スキーマ変更がフロントの型に影響することがあるためフロントのビルドまで確認します。

## 規約

- コミットメッセージ・PR説明は日本語で書く
- バックエンドのDBスキーマ変更は必ずAlembicマイグレーション（`backend/migrations/`）を追加する。`RAICA_BOOTSTRAP_SCHEMA_ENABLED`による自動生成に頼らない
- 新しいAPIエンドポイントは`backend/app/api.py`に追加し、Pydanticスキーマを`schemas.py`に定義する
- 外部送信（Gmail/Zalo/Asana）は直接呼ばず、必ずOutbox（`outbox_events`）を経由する
- マッチングロジック（9軸スコアリング）の変更時は`backend/tests/test_matching_accuracy.py`を更新する
- フロントはApple HIGを参考にした高密度UIの方針。既存コンポーネントのスタイルに合わせる

## 注意事項

- `data/`配下のSQLite・CSVはコミットしない
- APIキー・トークン類をコードに埋め込まない（`.env`経由のみ）
- リポジトリ内の個人名・企業名・業務数値はすべてPoC用の架空データだが、実データを新たに追加しない
- `RAICA_ENVIRONMENT=production`の挙動（APIキー必須）を変更しない
