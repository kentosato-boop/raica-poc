"""AI分析ステージ。

ルールベース一次選抜を通過した上位候補について、適合理由・懸念点・推薦可否を
自然言語で生成する。Claude API キーが設定されていれば実際に LLM を呼び、
未設定・未インストール・API失敗のいずれの場合も決定論スコアに基づく
説明へフォールバックするため、キー無しでもアプリは動作する。
"""
from __future__ import annotations

import json
import re
from typing import Any, Sequence

from .config import Settings
from .matching import AI_SHORTLIST_SIZE
from .models import Job, Match


SYSTEM_PROMPT = (
    "あなたはベトナムで日系企業向けの人材紹介を担当するシニアRA/CAです。"
    "求人要件と候補者データだけを根拠に、推薦可否を実務目線で簡潔に判断します。"
    "データに無い経歴・資格・意向を推測で補わないこと。回答は日本語。"
)

VERDICTS = {"推薦", "要検討", "見送り検討"}


def _job_brief(job: Job) -> dict[str, Any]:
    return {
        "title": job.title,
        "company": job.company.name if job.company else None,
        "industry": job.industry,
        "location": job.location,
        "salary_range_million": [job.salary_min_million, job.salary_max_million],
        "min_experience_years": job.min_experience_years,
        "specialization": job.specialization,
        "min_specialization_years": job.min_specialization_years,
        "min_jlpt": job.min_jlpt,
        "remote_mode": job.remote_mode,
        "preferred_age": [job.preferred_age_min, job.preferred_age_max],
        "required_skills": job.required_skills,
    }


def _candidate_brief(match: Match) -> dict[str, Any]:
    candidate = match.candidate
    return {
        "candidate_id": candidate.id,
        "name": candidate.name,
        "role_title": candidate.role_title,
        "specialization": candidate.specialization,
        "specialization_years": candidate.specialization_years,
        "years_experience": candidate.years_experience,
        "jlpt": candidate.jlpt,
        "age": candidate.age,
        "current_salary_million": candidate.current_salary_million,
        "desired_salary_million": candidate.desired_salary_million,
        "current_location": candidate.current_location,
        "remote_preference": candidate.remote_preference,
        "recent_tenure_years": candidate.recent_tenure_years,
        "skills": candidate.skills,
        "internal_parallel": candidate.internal_parallel_count,
        "external_parallel": candidate.external_parallel_count,
        "notes": candidate.notes,
        "rule_score": match.score,
        "axis_scores": {
            "skill": match.skill_score,
            "specialization": match.specialization_score,
            "experience": match.experience_score,
            "japanese": match.japanese_score,
            "salary": match.salary_score,
            "commute": match.commute_score,
            "age": match.age_score,
            "remote": match.remote_score,
            "stability": match.stability_score,
        },
    }


def _fallback_entry(match: Match) -> dict[str, Any]:
    score = match.score
    verdict = "推薦" if score >= 85 else "要検討" if score >= 70 else "見送り検討"
    return {
        "candidate_id": match.candidate_id,
        "candidate_name": match.candidate.name,
        "fit_reason": match.evidence_quote,
        "concerns": match.ng_check,
        "verdict": verdict,
    }


def _fallback(matches: Sequence[Match], reason: str) -> dict[str, Any]:
    return {
        "source": "rule-based",
        "model": None,
        "reason": reason,
        "analyses": [_fallback_entry(match) for match in matches],
    }


def _extract_json(text: str) -> Any:
    """コードフェンスや前置きが混ざっても配列部分を取り出す。"""
    fenced = re.search(r"```(?:json)?\s*(.+?)```", text, re.S)
    body = fenced.group(1) if fenced else text
    array = re.search(r"\[.*\]", body, re.S)
    return json.loads(array.group(0) if array else body)


def analyze_matches(settings: Settings, job: Job, matches: Sequence[Match]) -> dict[str, Any]:
    top = list(matches)[:AI_SHORTLIST_SIZE]
    if not top:
        return {"source": "none", "model": None, "reason": "推薦候補がありません", "analyses": []}
    if not settings.llm_configured:
        return _fallback(top, "ANTHROPIC_API_KEY が未設定のため、スコア根拠を表示しています")
    try:
        import anthropic
    except ImportError:
        return _fallback(top, "anthropic パッケージが未インストールのため、スコア根拠を表示しています")

    try:
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key, timeout=settings.llm_timeout_seconds)
        payload = {"job": _job_brief(job), "candidates": [_candidate_brief(match) for match in top]}
        user_prompt = (
            "以下は、ルールベースの一次選抜を通過した候補者です。"
            "各候補者について「適合理由」「懸念点」「推薦可否」を判断してください。\n"
            "推薦可否は 推薦 / 要検討 / 見送り検討 のいずれか。\n"
            "適合理由と懸念点はそれぞれ120文字以内の日本語で、具体的な数値や経歴に触れること。\n"
            "出力は次の形式のJSON配列のみとし、前後に説明文を書かないこと:\n"
            '[{"candidate_id":"...","fit_reason":"...","concerns":"...","verdict":"推薦"}]\n\n'
            f"データ:\n{json.dumps(payload, ensure_ascii=False, default=str)}"
        )
        response = client.messages.create(
            model=settings.llm_model,
            max_tokens=1500,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        text = "".join(block.text for block in response.content if getattr(block, "type", None) == "text")
        parsed = _extract_json(text)
        by_id = {str(item.get("candidate_id")): item for item in parsed if isinstance(item, dict)}
        analyses: list[dict[str, Any]] = []
        for match in top:
            item = by_id.get(match.candidate_id)
            if not item:
                analyses.append(_fallback_entry(match))
                continue
            verdict = str(item.get("verdict") or "").strip()
            analyses.append({
                "candidate_id": match.candidate_id,
                "candidate_name": match.candidate.name,
                "fit_reason": str(item.get("fit_reason") or "").strip()[:400] or match.evidence_quote,
                "concerns": str(item.get("concerns") or "").strip()[:400] or match.ng_check,
                "verdict": verdict if verdict in VERDICTS else "要検討",
            })
        return {"source": "llm", "model": settings.llm_model, "reason": None, "analyses": analyses}
    except Exception as exc:  # ネットワーク・認証・JSON崩れ等はすべてフォールバック
        return _fallback(top, f"LLM呼び出しに失敗したためスコア根拠を表示しています（{type(exc).__name__}）")
