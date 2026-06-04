"""
EngineOrchestrator — Routes API requests to the correct intelligence agents.

The orchestrator is the single entry point for all intelligence operations.
It coordinates: GraphService (data), algorithmic agents (scoring), and
ReasoningAgent (LLM explanations). Designed for easy explanation to faculty.
"""
import logging
from app.engine.algorithmic.skill_gap_agent import SkillGapAgent
from app.engine.algorithmic.recommendation_agent import RecommendationAgent
from app.engine.algorithmic.path_finder_agent import PathFinderAgent
from app.engine.algorithmic.market_agent import MarketAgent
from app.engine.reasoning.reasoning_agent import ReasoningAgent
from app.engine.llm.base import LLMProvider

logger = logging.getLogger(__name__)


class EngineOrchestrator:
    """
    Central coordinator for the CareerGraph Intelligence Engine.

    Wires together:
    - GraphService (Neo4j data access)
    - Algorithmic agents (SkillGap, Recommendation, PathFinder, Market)
    - ReasoningAgent (optional LLM layer for explanations)

    If llm_provider is None, all operations still work with template responses.
    """

    def __init__(self, graph_service, llm_provider: LLMProvider | None = None):
        self.graph = graph_service
        self.skill_gap_agent = SkillGapAgent()
        self.recommendation_agent = RecommendationAgent()
        self.path_finder_agent = PathFinderAgent()
        self.market_agent = MarketAgent()
        self.reasoning_agent = ReasoningAgent(llm_provider=llm_provider)

    async def get_recommendations(self, user_id: str, top_n: int = 20) -> list[dict]:
        """
        Get ranked job recommendations for a student.

        1. Load student skills from Neo4j
        2. Load all jobs from Neo4j
        3. Rank with RecommendationAgent (Jaccard similarity)
        4. Return top_n results as dicts
        """
        raw_skills = await self.graph.get_student_skills(user_id)
        student_skills = {s["name"] for s in raw_skills}
        jobs = await self.graph.get_all_jobs()
        recommendations = self.recommendation_agent.rank_jobs(student_skills, jobs, top_n=top_n)
        return [
            {
                "job_id": r.job_id,
                "title": r.title,
                "company": r.company,
                "location": r.location,
                "employment_type": r.employment_type,
                "salary_min": r.salary_min,
                "salary_max": r.salary_max,
                "score": r.score,
                "matched_skills": r.matched_skills,
                "missing_skills": r.missing_skills,
            }
            for r in recommendations
        ]

    async def analyze_gap(self, user_id: str, target_job_id: str, explain: bool = False) -> dict:
        """
        Analyze the skill gap between a student and a target job.

        1. Load student skills from Neo4j
        2. Load job requirements from Neo4j
        3. Compute gap with SkillGapAgent
        4. Optionally explain with ReasoningAgent
        """
        raw_skills = await self.graph.get_student_skills(user_id)
        student_skills = {s["name"]: s.get("proficiency", 5.0) for s in raw_skills}
        job = await self.graph.get_job_by_id(target_job_id)

        if not job:
            return {"error": f"Job {target_job_id} not found"}

        job_skills = job.get("skills_required", [])
        # Handle both flat list and list of dicts
        if job_skills and isinstance(job_skills[0], str):
            job_skills = [{"name": s, "importance": "must"} for s in job_skills]

        gap = self.skill_gap_agent.compute_gap(student_skills, job_skills)
        result = {
            "readiness_score": gap.readiness_score,
            "matched_skills": gap.matched_skills,
            "missing_skills": gap.missing_skills,
            "must_matched": gap.must_matched,
            "must_total": gap.must_total,
            "nice_matched": gap.nice_matched,
            "nice_total": gap.nice_total,
            "target_job_id": target_job_id,
            "target_job_title": job.get("title", ""),
        }

        if explain:
            narrative = await self.reasoning_agent.explain_gap(gap, job.get("title", ""))
            result.update(narrative)

        return result

    async def get_learning_path(self, user_id: str, target_job_id: str) -> dict:
        """
        Generate an ordered learning roadmap for a student.

        1. Get gap analysis to find missing skills
        2. Get prerequisite graph from Neo4j
        3. Build path with PathFinderAgent (BFS + topological sort)
        """
        gap_result = await self.analyze_gap(user_id, target_job_id)
        missing = gap_result.get("missing_skills", [])
        prereq_graph = await self.graph.get_prereq_graph()
        raw_skills = await self.graph.get_student_skills(user_id)
        student_skills = {s["name"] for s in raw_skills}

        path = self.path_finder_agent.build_learning_path(
            missing_skills=missing,
            prereq_graph=prereq_graph,
            student_skills=student_skills,
        )
        return {
            "milestones": path.milestones,
            "weeks_estimate": path.weeks_estimate,
            "total_skills": path.total_skills,
            "target_job_id": target_job_id,
        }

    async def get_market_insights(self) -> dict:
        """
        Get market-wide skill demand insights.

        Loads all jobs from Neo4j and aggregates with MarketAgent.
        """
        jobs = await self.graph.get_all_jobs()
        insights = self.market_agent.aggregate(jobs)
        return {
            "top_skills": insights.top_skills,
            "total_jobs": insights.total_jobs,
            "top_categories": insights.top_categories,
        }

    async def get_dashboard_stats(self, user_id: str) -> dict:
        """Get summary statistics for the student dashboard."""
        raw_skills = await self.graph.get_student_skills(user_id)
        jobs = await self.graph.get_all_jobs()
        insights = self.market_agent.aggregate(jobs)

        student_skills = {s["name"] for s in raw_skills}
        recs = self.recommendation_agent.rank_jobs(student_skills, jobs, top_n=5)
        top_readiness = recs[0].score * 100 if recs else 0

        return {
            "skills_count": len(raw_skills),
            "top_job_readiness": round(top_readiness, 1),
            "total_jobs_in_market": len(jobs),
            "top_demanded_skill": insights.top_skills[0]["name"] if insights.top_skills else "",
        }
