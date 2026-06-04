"""Pydantic schemas for profile endpoints."""
from pydantic import BaseModel, field_validator


class SkillEntry(BaseModel):
    name: str
    proficiency: float
    years: float


class ProfileResponse(BaseModel):
    user_id: str
    name: str
    email: str
    university: str | None
    graduation_year: int | None
    target_roles: list[str]
    bio: str | None
    skills: list[SkillEntry]


class ProfileUpdateRequest(BaseModel):
    name: str | None = None
    university: str | None = None
    graduation_year: int | None = None
    target_roles: list[str] | None = None
    bio: str | None = None


class AddSkillRequest(BaseModel):
    skill_name: str
    proficiency: float
    years: float

    @field_validator("proficiency")
    @classmethod
    def proficiency_range(cls, v: float) -> float:
        if not 0 <= v <= 10:
            raise ValueError("proficiency must be between 0 and 10")
        return v

    @field_validator("years")
    @classmethod
    def years_range(cls, v: float) -> float:
        if not 0 <= v <= 50:
            raise ValueError("years must be between 0 and 50")
        return v
