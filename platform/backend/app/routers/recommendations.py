"""
Recommendations router.

GET /api/v1/recommendations/jobs    — Top job matches for student (with LLM narration if configured)
GET /api/v1/recommendations/skills  — Skills to learn next
GET /api/v1/recommendations/courses — Courses for missing skills
"""
from fastapi import APIRouter, Query, Depends, Request
from app.database.neo4j import get_neo4j
from app.dependencies import get_current_user
from app.services.graph_service import GraphService
from app.engine.algorithmic.recommendation_agent import RecommendationAgent
from app.engine.reasoning.reasoning_agent import ReasoningAgent
from app.schemas.common import ok

router = APIRouter(prefix="/recommendations")


@router.get("/jobs")
async def recommend_jobs(
    request: Request,
    top_n: int = Query(20, ge=1, le=50),
    current_user=Depends(get_current_user),
    neo4j_session=Depends(get_neo4j),
):
    """Get top job recommendations ranked by skill overlap, with why_recommended narrative."""
    svc = GraphService(neo4j_session)
    try:
        raw_skills = await svc.get_student_skills(str(current_user.id))
        student_skills = {s["name"] for s in raw_skills}
        jobs = await svc.get_all_jobs()
        recommendations = RecommendationAgent().rank_jobs(student_skills, jobs, top_n=top_n)
        result = [
            {
                "job_id": r.job_id, "title": r.title, "company": r.company,
                "location": r.location, "employment_type": r.employment_type,
                "salary_min": r.salary_min, "salary_max": r.salary_max,
                "score": r.score, "matched_skills": r.matched_skills,
                "missing_skills": r.missing_skills,
            }
            for r in recommendations
        ]
    except Exception:
        result = []

    # Add why_recommended to each job (template or LLM)
    llm_provider = getattr(request.app.state, "llm_provider", None)
    result = await ReasoningAgent(llm_provider).narrate_recommendations(result)

    return ok({"recommendations": result})


@router.get("/skills")
async def recommend_skills(
    current_user=Depends(get_current_user),
    neo4j_session=Depends(get_neo4j),
):
    """Recommend the most valuable skills to learn next."""
    svc = GraphService(neo4j_session)
    try:
        raw_skills = await svc.get_student_skills(str(current_user.id))
        student_skill_names = {s["name"] for s in raw_skills}
        jobs = await svc.get_all_jobs()
        from app.engine.algorithmic.market_agent import MarketAgent
        insights = MarketAgent().aggregate(jobs)
        recommended = [
            s for s in insights.top_skills
            if s["name"] not in student_skill_names
        ][:20]
    except Exception:
        recommended = []
    return ok({"recommended_skills": recommended})


@router.get("/courses")
async def recommend_courses(
    current_user=Depends(get_current_user),
    neo4j_session=Depends(get_neo4j),
):
    """Recommend courses for the student's top missing skills."""
    svc = GraphService(neo4j_session)
    try:
        raw_skills = await svc.get_student_skills(str(current_user.id))
        student_skill_names = {s["name"] for s in raw_skills}
        jobs = await svc.get_all_jobs()
        from app.engine.algorithmic.market_agent import MarketAgent
        insights = MarketAgent().aggregate(jobs)
        missing_skills = [s["name"] for s in insights.top_skills if s["name"] not in student_skill_names][:10]
        courses = await svc.get_courses_for_skills(missing_skills)
    except Exception:
        courses = []
    return ok({"courses": courses})
