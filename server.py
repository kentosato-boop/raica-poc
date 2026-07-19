#!/usr/bin/env python3
"""RAiCA PoC backend.

Serves the existing HTML demo and exposes a small SQLite-backed API that can
later be replaced with Porters CSV/API sync.
"""

from __future__ import annotations

import csv
import json
import sqlite3
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent
DB_DIR = ROOT / "db"
DB_PATH = DB_DIR / "raica.sqlite3"


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    DB_DIR.mkdir(exist_ok=True)
    with connect() as conn:
        conn.executescript((DB_DIR / "schema.sql").read_text(encoding="utf-8"))
        conn.executescript((DB_DIR / "seed.sql").read_text(encoding="utf-8"))


def rows(sql: str, params: tuple = ()) -> list[dict]:
    with connect() as conn:
        return [dict(row) for row in conn.execute(sql, params).fetchall()]


def one(sql: str, params: tuple = ()) -> dict:
    with connect() as conn:
        row = conn.execute(sql, params).fetchone()
        return dict(row) if row else {}


def import_candidates_csv(path: Path) -> int:
    required = {
        "porters_id",
        "name",
        "status",
        "ca_owner",
        "role_title",
    }
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"missing columns: {', '.join(sorted(missing))}")
        records = list(reader)

    sql = """
        INSERT INTO candidates (
          id, porters_id, name, status, ca_owner, role_title,
          years_experience, jlpt, desired_salary_million, commute_minutes,
          work_style, last_contact_date, avg_response_days, notes
        ) VALUES (
          :id, :porters_id, :name, :status, :ca_owner, :role_title,
          :years_experience, :jlpt, :desired_salary_million, :commute_minutes,
          :work_style, :last_contact_date, :avg_response_days, :notes
        )
        ON CONFLICT(porters_id) DO UPDATE SET
          name=excluded.name,
          status=excluded.status,
          ca_owner=excluded.ca_owner,
          role_title=excluded.role_title,
          years_experience=excluded.years_experience,
          jlpt=excluded.jlpt,
          desired_salary_million=excluded.desired_salary_million,
          commute_minutes=excluded.commute_minutes,
          work_style=excluded.work_style,
          last_contact_date=excluded.last_contact_date,
          avg_response_days=excluded.avg_response_days,
          notes=excluded.notes
    """
    normalized = []
    for record in records:
        porters_id = record["porters_id"].strip()
        normalized.append(
            {
                "id": record.get("id") or f"cand-{porters_id.lower()}",
                "porters_id": porters_id,
                "name": record["name"].strip(),
                "status": record["status"].strip(),
                "ca_owner": record["ca_owner"].strip(),
                "role_title": record["role_title"].strip(),
                "years_experience": float(record.get("years_experience") or 0),
                "jlpt": record.get("jlpt") or None,
                "desired_salary_million": float(record.get("desired_salary_million") or 0),
                "commute_minutes": int(record.get("commute_minutes") or 0),
                "work_style": record.get("work_style") or "onsite",
                "last_contact_date": record.get("last_contact_date") or None,
                "avg_response_days": float(record.get("avg_response_days") or 0),
                "notes": record.get("notes") or None,
            }
        )
    with connect() as conn:
        conn.executemany(sql, normalized)
    return len(normalized)


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self.path = "/RAiCA.html"
            return super().do_GET()
        if parsed.path.startswith("/api/"):
            return self.handle_api(parsed.path, parse_qs(parsed.query))
        return super().do_GET()

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/import/candidates":
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length) or b"{}")
            try:
                count = import_candidates_csv(ROOT / payload["path"])
            except (KeyError, ValueError, FileNotFoundError) as exc:
                return self.json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
            return self.json({"imported": count})
        return self.json({"error": "not found"}, HTTPStatus.NOT_FOUND)

    def handle_api(self, path: str, query: dict[str, list[str]]) -> None:
        if path == "/api/health":
            return self.json({"ok": True, "database": str(DB_PATH.name)})
        if path == "/api/stats":
            return self.json(
                {
                    "candidates": one("SELECT COUNT(*) AS count FROM candidates")["count"],
                    "active": one("SELECT COUNT(*) AS count FROM candidates WHERE status='active'")["count"],
                    "dormant": one("SELECT COUNT(*) AS count FROM candidates WHERE status='dormant'")["count"],
                    "jobs": one("SELECT COUNT(*) AS count FROM jobs WHERE status!='closed'")["count"],
                    "shortlisted": one("SELECT COUNT(*) AS count FROM matches")["count"],
                    "open_queue": one("SELECT COUNT(*) AS count FROM action_queue WHERE status='open'")["count"],
                }
            )
        if path == "/api/candidates":
            return self.json(rows("SELECT * FROM candidates ORDER BY last_contact_date DESC, name"))
        if path == "/api/jobs":
            return self.json(
                rows(
                    """
                    SELECT jobs.*, companies.name AS company_name
                    FROM jobs
                    JOIN companies ON companies.id = jobs.company_id
                    ORDER BY received_date DESC
                    """
                )
            )
        if path == "/api/matches":
            job_id = query.get("job_id", [None])[0]
            where = "WHERE matches.job_id = ?" if job_id else ""
            params = (job_id,) if job_id else ()
            return self.json(
                rows(
                    f"""
                    SELECT
                      matches.*,
                      candidates.name AS candidate_name,
                      candidates.role_title,
                      candidates.jlpt,
                      jobs.title AS job_title,
                      companies.name AS company_name
                    FROM matches
                    JOIN candidates ON candidates.id = matches.candidate_id
                    JOIN jobs ON jobs.id = matches.job_id
                    JOIN companies ON companies.id = jobs.company_id
                    {where}
                    ORDER BY score DESC
                    """,
                    params,
                )
            )
        if path == "/api/queue":
            role = query.get("role", [None])[0]
            where = "WHERE owner_role = ?" if role else ""
            params = (role,) if role else ()
            return self.json(rows(f"SELECT * FROM action_queue {where} ORDER BY due_date, severity", params))
        return self.json({"error": "not found"}, HTTPStatus.NOT_FOUND)

    def json(self, payload: object, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    init_db()
    server = ThreadingHTTPServer(("127.0.0.1", 8000), Handler)
    print("RAiCA backend: http://127.0.0.1:8000")
    server.serve_forever()


if __name__ == "__main__":
    main()
