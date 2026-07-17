"""market router — module B7.

GET /market/insights -> top skills, trend bullets, summary (LLM-narrated
when configured, template narrative otherwise -- see EngineOrchestrator).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.deps import CurrentUser, get_current_user, get_orchestrator
from app.core.responses import envelope
from app.engine.orchestrator import EngineOrchestrator

router = APIRouter(prefix="/market", tags=["market"])


@router.get("/insights")
def market_insights(
    current: CurrentUser = Depends(get_current_user),
    orchestrator: EngineOrchestrator = Depends(get_orchestrator),
):
    return envelope(data=orchestrator.get_market_insights())
