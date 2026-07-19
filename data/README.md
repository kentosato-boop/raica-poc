# Porters CSV import

PoCでは、Porters API契約プランが確定するまでCSV日次同期を前提にする。

## 候補者CSV

`/api/import/candidates` に渡すCSVは以下の列を持つ。

必須:

- `porters_id`
- `name`
- `status` (`active`, `process`, `dormant`)
- `ca_owner`
- `role_title`

任意:

- `id`
- `years_experience`
- `jlpt`
- `desired_salary_million`
- `commute_minutes`
- `work_style`
- `last_contact_date`
- `avg_response_days`
- `notes`

実行例:

```bash
curl -X POST http://127.0.0.1:8000/api/import/candidates \
  -H 'Content-Type: application/json' \
  -d '{"path":"data/porters_candidates.csv"}'
```
