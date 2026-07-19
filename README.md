# RAiCA 2.0

RA（企業担当）とCA（候補者担当）が、推薦、面談、成約、並行状況、自分の次アクションを一つの業務画面で管理するアプリです。

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

- 候補者、企業、案件、AIマッチ、選考、自分のボール、連絡履歴
- スキル、総経験、日本語、給与、通勤、年齢、勤務形態、専門経験、職歴安定性の9軸スコアリング
- PDF/Wordスキルシート解析と候補者レコードへの反映
- 社内並行・他社並行の一覧と選考ステージ表示
- 推薦承認後の推薦文生成、スキルシート添付、Gmail API送信
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
| Gmail | `RAICA_GMAIL_ACCESS_TOKEN`, `RAICA_GMAIL_SENDER` | 承認済み推薦文とスキルシートをGmail APIで送信 |
| Zalo OA | `RAICA_ZALO_WEBHOOK_URL` | 承認済み候補者メッセージを送信 |
| Asana | `RAICA_ASANA_WEBHOOK_URL` | 電話・フォロータスクを外部同期 |

接続先が未設定・障害中でもイベントは`outbox_events`へ残り、画面から再送できます。

## API

| Method | Path | 内容 |
|---|---|---|
| GET | `/api/v1/dashboard` | KPI、パイプライン、優先対応、操作履歴 |
| GET | `/api/v1/candidates` | 候補者検索・状態フィルタ |
| POST | `/api/v1/candidates/{id}/skill-sheet` | スキルシート解析・候補者DB反映 |
| GET | `/api/v1/jobs?q=` | 案件検索 |
| POST | `/api/v1/jobs/{id}/matches/run` | 9軸マッチング再計算 |
| PATCH | `/api/v1/matches/{id}` | 推薦承認・推薦文生成・見送り |
| GET/PATCH | `/api/v1/actions` | RA/CAの自分のボール |
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
