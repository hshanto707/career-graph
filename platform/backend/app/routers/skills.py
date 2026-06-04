"""
Skills router — market demand and personal skill gap.

GET /api/v1/skills/market                    — Top demanded skills (public)
GET /api/v1/skills/gap?target_job_id=...     — Student's skill gap + roadmap (auth required)
"""
from fastapi import APIRouter, Query, Depends

from app.database.neo4j import get_neo4j
from app.dependencies import get_current_user
from app.services.graph_service import GraphService
from app.engine.algorithmic.skill_gap_agent import SkillGapAgent
from app.engine.algorithmic.path_finder_agent import PathFinderAgent
from app.engine.algorithmic.market_agent import MarketAgent
from app.schemas.common import ok

router = APIRouter(prefix="/skills")


@router.get("/market")
async def market_skills(neo4j_session=Depends(get_neo4j)):
    """Get the top demanded skills across all job postings. No auth required."""
    svc = GraphService(neo4j_session)
    try:
        jobs = await svc.get_all_jobs()
        insights = MarketAgent().aggregate(jobs)
        return ok({"top_skills": insights.top_skills[:50], "total_jobs": insights.total_jobs})
    except Exception:
        return ok({"top_skills": [], "total_jobs": 0})


@router.get("/gap")
async def skill_gap(
    target_job_id: str = Query(..., description="Job ID to analyze gap against"),
    current_user=Depends(get_current_user),
    neo4j_session=Depends(get_neo4j),
):
    """Compute skill gap and learning roadmap between student and a target job."""
    from fastapi import HTTPException, status
    svc = GraphService(neo4j_session)
    try:
        raw_skills = await svc.get_student_skills(str(current_user.id))
        student_skills = {s["name"]: s["proficiency"] for s in raw_skills}
        job = await svc.get_job_by_id(target_job_id)
    except Exception:
        student_skills, job = {}, None

    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job '{target_job_id}' not found")

    job_skills = job.get("skills_required", [])
    if job_skills and isinstance(job_skills[0], str):
        job_skills = [{"name": s, "importance": "must"} for s in job_skills]

    gap = SkillGapAgent().compute_gap(student_skills, job_skills)

    try:
        prereq_graph = await svc.get_prereq_graph()
    except Exception:
        prereq_graph = {}

    path = PathFinderAgent().build_learning_path(
        missing_skills=gap.missing_skills,
        prereq_graph=prereq_graph,
        student_skills=set(student_skills.keys()),
    )

    return ok({
        "readiness_score": gap.readiness_score,
        "matched_skills": gap.matched_skills,
        "missing_skills": gap.missing_skills,
        "must_matched": gap.must_matched,
        "must_total": gap.must_total,
        "roadmap": {
            "milestones": path.milestones,
            "weeks_estimate": path.weeks_estimate,
            "total_skills": path.total_skills,
        },
    })
