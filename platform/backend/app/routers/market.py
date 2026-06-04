"""
Market router — labor market trend insights.

GET /api/v1/market/insights — Market-wide skill demand (public)
"""
from fastapi import APIRouter, Depends
from app.database.neo4j import get_neo4j
from app.services.graph_service import GraphService
from app.engine.algorithmic.market_agent import MarketAgent
from app.schemas.common import ok

router = APIRouter(prefix="/market")


@router.get("/insights")
async def market_insights(neo4j_session=Depends(get_neo4j)):
    """Get market-wide skill demand trends. No auth required."""
    svc = GraphService(neo4j_session)
    try:
        jobs = await svc.get_all_jobs()
        insights = MarketAgent().aggregate(jobs)
        return ok({
            "total_jobs": insights.total_jobs,
            "top_skills": insights.top_skills[:30],
            "top_categories": insights.top_categories,
        })
    except Exception:
        return ok({"total_jobs": 0, "top_skills": [], "top_categories": []})
