"""
MarketAgent — Aggregates skill demand trends from job postings.

Algorithm:
    demand_count = number of jobs requiring this skill
    demand_score = normalized to 0-100 (max demand = 100)

No LLM required. Pure Python.
"""
from collections import Counter
from dataclasses import dataclass, field


@dataclass
class MarketInsights:
    """Aggregated market-wide skill demand data."""
    top_skills: list[dict]      # [{"name": str, "demand_count": int, "demand_score": float}]
    total_jobs: int
    top_categories: list[dict]  # [{"name": str, "job_count": int}]


class MarketAgent:
    """
    Aggregates skill demand from all available job postings.

    Produces a ranked list of skills by how frequently they appear
    in job requirements. This gives students a data-driven view
    of what employers actually want.
    """

    def aggregate(self, jobs: list[dict]) -> MarketInsights:
        """
        Aggregate skill demand across all job postings.

        Args:
            jobs: List of job dicts with 'skills_required' list.

        Returns:
            MarketInsights with sorted skill demand data.
        """
        if not jobs:
            return MarketInsights(top_skills=[], total_jobs=0, top_categories=[])

        skill_counter: Counter = Counter()
        category_counter: Counter = Counter()

        for job in jobs:
            skills = job.get("skills_required", [])
            for skill in skills:
                skill_counter[skill] += 1

            category = job.get("category", job.get("employment_type", "Other"))
            category_counter[category] += 1

        max_count = skill_counter.most_common(1)[0][1] if skill_counter else 1

        top_skills = [
            {
                "name": skill,
                "demand_count": count,
                "demand_score": round((count / max_count) * 100, 2),
            }
            for skill, count in skill_counter.most_common()
        ]

        top_categories = [
            {"name": cat, "job_count": count}
            for cat, count in category_counter.most_common(10)
        ]

        return MarketInsights(
            top_skills=top_skills,
            total_jobs=len(jobs),
            top_categories=top_categories,
        )
