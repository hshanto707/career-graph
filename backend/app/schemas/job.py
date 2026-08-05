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


class JobDetailOut(JobOut):
    """GET /jobs/{id} only -- adds the job's required skills (plain factual
    REQUIRES-edge data, not a personalized score/narrative, so this stays
    consistent with the "pure catalog" decision for /jobs; see
    docs/algorithmic-agents-decisions.md Open decision #3). Not added to
    JobOut/list_jobs to avoid an N+1 required-skills query per row of a
    paginated, debounced-search browse list.
    """

    required_skills: list[str] = []
