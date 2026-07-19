import os
import tempfile
from pathlib import Path

TEST_DIR = tempfile.TemporaryDirectory()
DB_PATH = Path(TEST_DIR.name) / "raica-test.sqlite3"
os.environ["RAICA_DATABASE_URL"] = f"sqlite:///{DB_PATH}"
os.environ.pop("RAICA_API_KEY", None)

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import select  # noqa: E402

from app.database import SessionLocal  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Application, Candidate, OutboxEvent  # noqa: E402


def test_health_and_dashboard():
    with TestClient(app) as client:
        assert client.get("/health").json()["ok"] is True
        dashboard = client.get("/api/v1/dashboard").json()
        assert dashboard["counts"]["candidates"] == 8
        assert dashboard["counts"]["open_jobs"] == 6
        assert dashboard["counts"]["open_actions"] == 5


def test_candidate_search_and_job_matching():
    with TestClient(app) as client:
        candidates = client.get("/api/v1/candidates", params={"q": "CNC"}).json()
        assert [candidate["id"] for candidate in candidates] == ["cand-huy"]
        result = client.post("/api/v1/jobs/job-c-cnc/matches/run", json={"actor": "pytest"})
        assert result.status_code == 201
        payload = result.json()
        assert payload["generated"] >= 1
        assert payload["matches"][0]["candidate_id"] == "cand-huy"
        assert payload["matches"][0]["score"] >= 70


def test_match_approval_persists_application():
    with TestClient(app) as client:
        match = client.get("/api/v1/jobs/job-a-phase2/matches").json()[0]
        response = client.patch(f"/api/v1/matches/{match['id']}", json={"status": "approved", "actor": "RA test"})
        assert response.status_code == 200
        assert response.json()["recommendation_status"] == "approved"
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
