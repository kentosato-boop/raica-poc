import os
import tempfile
from pathlib import Path

import pytest

TEST_DIR = tempfile.TemporaryDirectory()
DB_PATH = Path(TEST_DIR.name) / "raica-test.sqlite3"
os.environ["RAICA_DATABASE_URL"] = f"sqlite:///{DB_PATH}"
os.environ["RAICA_SKILL_SHEET_STORAGE_DIR"] = str(Path(TEST_DIR.name) / "skill_sheets")
os.environ.pop("RAICA_API_KEY", None)

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import func, select  # noqa: E402

from app.config import Settings, validate_runtime_settings  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.main import app  # noqa: E402
from app.matching import run_matching  # noqa: E402
from app.models import Application, Candidate, Company, Job, Match, OutboxEvent  # noqa: E402


def test_health_and_dashboard():
    with TestClient(app) as client:
        assert client.get("/health").json()["ok"] is True
        dashboard = client.get("/api/v1/dashboard").json()
        assert dashboard["counts"]["candidates"] == 12
        assert dashboard["counts"]["open_jobs"] == 10
        assert dashboard["counts"]["open_actions"] == 11
        assert dashboard["counts"]["recommendations"] >= 1
        assert dashboard["counts"]["closed_won"] == 1
        assert dashboard["pipeline_scope"] == "RA 太郎の担当企業"
        assert dashboard["targets"]["recommendations"] == 20
        assert dashboard["my_actions"]
        assert dashboard["waiting_actions"]
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(Candidate)) == 12
        assert db.scalar(select(func.count()).select_from(Company)) == 10
        assert db.scalar(select(func.count()).select_from(Job)) == 13


def test_production_requires_api_key():
    settings = Settings(environment="production", api_key=None, _env_file=None)
    with pytest.raises(RuntimeError, match="RAICA_API_KEY"):
        validate_runtime_settings(settings)
    validate_runtime_settings(Settings(environment="production", api_key="test-key", _env_file=None))


def test_role_specific_revival_data():
    with TestClient(app) as client:
        ra = client.get("/api/v1/revival", params={"role": "ra", "owner": "RA 太郎"}).json()
        ca = client.get("/api/v1/revival", params={"role": "ca", "owner": "CA Huong"}).json()
        assert ra["mode"] == "company_job_revival"
        assert all(item["kind"] == "company" for item in ra["items"])
        assert {item["id"] for item in ra["items"]} >= {"co-e", "co-g", "co-h"}
        assert ca["mode"] == "candidate_job_revival"
        assert all(item["kind"] == "candidate" for item in ca["items"])
        assert {item["id"] for item in ca["items"]} == {"cand-thao", "cand-duc"}
        assert all(item["job_title"] for item in ca["items"])
        assert {item["job_id"] for item in ca["items"]} == {"job-d-accountant", "job-f-frontend"}
        assert all(item["priority_score"] >= 80 for item in ca["items"])
        historical_jobs = client.get("/api/v1/jobs", params={"q": "G社", "include_closed": True}).json()
        assert [job["id"] for job in historical_jobs] == ["job-g-dormant"]
        assert historical_jobs[0]["status"] == "closed"


def test_candidate_search_and_job_matching():
    with TestClient(app) as client:
        candidates = client.get("/api/v1/candidates", params={"q": "CNC"}).json()
        assert [candidate["id"] for candidate in candidates] == ["cand-huy"]
        python_candidates = client.get("/api/v1/candidates", params={"q": "Python"}).json()
        assert {candidate["id"] for candidate in python_candidates} == {"cand-quan", "cand-yen"}
        assert all(candidate["search_match"] == "登録スキル" for candidate in python_candidates)
        assert all(candidate["current_location"] == "Ha Noi" for candidate in python_candidates)
        assert all(candidate["consent_status"] == "confirmed" for candidate in python_candidates)
        assert all(candidate["preferred_contact_channel"] == "gmail" for candidate in python_candidates)
        result = client.post("/api/v1/jobs/job-c-cnc/matches/run", json={"actor": "pytest"})
        assert result.status_code == 201
        payload = result.json()
        assert payload["generated"] >= 1
        assert payload["matches"][0]["candidate_id"] == "cand-huy"
        assert payload["matches"][0]["score"] >= 70
        assert payload["matches"][0]["score"] < 100
        assert {"age", "remote", "specialization", "stability"}.issubset(payload["matches"][0]["scores"])
        reverse_matches = client.get("/api/v1/candidates/cand-huy/matches").json()
        assert reverse_matches[0]["job_id"] == "job-c-cnc"


def test_rerun_removes_only_stale_shortlists():
    with TestClient(app):
        with SessionLocal() as db:
            candidate = db.get(Candidate, "cand-huy")
            candidate.status = "dormant"
            db.commit()
            run_matching(db, "job-c-cnc", "pytest")
            stale = db.scalar(select(Match).where(Match.job_id == "job-c-cnc", Match.candidate_id == "cand-huy"))
            assert stale is None
            candidate.status = "active"
            db.commit()
            run_matching(db, "job-c-cnc", "pytest-restore")


def test_match_approval_persists_application():
    with TestClient(app) as client:
        match = client.get("/api/v1/jobs/job-a-phase2/matches").json()[0]
        response = client.patch(f"/api/v1/matches/{match['id']}", json={"status": "approved", "actor": "RA test"})
        assert response.status_code == 200
        assert response.json()["recommendation_status"] == "approved"
        assert response.json()["recommendation_draft"]["subject"].startswith("【人材推薦】")
    with SessionLocal() as db:
        application = db.scalar(select(Application).where(Application.candidate_id == match["candidate_id"], Application.job_id == "job-a-phase2"))
        assert application is not None
        assert application.stage == "recommended"


def test_contact_uses_outbox_and_human_approval():
    with TestClient(app) as client:
        response = client.post("/api/v1/contacts", json={
            "channel": "zalo",
            "candidate_id": "cand-hoa",
            "body": "Follow-up message",
            "human_approved_by": "CA test",
            "action_id": "q-ca-hoa",
        })
        assert response.status_code == 201
        assert response.json()["delivery_status"] == "pending"
    with SessionLocal() as db:
        event = db.get(OutboxEvent, response.json()["outbox_event_id"])
        assert event is not None
        assert event.provider == "zalo"
        assert event.attempts == 1


def test_integration_status_reports_missing_configuration():
    with TestClient(app) as client:
        integrations = client.get("/api/v1/integrations").json()
        assert len(integrations) == 4
        assert all(item["configured"] is False for item in integrations)
        result = client.post("/api/v1/integrations/gmail/test", json={"actor": "pytest"}).json()
        assert result["status"] == "not_configured"


def test_job_search_and_skill_sheet_upload():
    with TestClient(app) as client:
        jobs = client.get("/api/v1/jobs", params={"q": "Backend"}).json()
        assert {job["id"] for job in jobs} == {"job-f-backend", "job-f-frontend"}
        assert all(job["company_name"] == "F社" for job in jobs)
        response = client.post(
            "/api/v1/candidates/cand-quan/skill-sheet",
            files={"file": ("quan-skill.txt", b"Python backend engineer 5 years FastAPI", "text/plain")},
        )
        assert response.status_code == 200
        payload = response.json()
        assert "python" in payload["candidate"]["skills"]
        assert payload["candidate"]["skill_sheet_filename"] == "quan-skill.txt"
        assert payload["candidate"]["current_salary_million"] == 25
        assert payload["candidate"]["work_style_options"] == ["remote", "hybrid"]
        skill_sheet_results = client.get("/api/v1/candidates", params={"q": "FastAPI"}).json()
        assert [candidate["id"] for candidate in skill_sheet_results] == ["cand-quan"]
        assert skill_sheet_results[0]["search_match"] == "スキルシート"
        factory_jobs = client.get("/api/v1/jobs", params={"q": "工場"}).json()
        assert {job["company_name"] for job in factory_jobs} >= {"A社", "I社"}
        assert "G社" not in {job["company_name"] for job in factory_jobs}
        assert all(job["search_match"] == "企業採用情報" for job in factory_jobs)
        download = client.get("/api/v1/candidates/cand-quan/skill-sheet")
        assert download.status_code == 200
        assert download.content == b"Python backend engineer 5 years FastAPI"
        invalid_pdf = client.post(
            "/api/v1/candidates/cand-quan/skill-sheet",
            files={"file": ("fake.pdf", b"not-a-pdf", "application/pdf")},
        )
        assert invalid_pdf.status_code == 422


def test_porters_sync_upserts_api_records(monkeypatch):
    from app import integrations as integration_module
    from app.config import get_settings

    settings = get_settings()
    settings.porters_token = "test-token"
    settings.porters_candidates_url = "https://porters.test/candidates"
    settings.porters_jobs_url = "https://porters.test/jobs"

    class FakeResponse:
        def __init__(self, payload): self.payload = payload
        def raise_for_status(self): return None
        def json(self): return self.payload

    class FakeClient:
        def __init__(self, **_): pass
        def __enter__(self): return self
        def __exit__(self, *_): return None
        def get(self, url, **_):
            if "candidates" in url:
                return FakeResponse({"items": [{"id": "PT-C-NEW", "name": "API Candidate", "status": "active", "role_title": "QA", "skills": ["testing"]}]})
            return FakeResponse({"items": [{"id": "PT-J-NEW", "title": "QA Engineer", "company_name": "API Company", "industry": "it", "required_skills": ["testing"], "received_date": "2026-07-19"}]})

    monkeypatch.setattr(integration_module.httpx, "Client", FakeClient)
    with TestClient(app) as client:
        result = client.post("/api/v1/sync/porters", json={"actor": "pytest"}).json()
        assert result["status"] == "completed"
        assert result["records_written"] == 2
    with SessionLocal() as db:
        candidate = db.scalar(select(Candidate).where(Candidate.porters_id == "PT-C-NEW"))
        assert candidate is not None
        assert candidate.name == "API Candidate"
