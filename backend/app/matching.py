from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import AuditLog, Candidate, Job, Match


JLPT_LEVEL = {None: 0, "": 0, "N5": 1, "N4": 2, "N3": 3, "N2": 4, "N1": 5}
WEIGHTS = {
    "skill": 0.20,
    "experience": 0.12,
    "japanese": 0.10,
    "salary": 0.08,
    "commute": 0.07,
    "age": 0.08,
    "remote": 0.10,
    "specialization": 0.15,
    "stability": 0.10,
}


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
    age = 100
    if candidate.age and job.preferred_age_min and candidate.age < job.preferred_age_min:
        age = max(30, 100 - (job.preferred_age_min - candidate.age) * 12)
    if candidate.age and job.preferred_age_max and candidate.age > job.preferred_age_max:
        age = max(30, 100 - (candidate.age - job.preferred_age_max) * 12)
    remote = 100 if job.remote_mode == "flexible" or candidate.remote_preference == "flexible" or candidate.remote_preference == job.remote_mode else 45
    if not job.specialization:
        specialization = 100
    elif candidate.specialization == job.specialization:
        required_years = job.min_specialization_years or 1
        specialization = min(100, round(100 * candidate.specialization_years / required_years))
    else:
        specialization = 35 if job.specialization in actual else 15
    tenure = candidate.recent_tenure_years or 0
    stability = 100 if tenure >= 3 else 85 if tenure >= 2 else 65 if tenure >= 1 else 40
    axes = {
        "skill": skill,
        "experience": experience,
        "japanese": japanese,
        "salary": salary,
        "commute": commute,
        "age": age,
        "remote": remote,
        "specialization": specialization,
        "stability": stability,
    }
    score = min(96, round(sum(int(axes[key]) * weight for key, weight in WEIGHTS.items())))
    issues = [key for key, value in axes.items() if int(value) < 75]
    shared = sorted(required & actual)
    return {
        **axes,
        "score": score,
        "similarity_pct": min(98, round(score * 0.9 + len(shared) * 4)),
        "ng_check": "要件ずらし: " + ", ".join(issues) if issues else "主要条件にNGパターンなし",
        "evidence_quote": (
            f"一致スキル: {', '.join(shared) if shared else 'なし'} / "
            f"専門: {candidate.specialization or '未登録'} {candidate.specialization_years:g}年 / "
            f"直近勤続 {candidate.recent_tenure_years:g}年 / "
            f"年齢 {candidate.age or '未登録'} / 勤務志向 {candidate.remote_preference}"
        ),
    }


def run_matching(db: Session, job_id: str, actor: str = "system") -> list[Match]:
    job = db.get(Job, job_id)
    if not job or job.status == "closed":
        raise ValueError("job not found or closed")
    candidates = db.scalars(select(Candidate).where(Candidate.status != "dormant")).all()
    existing = {
        item.candidate_id: item
        for item in db.scalars(select(Match).where(Match.job_id == job.id)).all()
    }
    generated: list[Match] = []
    for candidate in candidates:
        values = score_candidate(candidate, job)
        if int(values["score"]) < 70:
            continue
        current = existing.get(candidate.id)
        if not current:
            current = Match(id=f"match-{job.id}-{candidate.id}", candidate_id=candidate.id, job_id=job.id, score=0, skill_score=0, experience_score=0, japanese_score=0, salary_score=0, commute_score=0, age_score=0, remote_score=0, specialization_score=0, stability_score=0, similarity_pct=0, ng_check="", evidence_quote="")
            db.add(current)
        current.score = int(values["score"])
        current.skill_score = int(values["skill"])
        current.experience_score = int(values["experience"])
        current.japanese_score = int(values["japanese"])
        current.salary_score = int(values["salary"])
        current.commute_score = int(values["commute"])
        current.age_score = int(values["age"])
        current.remote_score = int(values["remote"])
        current.specialization_score = int(values["specialization"])
        current.stability_score = int(values["stability"])
        current.similarity_pct = int(values["similarity_pct"])
        current.ng_check = str(values["ng_check"])
        current.evidence_quote = str(values["evidence_quote"])
        generated.append(current)
    generated_ids = {item.candidate_id for item in generated}
    removed = 0
    for candidate_id, current in existing.items():
        if candidate_id not in generated_ids and current.recommendation_status == "shortlisted":
            db.delete(current)
            removed += 1
    job.ai_candidate_count = len(generated)
    db.add(AuditLog(actor=actor, action="matching.run", entity_type="job", entity_id=job.id, details={"generated": len(generated), "removed_stale": removed, "weights": WEIGHTS, "date": date.today().isoformat()}))
    db.commit()
    for item in generated:
        db.refresh(item)
    return sorted(generated, key=lambda item: item.score, reverse=True)
