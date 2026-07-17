"""ReasoningAgent — module B6 (system-design.md §9.5).

Sits on top of **algorithmic** output (SkillGapAgent / RecommendationAgent /
PathFinderAgent / MarketAgent results) and asks a pluggable `LLMProvider` to
narrate it in plain English. It adds no unvalidated business logic of its
own: every method builds a prompt from structured input, calls
`LLMProvider.complete()` with a Pydantic output schema, and returns whatever
validated model comes back, unmodified. The algorithmic scores/rankings
themselves are never recomputed or second-guessed here.

The four output schemas below (`GapExplanation`, `RecommendationNarratives`,
`RoadmapPlan`, `MarketSummary`) are the contracts `LLMProvider.complete()`
validates against -- raw LLM text can never reach a caller of this module.

Note: the four algorithmic agents' own shared result schemas (`GapResult`,
`RankedJob`, `LearningPath`, `DemandData` per features-todo.md B5) have not
been finalized yet as of this phase, so the methods below accept plain
`dict`/`list` structures shaped like those future schemas. Once B5 lands its
typed schemas, the type hints here should be tightened to import them
directly -- the prompt-building logic itself will not need to change.
"""
from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, Field

from app.engine.llm.base import LLMProvider

# --------------------------------------------------------------------------- #
# Output schemas
# --------------------------------------------------------------------------- #


class MissingSkillExplanation(BaseModel):
    """One entry of `GapExplanation.missing_skills` -- mirrors
    system-design.md §16 `MissingSkill` plus the narrative gloss."""

    skill_name: str
    importance: str = Field(description="'must' or 'nice'")
    estimated_learning_weeks: int = Field(ge=0, description="Must be non-negative")


class GapExplanation(BaseModel):
    """Output of `ReasoningAgent.explain_gap()`."""

    explanation: str
    encouragement: str
    missing_skills: list[MissingSkillExplanation] = Field(default_factory=list)


class JobNarrative(BaseModel):
    """One re-ranked, narrated job within `RecommendationNarratives`."""

    job_id: str
    why_recommended: str


class RecommendationNarratives(BaseModel):
    """Output of `ReasoningAgent.narrate_recommendations()`."""

    narratives: list[JobNarrative] = Field(default_factory=list)


class Milestone(BaseModel):
    """One weekly milestone within `RoadmapPlan` -- mirrors
    system-design.md §16 `Milestone`."""

    week_range: str
    skill_name: str
    course_title: str | None = None
    course_url: str | None = None
    goal: str


class RoadmapPlan(BaseModel):
    """Output of `ReasoningAgent.write_roadmap()`."""

    weekly_milestones: list[Milestone] = Field(default_factory=list)


class MarketSummary(BaseModel):
    """Output of `ReasoningAgent.summarize_market()`."""

    trend_bullets: list[str] = Field(default_factory=list)
    market_summary: str
    highlight_skills: list[str] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# Prompt templates (kept as module-level constants, not scattered inline
# strings, per features-todo.md B6's TODO list)
# --------------------------------------------------------------------------- #

_GAP_SYSTEM_PROMPT = (
    "You are a supportive career coach for a university student. You are given "
    "an already-computed skill-gap analysis (readiness score, matched skills, "
    "missing skills) for a specific target job. Do not invent or change any "
    "score or skill list -- only explain it in plain, encouraging English and "
    "estimate how many weeks it would realistically take to learn each missing "
    "skill. Respond with JSON only, matching the required schema exactly."
)

_RECOMMENDATION_SYSTEM_PROMPT = (
    "You are a career advisor. You are given a list of jobs already ranked by "
    "an algorithmic recommendation score, along with the student's current "
    "skills. For each job, write one or two sentences explaining, from the "
    "student's own skills and gaps, why it was recommended. Do not change the "
    "ranking or invent new jobs. Respond with JSON only, matching the required "
    "schema exactly."
)

_ROADMAP_SYSTEM_PROMPT = (
    "You are a curriculum planner. You are given an already-computed, ordered "
    "learning path (skills in prerequisite order, with attached courses). "
    "Turn it into a week-by-week roadmap: assign a week range to each skill in "
    "the given order, keep the given course, and write one concrete weekly "
    "goal per milestone. Do not reorder or add skills. Respond with JSON only, "
    "matching the required schema exactly."
)

_MARKET_SYSTEM_PROMPT = (
    "You are a labor-market analyst. You are given already-computed skill "
    "demand data (demand scores and trends across job postings). Summarize it "
    "for a student audience: exactly three short trend bullets, one short "
    "overall summary paragraph, and the list of skills worth highlighting. Do "
    "not invent numbers not present in the data. Respond with JSON only, "
    "matching the required schema exactly."
)


class ReasoningAgent:
    """LLM-powered narrative layer over the algorithmic agents' output.

    Optional by design (per system-design.md §9.1): every method here is a
    thin pass-through to `LLMProvider.complete()`. Removing/disabling the LLM
    provider never breaks the algorithmic agents -- callers of this class
    (the EngineOrchestrator, in a later phase) are responsible for falling
    back to template narratives when no provider is configured or the
    provider ultimately fails.
    """

    def __init__(self, llm_provider: LLMProvider):
        self._llm = llm_provider

    # ------------------------------------------------------------------ #
    # M1 -- explain_gap
    # ------------------------------------------------------------------ #
    def explain_gap(self, gap_result: dict[str, Any], *, timeout: int = 30, retries: int = 2) -> GapExplanation:
        """Input: a `GapResult`-shaped dict from SkillGapAgent (+ optionally
        PathFinderAgent's missing-skill ordering). Output: `GapExplanation`
        -- explanation, encouragement, and missing skills with estimated
        weeks -- returned exactly as the provider produced it."""
        user_prompt = (
            "Skill gap analysis (already computed, do not recompute the "
            f"score or skill sets):\n{json.dumps(gap_result, default=str)}"
        )
        return self._llm.complete(
            _GAP_SYSTEM_PROMPT, user_prompt, GapExplanation, timeout=timeout, retries=retries
        )

    # ------------------------------------------------------------------ #
    # M2 -- narrate_recommendations
    # ------------------------------------------------------------------ #
    def narrate_recommendations(
        self, ranked_jobs: list[dict[str, Any]], *, timeout: int = 30, retries: int = 2
    ) -> RecommendationNarratives:
        """Input: `RankedJob[]`-shaped list from RecommendationAgent. Output:
        `why_recommended` narrative per job, returned exactly as the
        provider produced it (re-ranking, if any, happens on the LLM side of
        the schema -- this method does not reorder the input itself)."""
        user_prompt = (
            "Ranked job candidates (already scored, do not recompute "
            f"final_score):\n{json.dumps(ranked_jobs, default=str)}"
        )
        return self._llm.complete(
            _RECOMMENDATION_SYSTEM_PROMPT,
            user_prompt,
            RecommendationNarratives,
            timeout=timeout,
            retries=retries,
        )

    # ------------------------------------------------------------------ #
    # M3 -- write_roadmap
    # ------------------------------------------------------------------ #
    def write_roadmap(self, learning_path: dict[str, Any], *, timeout: int = 30, retries: int = 2) -> RoadmapPlan:
        """Input: `LearningPath`-shaped dict from PathFinderAgent (ordered
        skills + attached courses). Output: `RoadmapPlan` with weekly
        milestones, returned exactly as the provider produced it."""
        user_prompt = (
            "Ordered learning path (already computed via BFS + topological "
            f"sort, do not reorder):\n{json.dumps(learning_path, default=str)}"
        )
        return self._llm.complete(
            _ROADMAP_SYSTEM_PROMPT, user_prompt, RoadmapPlan, timeout=timeout, retries=retries
        )

    # ------------------------------------------------------------------ #
    # M4 -- summarize_market
    # ------------------------------------------------------------------ #
    def summarize_market(self, demand_data: dict[str, Any], *, timeout: int = 30, retries: int = 2) -> MarketSummary:
        """Input: `DemandData`-shaped dict from MarketAgent. Output:
        `MarketSummary` (trend bullets, summary, highlight skills), returned
        exactly as the provider produced it."""
        user_prompt = (
            "Market demand data (already aggregated, do not invent new "
            f"numbers):\n{json.dumps(demand_data, default=str)}"
        )
        return self._llm.complete(
            _MARKET_SYSTEM_PROMPT, user_prompt, MarketSummary, timeout=timeout, retries=retries
        )
