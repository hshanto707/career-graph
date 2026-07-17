"""dashboard router — module B7.

GET /dashboard -> DashboardStats (readiness score, skills matched/total,
missing high-demand skills, market demand snapshot). Purely algorithmic --
see EngineOrchestrator.get_dashboard()'s docstring for why no LLM call is
ever made on this route, and how its readiness score is kept numerically
consistent with GET /skills/gap for the same student.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser, get_current_user, get_orchestrator
from app.core.responses import envelope
from app.database.postgres import get_db
from app.engine.orchestrator import EngineOrchestrator
from app.routers._shared import resolve_target_job_id

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("")
def dashboard(
    current: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    orchestrator: EngineOrchestrator = Depends(get_orchestrator),
):
    target_job_id = resolve_target_job_id(db, current.id)
    return envelope(data=orchestrator.get_dashboard(current.id, target_job_id=target_job_id))
