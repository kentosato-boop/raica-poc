"""マッチング精度検証。

シードデータには各求人に対する「設計上の本命候補」が存在する。ここでは
  1. ランキング精度（本命が1位に来るか）
  2. 推薦帯（70+）のノイズ（専門違いが紛れ込まないか）
  3. スコア解像度（完全適合と及第点の適合が区別できるか）
  4. コア適合ゲート（soft 要因だけでは推薦帯に届かないか）
を回帰テストとして固定する。
"""
import os
import tempfile
from pathlib import Path

TEST_DIR = tempfile.TemporaryDirectory()
DB_PATH = Path(TEST_DIR.name) / "raica-accuracy.sqlite3"
os.environ["RAICA_DATABASE_URL"] = f"sqlite:///{DB_PATH}"
os.environ["RAICA_SKILL_SHEET_STORAGE_DIR"] = str(Path(TEST_DIR.name) / "skill_sheets")
os.environ.pop("RAICA_API_KEY", None)

import pytest  # noqa: E402
from sqlalchemy import select  # noqa: E402

from app.database import SessionLocal  # noqa: E402
from app.main import app  # noqa: E402  (import triggers startup/seed wiring)
from app.matching import SCORE_CAP, score_candidate  # noqa: E402
from app.models import Candidate, Job  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402


# 求人ごとの「本命候補」。job-a-phase2 は同等資格が2名存在するため許容集合。
GROUND_TRUTH: dict[str, set[str]] = {
    "job-a-line": {"cand-hoa"},
    "job-a-phase2": {"cand-son", "cand-mai"},
    "job-b-qc": {"cand-minh"},
    "job-c-cnc": {"cand-huy"},
    "job-d-interpreter": {"cand-trang"},
    "job-f-backend": {"cand-quan"},
    "job-f-frontend": {"cand-duc"},
    "job-i-planning": {"cand-binh"},
    "job-j-data": {"cand-yen"},
    "job-d-accountant": {"cand-thao"},
}


def _rank(db, job_id: str) -> list[tuple[str, int]]:
    job = db.get(Job, job_id)
    rows = []
    for candidate in db.scalars(select(Candidate)).all():
        rows.append((candidate.id, int(score_candidate(candidate, job)["score"])))
    rows.sort(key=lambda item: item[1], reverse=True)
    return rows


def test_ranking_top1_accuracy():
    with TestClient(app):
        with SessionLocal() as db:
            hits = 0
            for job_id, expected in GROUND_TRUTH.items():
                top_id = _rank(db, job_id)[0][0]
                if top_id in expected:
                    hits += 1
            # 10/10 の本命が1位に来ることを固定
            assert hits == len(GROUND_TRUTH), f"top-1 accuracy regressed: {hits}/{len(GROUND_TRUTH)}"


def test_specialist_jobs_have_no_noise_over_threshold():
    """専門特化求人では、本命以外に閾値70以上のアクティブ候補が出ないこと。"""
    specialist_jobs = {
        "job-b-qc", "job-c-cnc", "job-d-interpreter", "job-f-backend",
        "job-f-frontend", "job-i-planning", "job-j-data", "job-d-accountant",
    }
    with TestClient(app):
        with SessionLocal() as db:
            for job_id in specialist_jobs:
                expected = GROUND_TRUTH[job_id]
                noise = []
                for candidate in db.scalars(select(Candidate)).all():
                    if candidate.id in expected or candidate.status == "dormant":
                        continue
                    score = int(score_candidate(candidate, db.get(Job, job_id))["score"])
                    if score >= 70:
                        noise.append((candidate.id, candidate.specialization, score))
                assert not noise, f"{job_id} surfaced non-specialist noise >=70: {noise}"


def test_core_fit_gate_blocks_soft_only_candidates():
    """コア適合が低ければ、他軸が満点でも推薦帯(70)未満に抑えられること。"""
    with TestClient(app):
        with SessionLocal() as db:
            job = db.get(Job, "job-c-cnc")  # required: cnc, lathe / 専門 cnc
            hoa = db.get(Candidate, "cand-hoa")  # 専門 line_management、CNCスキルなし
            result = score_candidate(hoa, job)
            assert int(result["specialization"]) < 40
            assert int(result["core_fit"]) < 40
            assert int(result["score"]) < 70, "soft 要因でコア不適合が推薦帯に浮上している"


def test_perfect_fit_is_distinguishable_from_strong_fit():
    """全軸100の完全適合が、及第点の適合と同点に潰れないこと（解像度）。"""
    with TestClient(app):
        with SessionLocal() as db:
            huy = score_candidate(db.get(Candidate, "cand-huy"), db.get(Job, "job-c-cnc"))
            assert all(int(huy[axis]) == 100 for axis in ("skill", "specialization", "experience"))
            assert int(huy["core_fit"]) == 100
            assert int(huy["score"]) == SCORE_CAP  # 完全適合は上限98に到達
            quan = score_candidate(db.get(Candidate, "cand-quan"), db.get(Job, "job-f-backend"))
            # quan は stability が満点未満 → 完全適合より低いスコアで区別される
            assert int(quan["score"]) < int(huy["score"])


def test_score_never_claims_full_certainty():
    with TestClient(app):
        with SessionLocal() as db:
            for job_id in GROUND_TRUTH:
                for _, score in _rank(db, job_id):
                    assert score <= SCORE_CAP < 100
