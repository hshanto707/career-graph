"""
ReasoningAgent — Wraps algorithmic outputs in natural language explanations.

Sits on top of the algorithmic agents and uses a pluggable LLM provider
to generate human-friendly explanations. Degrades gracefully to template
responses when no LLM is configured or when LLM calls fail.
"""
import json
import logging
from app.engine.llm.base import LLMProvider
from app.engine.algorithmic.skill_gap_agent import GapResult

logger = logging.getLogger(__name__)


class ReasoningAgent:
    """
    Generates natural language explanations for algorithmic outputs.

    The LLM layer is strictly additive — it never affects the underlying
    scores or rankings. If the LLM fails, template responses are used.
    """

    def __init__(self, llm_provider: LLMProvider | None = None):
        self.llm = llm_provider

    async def explain_gap(self, gap: GapResult, target_job_title: str) -> dict:
        """
        Generate a plain-English explanation of the skill gap.

        Returns dict with: explanation, encouragement, weeks_to_learn
        Also logs the (prompt, completion) pair for training data collection.
        """
        if self.llm is None:
            return self._template_gap_explanation(gap, target_job_title)

        system = (
            "You are a career coach. Given a student's skill gap analysis, "
            "provide a brief, encouraging explanation in JSON format with keys: "
            "'explanation' (2-3 sentences about the gap), "
            "'encouragement' (1 motivating sentence), "
            "'weeks_to_learn' (estimated integer weeks to fill the gap)."
        )
        user = (
            f"Target job: {target_job_title}\n"
            f"Readiness score: {gap.readiness_score:.1f}/100\n"
            f"Matched skills: {', '.join(gap.matched_skills)}\n"
            f"Missing skills: {', '.join(gap.missing_skills)}"
        )

        raw = await self.llm.complete(system, user)
        result = self._parse_json_response(raw) or self._template_gap_explanation(gap, target_job_title)

        # M-03: Log training pair when LLM returns a result
        if raw:
            try:
                from app.engine.reasoning.training_logger import TrainingLogger
                TrainingLogger().log_pair(
                    prompt={"messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]},
                    completion=raw,
                )
            except Exception as exc:
                logger.debug(f"Training logger error: {exc}")

        return result

    async def narrate_recommendations(self, jobs: list[dict]) -> list[dict]:
        """
        Add why_recommended explanations to job recommendations.

        Args:
            jobs: List of job recommendation dicts with score and matched_skills.

        Returns:
            Same list with 'why_recommended' field added to each job.
        """
        result = []
        for job in jobs:
            narrative = {
                "why_recommended": (
                    f"Strong match based on {len(job.get('matched_skills', []))} overlapping skills."
                )
            }

            if self.llm:
                system = (
                    "You are a career advisor. In one sentence, explain why this job matches the student. "
                    "Return JSON: {'why_recommended': '...'}"
                )
                user = (
                    f"Job: {job.get('title')} at score {job.get('score', 0):.0%}. "
                    f"Matched skills: {', '.join(job.get('matched_skills', [])[:5])}"
                )
                raw = await self.llm.complete(system, user)
                parsed = self._parse_json_response(raw)
                if parsed and "why_recommended" in parsed:
                    narrative = parsed

            result.append({**job, **narrative})
        return result

    async def write_roadmap(self, learning_path: dict) -> dict:
        """Add narrative descriptions to a learning path."""
        if self.llm is None:
            return {
                **learning_path,
                "summary": (
                    f"Follow this {learning_path.get('weeks_estimate', 0)}-week "
                    "learning plan to fill your skill gaps."
                ),
            }

        system = "Summarize a learning roadmap in 2 sentences. Return JSON: {'summary': '...'}"
        user = (
            f"Learning path with {learning_path.get('total_skills', 0)} skills "
            f"over {learning_path.get('weeks_estimate', 0)} weeks."
        )
        raw = await self.llm.complete(system, user)
        parsed = self._parse_json_response(raw)
        summary = parsed.get("summary", "") if parsed else ""
        if not summary:
            summary = (
                f"Complete this {learning_path.get('weeks_estimate', 0)}-week "
                "plan to achieve your career goals."
            )
        return {**learning_path, "summary": summary}

    def _template_gap_explanation(self, gap: GapResult, job_title: str) -> dict:
        """Fallback template when LLM is unavailable."""
        if gap.missing_skills:
            explanation = (
                f"Your readiness for {job_title} is {gap.readiness_score:.1f}%. "
                f"You match {gap.must_matched}/{gap.must_total} required skills. "
                f"Key skills to acquire: {', '.join(gap.missing_skills[:3])}."
            )
        else:
            explanation = (
                f"Excellent! You match all requirements for {job_title} "
                f"with a readiness score of {gap.readiness_score:.1f}%."
            )
        return {
            "explanation": explanation,
            "encouragement": "Every expert was once a beginner. Keep building your skills!",
            "weeks_to_learn": len(gap.missing_skills) * 2,
        }

    def _parse_json_response(self, raw: str) -> dict | None:
        """Try to parse a JSON response from the LLM."""
        if not raw:
            return None
        try:
            cleaned = raw.strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                cleaned = "\n".join(
                    lines[1:-1] if lines[-1].strip() == "```" else lines[1:]
                )
            return json.loads(cleaned)
        except (json.JSONDecodeError, ValueError):
            return None
