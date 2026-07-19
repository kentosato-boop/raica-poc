#!/usr/bin/env python3
"""RAiCA PoC: SQLite-backed API and static frontend server."""

from __future__ import annotations

import csv
import json
import os
import re
import sqlite3
import uuid
from datetime import date, datetime, timezone
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
DB_DIR = ROOT / "db"
DB_PATH = DB_DIR / "raica.sqlite3"
JLPT_LEVEL = {None: 0, "": 0, "N5": 1, "N4": 2, "N3": 3, "N2": 4, "N1": 5}


def connect(db_path: Path | None = None) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path or DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def migrate(conn: sqlite3.Connection) -> None:
    """Apply small additive migrations to databases created by earlier PoCs."""
    additions = {
        "candidates": {
            "age": "INTEGER",
            "gender": "TEXT",
            "skills_json": "TEXT NOT NULL DEFAULT '[]'",
        },
        "jobs": {
            "location": "TEXT",
            "min_experience_years": "REAL NOT NULL DEFAULT 0",
            "min_jlpt": "TEXT",
            "max_commute_minutes": "INTEGER",
            "required_skills_json": "TEXT NOT NULL DEFAULT '[]'",
        },
    }
    for table, columns in additions.items():
        existing = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})")}
        for name, definition in columns.items():
            if name not in existing:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")


def init_db(db_path: Path | None = None) -> None:
    target = db_path or DB_PATH
    target.parent.mkdir(exist_ok=True)
    with connect(target) as conn:
        conn.executescript((DB_DIR / "schema.sql").read_text(encoding="utf-8"))
        migrate(conn)
        conn.executescript((DB_DIR / "seed.sql").read_text(encoding="utf-8"))


def rows(sql: str, params: tuple = (), db_path: Path | None = None) -> list[dict]:
    with connect(db_path) as conn:
        return [decode_json_columns(dict(row)) for row in conn.execute(sql, params).fetchall()]


def one(sql: str, params: tuple = (), db_path: Path | None = None) -> dict:
    with connect(db_path) as conn:
        row = conn.execute(sql, params).fetchone()
        return decode_json_columns(dict(row)) if row else {}


def decode_json_columns(record: dict) -> dict:
    for key in tuple(record):
        if key.endswith("_json"):
            record[key.removesuffix("_json")] = json.loads(record.pop(key) or "[]")
    return record


def audit(conn: sqlite3.Connection, actor: str, action: str, entity_type: str, entity_id: str, details: dict) -> None:
    conn.execute(
        "INSERT INTO audit_logs(actor, action, entity_type, entity_id, details_json) VALUES (?, ?, ?, ?, ?)",
        (actor, action, entity_type, entity_id, json.dumps(details, ensure_ascii=False)),
    )


def import_candidates_csv(path: Path, db_path: Path | None = None) -> int:
    required = {"porters_id", "name", "status", "ca_owner", "role_title"}
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
          work_style, last_contact_date, avg_response_days, notes, age, gender, skills_json
        ) VALUES (
          :id, :porters_id, :name, :status, :ca_owner, :role_title,
          :years_experience, :jlpt, :desired_salary_million, :commute_minutes,
          :work_style, :last_contact_date, :avg_response_days, :notes, :age, :gender, :skills_json
        )
        ON CONFLICT(porters_id) DO UPDATE SET
          name=excluded.name, status=excluded.status, ca_owner=excluded.ca_owner,
          role_title=excluded.role_title, years_experience=excluded.years_experience,
          jlpt=excluded.jlpt, desired_salary_million=excluded.desired_salary_million,
          commute_minutes=excluded.commute_minutes, work_style=excluded.work_style,
          last_contact_date=excluded.last_contact_date, avg_response_days=excluded.avg_response_days,
          notes=excluded.notes, age=excluded.age, gender=excluded.gender, skills_json=excluded.skills_json
    """
    normalized = []
    for record in records:
        porters_id = record["porters_id"].strip()
        skills = [item.strip() for item in record.get("skills", "").split("|") if item.strip()]
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
                "age": int(record["age"]) if record.get("age") else None,
                "gender": record.get("gender") or None,
                "skills_json": json.dumps(skills),
            }
        )
    with connect(db_path) as conn:
        conn.executemany(sql, normalized)
        audit(conn, "porters-sync", "import", "candidate", "batch", {"count": len(normalized), "file": path.name})
    return len(normalized)


def axis_scores(candidate: dict, job: dict) -> dict[str, int]:
    candidate_skills = set(json.loads(candidate.get("skills_json") or "[]"))
    required_skills = set(json.loads(job.get("required_skills_json") or "[]"))
    skill = 100 if not required_skills else round(100 * len(candidate_skills & required_skills) / len(required_skills))
    minimum_exp = float(job.get("min_experience_years") or 0)
    experience = 100 if minimum_exp == 0 else min(100, round(100 * float(candidate["years_experience"]) / minimum_exp))
    required_jlpt = JLPT_LEVEL.get(job.get("min_jlpt"), 0)
    actual_jlpt = JLPT_LEVEL.get(candidate.get("jlpt"), 0)
    japanese = 100 if required_jlpt == 0 else min(100, round(100 * actual_jlpt / required_jlpt))
    desired = float(candidate.get("desired_salary_million") or 0)
    salary_max = float(job.get("salary_max_million") or 0)
    salary = 100 if not desired or not salary_max or desired <= salary_max else max(0, round(100 - ((desired - salary_max) / salary_max * 200)))
    max_commute = job.get("max_commute_minutes")
    commute_minutes = int(candidate.get("commute_minutes") or 0)
    commute = 100 if max_commute in (None, 0) or commute_minutes <= max_commute else max(0, round(100 - ((commute_minutes - max_commute) * 4)))
    return {"skill": skill, "experience": experience, "japanese": japanese, "salary": salary, "commute": commute}


def calculate_match(candidate: dict, job: dict) -> dict:
    axes = axis_scores(candidate, job)
    weights = {"skill": 0.35, "experience": 0.20, "japanese": 0.15, "salary": 0.15, "commute": 0.15}
    score = round(sum(axes[key] * weights[key] for key in weights))
    issues = [key for key, value in axes.items() if value < 75]
    shared = sorted(set(json.loads(candidate.get("skills_json") or "[]")) & set(json.loads(job.get("required_skills_json") or "[]")))
    return {
        **axes,
        "score": score,
        "similarity_pct": min(98, round(score * 0.9 + len(shared) * 4)),
        "ng_check": "要件ずらし: " + ", ".join(issues) if issues else "主要条件にNGパターンなし",
        "evidence_quote": f"候補者スキル: {', '.join(shared) if shared else '一致なし'} / 経験 {candidate['years_experience']}年 / {candidate.get('jlpt') or 'JLPT未登録'}",
    }


def run_matching(job_id: str, actor: str = "RA user", db_path: Path | None = None) -> list[dict]:
    with connect(db_path) as conn:
        job_row = conn.execute("SELECT * FROM jobs WHERE id=? AND status!='closed'", (job_id,)).fetchone()
        if not job_row:
            raise ValueError("job not found or closed")
        job = dict(job_row)
        candidates = [dict(row) for row in conn.execute("SELECT * FROM candidates WHERE status!='dormant'")]
        generated = []
        for candidate in candidates:
            result = calculate_match(candidate, job)
            if result["score"] < 70:
                continue
            match_id = f"match-{job_id}-{candidate['id']}"
            conn.execute(
                """INSERT INTO matches (
                  id, candidate_id, job_id, score, skill_score, experience_score, japanese_score,
                  salary_score, commute_score, similarity_pct, ng_check, evidence_quote
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(candidate_id, job_id) DO UPDATE SET
                  score=excluded.score, skill_score=excluded.skill_score,
                  experience_score=excluded.experience_score, japanese_score=excluded.japanese_score,
                  salary_score=excluded.salary_score, commute_score=excluded.commute_score,
                  similarity_pct=excluded.similarity_pct, ng_check=excluded.ng_check,
                  evidence_quote=excluded.evidence_quote, created_at=CURRENT_TIMESTAMP""",
                (match_id, candidate["id"], job_id, result["score"], result["skill"], result["experience"],
                 result["japanese"], result["salary"], result["commute"], result["similarity_pct"],
                 result["ng_check"], result["evidence_quote"]),
            )
            generated.append({"candidate_id": candidate["id"], **result})
        conn.execute("UPDATE jobs SET ai_candidate_count=? WHERE id=?", (len(generated), job_id))
        audit(conn, actor, "matching_run", "job", job_id, {"candidates": len(generated)})
    return sorted(generated, key=lambda item: item["score"], reverse=True)


class Handler(SimpleHTTPRequestHandler):
    db_path = DB_PATH

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self.path = "/RAiCA.html"
            return super().do_GET()
        if parsed.path.startswith("/api/"):
            return self.handle_get(parsed.path, parse_qs(parsed.query))
        return super().do_GET()

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        try:
            payload = self.read_json()
            return self.handle_post(parsed.path, payload)
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            return self.json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)

    def do_PATCH(self) -> None:
        parsed = urlparse(self.path)
        try:
            payload = self.read_json()
            return self.handle_patch(parsed.path, payload)
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            return self.json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)

    def handle_get(self, path: str, query: dict[str, list[str]]) -> None:
        if path == "/api/health":
            return self.json({"ok": True, "database": self.db_path.name, "time": datetime.now(timezone.utc).isoformat()})
        if path == "/api/stats":
            return self.json(self.stats())
        if path == "/api/dashboard":
            return self.json({"stats": self.stats(), "queue": self.queue_rows(None), "recent_activity": rows(
                "SELECT * FROM audit_logs ORDER BY id DESC LIMIT 10", db_path=self.db_path)})
        if path == "/api/candidates":
            clauses, params = [], []
            status = query.get("status", [None])[0]
            search = query.get("q", [None])[0]
            if status:
                clauses.append("status=?"); params.append(status)
            if search:
                clauses.append("(name LIKE ? OR role_title LIKE ? OR porters_id LIKE ?)")
                params.extend([f"%{search}%"] * 3)
            where = " WHERE " + " AND ".join(clauses) if clauses else ""
            return self.json(rows(f"SELECT * FROM candidates{where} ORDER BY last_contact_date DESC, name", tuple(params), self.db_path))
        if path == "/api/jobs":
            return self.json(rows("""SELECT jobs.*, companies.name AS company_name
                FROM jobs JOIN companies ON companies.id=jobs.company_id
                ORDER BY received_date DESC""", db_path=self.db_path))
        if path == "/api/matches":
            job_id = query.get("job_id", [None])[0]
            where, params = ("WHERE matches.job_id=?", (job_id,)) if job_id else ("", ())
            return self.json(rows(f"""SELECT matches.*, candidates.name AS candidate_name,
                candidates.role_title, candidates.years_experience, candidates.jlpt,
                candidates.age, candidates.gender, candidates.notes, jobs.title AS job_title,
                companies.name AS company_name
                FROM matches JOIN candidates ON candidates.id=matches.candidate_id
                JOIN jobs ON jobs.id=matches.job_id JOIN companies ON companies.id=jobs.company_id
                {where} ORDER BY score DESC""", params, self.db_path))
        if path == "/api/queue":
            return self.json(self.queue_rows(query.get("role", [None])[0]))
        if path == "/api/applications":
            return self.json(rows("""SELECT applications.*, candidates.name AS candidate_name,
                jobs.title AS job_title, companies.name AS company_name
                FROM applications JOIN candidates ON candidates.id=applications.candidate_id
                JOIN jobs ON jobs.id=applications.job_id JOIN companies ON companies.id=jobs.company_id
                ORDER BY applications.updated_at DESC""", db_path=self.db_path))
        if path == "/api/audit":
            return self.json(rows("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 100", db_path=self.db_path))
        return self.json({"error": "not found"}, HTTPStatus.NOT_FOUND)

    def handle_post(self, path: str, payload: dict) -> None:
        if path == "/api/import/candidates":
            requested = (DATA_DIR / payload["file"]).resolve()
            if DATA_DIR.resolve() not in requested.parents:
                raise ValueError("file must be inside data/")
            return self.json({"imported": import_candidates_csv(requested, self.db_path)}, HTTPStatus.CREATED)
        if path == "/api/matching/run":
            generated = run_matching(payload["job_id"], payload.get("actor", "RA user"), self.db_path)
            return self.json({"generated": len(generated), "matches": generated}, HTTPStatus.CREATED)
        if path == "/api/contacts":
            channel = payload["channel"]
            if channel not in {"gmail", "zalo", "phone", "email"}:
                raise ValueError("unsupported channel")
            log_id = f"contact-{uuid.uuid4().hex[:12]}"
            with connect(self.db_path) as conn:
                conn.execute("""INSERT INTO contact_logs
                    (id, candidate_id, company_id, channel, direction, sent_at, subject, body, human_approved_by)
                    VALUES (?, ?, ?, ?, 'outbound', ?, ?, ?, ?)""",
                    (log_id, payload.get("candidate_id"), payload.get("company_id"), channel,
                     datetime.now(timezone.utc).isoformat(), payload.get("subject"), payload["body"], payload["approved_by"]))
                if payload.get("queue_id"):
                    conn.execute("UPDATE action_queue SET status='done' WHERE id=?", (payload["queue_id"],))
                audit(conn, payload["approved_by"], "contact_recorded", "contact", log_id, {"channel": channel})
            return self.json({"id": log_id, "recorded": True}, HTTPStatus.CREATED)
        return self.json({"error": "not found"}, HTTPStatus.NOT_FOUND)

    def handle_patch(self, path: str, payload: dict) -> None:
        queue_match = re.fullmatch(r"/api/queue/([\w-]+)", path)
        match_match = re.fullmatch(r"/api/matches/([\w-]+)", path)
        if queue_match:
            status = payload["status"]
            if status not in {"open", "done", "snoozed"}:
                raise ValueError("invalid queue status")
            return self.update_record("action_queue", queue_match.group(1), "status", status, payload.get("actor", "RAiCA user"))
        if match_match:
            status = payload["recommendation_status"]
            if status not in {"shortlisted", "approved", "rejected", "process"}:
                raise ValueError("invalid recommendation status")
            match_id = match_match.group(1)
            with connect(self.db_path) as conn:
                current = conn.execute("SELECT candidate_id, job_id FROM matches WHERE id=?", (match_id,)).fetchone()
                if not current:
                    return self.json({"error": "not found"}, HTTPStatus.NOT_FOUND)
                conn.execute("UPDATE matches SET recommendation_status=? WHERE id=?", (status, match_id))
                if status in {"approved", "process"}:
                    app_id = f"app-{current['candidate_id']}-{current['job_id']}"
                    conn.execute("""INSERT INTO applications
                        (id, candidate_id, job_id, stage, recommended_at, last_event_at)
                        VALUES (?, ?, ?, 'recommended', ?, ?)
                        ON CONFLICT(candidate_id, job_id) DO UPDATE SET stage='recommended', updated_at=CURRENT_TIMESTAMP""",
                        (app_id, current["candidate_id"], current["job_id"], date.today().isoformat(), date.today().isoformat()))
                audit(conn, payload.get("actor", "RA user"), "status_change", "match", match_id, {"status": status})
            return self.json({"id": match_id, "recommendation_status": status})
        return self.json({"error": "not found"}, HTTPStatus.NOT_FOUND)

    def update_record(self, table: str, record_id: str, field: str, value: str, actor: str) -> None:
        with connect(self.db_path) as conn:
            cursor = conn.execute(f"UPDATE {table} SET {field}=? WHERE id=?", (value, record_id))
            if cursor.rowcount == 0:
                return self.json({"error": "not found"}, HTTPStatus.NOT_FOUND)
            audit(conn, actor, "status_change", table, record_id, {field: value})
        return self.json({"id": record_id, field: value})

    def stats(self) -> dict:
        return {
            "candidates": one("SELECT COUNT(*) count FROM candidates", db_path=self.db_path)["count"],
            "active": one("SELECT COUNT(*) count FROM candidates WHERE status='active'", db_path=self.db_path)["count"],
            "dormant": one("SELECT COUNT(*) count FROM candidates WHERE status='dormant'", db_path=self.db_path)["count"],
            "jobs": one("SELECT COUNT(*) count FROM jobs WHERE status!='closed'", db_path=self.db_path)["count"],
            "shortlisted": one("SELECT COUNT(*) count FROM matches WHERE recommendation_status='shortlisted'", db_path=self.db_path)["count"],
            "open_queue": one("SELECT COUNT(*) count FROM action_queue WHERE status='open'", db_path=self.db_path)["count"],
            "applications": one("SELECT COUNT(*) count FROM applications", db_path=self.db_path)["count"],
        }

    def queue_rows(self, role: str | None) -> list[dict]:
        where, params = ("WHERE owner_role=?", (role,)) if role else ("", ())
        return rows(f"SELECT * FROM action_queue {where} ORDER BY status='open' DESC, due_date, severity", params, self.db_path)

    def read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length > 1_000_000:
            raise ValueError("request body too large")
        payload = json.loads(self.rfile.read(length) or b"{}")
        if not isinstance(payload, dict):
            raise ValueError("JSON object required")
        return payload

    def json(self, payload: object, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        print(f"{self.address_string()} - {format % args}")


def main() -> None:
    init_db()
    port = int(os.environ.get("RAICA_PORT", "8000"))
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"RAiCA backend: http://127.0.0.1:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
