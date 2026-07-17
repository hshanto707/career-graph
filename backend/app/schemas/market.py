"""Pydantic schemas for `GET /market/insights` (B7)."""
from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.skill import SkillDemandOut


class MarketInsightsOut(BaseModel):
    top_skills: list[SkillDemandOut] = Field(default_factory=list)
    trend_bullets: list[str] = Field(default_factory=list)
    summary: str
