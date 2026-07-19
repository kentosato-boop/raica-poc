# Data directory

開発用SQLiteファイルとPorters CSVの受け渡し領域です。DB本体と実データCSVはGit管理しません。

本番は`RAICA_DATABASE_URL`にPostgreSQL接続文字列を設定します。Porters API連携は`.env.example`の`RAICA_PORTERS_*`を使用し、候補者・求人をupsertします。
