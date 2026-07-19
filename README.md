# RAiCA 2.0

RA（企業担当）とCA（候補者担当）の行動を、候補者・求人・選考データから生成するフルスタック業務アプリです。単一HTMLデモではなく、React/TypeScript、FastAPI、SQLAlchemy、PostgreSQL/SQLiteで構成しています。

## 構成

```text
frontend/             React + TypeScript + Vite
backend/app/          FastAPI、SQLAlchemyモデル、業務API、連携アダプター
backend/migrations/   Alembic DBマイグレーション
backend/tests/        API・DB・Porters同期テスト
data/                 開発用SQLiteとCSV受け渡し領域
compose.yaml          PostgreSQL + RAiCAの一括起動
```

## 実装済み

- 候補者、企業、求人、AIマッチ、選考、対応キュー、連絡履歴
- スキル35%、経験20%、日本語15%、給与15%、通勤15%の再スコアリング
- 推薦承認から選考レコード作成までのトランザクション
- Gmail、Zalo、Asana向けOutboxと再送処理
- Porters候補者・求人APIの取得、正規化、upsert、同期履歴
- 操作監査ログと任意APIキー認証
- SQLite開発環境とPostgreSQL本番環境
- Apple HIGを参考にした高密度・レスポンシブな業務UI

## ローカル起動

```bash
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements-dev.txt
cd frontend && npm install && npm run build && cd ..
python3 server.py
```

`http://127.0.0.1:8000`でアプリ、`http://127.0.0.1:8000/docs`でOpenAPIを確認できます。

開発時にフロントのホットリロードを使う場合:

```bash
make dev-api
make dev-web
```

フロントは`http://127.0.0.1:5173`です。

## PostgreSQL/Docker

```bash
docker compose up --build
```

PostgreSQLの永続ボリュームを使用し、ビルド済みフロントをFastAPIから配信します。

## 外部連携

`.env.example`を`.env`へ複製して認証情報を設定します。秘密情報はGitへ入れません。

| 連携 | 環境変数 | 動作 |
|---|---|---|
| Porters | `RAICA_PORTERS_*` | 候補者・求人APIを取得しDBへupsert |
| Gmail | `RAICA_GMAIL_WEBHOOK_URL` | 承認済み企業メールをOutbox経由で送信 |
| Zalo OA | `RAICA_ZALO_WEBHOOK_URL` | 承認済み候補者メッセージを送信 |
| Asana | `RAICA_ASANA_WEBHOOK_URL` | 電話・フォロータスクを外部同期 |

接続先が未設定・障害中でもイベントは`outbox_events`へ残り、画面から再送できます。

## API

| Method | Path | 内容 |
|---|---|---|
| GET | `/api/v1/dashboard` | KPI、パイプライン、優先対応、操作履歴 |
| GET | `/api/v1/candidates` | 候補者検索・状態フィルタ |
| GET | `/api/v1/jobs` | 求人一覧 |
| POST | `/api/v1/jobs/{id}/matches/run` | 5軸マッチング再計算 |
| PATCH | `/api/v1/matches/{id}` | 推薦承認・見送り |
| GET/PATCH | `/api/v1/actions` | RA/CA対応キュー |
| POST | `/api/v1/contacts` | HITL承認済み連絡をOutboxへ登録 |
| POST | `/api/v1/sync/porters` | Porters API同期 |
| GET | `/api/v1/integrations` | 外部接続状態 |
| GET | `/api/v1/outbox` | 外部送信キュー |
| GET | `/api/v1/audit` | 監査ログ |

## 検証

```bash
make test
```

個人名・企業名・業務数値はPoC用の架空データです。
