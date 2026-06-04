"""
Jobs router — browse and search job postings.

GET /api/v1/jobs           — List jobs with optional filters (public)
GET /api/v1/jobs/{job_id}  — Get a specific job (public)
"""
from fastapi import APIRouter, Query, HTTPException, status, Depends
from app.database.neo4j import get_neo4j
from app.services.graph_service import GraphService
from app.schemas.common import ok

router = APIRouter(prefix="/jobs")


@router.get("")
async def list_jobs(
    search: str | None = Query(None),
    location: str | None = Query(None),
    employment_type: str | None = Query(None),
    skill: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    neo4j_session=Depends(get_neo4j),
):
    """List job postings with optional filters. Paginated. No auth required."""
    svc = GraphService(neo4j_session)
    try:
        jobs, total = await svc.get_jobs_filtered(
            search=search, location=location,
            employment_type=employment_type, skill=skill,
            limit=limit, offset=offset,
        )
    except Exception:
        jobs, total = [], 0
    return ok({"jobs": jobs, "total": total, "limit": limit, "offset": offset})


@router.get("/{job_id}")
async def get_job(job_id: str, neo4j_session=Depends(get_neo4j)):
    """Get a single job posting by ID."""
    svc = GraphService(neo4j_session)
    try:
        job = await svc.get_job_by_id(job_id)
    except Exception:
        job = None
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job '{job_id}' not found")
    return ok(job)
