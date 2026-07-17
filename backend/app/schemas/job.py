"""Pydantic schemas for the jobs module (B7)."""
from __future__ import annotations

from pydantic import BaseModel


class JobOut(BaseModel):
    id: str
    title: str | None = None
    company: str | None = None
    location: str | None = None
    type: str | None = None
    source: str | None = None
    salary_min: int | None = None
    salary_max: int | None = None
