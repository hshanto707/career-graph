"""
Gap Analysis router.

POST /api/v1/gap-analysis — Full skill gap analysis + learning roadmap for a target job
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.database.neo4j import get_neo4j
from app.dependencies import get_current_user
from app.services.graph_service import GraphService
from app.engine.algorithmic.skill_gap_agent import SkillGapAgent
from app.engine.algorithmic.path_finder_agent import PathFinderAgent
from app.engine.reasoning.reasoning_agent import ReasoningAgent
from app.schemas.gap_analysis import GapAnalysisRequest
from app.schemas.common import ok

router = APIRouter(prefix="/gap-analysis")


@router.post("")
async def analyze_gap(
    request: Request,
    body: GapAnalysisRequest,
    current_user=Depends(get_current_user),
    neo4j_session=Depends(get_neo4j),
):
    """
    Compute a skill gap analysis for a target job, including a learning roadmap.

    When explain=true, also returns an LLM-generated explanation (if LLM is configured).
    """
    svc = GraphService(neo4j_session)
    try:
        raw_skills = await svc.get_student_skills(str(current_user.id))
        student_skills = {s["name"]: s["proficiency"] for s in raw_skills}
        student_skill_names = {s["name"] for s in raw_skills}
        job = await svc.get_job_by_id(body.target_job_id)
    except Exception:
        student_skills, student_skill_names, job = {}, set(), None

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{body.target_job_id}' not found",
        )

    job_skills = job.get("skills_required", [])
    if job_skills and isinstance(job_skills[0], str):
        job_skills = [{"name": s, "importance": "must"} for s in job_skills]
    elif job_skills and isinstance(job_skills[0], dict) and "name" not in job_skills[0]:
        job_skills = []

    gap = SkillGapAgent().compute_gap(student_skills, job_skills)

    # Build learning roadmap
    try:
        prereq_graph = await svc.get_prereq_graph()
    except Exception:
        prereq_graph = {}

    path = PathFinderAgent().build_learning_path(
        missing_skills=gap.missing_skills,
        prereq_graph=prereq_graph,
        student_skills=student_skill_names,
    )

    llm_provider = getattr(request.app.state, "llm_provider", None)
    reasoning_agent = ReasoningAgent(llm_provider)

    # LLM roadmap summary (template when no LLM)
    roadmap_data = await reasoning_agent.write_roadmap({
        "milestones": path.milestones,
        "weeks_estimate": path.weeks_estimate,
        "total_skills": path.total_skills,
    })

    # Optional LLM explanation
    reasoning_result: dict = {}
    if body.explain:
        reasoning_result = await reasoning_agent.explain_gap(gap, job.get("title", ""))

    return ok({
        "target_job_id": body.target_job_id,
        "target_job_title": job.get("title", ""),
        "readiness_score": gap.readiness_score,
        "matched_skills": gap.matched_skills,
        "missing_skills": gap.missing_skills,
        "must_matched": gap.must_matched,
        "must_total": gap.must_total,
        "nice_matched": gap.nice_matched,
        "nice_total": gap.nice_total,
        "roadmap": roadmap_data,
        **reasoning_result,
    })
