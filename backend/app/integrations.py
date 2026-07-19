from __future__ import annotations

import uuid
import base64
import mimetypes
from datetime import date, datetime, timezone
from email.message import EmailMessage
from typing import Any

import httpx
from sqlalchemy.orm import Session

from .config import Settings
from .models import AuditLog, Candidate, Company, IntegrationConnection, Job, OutboxEvent, SyncRun


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_date(value: Any) -> date | None:
    if not value:
        return None
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def as_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, str):
        return [item.strip() for item in value.split("|") if item.strip()]
    return []


def upsert_candidates(db: Session, records: list[dict[str, Any]]) -> int:
    written = 0
    for record in records:
        porters_id = str(record.get("porters_id") or record.get("id") or "").strip()
        if not porters_id or not record.get("name"):
            continue
        candidate = db.query(Candidate).filter(Candidate.porters_id == porters_id).one_or_none()
        if not candidate:
            candidate = Candidate(id=f"porters-candidate-{porters_id}", porters_id=porters_id, name=str(record["name"]), ca_owner="unassigned", role_title="未分類")
            db.add(candidate)
        candidate.name = str(record["name"])
        candidate.status = str(record.get("status") or "active")
        candidate.ca_owner = str(record.get("ca_owner") or record.get("owner") or "unassigned")
        candidate.email = record.get("email")
        candidate.role_title = str(record.get("role_title") or record.get("title") or "未分類")
        candidate.age = int(record["age"]) if record.get("age") not in (None, "") else None
        candidate.gender = record.get("gender")
        candidate.years_experience = float(record.get("years_experience") or 0)
        candidate.jlpt = record.get("jlpt")
        candidate.desired_salary_million = float(record["desired_salary_million"]) if record.get("desired_salary_million") not in (None, "") else None
        candidate.commute_minutes = int(record["commute_minutes"]) if record.get("commute_minutes") not in (None, "") else None
        candidate.work_style = str(record.get("work_style") or "onsite")
        candidate.remote_preference = str(record.get("remote_preference") or record.get("work_style") or "flexible")
        candidate.specialization = record.get("specialization")
        candidate.specialization_years = float(record.get("specialization_years") or 0)
        candidate.recent_tenure_years = float(record.get("recent_tenure_years") or 0)
        candidate.skills = as_list(record.get("skills"))
        candidate.internal_parallel_count = int(record.get("internal_parallel_count") or 0)
        candidate.external_parallel_count = int(record.get("external_parallel_count") or 0)
        candidate.current_processes = record.get("current_processes") if isinstance(record.get("current_processes"), list) else []
        candidate.last_contact_date = parse_date(record.get("last_contact_date"))
        candidate.avg_response_days = float(record["avg_response_days"]) if record.get("avg_response_days") not in (None, "") else None
        candidate.notes = record.get("notes")
        written += 1
    return written


def upsert_jobs(db: Session, records: list[dict[str, Any]]) -> int:
    written = 0
    for record in records:
        porters_id = str(record.get("porters_id") or record.get("id") or "").strip()
        company_name = str(record.get("company_name") or "未登録企業").strip()
        if not porters_id or not record.get("title"):
            continue
        company_id = str(record.get("company_id") or f"porters-company-{company_name.lower().replace(' ', '-')}")
        company = db.get(Company, company_id)
        if not company:
            company = Company(id=company_id, name=company_name, industry=str(record.get("industry") or "other"), ra_owner=str(record.get("ra_owner") or "RA 太郎"))
            db.add(company)
        job = db.query(Job).filter(Job.porters_id == porters_id).one_or_none()
        if not job:
            job = Job(id=f"porters-job-{porters_id}", porters_id=porters_id, company_id=company_id, title=str(record["title"]), category="other", industry="other", received_date=parse_date(record.get("received_date")) or date.today())
            db.add(job)
        job.company_id = company_id
        job.title = str(record["title"])
        job.category = str(record.get("category") or "other")
        job.industry = str(record.get("industry") or company.industry)
        job.status = str(record.get("status") or "open")
        job.location = record.get("location")
        job.salary_min_million = float(record["salary_min_million"]) if record.get("salary_min_million") not in (None, "") else None
        job.salary_max_million = float(record["salary_max_million"]) if record.get("salary_max_million") not in (None, "") else None
        job.received_date = parse_date(record.get("received_date")) or date.today()
        job.min_experience_years = float(record.get("min_experience_years") or 0)
        job.preferred_age_min = int(record["preferred_age_min"]) if record.get("preferred_age_min") not in (None, "") else None
        job.preferred_age_max = int(record["preferred_age_max"]) if record.get("preferred_age_max") not in (None, "") else None
        job.remote_mode = str(record.get("remote_mode") or "onsite")
        job.specialization = record.get("specialization")
        job.min_specialization_years = float(record.get("min_specialization_years") or 0)
        job.min_jlpt = record.get("min_jlpt")
        job.max_commute_minutes = int(record["max_commute_minutes"]) if record.get("max_commute_minutes") not in (None, "") else None
        job.required_skills = as_list(record.get("required_skills"))
        written += 1
    return written


def integration_snapshot(db: Session, settings: Settings) -> list[dict[str, Any]]:
    result = []
    for provider in ("porters", "gmail", "zalo", "asana"):
        connection = db.get(IntegrationConnection, provider)
        configured = bool(settings.porters_token and settings.porters_candidates_url) if provider == "porters" else settings.gmail_configured if provider == "gmail" else bool(settings.provider_url(provider))
        result.append({
            "provider": provider,
            "configured": configured,
            "status": connection.status if connection else "not_configured",
            "last_checked_at": connection.last_checked_at if connection else None,
            "last_success_at": connection.last_success_at if connection else None,
            "last_error": connection.last_error if connection else None,
            "capabilities": connection.capabilities if connection else [],
        })
    return result


def test_integration(db: Session, settings: Settings, provider: str, actor: str) -> dict[str, Any]:
    connection = db.get(IntegrationConnection, provider)
    if not connection:
        raise ValueError("unsupported provider")
    connection.last_checked_at = utc_now()
    try:
        if provider == "porters":
            if not settings.porters_token or not settings.porters_candidates_url:
                raise ValueError("PORTERS_TOKEN and PORTERS_CANDIDATES_URL are required")
            url = settings.porters_candidates_url
            headers = {"Authorization": f"Bearer {settings.porters_token}"}
        elif provider == "gmail" and settings.gmail_access_token:
            url = "https://gmail.googleapis.com/gmail/v1/users/me/profile"
            headers = {"Authorization": f"Bearer {settings.gmail_access_token}"}
        else:
            url = settings.provider_url(provider)
            if not url:
                raise ValueError(f"{provider.upper()}_WEBHOOK_URL is required")
            headers = {}
        with httpx.Client(timeout=settings.integration_timeout_seconds) as client:
            if provider in {"porters", "gmail"} and headers:
                response = client.get(url, headers=headers, params={"limit": 1})
            else:
                response = client.post(url, json={"event": "raica.connection.test", "provider": provider})
            response.raise_for_status()
        connection.status = "connected"
        connection.last_success_at = utc_now()
        connection.last_error = None
    except (ValueError, httpx.HTTPError) as exc:
        connection.status = "error" if "required" not in str(exc) else "not_configured"
        connection.last_error = str(exc)
    db.add(AuditLog(actor=actor, action="integration.test", entity_type="integration", entity_id=provider, details={"status": connection.status}))
    db.commit()
    return {"provider": provider, "status": connection.status, "error": connection.last_error}


def enqueue_event(db: Session, provider: str, event_type: str, aggregate_id: str, payload: dict[str, Any]) -> OutboxEvent:
    event = OutboxEvent(id=f"evt-{uuid.uuid4().hex[:16]}", provider=provider, event_type=event_type, aggregate_id=aggregate_id, payload=payload)
    db.add(event)
    db.flush()
    return event


def dispatch_event(db: Session, settings: Settings, event: OutboxEvent) -> OutboxEvent:
    url = settings.provider_url(event.provider)
    event.attempts += 1
    if event.provider == "gmail" and settings.gmail_access_token and settings.gmail_sender:
        payload = event.payload
        recipient = payload.get("recipient")
        if not recipient:
            event.status = "pending"
            event.last_error = "Gmail recipient is required"
            db.commit()
            return event
        message = EmailMessage()
        message["To"] = recipient
        message["From"] = settings.gmail_sender
        message["Subject"] = payload.get("subject") or "RAiCA recommendation"
        message.set_content(payload.get("body") or "")
        if payload.get("attachment_base64") and payload.get("attachment_name"):
            attachment = base64.b64decode(payload["attachment_base64"])
            mime_type, _ = mimetypes.guess_type(payload["attachment_name"])
            maintype, subtype = (mime_type or "application/octet-stream").split("/", 1)
            message.add_attachment(attachment, maintype=maintype, subtype=subtype, filename=payload["attachment_name"])
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode().rstrip("=")
        try:
            with httpx.Client(timeout=settings.integration_timeout_seconds) as client:
                response = client.post(
                    "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
                    headers={"Authorization": f"Bearer {settings.gmail_access_token}"},
                    json={"raw": raw},
                )
                response.raise_for_status()
            event.status = "delivered"
            event.processed_at = utc_now()
            event.last_error = None
        except httpx.HTTPError as exc:
            event.status = "failed"
            event.last_error = str(exc)
        db.commit()
        return event
    if not url:
        event.status = "pending"
        event.last_error = f"{event.provider.upper()}_WEBHOOK_URL is not configured"
        db.commit()
        return event
    try:
        with httpx.Client(timeout=settings.integration_timeout_seconds) as client:
            response = client.post(url, json={"event": event.event_type, "id": event.id, "data": event.payload})
            response.raise_for_status()
        event.status = "delivered"
        event.processed_at = utc_now()
        event.last_error = None
    except httpx.HTTPError as exc:
        event.status = "failed"
        event.last_error = str(exc)
    db.commit()
    return event


def sync_porters(db: Session, settings: Settings, actor: str) -> SyncRun:
    run = SyncRun(id=f"sync-{uuid.uuid4().hex[:16]}", provider="porters", resource="candidates_jobs", status="running")
    db.add(run)
    db.commit()
    if not settings.porters_token or not settings.porters_candidates_url:
        run.status = "not_configured"
        run.error_message = "PORTERS_TOKEN and PORTERS_CANDIDATES_URL are required"
        run.finished_at = utc_now()
        db.add(AuditLog(actor=actor, action="sync.skipped", entity_type="integration", entity_id="porters", details={"reason": run.error_message}))
        db.commit()
        return run
    try:
        headers = {"Authorization": f"Bearer {settings.porters_token}"}
        with httpx.Client(timeout=settings.integration_timeout_seconds) as client:
            candidate_response = client.get(settings.porters_candidates_url, headers=headers)
            candidate_response.raise_for_status()
            candidate_payload = candidate_response.json()
            job_payload: Any = []
            if settings.porters_jobs_url:
                job_response = client.get(settings.porters_jobs_url, headers=headers)
                job_response.raise_for_status()
                job_payload = job_response.json()
        candidates = candidate_payload.get("items", candidate_payload) if isinstance(candidate_payload, dict) else candidate_payload
        jobs = job_payload.get("items", job_payload) if isinstance(job_payload, dict) else job_payload
        run.records_read = len(candidates) + len(jobs)
        run.records_written = upsert_candidates(db, candidates) + upsert_jobs(db, jobs)
        run.status = "completed"
    except (httpx.HTTPError, ValueError, TypeError) as exc:
        run.status = "failed"
        run.error_message = str(exc)
    run.finished_at = utc_now()
    db.add(AuditLog(actor=actor, action="sync.finished", entity_type="integration", entity_id="porters", details={"status": run.status, "records_read": run.records_read}))
    db.commit()
    return run
