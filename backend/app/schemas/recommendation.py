"""Pydantic schemas for the recommendations module (B7)."""
from __future__ import annotations

from pydantic import BaseModel, Field


class JobRecommendationOut(BaseModel):
    job_id: str
    title: str | None = None
    match_percentage: float
    matched_skills: list[str] = Field(default_factory=list)
    why_recommended: str


class SkillRecommendationOut(BaseModel):
    skill_name: str
    demand_score: float
    demand_count: int


class CourseRecommendationOut(BaseModel):
    course_id: str | None = None
    title: str | None = None
    provider: str | None = None
    url: str | None = None
    duration: str | None = None
    free: bool = False
    skill_name: str | None = None
