"""Pydantic schemas for the student profile module."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SkillEntry(BaseModel):
    name: str
    proficiency: int = Field(ge=0, le=10)
    years: float = Field(ge=0)


class ExperienceItem(BaseModel):
    title: str
    company: str
    duration: str
    description: str = ""


class ProfileUpdate(BaseModel):
    major: str | None = None
    graduation_year: int | None = Field(default=None, ge=1900, le=2100)
    skills: list[SkillEntry] | None = None
    target_roles: list[str] | None = None
    experience: list[ExperienceItem] | None = None


class ProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    major: str | None = None
    graduation_year: int | None = None
    skills: list[SkillEntry] = Field(default_factory=list)
    target_roles: list[str] = Field(default_factory=list)
    experience: list[ExperienceItem] = Field(default_factory=list)
    updated_at: datetime
