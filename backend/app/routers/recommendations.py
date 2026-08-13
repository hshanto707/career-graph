"""recommendations router — module B7.

    GET /recommendations/jobs
    GET /recommendations/skills
    GET /recommendations/courses
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser, get_current_user, get_orchestrator
from app.core.responses import envelope
from app.database.postgres import get_db
from app.engine.orchestrator import EngineOrchestrator
from app.routers._shared import resolve_target_job_id

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("/jobs")
def recommended_jobs(
    limit: int = Query(default=10, ge=1, le=20),
    current: CurrentUser = Depends(get_current_user),
    orchestrator: EngineOrchestrator = Depends(get_orchestrator),
):
    return envelope(data=orchestrator.get_job_recommendations(current.id, limit=limit))


@router.get("/skills")
def recommended_skills(
    target_job_id: str | None = Query(default=None),
    limit: int = Query(default=10, ge=1, le=50),
    current: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    orchestrator: EngineOrchestrator = Depends(get_orchestrator),
):
    resolved_job_id = target_job_id or resolve_target_job_id(db, current.id)
    return envelope(
        data=orchestrator.get_skill_recommendations(current.id, target_job_id=resolved_job_id, limit=limit)
    )


@router.get("/courses")
def recommended_courses(
    target_job_id: str | None = Query(default=None),
    limit: int = Query(default=10, ge=1, le=50),
    current: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    orchestrator: EngineOrchestrator = Depends(get_orchestrator),
):
    resolved_job_id = target_job_id or resolve_target_job_id(db, current.id)
    return envelope(
        data=orchestrator.get_course_recommendations(current.id, target_job_id=resolved_job_id, limit=limit)
    )
