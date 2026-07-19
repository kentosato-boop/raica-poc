from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, Optional

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class Candidate(TimestampMixin, Base):
    __tablename__ = "candidates"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    porters_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(160), index=True)
    status: Mapped[str] = mapped_column(String(24), index=True, default="active")
    ca_owner: Mapped[str] = mapped_column(String(100))
    role_title: Mapped[str] = mapped_column(String(160))
    age: Mapped[Optional[int]] = mapped_column(Integer)
    gender: Mapped[Optional[str]] = mapped_column(String(12))
    years_experience: Mapped[float] = mapped_column(Float, default=0)
    jlpt: Mapped[Optional[str]] = mapped_column(String(8))
    desired_salary_million: Mapped[Optional[float]] = mapped_column(Float)
    commute_minutes: Mapped[Optional[int]] = mapped_column(Integer)
    work_style: Mapped[str] = mapped_column(String(24), default="onsite")
    skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    last_contact_date: Mapped[Optional[date]] = mapped_column(Date)
    avg_response_days: Mapped[Optional[float]] = mapped_column(Float)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    matches: Mapped[list[Match]] = relationship(back_populates="candidate", cascade="all, delete-orphan")


class Company(TimestampMixin, Base):
    __tablename__ = "companies"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(160), index=True)
    industry: Mapped[str] = mapped_column(String(60))
    avg_reply_days: Mapped[Optional[float]] = mapped_column(Float)
    hiring_signal: Mapped[Optional[str]] = mapped_column(String(200))
    notes: Mapped[Optional[str]] = mapped_column(Text)

    jobs: Mapped[list[Job]] = relationship(back_populates="company", cascade="all, delete-orphan")


class Job(TimestampMixin, Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    porters_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    company_id: Mapped[str] = mapped_column(ForeignKey("companies.id"), index=True)
    title: Mapped[str] = mapped_column(String(180), index=True)
    category: Mapped[str] = mapped_column(String(60))
    industry: Mapped[str] = mapped_column(String(60))
    status: Mapped[str] = mapped_column(String(24), index=True, default="open")
    location: Mapped[Optional[str]] = mapped_column(String(120))
    salary_min_million: Mapped[Optional[float]] = mapped_column(Float)
    salary_max_million: Mapped[Optional[float]] = mapped_column(Float)
    received_date: Mapped[date] = mapped_column(Date)
    min_experience_years: Mapped[float] = mapped_column(Float, default=0)
    min_jlpt: Mapped[Optional[str]] = mapped_column(String(8))
    max_commute_minutes: Mapped[Optional[int]] = mapped_column(Integer)
    required_skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    ai_candidate_count: Mapped[int] = mapped_column(Integer, default=0)

    company: Mapped[Company] = relationship(back_populates="jobs")
    matches: Mapped[list[Match]] = relationship(back_populates="job", cascade="all, delete-orphan")


class Match(TimestampMixin, Base):
    __tablename__ = "matches"
    __table_args__ = (
        UniqueConstraint("candidate_id", "job_id", name="uq_match_candidate_job"),
        Index("ix_matches_job_score", "job_id", "score"),
    )

    id: Mapped[str] = mapped_column(String(96), primary_key=True)
    candidate_id: Mapped[str] = mapped_column(ForeignKey("candidates.id"), index=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id"), index=True)
    score: Mapped[int] = mapped_column(Integer)
    skill_score: Mapped[int] = mapped_column(Integer)
    experience_score: Mapped[int] = mapped_column(Integer)
    japanese_score: Mapped[int] = mapped_column(Integer)
    salary_score: Mapped[int] = mapped_column(Integer)
    commute_score: Mapped[int] = mapped_column(Integer)
    similarity_pct: Mapped[int] = mapped_column(Integer)
    ng_check: Mapped[str] = mapped_column(Text)
    evidence_quote: Mapped[str] = mapped_column(Text)
    recommendation_status: Mapped[str] = mapped_column(String(24), default="shortlisted", index=True)

    candidate: Mapped[Candidate] = relationship(back_populates="matches")
    job: Mapped[Job] = relationship(back_populates="matches")


class Application(TimestampMixin, Base):
    __tablename__ = "applications"
    __table_args__ = (UniqueConstraint("candidate_id", "job_id", name="uq_application_candidate_job"),)

    id: Mapped[str] = mapped_column(String(96), primary_key=True)
    candidate_id: Mapped[str] = mapped_column(ForeignKey("candidates.id"), index=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id"), index=True)
    stage: Mapped[str] = mapped_column(String(32), index=True)
    recommended_at: Mapped[Optional[date]] = mapped_column(Date)
    last_event_at: Mapped[date] = mapped_column(Date)
    company_ok: Mapped[bool] = mapped_column(Boolean, default=False)
    candidate_ok: Mapped[bool] = mapped_column(Boolean, default=False)
    lost_reason: Mapped[Optional[str]] = mapped_column(Text)


class ActionItem(TimestampMixin, Base):
    __tablename__ = "action_items"
    __table_args__ = (Index("ix_action_owner_status_due", "owner_role", "status", "due_date"),)

    id: Mapped[str] = mapped_column(String(96), primary_key=True)
    owner_role: Mapped[str] = mapped_column(String(12), index=True)
    queue_type: Mapped[str] = mapped_column(String(40))
    target_label: Mapped[str] = mapped_column(String(220))
    due_date: Mapped[date] = mapped_column(Date)
    severity: Mapped[str] = mapped_column(String(16), index=True)
    reason: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(16), default="open", index=True)
    source_ref: Mapped[Optional[str]] = mapped_column(String(96))


class ContactLog(TimestampMixin, Base):
    __tablename__ = "contact_logs"

    id: Mapped[str] = mapped_column(String(96), primary_key=True)
    candidate_id: Mapped[Optional[str]] = mapped_column(ForeignKey("candidates.id"), index=True)
    company_id: Mapped[Optional[str]] = mapped_column(ForeignKey("companies.id"), index=True)
    channel: Mapped[str] = mapped_column(String(24), index=True)
    direction: Mapped[str] = mapped_column(String(16), default="outbound")
    subject: Mapped[Optional[str]] = mapped_column(String(240))
    body: Mapped[str] = mapped_column(Text)
    human_approved_by: Mapped[str] = mapped_column(String(120))
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    response_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))


class IntegrationConnection(TimestampMixin, Base):
    __tablename__ = "integration_connections"

    provider: Mapped[str] = mapped_column(String(32), primary_key=True)
    status: Mapped[str] = mapped_column(String(24), default="not_configured")
    last_checked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_success_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[Optional[str]] = mapped_column(Text)
    capabilities: Mapped[list[str]] = mapped_column(JSON, default=list)


class SyncRun(Base):
    __tablename__ = "sync_runs"

    id: Mapped[str] = mapped_column(String(96), primary_key=True)
    provider: Mapped[str] = mapped_column(String(32), index=True)
    resource: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(24), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    records_read: Mapped[int] = mapped_column(Integer, default=0)
    records_written: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text)


class OutboxEvent(Base):
    __tablename__ = "outbox_events"

    id: Mapped[str] = mapped_column(String(96), primary_key=True)
    provider: Mapped[str] = mapped_column(String(32), index=True)
    event_type: Mapped[str] = mapped_column(String(60))
    aggregate_id: Mapped[str] = mapped_column(String(96), index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(24), default="pending", index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[Optional[str]] = mapped_column(Text)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    actor: Mapped[str] = mapped_column(String(120))
    action: Mapped[str] = mapped_column(String(80), index=True)
    entity_type: Mapped[str] = mapped_column(String(60))
    entity_id: Mapped[str] = mapped_column(String(96), index=True)
    details: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)
