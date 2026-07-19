from __future__ import annotations

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .models import ActionItem, Application, Candidate, Company, IntegrationConnection, Job


def seed_database(db: Session) -> None:
    if db.scalar(select(func.count()).select_from(Candidate)):
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
    db.commit()
