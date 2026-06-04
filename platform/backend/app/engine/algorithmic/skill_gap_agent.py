"""
SkillGapAgent — Computes a weighted readiness score for a student against a job.

Algorithm:
    readiness = (must_matched / must_total) * 0.7
              + (nice_matched / nice_total) * 0.3
              + proficiency_bonus

Proficiency bonus: up to 5 points added when student's average proficiency
on matched must-skills is high (proficiency/10 * 5).

No LLM required. Pure Python.
"""
from dataclasses import dataclass, field


@dataclass
class GapResult:
    """Result of a skill gap computation."""
    readiness_score: float          # 0-100
    matched_skills: list[str]       # Skills the student has
    missing_skills: list[str]       # Skills the student lacks
    must_total: int                 # Total must-have skills in job
    nice_total: int                 # Total nice-to-have skills in job
    must_matched: int               # How many must-haves student has
    nice_matched: int               # How many nice-to-haves student has


class SkillGapAgent:
    """
    Computes a weighted readiness score for a student against a specific job.

    The score uses a 70/30 split between must-have and nice-to-have skills,
    with a small proficiency bonus for students with deep expertise.
    """

    MUST_WEIGHT = 0.70
    NICE_WEIGHT = 0.30
    MAX_PROFICIENCY_BONUS = 5.0  # Up to 5 extra points for high proficiency

    def compute_gap(
        self,
        student_skills: dict[str, float],  # {skill_name: proficiency 0-10}
        job_required_skills: list[dict],   # [{"name": str, "importance": "must"|"nice"}]
    ) -> GapResult:
        """
        Compute the skill gap between a student and a job.

        Args:
            student_skills: Dict mapping skill name to proficiency (0-10).
            job_required_skills: List of dicts with 'name' and 'importance' keys.

        Returns:
            GapResult with readiness_score, matched/missing skills, and counts.
        """
        if not job_required_skills:
            return GapResult(
                readiness_score=100.0,
                matched_skills=list(student_skills.keys()),
                missing_skills=[],
                must_total=0, nice_total=0, must_matched=0, nice_matched=0,
            )

        # Normalize skill names for case-insensitive comparison
        student_lower = {k.lower(): (k, v) for k, v in student_skills.items()}

        must_skills = [s for s in job_required_skills if s.get("importance") == "must"]
        nice_skills = [s for s in job_required_skills if s.get("importance") != "must"]

        matched, missing = [], []
        must_matched = 0
        proficiencies_of_matched_must = []

        for skill in must_skills:
            name = skill["name"]
            if name.lower() in student_lower:
                must_matched += 1
                matched.append(name)
                proficiencies_of_matched_must.append(student_lower[name.lower()][1])
            else:
                missing.append(name)

        nice_matched = 0
        for skill in nice_skills:
            name = skill["name"]
            if name.lower() in student_lower:
                nice_matched += 1
                matched.append(name)
            else:
                missing.append(name)

        must_total = len(must_skills)
        nice_total = len(nice_skills)

        # Each category contributes its weighted portion only if it exists in the job.
        # If a category has no skills in the job, it contributes 0 (not the free weight).
        must_score = (must_matched / must_total * self.MUST_WEIGHT * 100) if must_total > 0 else 0.0
        nice_score = (nice_matched / nice_total * self.NICE_WEIGHT * 100) if nice_total > 0 else 0.0

        # Proficiency bonus: average proficiency of matched must-skills / 10 * max_bonus
        proficiency_bonus = 0.0
        if proficiencies_of_matched_must:
            avg_prof = sum(proficiencies_of_matched_must) / len(proficiencies_of_matched_must)
            proficiency_bonus = (avg_prof / 10.0) * self.MAX_PROFICIENCY_BONUS

        raw_score = must_score + nice_score + proficiency_bonus
        readiness_score = min(100.0, raw_score)

        return GapResult(
            readiness_score=round(readiness_score, 2),
            matched_skills=matched,
            missing_skills=missing,
            must_total=must_total,
            nice_total=nice_total,
            must_matched=must_matched,
            nice_matched=nice_matched,
        )
