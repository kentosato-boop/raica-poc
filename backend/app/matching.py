from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import AuditLog, Candidate, Job, Match


JLPT_LEVEL = {None: 0, "": 0, "N5": 1, "N4": 2, "N3": 3, "N2": 4, "N1": 5}
# RA/CA 実務では「コア適合（スキル + 専門）」が推薦可否のゲートであり、
# 年収・通勤・年齢などの soft 要因はタイブレーク。重みはこの階層を反映する。
WEIGHTS = {
    "skill": 0.24,
    "specialization": 0.22,
    "experience": 0.12,
    "japanese": 0.10,
    "stability": 0.08,
    "remote": 0.08,
    "age": 0.06,
    "salary": 0.06,
    "commute": 0.04,
}
# コア適合の内訳（合計 1.0）。skill は具体的な一致スキル、specialization は専門領域の深さ。
CORE_SKILL_WEIGHT = 0.55
CORE_SPECIALIZATION_WEIGHT = 0.45
# AI は 100% の確度を主張しない。上限は 98。
SCORE_CAP = 98
# 天井 = CEILING_BASE + CEILING_SLOPE * core_fit。
# soft 要因だけが満点でも、コア適合が低ければ推薦帯（70+）には届かない。
CEILING_BASE = 55
CEILING_SLOPE = 0.43
# AI 分析ステージで「上位◯人」として強調する人数。
AI_SHORTLIST_SIZE = 3


def evaluate_rules(candidate: Candidate, job: Job) -> dict[str, list[str] | bool]:
    """一次選抜（ルールベース）。案件要件から自動導出したハードルールで足切りする。

    ここを通らない候補者は「会う価値なし」としてAI分析ステージへ進めない。
    手動の閾値設定は不要で、案件が持つ要件そのものが基準になる。
    """
    required = set(job.required_skills or [])
    actual = set(candidate.skills or [])
    failures: list[str] = []
    # 専門・スキル不一致: 専門領域が違い、専門をスキルとしても持たず、必須スキルも一つも重ならない。
    if job.specialization and candidate.specialization != job.specialization and job.specialization not in actual and not (required & actual):
        failures.append("専門・必須スキルの一致なし")
    # 必須スキルが定義されているのに1つも一致しない。
    elif required and not (required & actual):
        failures.append("必須スキルの一致なし")
    # 経験年数が要件の半分未満（大幅不足）。
    if job.min_experience_years and candidate.years_experience < job.min_experience_years * 0.5:
        failures.append("経験年数が要件の半分未満")
    # 日本語が要件を2段階以上下回る（例: N2要件にN4）。
    required_jlpt = JLPT_LEVEL.get(job.min_jlpt, 0)
    actual_jlpt = JLPT_LEVEL.get(candidate.jlpt, 0)
    if required_jlpt and actual_jlpt <= required_jlpt - 2:
        failures.append("日本語が要件を大きく下回る")
    return {"passed": not failures, "failures": failures}


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
    core_fit = round(CORE_SKILL_WEIGHT * skill + CORE_SPECIALIZATION_WEIGHT * specialization)
    weighted = sum(int(axes[key]) * weight for key, weight in WEIGHTS.items())
    ceiling = CEILING_BASE + CEILING_SLOPE * core_fit
    score = min(round(weighted), round(ceiling), SCORE_CAP)
    issues = [key for key, value in axes.items() if int(value) < 75]
    shared = sorted(required & actual)
    return {
        **axes,
        "score": score,
        "core_fit": core_fit,
        "ng_check": "要件ずらし: " + ", ".join(issues) if issues else "主要条件にNGパターンなし",
        "evidence_quote": (
            f"コア適合 {core_fit}% / "
            f"一致スキル: {', '.join(shared) if shared else 'なし'} / "
            f"専門: {candidate.specialization or '未登録'} {candidate.specialization_years:g}年 / "
            f"直近勤続 {candidate.recent_tenure_years:g}年 / "
            f"年齢 {candidate.age or '未登録'} / 勤務志向 {candidate.remote_preference}"
        ),
    }


def run_matching(db: Session, job_id: str, actor: str = "system") -> list[Match]:
    """2段構成のマッチング。

    Stage 1（ルールベース一次選抜）: evaluate_rules で案件要件のハードルールに
      掛け、明確に不適合な候補者を除外する（＝会う価値がある母集団に絞る）。
    Stage 2（AI分析ステージ）: 通過者を score_candidate でスコアリングして順位付け。
      上位 AI_SHORTLIST_SIZE 名を推薦フォーカスとして扱う。
    """
    job = db.get(Job, job_id)
    if not job or job.status == "closed":
        raise ValueError("job not found or closed")
    candidates = db.scalars(select(Candidate).where(Candidate.status != "dormant")).all()
    existing = {
        item.candidate_id: item
        for item in db.scalars(select(Match).where(Match.job_id == job.id)).all()
    }
    # --- Stage 1: rule-based screening ---
    eligible = [candidate for candidate in candidates if evaluate_rules(candidate, job)["passed"]]
    screened_out = len(candidates) - len(eligible)
    # --- Stage 2: AI scoring on survivors ---
    generated: list[Match] = []
    for candidate in eligible:
        values = score_candidate(candidate, job)
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
        current.similarity_pct = int(values["score"])  # score に一本化（旧 similarity 指標は廃止）
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
    db.add(AuditLog(actor=actor, action="matching.run", entity_type="job", entity_id=job.id, details={"eligible": len(generated), "screened_out": screened_out, "shortlist": AI_SHORTLIST_SIZE, "weights": WEIGHTS, "date": date.today().isoformat()}))
    db.commit()
    for item in generated:
        db.refresh(item)
    return sorted(generated, key=lambda item: item.score, reverse=True)
