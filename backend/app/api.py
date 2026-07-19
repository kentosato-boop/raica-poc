from __future__ import annotations

import uuid
import hashlib
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import base64

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import Text, and_, cast, func, or_, select
from sqlalchemy.orm import Session, selectinload

from .config import Settings, get_settings
from .database import get_db
from .integrations import dispatch_event, enqueue_event, integration_snapshot, sync_porters, test_integration
from .matching import WEIGHTS, run_matching, score_candidate
from .models import ActionItem, Application, AuditLog, Candidate, Company, ContactLog, IntegrationConnection, Job, Match, OutboxEvent, SyncRun
from .schemas import ActionUpdate, ActorRequest, ContactCreate, MatchDecision, OutboxRetry
from .skill_sheets import analyze_skill_sheet, extract_text


router = APIRouter(prefix="/api/v1")


def candidate_dict(candidate: Candidate) -> dict:
    return {
        "id": candidate.id,
        "porters_id": candidate.porters_id,
        "name": candidate.name,
        "status": candidate.status,
        "ca_owner": candidate.ca_owner,
        "email": candidate.email,
        "role_title": candidate.role_title,
        "age": candidate.age,
        "gender": candidate.gender,
        "years_experience": candidate.years_experience,
        "jlpt": candidate.jlpt,
        "current_salary_million": candidate.current_salary_million,
        "desired_salary_million": candidate.desired_salary_million,
        "commute_minutes": candidate.commute_minutes,
        "work_style": candidate.work_style,
        "work_style_options": candidate.work_style_options,
        "remote_preference": candidate.remote_preference,
        "specialization": candidate.specialization,
        "specialization_years": candidate.specialization_years,
        "recent_tenure_years": candidate.recent_tenure_years,
        "current_location": candidate.current_location,
        "desired_locations": candidate.desired_locations,
        "inflow_date": candidate.inflow_date,
        "inflow_days": (date.today() - candidate.inflow_date).days if candidate.inflow_date else None,
        "available_from": candidate.available_from,
        "work_authorization": candidate.work_authorization,
        "source_channel": candidate.source_channel,
        "preferred_contact_channel": candidate.preferred_contact_channel,
        "consent_status": candidate.consent_status,
        "skills": candidate.skills,
        "internal_parallel_count": candidate.internal_parallel_count,
        "external_parallel_count": candidate.external_parallel_count,
        "current_processes": candidate.current_processes,
        "skill_sheet_filename": candidate.skill_sheet_filename,
        "skill_sheet_uploaded_at": candidate.skill_sheet_uploaded_at,
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
        "preferred_age_min": job.preferred_age_min,
        "preferred_age_max": job.preferred_age_max,
        "remote_mode": job.remote_mode,
        "specialization": job.specialization,
        "min_specialization_years": job.min_specialization_years,
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
        "candidate_internal_parallel": item.candidate.internal_parallel_count,
        "candidate_external_parallel": item.candidate.external_parallel_count,
        "candidate_skill_sheet": item.candidate.skill_sheet_filename,
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
            "age": item.age_score,
            "remote": item.remote_score,
            "specialization": item.specialization_score,
            "stability": item.stability_score,
        },
        "similarity_pct": item.similarity_pct,
        "ng_check": item.ng_check,
        "evidence_quote": item.evidence_quote,
        "recommendation_status": item.recommendation_status,
        "updated_at": item.updated_at,
    }


def resolve_action_target(item: ActionItem, db: Session) -> tuple[str | None, str | None]:
    """source_ref を画面遷移可能なターゲット（候補者）へ解決する。

    - cand-*: 候補者を直接指す。
    - app-*: 応募（候補者×案件）。担当者が動かす対象は候補者本人なので候補者へ寄せる。
    - それ以外/None: 遷移先なし（一覧へフォールバック）。
    """
    ref = item.source_ref
    if not ref:
        return None, None
    if ref.startswith("cand-"):
        return ("candidate", ref) if db.get(Candidate, ref) else (None, None)
    if ref.startswith("app-"):
        application = db.get(Application, ref)
        if application:
            return "candidate", application.candidate_id
    return None, None


def action_dict(item: ActionItem, db: Session) -> dict:
    target_type, target_id = resolve_action_target(item, db)
    return {
        "id": item.id,
        "owner_role": item.owner_role,
        "ball_owner": item.ball_owner,
        "queue_type": item.queue_type,
        "target_label": item.target_label,
        "due_date": item.due_date,
        "severity": item.severity,
        "reason": item.reason,
        "status": item.status,
        "source_ref": item.source_ref,
        "target_type": target_type,
        "target_id": target_id,
    }


@router.get("/dashboard")
def dashboard(role: str = "ra", owner: str | None = None, db: Session = Depends(get_db)) -> dict:
    today = date.today()
    owner = owner or ("RA 太郎" if role == "ra" else "CA Huong")
    application_scope = select(Application)
    if role == "ra":
        application_scope = application_scope.join(Job, Application.job_id == Job.id).join(Company, Job.company_id == Company.id).where(Company.ra_owner == owner)
    else:
        application_scope = application_scope.join(Candidate, Application.candidate_id == Candidate.id).where(Candidate.ca_owner == owner)
    scoped_applications = db.scalars(application_scope).all()
    recommendation_count = sum(item.stage in {"recommended", "screening", "first_interview", "final_interview", "offer", "closed_won"} for item in scoped_applications)
    interview_count = sum(item.stage in {"first_interview", "final_interview"} for item in scoped_applications)
    closed_won_count = sum(item.stage == "closed_won" or (item.company_ok and item.candidate_ok) for item in scoped_applications)
    counts = {
        "candidates": db.scalar(select(func.count()).select_from(Candidate)) or 0,
        "active_candidates": db.scalar(select(func.count()).select_from(Candidate).where(Candidate.status == "active")) or 0,
        "dormant_candidates": db.scalar(select(func.count()).select_from(Candidate).where(Candidate.status == "dormant")) or 0,
        "open_jobs": db.scalar(select(func.count()).select_from(Job).where(Job.status != "closed")) or 0,
        "applications": db.scalar(select(func.count()).select_from(Application)) or 0,
        "open_actions": db.scalar(select(func.count()).select_from(ActionItem).where(ActionItem.status == "open", ActionItem.owner_role == role)) or 0,
        "pending_outbox": db.scalar(select(func.count()).select_from(OutboxEvent).where(OutboxEvent.status.in_(["pending", "failed"]))) or 0,
        "recommendations": recommendation_count,
        "interviews": interview_count,
        "closed_won": closed_won_count,
        "new_jobs": db.scalar(select(func.count()).select_from(Job).where(Job.received_date >= today - timedelta(days=7))) or 0,
    }
    stages: dict[str, int] = {}
    for item in scoped_applications:
        stages[item.stage] = stages.get(item.stage, 0) + 1
    actions = db.scalars(select(ActionItem).where(ActionItem.status == "open", ActionItem.owner_role == role).order_by(ActionItem.due_date, ActionItem.severity).limit(12)).all()
    my_actions = [item for item in actions if item.ball_owner == "mine"]
    waiting_actions = [item for item in actions if item.ball_owner == "theirs"]
    activity = db.scalars(select(AuditLog).order_by(AuditLog.id.desc()).limit(8)).all()
    company_names = []
    if role == "ra":
        company_names = list(db.scalars(select(Company.name).where(Company.ra_owner == owner).order_by(Company.name)).all())
    return {
        "counts": counts,
        "pipeline": stages,
        "actions": [action_dict(item, db) for item in actions],
        "my_actions": [action_dict(item, db) for item in my_actions[:4]],
        "waiting_actions": [action_dict(item, db) for item in waiting_actions[:4]],
        "targets": {"recommendations": 20, "interviews": 12, "closed_won": 3, "new_jobs": 6},
        "pipeline_scope": f"{owner}の担当企業" if role == "ra" else f"{owner}の担当候補者",
        "companies": company_names,
        "activity": [{"id": item.id, "actor": item.actor, "action": item.action, "entity_type": item.entity_type, "entity_id": item.entity_id, "details": item.details, "created_at": item.created_at} for item in activity],
    }


@router.get("/revival")
def revival(role: str = "ra", owner: str | None = None, db: Session = Depends(get_db)) -> dict:
    today = date.today()
    if role == "ra":
        owner = owner or "RA 太郎"
        companies = db.scalars(
            select(Company)
            .where(Company.ra_owner == owner, Company.revival_status.in_(["hot", "watching"]))
            .order_by(Company.revival_status, Company.last_contact_date)
        ).all()
        items = []
        for company in companies:
            dormant_days = (today - company.last_contact_date).days if company.last_contact_date else 0
            score = min(98, 62 + dormant_days // 18 + (12 if company.revival_status == "hot" else 0))
            items.append({
                "id": company.id, "kind": "company", "name": company.name, "owner": company.ra_owner,
                "primary_label": company.dormant_job_title or "過去求人", "secondary_label": company.industry,
                "last_contact_date": company.last_contact_date, "dormant_days": dormant_days,
                "priority_score": score, "status": company.revival_status,
                "signal": company.hiring_signal, "reason": company.dormancy_reason or company.notes,
                "recommendation": f"{company.dormant_job_title or '過去求人'}の採用再開状況を確認し、前回要件を更新する",
                "channel": "Gmail / 電話", "target_id": company.id,
            })
        return {"role": "ra", "mode": "company_job_revival", "items": items}

    owner = owner or "CA Huong"
    candidates = db.scalars(select(Candidate).where(Candidate.status == "dormant", Candidate.ca_owner == owner).order_by(Candidate.last_contact_date)).all()
    jobs = db.scalars(select(Job).where(Job.status != "closed").options(selectinload(Job.company))).all()
    items = []
    for candidate in candidates:
        scored_jobs = [(job, score_candidate(candidate, job)) for job in jobs]
        best_job, best_score = max(scored_jobs, key=lambda pair: int(pair[1]["score"])) if scored_jobs else (None, None)
        dormant_days = (today - candidate.last_contact_date).days if candidate.last_contact_date else 0
        items.append({
            "id": candidate.id, "kind": "candidate", "name": candidate.name, "owner": candidate.ca_owner,
            "primary_label": candidate.role_title, "secondary_label": candidate.specialization or candidate.role_title,
            "last_contact_date": candidate.last_contact_date, "dormant_days": dormant_days,
            "priority_score": int(best_score["score"]) if best_score else 0, "status": candidate.status,
            "signal": f"{best_job.company.name} / {best_job.title}" if best_job else "現在の案件を再検索",
            "reason": candidate.notes,
            "recommendation": str(best_score["evidence_quote"]) if best_score else "希望条件を更新して案件を再検索する",
            "channel": "Zalo / Gmail", "target_id": candidate.id,
            "job_id": best_job.id if best_job else None, "job_title": best_job.title if best_job else None,
            "company_name": best_job.company.name if best_job else None,
        })
    return {"role": "ca", "mode": "candidate_job_revival", "items": items}


@router.get("/candidates")
def candidates(
    q: str | None = Query(default=None, max_length=100),
    candidate_status: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[dict]:
    statement = select(Candidate)
    if candidate_status:
        statement = statement.where(Candidate.status == candidate_status)
    if q:
        terms = [term for term in q.strip().split() if term]
        statement = statement.where(and_(*[
            or_(
                Candidate.name.ilike(f"%{term}%"),
                Candidate.role_title.ilike(f"%{term}%"),
                Candidate.porters_id.ilike(f"%{term}%"),
                Candidate.specialization.ilike(f"%{term}%"),
                Candidate.current_location.ilike(f"%{term}%"),
                cast(Candidate.desired_locations, Text).ilike(f"%{term}%"),
                Candidate.notes.ilike(f"%{term}%"),
                Candidate.skill_sheet_text.ilike(f"%{term}%"),
                cast(Candidate.skills, Text).ilike(f"%{term}%"),
            )
            for term in terms
        ]))
    items = db.scalars(statement.order_by(Candidate.last_contact_date.desc(), Candidate.name).limit(limit).offset(offset)).all()
    payload = [candidate_dict(item) for item in items]
    if q:
        query = q.casefold()
        for result, item in zip(payload, items):
            if query in (item.skill_sheet_text or "").casefold():
                result["search_match"] = "スキルシート"
            elif query in " ".join(item.skills or []).casefold():
                result["search_match"] = "登録スキル"
            elif query in (item.specialization or "").casefold():
                result["search_match"] = "専門領域"
            else:
                result["search_match"] = "候補者情報"
    return payload


@router.get("/candidates/{candidate_id}")
def candidate_detail(candidate_id: str, db: Session = Depends(get_db)) -> dict:
    candidate = db.get(Candidate, candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="candidate not found")
    return candidate_dict(candidate)


@router.post("/candidates/{candidate_id}/skill-sheet")
async def upload_skill_sheet(
    candidate_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict:
    candidate = db.get(Candidate, candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="candidate not found")
    content = await file.read()
    if len(content) > 8 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="skill sheet must be 8MB or smaller")
    safe_filename = Path(file.filename or "skill-sheet").name
    try:
        text = extract_text(safe_filename, content)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    analysis = analyze_skill_sheet(text)
    candidate.skills = sorted(set(candidate.skills or []) | set(analysis["skills"]))
    if analysis["specialization"]:
        candidate.specialization = str(analysis["specialization"])
    candidate.specialization_years = max(candidate.specialization_years or 0, float(analysis["specialization_years"]))
    candidate.skill_sheet_filename = safe_filename
    suffix = Path(safe_filename).suffix.lower()
    storage_dir = Path(settings.skill_sheet_storage_dir).resolve()
    storage_dir.mkdir(parents=True, exist_ok=True)
    storage_path = storage_dir / f"{candidate.id}{suffix}"
    previous_path = Path(candidate.skill_sheet_path) if candidate.skill_sheet_path else None
    storage_path.write_bytes(content)
    if previous_path and previous_path != storage_path and previous_path.exists() and previous_path.parent == storage_dir:
        previous_path.unlink()
    candidate.skill_sheet_path = str(storage_path)
    candidate.skill_sheet_uploaded_at = datetime.now(timezone.utc)
    candidate.skill_sheet_text = text[:50000]
    db.add(AuditLog(actor=candidate.ca_owner, action="candidate.skill_sheet.upload", entity_type="candidate", entity_id=candidate.id, details={"filename": safe_filename, "sha256": hashlib.sha256(content).hexdigest(), "skills": analysis["skills"]}))
    db.commit()
    db.refresh(candidate)
    return {"candidate": candidate_dict(candidate), "analysis": analysis}


@router.get("/candidates/{candidate_id}/skill-sheet", response_class=FileResponse)
def download_skill_sheet(candidate_id: str, db: Session = Depends(get_db)) -> FileResponse:
    candidate = db.get(Candidate, candidate_id)
    if not candidate or not candidate.skill_sheet_path:
        raise HTTPException(status_code=404, detail="skill sheet not found")
    path = Path(candidate.skill_sheet_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="skill sheet file is missing")
    return FileResponse(path, filename=candidate.skill_sheet_filename or path.name)


@router.get("/candidates/{candidate_id}/matches")
def candidate_matches(candidate_id: str, db: Session = Depends(get_db)) -> list[dict]:
    if not db.get(Candidate, candidate_id):
        raise HTTPException(status_code=404, detail="candidate not found")
    statement = select(Match).where(Match.candidate_id == candidate_id).options(
        selectinload(Match.candidate), selectinload(Match.job).selectinload(Job.company)
    ).order_by(Match.score.desc())
    return [match_dict(item) for item in db.scalars(statement).all()]


@router.get("/jobs")
def jobs(
    q: str | None = Query(default=None, max_length=100),
    include_closed: bool = False,
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[dict]:
    statement = select(Job).options(selectinload(Job.company)).order_by(Job.received_date.desc())
    if not include_closed:
        statement = statement.where(Job.status != "closed")
    if q:
        terms = [term for term in q.strip().split() if term]
        statement = statement.join(Company).where(and_(*[
            or_(
                Job.title.ilike(f"%{term}%"),
                Job.location.ilike(f"%{term}%"),
                Job.industry.ilike(f"%{term}%"),
                Job.category.ilike(f"%{term}%"),
                Job.specialization.ilike(f"%{term}%"),
                cast(Job.required_skills, Text).ilike(f"%{term}%"),
                Company.name.ilike(f"%{term}%"),
                Company.industry.ilike(f"%{term}%"),
                Company.hiring_signal.ilike(f"%{term}%"),
                Company.dormant_job_title.ilike(f"%{term}%"),
                Company.dormancy_reason.ilike(f"%{term}%"),
                Company.notes.ilike(f"%{term}%"),
            )
            for term in terms
        ]))
    items = db.scalars(statement.limit(limit).offset(offset)).all()
    payload = [job_dict(item) for item in items]
    if q:
        query = q.casefold()
        for result, item in zip(payload, items):
            company_context = " ".join(filter(None, [item.company.name, item.company.industry, item.company.hiring_signal, item.company.dormant_job_title, item.company.dormancy_reason, item.company.notes])).casefold()
            if query in company_context:
                result["search_match"] = "企業採用情報"
            elif query in " ".join(item.required_skills or []).casefold():
                result["search_match"] = "案件スキル"
            else:
                result["search_match"] = "案件情報"
    return payload


def build_recommendation_draft(item: Match) -> dict:
    candidate = item.candidate
    job = item.job
    recipient = job.company.name
    subject = f"【人材推薦】{candidate.name}様 / {job.title}"
    body = (
        f"{recipient} 採用ご担当者様\n\n"
        f"{job.title}の候補者として、{candidate.name}様をご推薦いたします。\n\n"
        f"■ 推薦理由\n{item.evidence_quote}\n"
        f"・総合適合度: {item.score}点\n"
        f"・専門領域: {candidate.specialization or '未登録'}（{candidate.specialization_years:g}年）\n"
        f"・直近勤続: {candidate.recent_tenure_years:g}年\n"
        f"・社内並行: {candidate.internal_parallel_count}件 / 他社並行: {candidate.external_parallel_count}件\n\n"
        f"スキルシート: {candidate.skill_sheet_filename or '未登録'}\n"
        "ご確認のうえ、面談可否をご返信いただけますと幸いです。"
    )
    return {"match_id": item.id, "candidate_id": candidate.id, "company_id": job.company_id, "recipient_label": recipient, "recipient": None, "subject": subject, "body": body, "skill_sheet_filename": candidate.skill_sheet_filename}


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
    item = db.scalar(select(Match).where(Match.id == match_id).options(selectinload(Match.candidate), selectinload(Match.job).selectinload(Job.company)))
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
    return {"id": item.id, "recommendation_status": item.recommendation_status, "recommendation_draft": build_recommendation_draft(item) if payload.status in {"approved", "process"} else None}


@router.get("/matches/{match_id}/recommendation-draft")
def recommendation_draft(match_id: str, db: Session = Depends(get_db)) -> dict:
    item = db.scalar(select(Match).where(Match.id == match_id).options(selectinload(Match.candidate), selectinload(Match.job).selectinload(Job.company)))
    if not item:
        raise HTTPException(status_code=404, detail="match not found")
    return build_recommendation_draft(item)


@router.get("/actions")
def actions(role: str | None = None, item_status: str | None = Query(default=None, alias="status"), db: Session = Depends(get_db)) -> list[dict]:
    statement = select(ActionItem)
    if role:
        statement = statement.where(ActionItem.owner_role == role)
    if item_status:
        statement = statement.where(ActionItem.status == item_status)
    return [action_dict(item, db) for item in db.scalars(statement.order_by(ActionItem.status, ActionItem.due_date)).all()]


@router.patch("/actions/{action_id}")
def update_action(action_id: str, payload: ActionUpdate, db: Session = Depends(get_db)) -> dict:
    item = db.get(ActionItem, action_id)
    if not item:
        raise HTTPException(status_code=404, detail="action not found")
    item.status = payload.status
    db.add(AuditLog(actor=payload.actor, action="action.status", entity_type="action", entity_id=item.id, details={"status": payload.status}))
    db.commit()
    return action_dict(item, db)


@router.post("/contacts", status_code=status.HTTP_201_CREATED)
def create_contact(payload: ContactCreate, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)) -> dict:
    contact_id = f"contact-{uuid.uuid4().hex[:16]}"
    contact = ContactLog(id=contact_id, candidate_id=payload.candidate_id, company_id=payload.company_id, channel=payload.channel, subject=payload.subject, body=payload.body, human_approved_by=payload.human_approved_by)
    db.add(contact)
    provider = payload.channel if payload.channel in {"gmail", "zalo"} else "asana"
    event_payload = payload.model_dump()
    if payload.channel == "gmail" and payload.candidate_id:
        candidate = db.get(Candidate, payload.candidate_id)
        if candidate and candidate.skill_sheet_path and Path(candidate.skill_sheet_path).exists():
            event_payload["attachment_name"] = candidate.skill_sheet_filename
            event_payload["attachment_base64"] = base64.b64encode(Path(candidate.skill_sheet_path).read_bytes()).decode()
    event = enqueue_event(db, provider, "contact.send" if payload.channel != "phone" else "task.create", contact_id, event_payload)
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
