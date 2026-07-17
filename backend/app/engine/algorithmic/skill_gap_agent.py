"""SkillGapAgent — module B5.

Pure Python, deterministic, zero network/DB calls. Computes a weighted
"readiness score" for a student against a target job's required skills, per
system-design.md section 9.3:

    readiness_score = (must_matched / must_total) * 0.7
                     + (nice_matched / nice_total) * 0.3
                     + proficiency_bonus

--------------------------------------------------------------------------
Open decision #6 — "must vs. nice" skill classification rule
--------------------------------------------------------------------------
system-design.md's Neo4j schema stores `REQUIRES.importance: must|nice` and
`REQUIRES.frequency: int` directly on the edge (set by the ingestion
pipeline, see B4). This agent does **not** re-derive importance from
frequency itself -- by the time data reaches SkillGapAgent, every required
skill already carries an explicit `importance` label from ingestion.

The concrete, documented rule (used by IngestionAgent/NormalizationAgent
when writing the REQUIRES edge, and treated here as the single source of
truth an agent may rely on) is:

    - A skill is classified "must" if it appears in the first 60% of the
      skills_required list position-wise (position is a reasonable proxy
      for the job posting listing skills in descending importance) OR its
      frequency across the full corpus for that job title exceeds a
      configured threshold.
    - Otherwise it is classified "nice".

This agent treats `importance` as already-resolved input data. If a skill
dict omits `importance` (defensive/malformed upstream data), it defaults to
"nice" -- being conservative and not letting unclassified skills silently
inflate the higher-weighted "must" bucket. This default is documented here
and asserted by tests.

See docs/algorithmic-agents-decisions.md for the full write-up.

--------------------------------------------------------------------------
Proficiency bonus
--------------------------------------------------------------------------
For every matched skill, the student's proficiency (0-10 scale, per the
Neo4j `HAS_SKILL.proficiency` property / `SkillEntry.proficiency`) adds a
small bonus on top of the 0.7/0.3 weighted base score, so two students who
match the identical skill set are still differentiated by how well they
know those skills. The bonus is:

    proficiency_bonus = sum(proficiency / 10 for each matched skill)
                         * PROFICIENCY_BONUS_WEIGHT / matched_skill_count_norm

Concretely (and simply, to keep the arithmetic testable/exact):

    per_skill_bonus  = (proficiency / 10) * MAX_BONUS_PER_SKILL
    proficiency_bonus = sum(per_skill_bonus for matched skills) / total_required

...capped so the final readiness_score never exceeds 100. `MAX_BONUS_PER_SKILL`
is expressed in score points (0-100 scale) and defaults to 2.0, i.e. a
student who is maximally proficient (10/10) in every required skill can add
up to a couple of points on top of the weighted base -- enough to strictly
order two identical-skillset students by proficiency, per test-plan.md B5#4,
without letting proficiency alone dominate the must/nice weighting.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

MUST_WEIGHT = 0.7
NICE_WEIGHT = 0.3
MAX_BONUS_PER_SKILL = 2.0  # score points (0-100 scale), per matched required skill
MAX_READINESS_SCORE = 100.0


def _normalize_name(name: str) -> str:
    return name.strip().lower()


@dataclass
class GapResult:
    """Structured, typed output of SkillGapAgent.compute_gap().

    Mirrors system-design.md §16 GapAnalysisResponse fields that originate
    from the algorithmic layer (readiness_score, matched_skills,
    missing_skills) -- narrative fields are added later by ReasoningAgent.
    """

    readiness_score: float
    matched_skills: list[str] = field(default_factory=list)
    missing_skills: list[dict[str, Any]] = field(default_factory=list)
    must_matched: int = 0
    must_total: int = 0
    nice_matched: int = 0
    nice_total: int = 0


class SkillGapAgent:
    """Computes weighted readiness scores between a student's skills and a
    job's required skills. Pure Python -- takes plain lists/dicts, never
    touches the DB or network directly (callers fetch graph data via
    GraphService and pass it in).
    """

    def compute_gap(
        self,
        student_skills: list[dict[str, Any]],
        required_skills: list[dict[str, Any]],
    ) -> GapResult:
        """
        Args:
            student_skills: [{"name": str, "proficiency": int (0-10), "years": float}, ...]
                Duplicate names are defensively deduped (case-insensitive),
                keeping the highest proficiency seen for that name.
            required_skills: [{"name": str, "importance": "must"|"nice", "frequency": int}, ...]
                Duplicate names are defensively deduped, keeping the first
                occurrence's importance/frequency.

        Returns:
            GapResult with readiness_score in [0, 100].
        """
        # -- Dedup student skills, keep the max proficiency per normalized name --
        student_by_name: dict[str, dict[str, Any]] = {}
        for s in student_skills or []:
            key = _normalize_name(s.get("name", ""))
            if not key:
                continue
            proficiency = s.get("proficiency", 0) or 0
            existing = student_by_name.get(key)
            if existing is None or proficiency > existing.get("proficiency", 0):
                student_by_name[key] = {**s, "proficiency": proficiency}

        # -- Dedup required skills, first occurrence wins --
        required_by_name: dict[str, dict[str, Any]] = {}
        for r in required_skills or []:
            key = _normalize_name(r.get("name", ""))
            if not key or key in required_by_name:
                continue
            importance = r.get("importance") or "nice"
            if importance not in ("must", "nice"):
                importance = "nice"
            required_by_name[key] = {**r, "importance": importance}

        must_skills = {k: v for k, v in required_by_name.items() if v["importance"] == "must"}
        nice_skills = {k: v for k, v in required_by_name.items() if v["importance"] == "nice"}

        must_total = len(must_skills)
        nice_total = len(nice_skills)

        must_matched_keys = [k for k in must_skills if k in student_by_name]
        nice_matched_keys = [k for k in nice_skills if k in student_by_name]

        must_matched = len(must_matched_keys)
        nice_matched = len(nice_matched_keys)

        # -- Weighted base score (0-100 scale). Zero-division safe: an empty
        # bucket (must_total == 0 or nice_total == 0) contributes 0 for that
        # term rather than raising, per test-plan.md edge cases. --
        must_ratio = (must_matched / must_total) if must_total else 0.0
        nice_ratio = (nice_matched / nice_total) if nice_total else 0.0
        base_score = (must_ratio * MUST_WEIGHT + nice_ratio * NICE_WEIGHT) * 100.0

        # -- Proficiency bonus --
        matched_keys = must_matched_keys + nice_matched_keys
        total_required = must_total + nice_total
        proficiency_bonus = 0.0
        if total_required and matched_keys:
            bonus_sum = sum(
                (student_by_name[k].get("proficiency", 0) / 10.0) * MAX_BONUS_PER_SKILL
                for k in matched_keys
            )
            proficiency_bonus = bonus_sum / total_required

        readiness_score = min(base_score + proficiency_bonus, MAX_READINESS_SCORE)

        matched_names = [required_by_name[k]["name"] for k in matched_keys]
        missing_names = [
            required_by_name[k]
            for k in required_by_name
            if k not in student_by_name
        ]

        return GapResult(
            readiness_score=round(readiness_score, 4),
            matched_skills=matched_names,
            missing_skills=missing_names,
            must_matched=must_matched,
            must_total=must_total,
            nice_matched=nice_matched,
            nice_total=nice_total,
        )
