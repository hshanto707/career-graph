"""Pydantic schemas for `GET /dashboard` (B7)."""
from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.skill import SkillDemandOut


class DashboardStatsOut(BaseModel):
    job_readiness_score: int
    skills_matched: int
    total_required_skills: int
    missing_high_demand_skills: list[str] = Field(default_factory=list)
    market_demand: list[SkillDemandOut] = Field(default_factory=list)
