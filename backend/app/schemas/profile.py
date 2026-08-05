"""Pydantic schemas for the student profile module."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SkillEntry(BaseModel):
    name: str
    proficiency: int = Field(ge=0, le=10)
    years: float = Field(ge=0)


class ExperienceItem(BaseModel):
    title: str
    company: str
    start_month: int = Field(ge=1, le=12)
    start_year: int = Field(ge=1950, le=2100)
    end_month: int | None = Field(default=None, ge=1, le=12)
    end_year: int | None = Field(default=None, ge=1950, le=2100)
    is_current: bool = False
    description: str = ""

    @model_validator(mode="after")
    def _validate_end_date(self) -> "ExperienceItem":
        if self.is_current:
            self.end_month = None
            self.end_year = None
            return self
        if self.end_month is None or self.end_year is None:
            raise ValueError("end_month and end_year are required unless is_current is true")
        if (self.end_year, self.end_month) < (self.start_year, self.start_month):
            raise ValueError("End date must not be before the start date")
        return self


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
