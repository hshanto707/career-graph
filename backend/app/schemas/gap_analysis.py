"""Pydantic schemas for `POST /gap-analysis` (B7)."""
from __future__ import annotations

from pydantic import BaseModel, Field


class GapAnalysisRequest(BaseModel):
    target_job_id: str = Field(min_length=1)
