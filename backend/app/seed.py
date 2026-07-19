from __future__ import annotations

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .models import ActionItem, Application, Candidate, Company, IntegrationConnection, Job


def enrich_workflow_data(db: Session) -> None:
    candidate_profiles = {
        "cand-hoa": ("hoa@example.invalid", 12.5, ["onsite", "hybrid"], "onsite", "line_management", 4.5, 3.2, 2, 1, [{"scope": "internal", "label": "A社 ラインリーダー", "stage": "オファー"}, {"scope": "internal", "label": "B社 製造管理", "stage": "意向確認"}, {"scope": "external", "label": "他社選考", "stage": "一次面接"}]),
        "cand-son": ("son@example.invalid", 10.5, ["onsite"], "onsite", "line_management", 2.5, 1.3, 1, 0, [{"scope": "internal", "label": "A社 第2ライン", "stage": "書類選考"}]),
        "cand-minh": ("minh@example.invalid", 11.5, ["onsite", "hybrid"], "flexible", "qc", 4, 2.8, 1, 1, [{"scope": "internal", "label": "B社 QC", "stage": "一次面接"}, {"scope": "external", "label": "他社品質管理", "stage": "書類選考"}]),
        "cand-huy": ("huy@example.invalid", 13, ["onsite"], "onsite", "cnc", 5.5, 3.5, 1, 2, [{"scope": "internal", "label": "C社 CNC", "stage": "書類選考"}, {"scope": "external", "label": "他社CNC", "stage": "最終面接"}, {"scope": "external", "label": "他社旋盤", "stage": "一次面接"}]),
        "cand-trang": ("trang@example.invalid", 14, ["onsite", "hybrid"], "hybrid", "interpretation", 4, 2.1, 1, 0, [{"scope": "internal", "label": "D社 総務通訳", "stage": "意向確認"}]),
        "cand-mai": ("mai@example.invalid", 10.5, ["onsite"], "onsite", "line_management", 2, 2.4, 0, 0, []),
        "cand-quan": ("quan@example.invalid", 25, ["remote", "hybrid"], "remote", "backend", 5, 1.8, 1, 2, [{"scope": "internal", "label": "F社 Backend", "stage": "推薦準備"}, {"scope": "external", "label": "他社SaaS", "stage": "技術面接通過"}, {"scope": "external", "label": "他社Fintech", "stage": "一次面接"}]),
        "cand-lan": ("lan@example.invalid", 10, ["onsite"], "onsite", "assembly", 3, 0.8, 0, 0, []),
    }
    keys = ("email", "current_salary_million", "work_style_options", "remote_preference", "specialization", "specialization_years", "recent_tenure_years", "internal_parallel_count", "external_parallel_count", "current_processes")
    candidate_profiles = {candidate_id: dict(zip(keys, values)) for candidate_id, values in candidate_profiles.items()}
    for candidate_id, values in candidate_profiles.items():
        candidate = db.get(Candidate, candidate_id)
        if candidate:
            for key, value in values.items():
                setattr(candidate, key, value)

    company_owners = {"co-a": "RA 太郎", "co-b": "RA 太郎", "co-c": "RA 太郎", "co-d": "RA Linh", "co-e": "RA 太郎", "co-f": "RA Linh"}
    for company_id, owner in company_owners.items():
        company = db.get(Company, company_id)
        if company:
            company.ra_owner = owner

    job_profiles = {
        "job-a-line": (24, 35, "onsite", "line_management", 4),
        "job-a-phase2": (22, 38, "onsite", "line_management", 2),
        "job-b-qc": (24, 38, "onsite", "qc", 3),
        "job-c-cnc": (22, 40, "onsite", "cnc", 3),
        "job-d-interpreter": (24, 38, "hybrid", "interpretation", 3),
        "job-f-backend": (24, 40, "remote", "backend", 4),
    }
    for job_id, (age_min, age_max, remote_mode, specialization, years) in job_profiles.items():
        job = db.get(Job, job_id)
        if job:
            job.preferred_age_min = age_min
            job.preferred_age_max = age_max
            job.remote_mode = remote_mode
            job.specialization = specialization
            job.min_specialization_years = years

    if db.get(Candidate, "cand-mai") and db.get(Job, "job-a-line") and not db.get(Application, "app-mai-a-won"):
        db.add(Application(id="app-mai-a-won", candidate_id="cand-mai", job_id="job-a-line", stage="closed_won", recommended_at=date(2026, 7, 2), last_event_at=date(2026, 7, 18), company_ok=True, candidate_ok=True))
    action_profiles = [
        ("q-ra-son", "ra", "mine", "client_chase", "A社へ書類選考結果の催促（Phan Van Son推薦）", "over", "推薦から5営業日経過。企業平均2.5日を超過。", "app-son-a2"),
        ("q-ra-huy", "ra", "mine", "client_chase", "C社 求人票の追加ヒアリング回答をCAへ共有", "due", "夜勤有無・送迎バス範囲を確認済み。未共有。", "app-huy-c"),
        ("q-ra-trang", "ra", "mine", "candidate_follow", "D社 面接候補日をCA経由で候補者へ確認", "due", "企業から3枠提示あり。本日中に一次回答が必要。", "app-trang-d"),
        ("q-ra-food", "ra", "mine", "approval", "食品加工G社 推薦メール下書きの承認", "ok", "AI生成済み。承認後にGmail送信キューへ登録。", None),
        ("q-ra-minh-wait", "ra", "theirs", "client_reply", "B社 一次面接の合否連絡待ち（Tran Van Minh）", "due", "平均返答4日。週明けにAIが催促文面を提案予定。", "app-minh-b"),
        ("q-ra-hoa-wait", "ra", "theirs", "offer_reply", "A社 給与再提示の回答待ち（Nguyen Thi Hoa）", "due", "14.5Mで再提示済み。回答期限は本日。", "app-hoa-a"),
        ("q-ra-trang-wait", "ra", "theirs", "candidate_reply", "Pham Thu Trang 意向確認の返信待ち", "ok", "CA経由で連絡済み。候補者の返答待ち。", "cand-trang"),
        ("q-ca-hoa", "ca", "mine", "candidate_follow", "Nguyen Thi Hoaへオファー意向を確認", "over", "平均反応1.5日超過。電話確認を推奨。", "cand-hoa"),
        ("q-ca-trang", "ca", "mine", "candidate_follow", "Pham Thu Trangへ面接候補日を確認", "call", "既読無反応2回。D社へ本日中に回答が必要。", "cand-trang"),
        ("q-ca-son-wait", "ca", "theirs", "client_reply", "A社 書類選考結果待ち（Phan Van Son）", "due", "RAが企業へ催促中。", "app-son-a2"),
    ]
    for action_id, owner_role, ball_owner, queue_type, label, severity, reason, source_ref in action_profiles:
        action = db.get(ActionItem, action_id)
        if not action:
            action = ActionItem(id=action_id, owner_role=owner_role, queue_type=queue_type, target_label=label, due_date=date(2026, 7, 19), severity=severity, reason=reason, source_ref=source_ref)
            db.add(action)
        action.ball_owner = ball_owner
        action.target_label = label
        action.reason = reason
    db.commit()


def seed_database(db: Session) -> None:
    if db.scalar(select(func.count()).select_from(Candidate)):
        enrich_workflow_data(db)
        return

    companies = [
        Company(id="co-a", name="A社", industry="mfg", avg_reply_days=2.5, hiring_signal="第2工場拡張", notes="ライン長の採用実績あり"),
        Company(id="co-b", name="B社", industry="mfg", avg_reply_days=4.0, hiring_signal="QC増員", notes="品質管理職の採用を継続"),
        Company(id="co-c", name="C社", industry="mfg", avg_reply_days=3.0, hiring_signal="CNC急募", notes="急募時は面接設定が早い"),
        Company(id="co-d", name="D社", industry="trade", avg_reply_days=2.0, hiring_signal="総務通訳3枠", notes="日本語要件を重視"),
        Company(id="co-e", name="E社", industry="log", avg_reply_days=5.0, hiring_signal="倉庫ライン欠員", notes="返信遅延時は電話切替"),
        Company(id="co-f", name="F社", industry="it", avg_reply_days=3.5, hiring_signal="Backend増員", notes="技術面接の速度を重視"),
    ]
    jobs = [
        Job(id="job-a-line", porters_id="PT-J-0001", company_id="co-a", title="製造ラインリーダー", category="worker", industry="mfg", status="open", location="Bac Ninh", salary_min_million=13, salary_max_million=16, received_date=date(2026, 7, 7), min_experience_years=4, min_jlpt="N3", max_commute_minutes=45, required_skills=["line_management", "5s"]),
        Job(id="job-a-phase2", porters_id="PT-J-0002", company_id="co-a", title="第2ライン要員", category="worker", industry="mfg", status="phase2", location="Bac Ninh", salary_min_million=11, salary_max_million=14, received_date=date(2026, 7, 10), min_experience_years=2, min_jlpt="N4", max_commute_minutes=45, required_skills=["line_management", "assembly"]),
        Job(id="job-b-qc", porters_id="PT-J-0003", company_id="co-b", title="QCスタッフ", category="worker", industry="mfg", status="open", location="Hung Yen", salary_min_million=12, salary_max_million=14, received_date=date(2026, 7, 9), min_experience_years=3, min_jlpt="N4", max_commute_minutes=45, required_skills=["qc", "kaizen"]),
        Job(id="job-c-cnc", porters_id="PT-J-0004", company_id="co-c", title="CNCオペレーター", category="worker", industry="mfg", status="urgent", location="Ha Noi", salary_min_million=13, salary_max_million=16, received_date=date(2026, 7, 13), min_experience_years=3, min_jlpt="N4", max_commute_minutes=40, required_skills=["cnc", "lathe"]),
        Job(id="job-d-interpreter", porters_id="PT-J-0005", company_id="co-d", title="総務通訳", category="jp", industry="trade", status="open", location="Ha Noi", salary_min_million=14, salary_max_million=18, received_date=date(2026, 7, 8), min_experience_years=3, min_jlpt="N2", max_commute_minutes=60, required_skills=["interpretation", "administration"]),
        Job(id="job-f-backend", porters_id="PT-J-0006", company_id="co-f", title="Backend Engineer", category="eng", industry="it", status="urgent", location="Ha Noi / Remote", salary_min_million=25, salary_max_million=35, received_date=date(2026, 7, 16), min_experience_years=4, min_jlpt="N3", max_commute_minutes=0, required_skills=["backend", "python"]),
    ]
    candidates = [
        Candidate(id="cand-hoa", porters_id="PT-C-0001", name="Nguyen Thi Hoa", status="process", ca_owner="CA Huong", role_title="Line Leader", age=27, gender="F", years_experience=5, jlpt="N3", desired_salary_million=14, commute_minutes=35, work_style="onsite", skills=["line_management", "5s", "kaizen"], last_contact_date=date(2026, 7, 16), avg_response_days=1.5, notes="希望14M。通訳常駐ラインなら前向き。"),
        Candidate(id="cand-son", porters_id="PT-C-0002", name="Phan Van Son", status="process", ca_owner="CA Huong", role_title="Line Staff", age=33, gender="M", years_experience=3, jlpt="N4", desired_salary_million=12, commute_minutes=40, work_style="onsite", skills=["line_management", "assembly"], last_contact_date=date(2026, 7, 10), avg_response_days=2, notes="夜勤不可。日勤枠なら推薦可。"),
        Candidate(id="cand-minh", porters_id="PT-C-0003", name="Tran Van Minh", status="active", ca_owner="CA Linh", role_title="QC Staff", age=31, gender="M", years_experience=4, jlpt="N3", desired_salary_million=13, commute_minutes=25, work_style="onsite", skills=["qc", "iso9001", "kaizen"], last_contact_date=date(2026, 7, 15), avg_response_days=2.5, notes="品質記録と改善提案の経験あり。"),
        Candidate(id="cand-huy", porters_id="PT-C-0004", name="Le Quang Huy", status="active", ca_owner="CA Linh", role_title="CNC Operator", age=24, gender="M", years_experience=6, jlpt="N4", desired_salary_million=15, commute_minutes=30, work_style="onsite", skills=["cnc", "lathe", "night_shift"], last_contact_date=date(2026, 7, 14), avg_response_days=2, notes="CNC旋盤と夜勤対応が可能。"),
        Candidate(id="cand-trang", porters_id="PT-C-0005", name="Pham Thu Trang", status="process", ca_owner="CA Mai", role_title="Interpreter", age=29, gender="F", years_experience=4, jlpt="N2", desired_salary_million=16, commute_minutes=45, work_style="onsite", skills=["interpretation", "administration"], last_contact_date=date(2026, 7, 15), avg_response_days=1.8, notes="総務通訳経験。意思決定に時間がかかる。"),
        Candidate(id="cand-mai", porters_id="PT-C-0006", name="Ngo Thi Mai", status="active", ca_owner="CA Huong", role_title="Line Staff", age=28, gender="F", years_experience=2, jlpt="N3", desired_salary_million=12.5, commute_minutes=35, work_style="onsite", skills=["line_management", "assembly"], last_contact_date=date(2026, 7, 19), avg_response_days=1.2, notes="A社2024年成約者と近い経歴。"),
        Candidate(id="cand-quan", porters_id="PT-C-0007", name="Dang Minh Quan", status="active", ca_owner="CA Linh", role_title="Backend Engineer", age=26, gender="M", years_experience=5, jlpt="N3", desired_salary_million=30, commute_minutes=0, work_style="remote", skills=["backend", "python", "nodejs"], last_contact_date=date(2026, 7, 18), avg_response_days=1, notes="他社で技術面接通過済み。スピード勝負。"),
        Candidate(id="cand-lan", porters_id="PT-C-9001", name="Vu Thi Lan", status="dormant", ca_owner="CA Mai", role_title="Factory Staff", age=30, gender="F", years_experience=3, jlpt="N4", desired_salary_million=11.5, commute_minutes=45, work_style="onsite", skills=["assembly"], last_contact_date=date(2025, 3, 1), avg_response_days=3.5, notes="Zalo OA連携済み。家庭都合で一度辞退。"),
    ]
    applications = [
        Application(id="app-hoa-a", candidate_id="cand-hoa", job_id="job-a-line", stage="offer", recommended_at=date(2026, 7, 8), last_event_at=date(2026, 7, 14), company_ok=True, candidate_ok=False),
        Application(id="app-son-a2", candidate_id="cand-son", job_id="job-a-phase2", stage="screening", recommended_at=date(2026, 7, 10), last_event_at=date(2026, 7, 10), company_ok=False, candidate_ok=True),
        Application(id="app-minh-b", candidate_id="cand-minh", job_id="job-b-qc", stage="first_interview", recommended_at=date(2026, 7, 10), last_event_at=date(2026, 7, 15), company_ok=False, candidate_ok=True),
        Application(id="app-huy-c", candidate_id="cand-huy", job_id="job-c-cnc", stage="screening", recommended_at=date(2026, 7, 14), last_event_at=date(2026, 7, 14), company_ok=False, candidate_ok=True),
        Application(id="app-trang-d", candidate_id="cand-trang", job_id="job-d-interpreter", stage="intent_check", recommended_at=date(2026, 7, 10), last_event_at=date(2026, 7, 16), company_ok=True, candidate_ok=False),
    ]
    actions = [
        ActionItem(id="q-ra-son", owner_role="ra", queue_type="client_chase", target_label="A社 / Phan Van Son", due_date=date(2026, 7, 19), severity="over", reason="書類5営業日無返答。企業平均2.5日も超過。", source_ref="app-son-a2"),
        ActionItem(id="q-ra-huy", owner_role="ra", queue_type="client_chase", target_label="C社 / Le Quang Huy", due_date=date(2026, 7, 19), severity="due", reason="推薦から3営業日目。催促1回目。", source_ref="app-huy-c"),
        ActionItem(id="q-ra-long", owner_role="ra", queue_type="client_call", target_label="E社 / Do Van Long", due_date=date(2026, 7, 19), severity="call", reason="催促2回後も未返信。電話切替。"),
        ActionItem(id="q-ca-hoa", owner_role="ca", queue_type="candidate_follow", target_label="Nguyen Thi Hoa", due_date=date(2026, 7, 19), severity="over", reason="平均反応1.5日超過。電話推奨。", source_ref="cand-hoa"),
        ActionItem(id="q-ca-trang", owner_role="ca", queue_type="candidate_follow", target_label="Pham Thu Trang", due_date=date(2026, 7, 19), severity="call", reason="既読無反応2回。D社へ本日中に回答が必要。", source_ref="cand-trang"),
    ]
    integrations = [
        IntegrationConnection(provider="porters", status="not_configured", capabilities=["candidates.read", "jobs.read"]),
        IntegrationConnection(provider="gmail", status="not_configured", capabilities=["message.send"]),
        IntegrationConnection(provider="zalo", status="not_configured", capabilities=["message.send"]),
        IntegrationConnection(provider="asana", status="not_configured", capabilities=["task.create", "task.complete"]),
    ]
    db.add_all(companies + jobs + candidates + applications + actions + integrations)
    db.flush()
    enrich_workflow_data(db)
