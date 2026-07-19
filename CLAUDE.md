# CLAUDE.md

Claude Code がこのリポジトリで毎回同じ前提・ルール・フローで作業するための指示書。
迷ったら本ファイルを最優先の根拠とする。曖昧な判断は避け、ここに書かれた具体ルールに従う。

---

## 1. Project Overview

### 概要
RAiCA 2.0 は人材紹介業務の業務アプリ。RA（企業担当）と CA（候補者担当）が、推薦・面談・成約・並行状況・自分の次アクションを 1 画面で管理する。個人名・企業名・数値は PoC 用の架空データ。

### 目的
- 候補者と案件を 9 軸スコアでマッチングし、推薦判断を支援する。
- 承認済み（HITL: Human-in-the-loop）の連絡のみ Gmail / Zalo / Asana へ送信する。
- Porters など外部システムと同期し、業務データを一元管理する。

### アーキテクチャ概要
- **モノレポ**構成。フロント（SPA）とバックエンド（REST API）を分離。
- バックエンドは FastAPI が REST API を提供し、本番はビルド済みフロントを静的配信する。
- データは SQLAlchemy モデル経由で SQLite（開発）/ PostgreSQL（本番）に永続化。
- 外部連携は失敗しても `outbox_events` に残り、画面から再送できる（アダプター + Outbox パターン）。

### 使用技術（サマリ）
React 19 + TypeScript + Vite（フロント） / FastAPI + SQLAlchemy 2.0 + Alembic（バックエンド） / SQLite・PostgreSQL（DB）。詳細は §2。

### ディレクトリ構成（必要最低限）
```text
frontend/src/
  components/     再利用 UI（Badge, Sidebar, Topbar, EmptyState, RecommendationComposer）
  views/          画面単位のコンポーネント（Dashboard, Candidates, Jobs, Matching, ...）
  api.ts          API クライアント（fetch ラッパー）
  types.ts        フロント側の型定義
  i18n.tsx        多言語辞書（ja / vi / en）
  styles.css      全 CSS（CSS 変数ベース）
backend/app/
  main.py         FastAPI アプリ生成・起動処理
  api.py          業務エンドポイント
  models.py       SQLAlchemy モデル
  schemas.py      Pydantic スキーマ
  matching.py     9 軸スコアリング
  skill_sheets.py PDF/Word 解析
  integrations.py 外部連携アダプター
  config.py       設定（環境変数 RAICA_*）
backend/migrations/  Alembic マイグレーション
backend/tests/       pytest
data/                開発用 SQLite と CSV 受け渡し
```

---

## 2. Tech Stack

| 領域 | 採用技術 |
|---|---|
| Frontend | React 19 + TypeScript（strict）+ Vite 8。状態管理ライブラリは不使用（React hooks のみ）。 |
| Backend | Python 3 + FastAPI + SQLAlchemy 2.0 + Pydantic Settings。外部 HTTP は httpx。 |
| Database | SQLite（開発）/ PostgreSQL 16（本番, psycopg3）。マイグレーションは Alembic。 |
| Authentication | 任意の API キー方式（`X-RAICA-Key` ヘッダ）。本番はゲートウェイ配下前提。 |
| Hosting | Docker Compose（PostgreSQL + FastAPI）。FastAPI がビルド済みフロントを配信。 |
| Package Manager | フロント: npm / バックエンド: pip + venv（`.venv`）。 |
| Testing | バックエンド: pytest（`backend/tests`）/ フロント: `tsc` 型チェック + `vite build`。 |
| CI/CD | 現時点で CI 定義なし。ローカルは `make test` を基準とする。 |
| Linter | フロント: `tsc -b`（`npm run lint` = 型チェック）。バックエンド: 専用 linter 未導入。 |
| Formatter | 専用 formatter は未導入。既存ファイルのスタイルに合わせる。 |

> 重要: ESLint / Prettier / Ruff / Black は未導入。品質担保は型チェック・build・pytest で行う。新規ツールを勝手に追加しない（§8）。

---

## 3. Coding Standards

### TypeScript ルール
- `strict` を維持。`any` を新規に増やさない。型は `types.ts` に集約し、`import type { ... }` で読み込む。
- API レスポンスは `api.ts` の型付き関数経由でのみ取得する（生 `fetch` を各所に散らさない）。
- null/undefined は `??` / オプショナルチェーンで明示的に扱う。

### 命名規則
- コンポーネント・型: `PascalCase`（`JobsView`, `MatchItem`）。
- 変数・関数: `camelCase`。定数辞書も `camelCase`（例: `statusLabels`）。
- Python: モジュール・関数・変数は `snake_case`、クラスは `PascalCase`。
- 環境変数はすべて `RAICA_` プレフィックス（フロント公開用は `VITE_` プレフィックス）。

### Component 設計
- 1 画面 = `views/` の 1 コンポーネント。共通 UI は `components/` に置く。
- props はインラインの型注釈で受ける（既存 View と同じ形式）。分割代入で受け取る。
- 表示テキストは原則 `i18n.tsx` の辞書キー経由（`useI18n()` の `t()`）。ja / vi / en の 3 言語すべてにキーを追加する。

### 関数設計
- 単一責務・短く保つ。派生データは `useMemo`、副作用は `useEffect` に閉じる。
- バックエンドは「API 層（`api.py`）→ ドメイン処理（`matching.py` 等）→ モデル（`models.py`）」の責務分離を守る。

### コメント方針
- 「なぜ」を書く。自明な「何を」は書かない。TODO/デバッグ用の一時コメントは残さない（§6）。

### Import ルール
- 型のみの import は `import type`。
- 相対 import は近接モジュールのみ（`../components`, `../i18n`）。深いネストの相対 import を避ける。
- 未使用 import を残さない（`tsc` で検出される）。

### Error Handling
- フロント: API エラーは `api.ts` の `request()` が `Error` を throw。呼び出し側で捕捉し、ユーザーに分かる形で表示する（握りつぶさない）。
- バックエンド: 想定エラーは適切な HTTP ステータスと `detail` を返す。外部連携失敗は例外で落とさず Outbox に退避する。

### Logging
- 監査対象の業務操作は監査ログ（audit）に記録する既存パターンに従う。
- `console.log` / `print` のデバッグ出力を本番コードに残さない。

### Folder 構成
- 新規ファイルは §1 の構成に従い、責務が一致するディレクトリへ置く。新カテゴリのディレクトリを勝手に作らない。

### 再利用性の考え方
- 2 箇所以上で使う UI・ロジックは共通化する。ただし 1 箇所しか使わないものを早すぎる抽象化で共通化しない（YAGNI）。

---

## 4. UI / UX Guidelines

### デザイン方針
- Apple HIG を参考にした**高密度・情報整理型**の業務 UI。装飾より一覧性・可読性を優先。
- 既存の `styles.css` の CSS 変数（`--surface`, `--border`, `--text`, セマンティックカラー）を使う。色を直値でハードコードしない。

### コンポーネント利用ルール
- 状態表示は `Badge`（`tone` は `statusTone()` で決定）、空状態は `EmptyState` を必ず使う。独自の代替を作らない。

### レスポンシブ対応
- デスクトップ主体だが 390px 幅で横スクロール（オーバーフロー）が出ないこと。テーブルは `table-scroll` でラップする。

### アクセシビリティ
- インタラクティブ要素にはラベル/`title`/`aria-label` を付ける（既存 View 準拠）。
- 色だけで情報を伝えない（テキスト併記）。

### アイコン利用
- アイコンは `lucide-react` のみ。他アイコンライブラリや画像アイコンを追加しない。サイズは既存に合わせる（13–16px 目安）。

### 色・余白・タイポグラフィ
- 色: `styles.css` の変数のみ。セマンティック（blue=情報 / green=成功 / red=注意 / orange=警告 / violet）を意味に沿って使う。
- 余白・角丸・影: 既存のリズム（surface, radii, shadow 変数）に合わせる。新しい値を独自に増やさない。
- フォント: システム UI フォント、letter-spacing 0。階層は既存の見出し要素（`eyebrow` / `h1` / `h2`）で表現。

### アニメーション方針
- 最小限。ローディングの `spin` など既存クラスを再利用。過度なトランジションを追加しない。

---

## 5. Development Workflow

Claude はタスクごとに以下を順に実施する。

1. **要件整理** — タスクの入出力・完了条件を言語化し、不明点は先に確認する。
2. **実装方針作成** — 変更するファイルと影響範囲を洗い出す。
3. **設計提案（必要時）** — DB スキーマ・API・大きな構造変更を伴う場合は、実装前に方針を提示して合意を取る。
4. **実装** — 最小差分で行う。既存の規約（§3, §4）に従う。
5. **Build** — `make build`（= `npm run build`）でフロントが通ることを確認。
6. **Lint / 型チェック** — `npm run lint`（= `tsc -b`）で型エラー 0。
7. **Test** — `make test`（backend pytest + frontend build）が緑になること。
8. **修正** — 失敗があれば原因を特定して直し、6〜7 を再実行する。
9. **最終確認** — §6 のチェックリストを 1 項目ずつ確認する。
10. **完了報告** — 変更点・実行したコマンドと結果・残課題を簡潔に報告する。

主要コマンド:
```bash
make install    # 依存インストール（venv + npm）
make dev-api    # バックエンド開発サーバ（:8000, reload）
make dev-web    # フロント開発サーバ（:5173, HMR）
make build      # フロントビルド
make test       # pytest + フロントビルド
```

---

## 6. Verification Checklist

タスク完了前に必ず全項目を確認する（1 つでも未達なら「完了」と報告しない）。

- [ ] Build 成功（`make build`）
- [ ] Lint / 型チェック成功（`npm run lint` = `tsc -b`、エラー 0）
- [ ] Test 成功（`make test`）
- [ ] 型エラーなし（フロント・Pydantic 双方）
- [ ] Console にエラー/警告なし（該当画面を確認）
- [ ] 不要なコメント（TODO・デバッグ）を残していない
- [ ] 不要なファイル（一時ファイル・実験コード）を残していない
- [ ] デッドコード・未使用 import / 変数なし
- [ ] i18n キーを ja / vi / en すべてに追加済み（UI 文言を触った場合）
- [ ] 秘密情報（`.env`・トークン）をコミットに含めていない

---

## 7. Git Workflow

### Branch 戦略
- `main` は常にデプロイ可能な状態を保つ。作業は必ずフィーチャーブランチで行う。
- ブランチ名は用途が分かる形式（例: `feature/...`, `fix/...`, `claude/...`）。

### Commit ルール
- 1 コミット = 1 論理変更。命令形の要約（例: `Add job filter by industry`）。
- 生成物・依存物（`node_modules`, `dist`, `*.sqlite3`, `.env`）はコミットしない（`.gitignore` 準拠）。

### Pull Request ルール
- PR は Draft で作成。目的・変更点・確認方法・影響範囲を記載する。
- リポジトリに PR テンプレートがあれば見出し構成に従う。

### レビュー前チェック
- §6 のチェックリストを全て満たしてから PR を出す。
- 差分に不要な変更（自動整形の巻き込み・無関係ファイル）が混ざっていないか確認する。

### Main ブランチへの扱い
- `main` へ直接コミット/直接 push しない。マージは PR 経由のみ。
- force push を `main` に対して行わない。

---

## 8. Restrictions（禁止事項 / 事前確認が必須）

以下は Claude が**勝手に**行わない。必要な場合は理由を添えて確認・提案してから着手する。

- ライブラリ・依存を勝手に追加/更新/削除しない（`package.json` / `requirements*.txt`）。
- DB スキーマ（`models.py` / Alembic マイグレーション）を勝手に変更しない。
- 環境変数（`RAICA_*` / `.env` / `.env.example`）を勝手に増減・変更しない。
- API 仕様（エンドポイント・リクエスト/レスポンス形状）を勝手に変更しない。既存フロントとの互換を壊さない。
- UI デザイン（レイアウト・配色・情報設計）を勝手に変更しない。
- 大規模リファクタリング（広域なファイル移動・命名変更・構造変更）を勝手に行わない。
- 秘密情報をコード/ログ/コミットに埋め込まない。
- 依頼範囲外のファイルを「ついでに」変更しない。

---

## 9. Best Practices（優先する実装方針）

- **シンプルさを優先** — 動く最小の実装を選ぶ。過剰な抽象化をしない。
- **可読性を優先** — 半年後の担当者が読める素直なコードにする。
- **再利用性を重視** — 既存の共通コンポーネント/関数をまず探し、あれば使う。
- **パフォーマンスを考慮** — 大きなリスト/再計算は `useMemo` 等で無駄な再描画を避ける。
- **型安全を維持** — 型で不整合を早期に潰す。`any` に逃げない。
- **保守性を重視** — 既存パターンに合わせ、局所的な例外ルールを作らない。
- **最小差分** — 目的に必要な変更だけを行い、レビューしやすくする。

---

## 10. Decision Rules（判断の優先順位）

実装で迷ったとき、上位を優先して判断する。

1. **正確性** — 仕様どおり正しく動くこと。データを壊さないこと。
2. **保守性** — 既存構造・規約に沿い、後から直しやすいこと。
3. **可読性** — 読んで意図が分かること。
4. **セキュリティ** — 秘密情報の保護・入力検証・権限の妥当性。
5. **パフォーマンス** — 上位を損なわない範囲で最適化する。
6. **実装速度** — 上位すべてを満たしたうえで最短を選ぶ。

判断がつかない・上位項目間でトレードオフが生じる場合は、独断で進めず選択肢を添えて確認する。
