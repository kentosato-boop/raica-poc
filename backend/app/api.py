from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from .config import Settings, get_settings
from .database import get_db
from .integrations import dispatch_event, enqueue_event, integration_snapshot, sync_porters, test_integration
from .matching import WEIGHTS, run_matching
from .models import ActionItem, Application, AuditLog, Candidate, Company, ContactLog, IntegrationConnection, Job, Match, OutboxEvent, SyncRun
from .schemas import ActionUpdate, ActorRequest, ContactCreate, MatchDecision, OutboxRetry


router = APIRouter(prefix="/api/v1")


def candidate_dict(candidate: Candidate) -> dict:
    return {
        "id": candidate.id,
        "porters_id": candidate.porters_id,
        "name": candidate.name,
        "status": candidate.status,
        "ca_owner": candidate.ca_owner,
        "role_title": candidate.role_title,
        "age": candidate.age,
        "gender": candidate.gender,
        "years_experience": candidate.years_experience,
        "jlpt": candidate.jlpt,
        "desired_salary_million": candidate.desired_salary_million,
        "commute_minutes": candidate.commute_minutes,
        "work_style": candidate.work_style,
        "skills": candidate.skills,
        "last_contact_date": candidate.last_contact_date,
        "avg_response_days": candidate.avg_response_days,
        "notes": candidate.notes,
    }


def job_dict(job: Job) -> dict:
    return {
        "id": job.id,
        "porters_id": job.porters_id,
        "company_id": job.company_id,
        "company_name": job.company.name if job.company else None,
        "title": job.title,
        "category": job.category,
        "industry": job.industry,
        "status": job.status,
        "location": job.location,
        "salary_min_million": job.salary_min_million,
        "salary_max_million": job.salary_max_million,
        "received_date": job.received_date,
        "min_experience_years": job.min_experience_years,
        "min_jlpt": job.min_jlpt,
        "max_commute_minutes": job.max_commute_minutes,
        "required_skills": job.required_skills,
        "ai_candidate_count": job.ai_candidate_count,
    }


def match_dict(item: Match) -> dict:
    return {
        "id": item.id,
        "candidate_id": item.candidate_id,
        "candidate_name": item.candidate.name,
        "candidate_role": item.candidate.role_title,
        "candidate_age": item.candidate.age,
        "candidate_jlpt": item.candidate.jlpt,
        "candidate_experience": item.candidate.years_experience,
        "candidate_owner": item.candidate.ca_owner,
        "candidate_notes": item.candidate.notes,
        "job_id": item.job_id,
        "job_title": item.job.title,
        "company_name": item.job.company.name,
        "score": item.score,
        "scores": {
            "skill": item.skill_score,
            "experience": item.experience_score,
            "japanese": item.japanese_score,
            "salary": item.salary_score,
            "commute": item.commute_score,
        },
        "similarity_pct": item.similarity_pct,
        "ng_check": item.ng_check,
        "evidence_quote": item.evidence_quote,
        "recommendation_status": item.recommendation_status,
        "updated_at": item.updated_at,
    }


def action_dict(item: ActionItem) -> dict:
    return {
        "id": item.id,
        "owner_role": item.owner_role,
        "queue_type": item.queue_type,
        "target_label": item.target_label,
        "due_date": item.due_date,
        "severity": item.severity,
        "reason": item.reason,
        "status": item.status,
        "source_ref": item.source_ref,
    }


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)) -> dict:
    counts = {
        "candidates": db.scalar(select(func.count()).select_from(Candidate)) or 0,
        "active_candidates": db.scalar(select(func.count()).select_from(Candidate).where(Candidate.status == "active")) or 0,
        "dormant_candidates": db.scalar(select(func.count()).select_from(Candidate).where(Candidate.status == "dormant")) or 0,
        "open_jobs": db.scalar(select(func.count()).select_from(Job).where(Job.status != "closed")) or 0,
        "applications": db.scalar(select(func.count()).select_from(Application)) or 0,
        "open_actions": db.scalar(select(func.count()).select_from(ActionItem).where(ActionItem.status == "open")) or 0,
        "pending_outbox": db.scalar(select(func.count()).select_from(OutboxEvent).where(OutboxEvent.status.in_(["pending", "failed"]))) or 0,
    }
    stages = dict(db.execute(select(Application.stage, func.count()).group_by(Application.stage)).all())
    actions = db.scalars(select(ActionItem).where(ActionItem.status == "open").order_by(ActionItem.due_date, ActionItem.severity).limit(6)).all()
    activity = db.scalars(select(AuditLog).order_by(AuditLog.id.desc()).limit(8)).all()
    return {
        "counts": counts,
        "pipeline": stages,
        "actions": [action_dict(item) for item in actions],
        "activity": [{"id": item.id, "actor": item.actor, "action": item.action, "entity_type": item.entity_type, "entity_id": item.entity_id, "details": item.details, "created_at": item.created_at} for item in activity],
    }


@router.get("/candidates")
def candidates(
    q: str | None = Query(default=None, max_length=100),
    candidate_status: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
) -> list[dict]:
    statement = select(Candidate)
    if candidate_status:
        statement = statement.where(Candidate.status == candidate_status)
    if q:
        token = f"%{q}%"
        statement = statement.where(or_(Candidate.name.ilike(token), Candidate.role_title.ilike(token), Candidate.porters_id.ilike(token)))
    return [candidate_dict(item) for item in db.scalars(statement.order_by(Candidate.last_contact_date.desc(), Candidate.name)).all()]


@router.get("/jobs")
def jobs(db: Session = Depends(get_db)) -> list[dict]:
    statement = select(Job).options(selectinload(Job.company)).order_by(Job.received_date.desc())
    return [job_dict(item) for item in db.scalars(statement).all()]


@router.get("/jobs/{job_id}/matches")
def matches(job_id: str, db: Session = Depends(get_db)) -> list[dict]:
    statement = select(Match).where(Match.job_id == job_id).options(selectinload(Match.candidate), selectinload(Match.job).selectinload(Job.company)).order_by(Match.score.desc())
    return [match_dict(item) for item in db.scalars(statement).all()]


@router.post("/jobs/{job_id}/matches/run", status_code=status.HTTP_201_CREATED)
def rerun_matches(job_id: str, payload: ActorRequest, db: Session = Depends(get_db)) -> dict:
    try:
        generated = run_matching(db, job_id, payload.actor)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    statement = select(Match).where(Match.id.in_([item.id for item in generated])).options(selectinload(Match.candidate), selectinload(Match.job).selectinload(Job.company)).order_by(Match.score.desc())
    hydrated = db.scalars(statement).all()
    return {"generated": len(hydrated), "weights": WEIGHTS, "matches": [match_dict(item) for item in hydrated]}


@router.patch("/matches/{match_id}")
def decide_match(match_id: str, payload: MatchDecision, db: Session = Depends(get_db)) -> dict:
    item = db.get(Match, match_id)
    if not item:
        raise HTTPException(status_code=404, detail="match not found")
    item.recommendation_status = payload.status
    if payload.status in {"approved", "process"}:
        application = db.scalar(select(Application).where(Application.candidate_id == item.candidate_id, Application.job_id == item.job_id))
        if not application:
            application = Application(id=f"app-{uuid.uuid4().hex[:16]}", candidate_id=item.candidate_id, job_id=item.job_id, stage="recommended", recommended_at=date.today(), last_event_at=date.today())
            db.add(application)
        else:
            application.stage = "recommended"
            application.last_event_at = date.today()
    db.add(AuditLog(actor=payload.actor, action="match.decision", entity_type="match", entity_id=item.id, details={"status": payload.status}))
    db.commit()
    return {"id": item.id, "recommendation_status": item.recommendation_status}


@router.get("/actions")
def actions(role: str | None = None, item_status: str | None = Query(default=None, alias="status"), db: Session = Depends(get_db)) -> list[dict]:
    statement = select(ActionItem)
    if role:
        statement = statement.where(ActionItem.owner_role == role)
    if item_status:
        statement = statement.where(ActionItem.status == item_status)
    return [action_dict(item) for item in db.scalars(statement.order_by(ActionItem.status, ActionItem.due_date)).all()]


@router.patch("/actions/{action_id}")
def update_action(action_id: str, payload: ActionUpdate, db: Session = Depends(get_db)) -> dict:
    item = db.get(ActionItem, action_id)
    if not item:
        raise HTTPException(status_code=404, detail="action not found")
    item.status = payload.status
    db.add(AuditLog(actor=payload.actor, action="action.status", entity_type="action", entity_id=item.id, details={"status": payload.status}))
    db.commit()
    return action_dict(item)


@router.post("/contacts", status_code=status.HTTP_201_CREATED)
def create_contact(payload: ContactCreate, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)) -> dict:
    contact_id = f"contact-{uuid.uuid4().hex[:16]}"
    contact = ContactLog(id=contact_id, candidate_id=payload.candidate_id, company_id=payload.company_id, channel=payload.channel, subject=payload.subject, body=payload.body, human_approved_by=payload.human_approved_by)
    db.add(contact)
    provider = payload.channel if payload.channel in {"gmail", "zalo"} else "asana"
    event = enqueue_event(db, provider, "contact.send" if payload.channel != "phone" else "task.create", contact_id, payload.model_dump())
    if payload.action_id:
        action = db.get(ActionItem, payload.action_id)
        if action:
            action.status = "done"
    db.add(AuditLog(actor=payload.human_approved_by, action="contact.approved", entity_type="contact", entity_id=contact_id, details={"channel": payload.channel, "event_id": event.id}))
    db.commit()
    dispatch_event(db, settings, event)
    if event.status == "delivered":
        contact.sent_at = datetime.now(timezone.utc)
        db.commit()
    return {"id": contact_id, "outbox_event_id": event.id, "delivery_status": event.status, "delivery_error": event.last_error}


@router.get("/integrations")
def integrations(db: Session = Depends(get_db), settings: Settings = Depends(get_settings)) -> list[dict]:
    return integration_snapshot(db, settings)


@router.post("/integrations/{provider}/test")
def integration_test(provider: str, payload: ActorRequest, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)) -> dict:
    try:
        return test_integration(db, settings, provider, payload.actor)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/sync/porters", status_code=status.HTTP_202_ACCEPTED)
def porters_sync(payload: ActorRequest, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)) -> dict:
    run = sync_porters(db, settings, payload.actor)
    return {"id": run.id, "status": run.status, "records_read": run.records_read, "records_written": run.records_written, "error_message": run.error_message}


@router.get("/sync-runs")
def sync_runs(db: Session = Depends(get_db)) -> list[dict]:
    items = db.scalars(select(SyncRun).order_by(SyncRun.started_at.desc()).limit(30)).all()
    return [{"id": item.id, "provider": item.provider, "resource": item.resource, "status": item.status, "started_at": item.started_at, "finished_at": item.finished_at, "records_read": item.records_read, "records_written": item.records_written, "error_message": item.error_message} for item in items]


@router.get("/outbox")
def outbox(db: Session = Depends(get_db)) -> list[dict]:
    items = db.scalars(select(OutboxEvent).order_by(OutboxEvent.available_at.desc()).limit(50)).all()
    return [{"id": item.id, "provider": item.provider, "event_type": item.event_type, "aggregate_id": item.aggregate_id, "status": item.status, "attempts": item.attempts, "last_error": item.last_error, "available_at": item.available_at, "processed_at": item.processed_at} for item in items]


@router.post("/outbox/{event_id}/retry")
def retry_outbox(event_id: str, payload: OutboxRetry, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)) -> dict:
    item = db.get(OutboxEvent, event_id)
    if not item:
        raise HTTPException(status_code=404, detail="outbox event not found")
    dispatch_event(db, settings, item)
    db.add(AuditLog(actor=payload.actor, action="outbox.retry", entity_type="outbox", entity_id=item.id, details={"status": item.status}))
    db.commit()
    return {"id": item.id, "status": item.status, "attempts": item.attempts, "last_error": item.last_error}


@router.get("/audit")
def audit(limit: int = Query(default=50, ge=1, le=200), db: Session = Depends(get_db)) -> list[dict]:
    items = db.scalars(select(AuditLog).order_by(AuditLog.id.desc()).limit(limit)).all()
    return [{"id": item.id, "actor": item.actor, "action": item.action, "entity_type": item.entity_type, "entity_id": item.entity_id, "details": item.details, "created_at": item.created_at} for item in items]
