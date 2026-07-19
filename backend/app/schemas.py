from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class MatchDecision(BaseModel):
    status: Literal["shortlisted", "approved", "rejected", "process"]
    actor: str = Field(min_length=1, max_length=120)


class ActionUpdate(BaseModel):
    status: Literal["open", "done", "snoozed"]
    actor: str = Field(min_length=1, max_length=120)


class ContactCreate(BaseModel):
    channel: Literal["gmail", "zalo", "phone"]
    body: str = Field(min_length=1, max_length=10000)
    human_approved_by: str = Field(min_length=1, max_length=120)
    candidate_id: str | None = None
    company_id: str | None = None
    subject: str | None = Field(default=None, max_length=240)
    action_id: str | None = None


class ActorRequest(BaseModel):
    actor: str = Field(default="RAiCA user", min_length=1, max_length=120)


class OutboxRetry(BaseModel):
    actor: str = Field(default="RAiCA user", min_length=1, max_length=120)


class ApiError(BaseModel):
    detail: str
    context: dict[str, Any] | None = None
