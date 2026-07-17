"""gap_analysis router — module B7.

POST /gap-analysis with `target_job_id` body -> GapAnalysisResponse
(+ roadmap). See app/routers/skills.py's module docstring for the full
reconciliation between this route and GET /skills/gap (features-todo.md
open decision #2).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.deps import CurrentUser, get_current_user, get_graph_service, get_orchestrator
from app.core.responses import AppError, envelope
from app.engine.orchestrator import EngineOrchestrator
from app.schemas.gap_analysis import GapAnalysisRequest
from app.services.graph_service import GraphService

router = APIRouter(prefix="/gap-analysis", tags=["gap_analysis"])


@router.post("")
def gap_analysis(
    payload: GapAnalysisRequest,
    current: CurrentUser = Depends(get_current_user),
    graph_service: GraphService = Depends(get_graph_service),
    orchestrator: EngineOrchestrator = Depends(get_orchestrator),
):
    if graph_service.get_job(payload.target_job_id) is None:
        raise AppError("NOT_FOUND", f"Job {payload.target_job_id} does not exist.", 404)

    result = orchestrator.compute_gap_analysis(current.id, payload.target_job_id)
    return envelope(data=result)
