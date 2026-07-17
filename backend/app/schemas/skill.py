"""Pydantic schemas for the skills module (B7): GET /skills/market,
GET /skills/gap."""
from __future__ import annotations

from pydantic import BaseModel, Field


class SkillDemandOut(BaseModel):
    skill_name: str
    demand_count: int
    demand_score: float
    trend: int | None = None


class MissingSkillOut(BaseModel):
    skill_name: str
    importance: str
    estimated_learning_weeks: int = Field(ge=0)


class MilestoneOut(BaseModel):
    week_range: str
    skill_name: str
    course_title: str | None = None
    course_url: str | None = None
    goal: str


class GapAnalysisResponse(BaseModel):
    """Shared response shape for both `POST /gap-analysis` and
    `GET /skills/gap` -- see docs/algorithmic-agents-decisions.md for the
    contract-reconciliation writeup (features-todo.md open decision #2)."""

    target_job_id: str | None = None
    readiness_score: int
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[MissingSkillOut] = Field(default_factory=list)
    explanation: str
    encouragement: str
    roadmap: list[MilestoneOut] = Field(default_factory=list)
    message: str | None = None
