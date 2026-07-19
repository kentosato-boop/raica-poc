from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import AuditLog, Candidate, Job, Match


JLPT_LEVEL = {None: 0, "": 0, "N5": 1, "N4": 2, "N3": 3, "N2": 4, "N1": 5}
WEIGHTS = {"skill": 0.35, "experience": 0.20, "japanese": 0.15, "salary": 0.15, "commute": 0.15}


def score_candidate(candidate: Candidate, job: Job) -> dict[str, int | str]:
    required = set(job.required_skills or [])
    actual = set(candidate.skills or [])
    skill = 100 if not required else round(100 * len(required & actual) / len(required))
    experience = 100 if not job.min_experience_years else min(100, round(100 * candidate.years_experience / job.min_experience_years))
    required_jlpt = JLPT_LEVEL.get(job.min_jlpt, 0)
    actual_jlpt = JLPT_LEVEL.get(candidate.jlpt, 0)
    japanese = 100 if required_jlpt == 0 else min(100, round(100 * actual_jlpt / required_jlpt))
    desired = candidate.desired_salary_million or 0
    maximum = job.salary_max_million or 0
    salary = 100 if not desired or not maximum or desired <= maximum else max(0, round(100 - ((desired - maximum) / maximum * 200)))
    commute_minutes = candidate.commute_minutes or 0
    commute = 100 if job.max_commute_minutes in (None, 0) or commute_minutes <= job.max_commute_minutes else max(0, 100 - (commute_minutes - job.max_commute_minutes) * 4)
    axes = {"skill": skill, "experience": experience, "japanese": japanese, "salary": salary, "commute": commute}
    score = round(sum(int(axes[key]) * weight for key, weight in WEIGHTS.items()))
    issues = [key for key, value in axes.items() if int(value) < 75]
    shared = sorted(required & actual)
    return {
        **axes,
        "score": score,
        "similarity_pct": min(98, round(score * 0.9 + len(shared) * 4)),
        "ng_check": "要件ずらし: " + ", ".join(issues) if issues else "主要条件にNGパターンなし",
        "evidence_quote": f"一致スキル: {', '.join(shared) if shared else 'なし'} / 経験 {candidate.years_experience:g}年 / {candidate.jlpt or 'JLPT未登録'}",
    }


def run_matching(db: Session, job_id: str, actor: str = "system") -> list[Match]:
    job = db.get(Job, job_id)
    if not job or job.status == "closed":
        raise ValueError("job not found or closed")
    candidates = db.scalars(select(Candidate).where(Candidate.status != "dormant")).all()
    generated: list[Match] = []
    for candidate in candidates:
        values = score_candidate(candidate, job)
        if int(values["score"]) < 70:
            continue
        current = db.scalar(select(Match).where(Match.candidate_id == candidate.id, Match.job_id == job.id))
        if not current:
            current = Match(id=f"match-{job.id}-{candidate.id}", candidate_id=candidate.id, job_id=job.id, score=0, skill_score=0, experience_score=0, japanese_score=0, salary_score=0, commute_score=0, similarity_pct=0, ng_check="", evidence_quote="")
            db.add(current)
        current.score = int(values["score"])
        current.skill_score = int(values["skill"])
        current.experience_score = int(values["experience"])
        current.japanese_score = int(values["japanese"])
        current.salary_score = int(values["salary"])
        current.commute_score = int(values["commute"])
        current.similarity_pct = int(values["similarity_pct"])
        current.ng_check = str(values["ng_check"])
        current.evidence_quote = str(values["evidence_quote"])
        generated.append(current)
    job.ai_candidate_count = len(generated)
    db.add(AuditLog(actor=actor, action="matching.run", entity_type="job", entity_id=job.id, details={"generated": len(generated), "weights": WEIGHTS, "date": date.today().isoformat()}))
    db.commit()
    for item in generated:
        db.refresh(item)
    return sorted(generated, key=lambda item: item.score, reverse=True)
