"""MarketAgent — module B5.

Pure Python, deterministic. Aggregates `REQUIRES` edge counts per skill
across all jobs into a normalized 0-100 `demand_score`, per
system-design.md section 9.3.

--------------------------------------------------------------------------
Demand aggregation
--------------------------------------------------------------------------
    demand_score(skill) = (skill's REQUIRES count / max REQUIRES count
                            across all skills) * 100

Normalizing against the corpus max (rather than a fixed constant) keeps the
score meaningful regardless of dataset size (50-job demo seed vs. 10k-job
Kaggle corpus) -- the most in-demand skill in *this* dataset always scores
100, everything else scaled relative to it. An empty dataset (no REQUIRES
edges at all) returns an empty demand list, never divides by zero.

--------------------------------------------------------------------------
Open decision #5 — trend calculation without historical time-series data
--------------------------------------------------------------------------
The Neo4j schema (system-design.md §7.2) has no time-series/snapshot node
today, so a true "demand delta over time" is not yet possible in v1. This
agent implements the documented v1 proxy:

    - If the caller supplies `previous_demand_counts` (a prior ingestion
      run's skill -> REQUIRES-count snapshot, e.g. saved to a small JSON/DB
      row by the ingestion pipeline), trend = current_count - previous_count
      per skill, and "trending_skills" are those with trend > 0 sorted
      descending by trend.
    - If no previous snapshot is supplied (the common v1 case -- only one
      ingestion run exists so far), trend is explicitly reported as
      unavailable (`trend: None`) rather than a fabricated number, and
      "trending_skills" is empty. This is a deliberate, documented decision
      (see docs/algorithmic-agents-decisions.md) rather than silently
      returning zeros that would look like "no growth" instead of "unknown".
    - Future work (once multiple ingestion snapshots exist): switch to a
      proper recency-weighted multi-snapshot trend without changing this
      method's public contract.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

MAX_DEMAND_SCORE = 100.0


def _normalize_name(name: str) -> str:
    return name.strip().lower()


@dataclass
class SkillDemand:
    skill_name: str
    demand_count: int
    demand_score: float
    trend: int | None = None


@dataclass
class DemandData:
    skill_demand: list[SkillDemand] = field(default_factory=list)
    trending_skills: list[str] = field(default_factory=list)
    top_categories: list[str] = field(default_factory=list)


class MarketAgent:
    """Aggregates REQUIRES-edge demand across all jobs into normalized
    skill_demand scores. Pure Python -- takes plain lists/dicts fetched
    separately via GraphService.
    """

    def aggregate_demand(
        self,
        all_jobs: list[dict[str, Any]],
        previous_demand_counts: dict[str, int] | None = None,
        top_n_trending: int = 5,
    ) -> DemandData:
        """
        Args:
            all_jobs: [{"job_id": str, "title": str,
                        "required_skills": [{"name": str, ...}, ...]}, ...]
                (the same shape GraphService.get_all_jobs_with_requires()
                returns). Duplicate skill names *within* a single job are
                deduped so one job can't inflate a skill's REQUIRES count
                by listing it twice.
            previous_demand_counts: optional {normalized_skill_name: count}
                from a prior ingestion snapshot, see module docstring.
            top_n_trending: how many trending skills to surface.

        Returns:
            DemandData with demand_score in [0, 100], empty-safe on an
            empty dataset.
        """
        counts: dict[str, int] = {}
        display_name_by_key: dict[str, str] = {}

        for job in all_jobs or []:
            seen_in_job: set[str] = set()
            for skill in job.get("required_skills", []) or []:
                name = skill.get("name", "")
                key = _normalize_name(name)
                if not key or key in seen_in_job:
                    continue
                seen_in_job.add(key)
                counts[key] = counts.get(key, 0) + 1
                display_name_by_key.setdefault(key, name.strip())

        if not counts:
            return DemandData(skill_demand=[], trending_skills=[], top_categories=[])

        max_count = max(counts.values())

        previous_demand_counts = previous_demand_counts or {}
        skill_demand: list[SkillDemand] = []
        for key, count in counts.items():
            score = (count / max_count) * MAX_DEMAND_SCORE if max_count else 0.0
            trend: int | None = None
            if previous_demand_counts:
                prev = previous_demand_counts.get(key)
                if prev is not None:
                    trend = count - prev
            skill_demand.append(
                SkillDemand(
                    skill_name=display_name_by_key[key],
                    demand_count=count,
                    demand_score=round(score, 4),
                    trend=trend,
                )
            )

        # Sort by demand_score desc, tie-broken alphabetically for determinism.
        skill_demand.sort(key=lambda sd: (-sd.demand_score, sd.skill_name.lower()))

        trending_skills: list[str] = []
        if previous_demand_counts:
            positive_trend = [sd for sd in skill_demand if (sd.trend or 0) > 0]
            positive_trend.sort(key=lambda sd: (-(sd.trend or 0), sd.skill_name.lower()))
            trending_skills = [sd.skill_name for sd in positive_trend[:top_n_trending]]

        return DemandData(
            skill_demand=skill_demand,
            trending_skills=trending_skills,
            top_categories=[],
        )
