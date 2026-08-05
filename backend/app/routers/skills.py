"""skills router — module B7.

    GET /skills/market  -- pure algorithmic aggregate demand (MarketAgent),
                            no LLM narrative.
    GET /skills/gap     -- current user vs. their target role.

--------------------------------------------------------------------------
Open decision #2 -- GET /skills/gap vs. POST /gap-analysis
--------------------------------------------------------------------------
Both compute a skill gap for a student against a job. Resolution (see
docs/algorithmic-agents-decisions.md for the full write-up):

  - `POST /gap-analysis` takes an explicit `target_job_id` in the body --
    the "analyze against *this specific* job" entry point (used from the
    Job Explorer / Recommendations pages). An unknown `target_job_id` is a
    client error -> 404.
  - `GET /skills/gap` is the "just show me my current standing" entry point
    (used by the Skill Analysis page on load, no job picked yet) -- it
    resolves the target job automatically from the student's own profile
    (`resolve_target_job_id`: most-recently-added `target_roles` entry), or
    accepts an optional `?target_job_id=` query override for callers that
    already know which job they mean.
  - Both ultimately call the exact same
    `EngineOrchestrator.compute_gap_analysis()` method, so the readiness
    score for a given (student, job) pair is byte-for-byte identical no
    matter which route computed it (test-plan.md B7#7).
  - A student with no target role set (and no `?target_job_id=` override)
    gets a defined, non-error empty state (`readiness_score: 0`, empty
    matched/missing, a message explaining why) -- never a 404/500, since
    this route is meant to be safe to call from the moment a student logs
    in, before they've picked a target role.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser, get_current_user, get_graph_service, get_orchestrator
from app.core.responses import AppError, envelope
from app.database.postgres import get_db
from app.engine.orchestrator import EngineOrchestrator
from app.routers._shared import resolve_target_job_id
from app.services.graph_service import GraphService

router = APIRouter(prefix="/skills", tags=["skills"])


@router.get("")
def list_skills(
    search: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    graph_service: GraphService = Depends(get_graph_service),
):
    return envelope(data=graph_service.list_skill_names(search=search, limit=limit))


@router.get("/market")
def skill_market(
    current: CurrentUser = Depends(get_current_user),
    orchestrator: EngineOrchestrator = Depends(get_orchestrator),
):
    return envelope(data=orchestrator.get_skill_demand())


@router.get("/gap")
def skill_gap(
    target_job_id: str | None = Query(default=None),
    current: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    graph_service: GraphService = Depends(get_graph_service),
    orchestrator: EngineOrchestrator = Depends(get_orchestrator),
):
    resolved_job_id = target_job_id
    if resolved_job_id:
        # Explicitly supplied -> validate it exists, mirroring POST
        # /gap-analysis's contract exactly.
        if graph_service.get_job(resolved_job_id) is None:
            raise AppError("NOT_FOUND", f"Job {resolved_job_id} does not exist.", 404)
    else:
        resolved_job_id = resolve_target_job_id(db, current.id)

    if resolved_job_id is None:
        return envelope(
            data={
                "target_job_id": None,
                "readiness_score": 0,
                "matched_skills": [],
                "missing_skills": [],
                "explanation": "You haven't set a target role yet, so there's nothing to compare your skills against.",
                "encouragement": "Add a target role in your Profile to see a personalized skill gap analysis.",
                "roadmap": [],
            },
            message="No target role set.",
        )

    result = orchestrator.compute_gap_analysis(current.id, resolved_job_id)
    return envelope(data=result)
