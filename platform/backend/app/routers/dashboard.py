"""
Dashboard router — personalized student stats.

GET /api/v1/dashboard — Summary stats for the authenticated student
"""
from fastapi import APIRouter, Depends
from app.database.neo4j import get_neo4j
from app.dependencies import get_current_user
from app.services.graph_service import GraphService
from app.engine.algorithmic.recommendation_agent import RecommendationAgent
from app.engine.algorithmic.market_agent import MarketAgent
from app.schemas.common import ok

router = APIRouter(prefix="/dashboard")


@router.get("")
async def get_dashboard(
    current_user=Depends(get_current_user),
    neo4j_session=Depends(get_neo4j),
):
    """Get personalized dashboard statistics for the authenticated student."""
    svc = GraphService(neo4j_session)
    try:
        raw_skills = await svc.get_student_skills(str(current_user.id))
        jobs = await svc.get_all_jobs()
        insights = MarketAgent().aggregate(jobs)
        student_skills = {s["name"] for s in raw_skills}
        recs = RecommendationAgent().rank_jobs(student_skills, jobs, top_n=5)
        top_readiness = round(recs[0].score * 100, 1) if recs else 0.0
        top_demanded = insights.top_skills[0]["name"] if insights.top_skills else ""
    except Exception:
        raw_skills, top_readiness, top_demanded = [], 0.0, ""
        jobs = []

    return ok({
        "skills_count": len(raw_skills),
        "top_job_readiness": top_readiness,
        "total_jobs_in_market": len(jobs),
        "top_demanded_skill": top_demanded,
    })
