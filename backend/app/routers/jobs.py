"""jobs router — module B7.

GET /jobs?type=&location=&search=&limit=&offset=, GET /jobs/:id. Thin
controllers delegating entirely to `GraphService` -- all filter values are
passed through as bound parameters (see `GraphService.list_jobs`), so a
`search` value containing Cypher-special characters is treated as literal
text, never interpreted as Cypher (system-design.md §15 control C6).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.core.deps import CurrentUser, get_current_user, get_graph_service
from app.core.responses import AppError, envelope
from app.schemas.job import JobDetailOut, JobOut
from app.services.graph_service import GraphService

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("")
def list_jobs(
    type: str | None = Query(default=None),
    location: str | None = Query(default=None),
    search: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current: CurrentUser = Depends(get_current_user),
    graph_service: GraphService = Depends(get_graph_service),
):
    filters: dict = {"limit": offset + limit}
    if type:
        filters["type"] = type
    if location:
        filters["location"] = location
    if search:
        filters["search"] = search

    jobs = graph_service.list_jobs(filters)
    page = jobs[offset : offset + limit]
    return envelope(data=[JobOut(**j).model_dump() for j in page])


@router.get("/titles")
def list_job_titles(
    search: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    graph_service: GraphService = Depends(get_graph_service),
):
    return envelope(data=graph_service.list_job_titles(search=search, limit=limit))


@router.get("/{job_id}")
def get_job(
    job_id: str,
    current: CurrentUser = Depends(get_current_user),
    graph_service: GraphService = Depends(get_graph_service),
):
    job = graph_service.get_job(job_id)
    if job is None:
        raise AppError("NOT_FOUND", f"Job {job_id} does not exist.", 404)
    required_skills = [s["name"] for s in graph_service.get_job_required_skills(job_id) if s.get("name")]
    return envelope(data=JobDetailOut(**job, required_skills=required_skills).model_dump())
