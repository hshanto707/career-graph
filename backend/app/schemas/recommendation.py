"""Pydantic schemas for the recommendations module (B7)."""
from __future__ import annotations

from pydantic import BaseModel, Field


class JobRecommendationOut(BaseModel):
    job_id: str
    title: str | None = None
    match_percentage: float
    matched_skills: list[str] = Field(default_factory=list)
    why_recommended: str
    # "gnn" when the trained GraphSAGE model contributed a rerank score for
    # this job, "algorithmic" when it's Jaccard/LEADS_TO-only (GNN
    # unavailable, or this job fell outside the rerank pool). See
    # RecommendationAgent.rank_jobs's module docstring.
    match_source: str = "algorithmic"


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
