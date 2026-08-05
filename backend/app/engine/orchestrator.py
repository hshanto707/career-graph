"""EngineOrchestrator — module B6/B7 (system-design.md §9.6).

Coordinates the four algorithmic agents (SkillGapAgent, RecommendationAgent,
PathFinderAgent, MarketAgent) and the optional ReasoningAgent for every
student-facing route, per the §9.6 flowchart:

    1. Run the relevant algorithmic agent(s) -- always, deterministically,
       zero network calls.
    2. Check whether an LLM provider is configured (`Settings.LLM_PROVIDER`).
    3. If yes, ask the `ReasoningAgent` to narrate the algorithmic result. If
       that call fails for *any* reason (misconfiguration, timeout, malformed
       output after retries, or literally any other exception) -- catch it
       and fall back to template narratives. **An LLM failure must never
       propagate as a 500** to a route caller.
    4. If no LLM is configured, skip straight to template narratives.

Every "narrative" method below (`_gap_narrative`, `_roadmap_narrative`,
`_recommendation_narratives`, `_market_narrative`) follows this same
try-LLM-then-fall-back-to-template shape. The template strings are real,
written-out, non-empty copy -- not placeholders -- because the frontend (and
the demo) must never show a blank explanation just because no LLM key is
configured.
"""
from __future__ import annotations

import logging
from typing import Any

from app.core.config import Settings, get_settings
from app.engine.algorithmic.market_agent import DemandData, MarketAgent
from app.engine.algorithmic.path_finder_agent import LearningPath, PathFinderAgent
from app.engine.algorithmic.recommendation_agent import RankedJob, RecommendationAgent
from app.engine.algorithmic.skill_gap_agent import GapResult, SkillGapAgent
from app.engine.llm.base import LLMProvider
from app.engine.llm.factory import create_llm_provider
from app.engine.reasoning.reasoning_agent import ReasoningAgent

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Template-narrative defaults (used whenever no LLM is configured, or the LLM
# call fails after exhausting its retries -- see module docstring).
# --------------------------------------------------------------------------- #
DEFAULT_SKILL_LEARNING_WEEKS = 4


class EngineOrchestrator:
    """Coordinates algorithmic agents + the optional ReasoningAgent for every
    student-facing route. One instance is created per request (see
    `app.core.deps.get_orchestrator`); construction is cheap -- the agents are
    pure Python and the LLM provider (if any) is built lazily on first use.
    """

    def __init__(
        self,
        graph_service: Any,
        settings: Settings | None = None,
        llm_provider: LLMProvider | None = None,
    ):
        """
        Args:
            graph_service: anything implementing the `GraphService` method
                surface (the real Neo4j-backed one, or `FakeGraphService` in
                tests) -- duck-typed, never imported concretely here.
            settings: defaults to `get_settings()`. Passed explicitly in
                tests that want to force a particular `LLM_PROVIDER` without
                mutating process-wide environment state.
            llm_provider: an already-constructed `LLMProvider` to use
                instead of building one from `settings`. This is the seam
                tests use to simulate "LLM configured but raises after
                retries" (B6 #5) without touching real environment/factory
                plumbing.
        """
        self.graph = graph_service
        self.settings = settings or get_settings()
        self._explicit_llm_provider = llm_provider
        self._reasoning_agent_cache: ReasoningAgent | None | bool = False  # False = not computed yet

        self.skill_gap_agent = SkillGapAgent()
        self.recommendation_agent = RecommendationAgent()
        self.path_finder_agent = PathFinderAgent()
        self.market_agent = MarketAgent()

    # ------------------------------------------------------------------ #
    # LLM configuration / ReasoningAgent construction
    # ------------------------------------------------------------------ #
    def _reasoning_agent(self) -> ReasoningAgent | None:
        """Returns a `ReasoningAgent` if an LLM is configured and constructs
        successfully, else `None`. Never raises -- a construction failure
        (missing API key, unknown provider name) is treated identically to
        "no LLM configured": skip straight to template narratives.
        """
        if self._reasoning_agent_cache is not False:
            return self._reasoning_agent_cache  # type: ignore[return-value]

        provider = self._explicit_llm_provider
        if provider is None:
            provider_name = (self.settings.LLM_PROVIDER or "none").strip().lower()
            if provider_name in ("", "none"):
                self._reasoning_agent_cache = None
                return None
            try:
                api_key = None
                if provider_name == "claude":
                    api_key = self.settings.ANTHROPIC_API_KEY
                elif provider_name == "openai":
                    api_key = self.settings.OPENAI_API_KEY
                provider = create_llm_provider(
                    provider_name,
                    model=self.settings.LLM_MODEL,
                    api_key=api_key,
                    base_url=self.settings.OLLAMA_BASE_URL,
                )
            except Exception:  # noqa: BLE001 - any construction failure -> no LLM
                logger.warning("LLM provider %r failed to construct; falling back to templates.", provider_name)
                self._reasoning_agent_cache = None
                return None

        agent = ReasoningAgent(provider)
        self._reasoning_agent_cache = agent
        return agent

    # ------------------------------------------------------------------ #
    # Skill gap analysis (shared by POST /gap-analysis and GET /skills/gap)
    # ------------------------------------------------------------------ #
    def _compute_gap_result(self, student_id: str, target_job_id: str) -> GapResult:
        student_skills = self.graph.get_student_skills(student_id)
        required_skills = self.graph.get_job_required_skills(target_job_id)
        return self.skill_gap_agent.compute_gap(student_skills, required_skills)

    def _compute_learning_path(self, gap_result: GapResult) -> LearningPath:
        missing_names = [m["name"] for m in gap_result.missing_skills]
        if not missing_names:
            return LearningPath(milestones=[])
        leads_to_edges = self.graph.get_leads_to_graph()
        courses = self.graph.get_teaches_courses(missing_names)
        return self.path_finder_agent.find_path(missing_names, leads_to_edges, courses)

    def compute_gap_analysis(self, student_id: str, target_job_id: str) -> dict[str, Any]:
        """Full `GapAnalysisResponse` (+ roadmap) for one student/job pair.

        This is the single method both `POST /gap-analysis` and
        `GET /skills/gap` call -- guaranteeing identical readiness scores for
        the same (student, job) pair per test-plan.md B7#7, and resolving
        features-todo.md's open decision #2 (see
        docs/algorithmic-agents-decisions.md).
        """
        gap_result = self._compute_gap_result(student_id, target_job_id)
        learning_path = self._compute_learning_path(gap_result)

        narrative = self._gap_narrative(gap_result)
        roadmap = self._roadmap_narrative(learning_path)

        return {
            "target_job_id": target_job_id,
            "readiness_score": round(gap_result.readiness_score),
            "matched_skills": gap_result.matched_skills,
            "missing_skills": narrative["missing_skills"],
            "explanation": narrative["explanation"],
            "encouragement": narrative["encouragement"],
            "roadmap": roadmap["weekly_milestones"],
        }

    def _gap_narrative(self, gap_result: GapResult) -> dict[str, Any]:
        ra = self._reasoning_agent()
        if ra is not None:
            try:
                explanation = ra.explain_gap(
                    {
                        "readiness_score": gap_result.readiness_score,
                        "matched_skills": gap_result.matched_skills,
                        "missing_skills": gap_result.missing_skills,
                        "must_matched": gap_result.must_matched,
                        "must_total": gap_result.must_total,
                        "nice_matched": gap_result.nice_matched,
                        "nice_total": gap_result.nice_total,
                    }
                )
                return {
                    "explanation": explanation.explanation,
                    "encouragement": explanation.encouragement,
                    "missing_skills": [m.model_dump() for m in explanation.missing_skills],
                }
            except Exception:  # noqa: BLE001 - LLM failure must never surface as a 500
                logger.warning("ReasoningAgent.explain_gap() failed; falling back to template narrative.")
        return self._template_gap_narrative(gap_result)

    def _template_gap_narrative(self, gap_result: GapResult) -> dict[str, Any]:
        pct = round(gap_result.readiness_score)
        total_required = gap_result.must_total + gap_result.nice_total
        total_matched = gap_result.must_matched + gap_result.nice_matched

        explanation = (
            f"Based on your skills, you match {pct}% of required skills for this role. "
            f"You currently have {total_matched} of {total_required} required skills "
            f"({gap_result.must_matched}/{gap_result.must_total} must-have skills and "
            f"{gap_result.nice_matched}/{gap_result.nice_total} nice-to-have skills)."
        )
        if gap_result.missing_skills:
            encouragement = (
                "You're making solid progress. Focus on the missing skills below one at a "
                "time, starting with the must-have ones, and your readiness score will keep "
                "climbing."
            )
        else:
            encouragement = (
                "You already match every skill required for this role -- great work! "
                "Consider applying now or exploring an even more advanced target role."
            )

        missing_skills = [
            {
                "skill_name": m["name"],
                "importance": m.get("importance", "nice"),
                "estimated_learning_weeks": DEFAULT_SKILL_LEARNING_WEEKS,
            }
            for m in gap_result.missing_skills
        ]
        return {"explanation": explanation, "encouragement": encouragement, "missing_skills": missing_skills}

    def _roadmap_narrative(self, learning_path: LearningPath) -> dict[str, Any]:
        ra = self._reasoning_agent()
        if ra is not None and learning_path.milestones:
            try:
                plan = ra.write_roadmap(
                    {
                        "milestones": [
                            {
                                "skill_name": m.skill_name,
                                "weeks_estimate": m.weeks_estimate,
                                "courses": m.courses,
                            }
                            for m in learning_path.milestones
                        ]
                    }
                )
                return {"weekly_milestones": [ms.model_dump() for ms in plan.weekly_milestones]}
            except Exception:  # noqa: BLE001 - LLM failure must never surface as a 500
                logger.warning("ReasoningAgent.write_roadmap() failed; falling back to template roadmap.")
        return self._template_roadmap(learning_path)

    def _template_roadmap(self, learning_path: LearningPath) -> dict[str, Any]:
        milestones: list[dict[str, Any]] = []
        week_cursor = 1
        for m in learning_path.milestones:
            start = week_cursor
            end = week_cursor + max(m.weeks_estimate, 1) - 1
            course = m.courses[0] if m.courses else {}
            milestones.append(
                {
                    "week_range": f"Week {start}-{end}",
                    "skill_name": m.skill_name,
                    "course_title": course.get("title"),
                    "course_url": course.get("url"),
                    "goal": f"Build working proficiency in {m.skill_name}.",
                }
            )
            week_cursor = end + 1
        return {"weekly_milestones": milestones}

    # ------------------------------------------------------------------ #
    # Recommendations
    # ------------------------------------------------------------------ #
    def get_job_recommendations(self, student_id: str, limit: int = 10) -> list[dict[str, Any]]:
        student_skills = self.graph.get_student_skills(student_id)
        all_jobs = self.graph.get_all_jobs_with_requires()
        leads_to = self.graph.get_leads_to_graph()
        ranked = self.recommendation_agent.rank_jobs(student_skills, all_jobs, leads_to)
        top20 = ranked[:20]

        narratives = self._recommendation_narratives(top20)

        results: list[dict[str, Any]] = []
        for r in top20[:limit]:
            results.append(
                {
                    "job_id": r.job_id,
                    "title": r.title,
                    "match_percentage": round(r.final_score * 100, 2),
                    "matched_skills": r.matched_skills,
                    "why_recommended": narratives.get(r.job_id) or self._template_why_recommended(r),
                }
            )
        return results

    def _recommendation_narratives(self, ranked_jobs: list[RankedJob]) -> dict[str, str]:
        if not ranked_jobs:
            return {}
        ra = self._reasoning_agent()
        if ra is not None:
            try:
                out = ra.narrate_recommendations(
                    [
                        {
                            "job_id": r.job_id,
                            "title": r.title,
                            "final_score": r.final_score,
                            "matched_skills": r.matched_skills,
                        }
                        for r in ranked_jobs
                    ]
                )
                return {n.job_id: n.why_recommended for n in out.narratives}
            except Exception:  # noqa: BLE001 - LLM failure must never surface as a 500
                logger.warning("ReasoningAgent.narrate_recommendations() failed; falling back to templates.")
        return {}

    @staticmethod
    def _template_why_recommended(ranked_job: RankedJob) -> str:
        pct = round(ranked_job.final_score * 100)
        if ranked_job.matched_skills:
            skills_str = ", ".join(ranked_job.matched_skills[:3])
            return (
                f"Recommended because you already match {pct}% of the skills required for "
                f"this role, including {skills_str}."
            )
        return f"Recommended based on an overall skill fit of {pct}% with this role."

    def get_skill_recommendations(self, student_id: str, limit: int = 10) -> list[dict[str, Any]]:
        """Skills the student doesn't yet have, ranked by market demand."""
        student_names = self._student_skill_names(student_id)
        demand = self._demand_data()
        recs = [
            {
                "skill_name": sd.skill_name,
                "demand_score": sd.demand_score,
                "demand_count": sd.demand_count,
            }
            for sd in demand.skill_demand
            if sd.skill_name.strip().lower() not in student_names
        ]
        return recs[:limit]

    def get_course_recommendations(
        self, student_id: str, target_job_id: str | None = None, limit: int = 10
    ) -> list[dict[str, Any]]:
        """Courses teaching skills the student is missing -- scoped to
        `target_job_id`'s required skills if given, else the highest-demand
        missing skills across the whole market."""
        student_names = self._student_skill_names(student_id)

        if target_job_id:
            required = self.graph.get_job_required_skills(target_job_id)
            missing = [
                r["name"] for r in required if r.get("name", "").strip().lower() not in student_names
            ]
        else:
            demand = self._demand_data()
            missing = [
                sd.skill_name
                for sd in demand.skill_demand
                if sd.skill_name.strip().lower() not in student_names
            ][:10]

        if not missing:
            return []

        courses = self.graph.get_teaches_courses(missing)
        seen: set[tuple[Any, Any]] = set()
        out: list[dict[str, Any]] = []
        for c in courses:
            key = (c.get("id"), c.get("skill_name"))
            if key in seen:
                continue
            seen.add(key)
            out.append(
                {
                    "course_id": c.get("id"),
                    "title": c.get("title"),
                    "provider": c.get("provider"),
                    "url": c.get("url"),
                    "duration": c.get("duration"),
                    "free": c.get("free", False),
                    "skill_name": c.get("skill_name"),
                }
            )
        return out[:limit]

    def _student_skill_names(self, student_id: str) -> set[str]:
        student_skills = self.graph.get_student_skills(student_id)
        return {s["name"].strip().lower() for s in student_skills if s.get("name")}

    # ------------------------------------------------------------------ #
    # Market
    # ------------------------------------------------------------------ #
    def _demand_data(self) -> DemandData:
        all_jobs = self.graph.get_all_jobs_with_requires()
        return self.market_agent.aggregate_demand(all_jobs)

    def get_skill_demand(self) -> list[dict[str, Any]]:
        """Pure algorithmic output (no LLM narrative) -- backs
        `GET /skills/market`."""
        demand = self._demand_data()
        return [
            {
                "skill_name": sd.skill_name,
                "demand_count": sd.demand_count,
                "demand_score": sd.demand_score,
                "trend": sd.trend,
            }
            for sd in demand.skill_demand
        ]

    def get_market_insights(self, top_n: int = 10) -> dict[str, Any]:
        """LLM-narrated market summary -- backs `GET /market/insights`."""
        demand = self._demand_data()
        top_skills = [
            {
                "skill_name": sd.skill_name,
                "demand_count": sd.demand_count,
                "demand_score": sd.demand_score,
                "trend": sd.trend,
            }
            for sd in demand.skill_demand[:top_n]
        ]
        narrative = self._market_narrative(demand)
        return {
            "top_skills": top_skills,
            "trend_bullets": narrative["trend_bullets"],
            "summary": narrative["summary"],
        }

    def _market_narrative(self, demand: DemandData) -> dict[str, Any]:
        ra = self._reasoning_agent()
        if ra is not None and demand.skill_demand:
            try:
                out = ra.summarize_market(
                    {
                        "skill_demand": [
                            {
                                "skill_name": sd.skill_name,
                                "demand_score": sd.demand_score,
                                "demand_count": sd.demand_count,
                                "trend": sd.trend,
                            }
                            for sd in demand.skill_demand
                        ],
                        "trending_skills": demand.trending_skills,
                    }
                )
                return {"trend_bullets": out.trend_bullets, "summary": out.market_summary}
            except Exception:  # noqa: BLE001 - LLM failure must never surface as a 500
                logger.warning("ReasoningAgent.summarize_market() failed; falling back to template summary.")
        return self._template_market_narrative(demand)

    @staticmethod
    def _template_market_narrative(demand: DemandData) -> dict[str, Any]:
        if not demand.skill_demand:
            return {
                "trend_bullets": [
                    "No market data is available yet -- run the ingestion pipeline to load job postings.",
                    "Once postings are ingested, the top in-demand skills will appear here.",
                    "In the meantime, complete your profile so gap analysis is ready as soon as data loads.",
                ],
                "summary": "Market data is not yet available for this dataset.",
            }

        top3 = demand.skill_demand[:3]
        bullets = [
            f"{sd.skill_name} is the most in-demand skill in the current dataset, "
            f"with a demand score of {round(sd.demand_score)}."
            if i == 0
            else f"{sd.skill_name} ranks #{i + 1} in overall market demand."
            for i, sd in enumerate(top3)
        ]
        while len(bullets) < 3:
            bullets.append("More trend data will appear as additional postings are ingested.")

        summary = (
            f"Across {len(demand.skill_demand)} tracked skills, {top3[0].skill_name} leads "
            "current market demand in this dataset."
        )
        return {"trend_bullets": bullets[:3], "summary": summary}

    # ------------------------------------------------------------------ #
    # Dashboard
    # ------------------------------------------------------------------ #
    def get_dashboard(self, student_id: str, target_job_id: str | None = None) -> dict[str, Any]:
        """Purely algorithmic (per system-design.md §9.1: "dashboard is
        largely algorithmic") -- no LLM narrative is fetched here, so a
        missing/misconfigured LLM can never affect this route at all.

        `target_job_id` is resolved by the router the same way
        `GET /skills/gap` resolves it (student's most-recently-added target
        role), so `job_readiness_score`/`skills_matched` are guaranteed
        numerically identical to what `GET /skills/gap` reports for the same
        student -- test-plan.md B7#10.
        """
        market_top_skills = self.get_skill_demand()[:5]

        if target_job_id:
            gap_result = self._compute_gap_result(student_id, target_job_id)
        else:
            gap_result = GapResult(readiness_score=0.0, matched_skills=[], missing_skills=[])

        total_required = gap_result.must_total + gap_result.nice_total
        total_matched = gap_result.must_matched + gap_result.nice_matched
        missing_names = {m["name"].strip().lower() for m in gap_result.missing_skills}

        missing_high_demand = [
            sd["skill_name"] for sd in market_top_skills if sd["skill_name"].strip().lower() in missing_names
        ]

        # "Skills You Have" in the dashboard's Skill Gap Analysis widget must
        # reflect the student's *actual* HAS_SKILL edges -- not merely "not
        # flagged as missing for the current target job". A market-top skill
        # the student never listed, but that also isn't required by their
        # target job (or no target job is set at all), is neither matched nor
        # missing and must not be silently presented as owned.
        student_skill_names = {
            s["name"].strip().lower()
            for s in self.graph.get_student_skills(student_id)
            if s.get("name")
        }
        matched_market_skills = [
            sd["skill_name"] for sd in market_top_skills if sd["skill_name"].strip().lower() in student_skill_names
        ]

        return {
            "job_readiness_score": round(gap_result.readiness_score),
            "skills_matched": total_matched,
            "total_required_skills": total_required,
            "missing_high_demand_skills": missing_high_demand,
            "matched_market_skills": matched_market_skills,
            "market_demand": market_top_skills,
        }
