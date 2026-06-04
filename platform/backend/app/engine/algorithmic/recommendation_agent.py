"""
RecommendationAgent — Ranks jobs for a student using Jaccard similarity.

Algorithm:
    exact_score = |student_skills ∩ job_skills| / |student_skills ∪ job_skills|
    final_score = exact_score  (partial score via LEADS_TO is computed by orchestrator)

No LLM required. Pure Python.
"""
from dataclasses import dataclass


@dataclass
class JobRecommendation:
    """A job recommendation with its relevance score."""
    job_id: str
    title: str
    company: str
    location: str
    employment_type: str
    salary_min: int | None
    salary_max: int | None
    skills_required: list[str]
    score: float  # 0.0 - 1.0
    matched_skills: list[str]
    missing_skills: list[str]


class RecommendationAgent:
    """
    Ranks job postings by skill relevance for a given student.

    Uses Jaccard similarity: |intersection| / |union| of skill sets.
    This is transparent and easily explainable — faculty can see exactly
    why each job was ranked higher than others.
    """

    def rank_jobs(
        self,
        student_skills: set[str],
        jobs: list[dict],
        top_n: int | None = None,
    ) -> list[JobRecommendation]:
        """
        Rank jobs by skill overlap with student profile.

        Args:
            student_skills: Set of skill names the student has.
            jobs: List of job dicts with 'id', 'title', 'skills_required', etc.
            top_n: If set, return only the top N results.

        Returns:
            List of JobRecommendation sorted by score descending.
        """
        if not jobs:
            return []

        student_lower = {s.lower() for s in student_skills}
        recommendations = []

        for job in jobs:
            job_skills = [s for s in job.get("skills_required", [])]
            job_lower = {s.lower() for s in job_skills}

            matched_lower = student_lower & job_lower
            union_lower = student_lower | job_lower

            score = len(matched_lower) / len(union_lower) if union_lower else 0.0

            # Build matched/missing using original casing
            matched = [s for s in job_skills if s.lower() in matched_lower]
            missing = [s for s in job_skills if s.lower() not in matched_lower]

            recommendations.append(JobRecommendation(
                job_id=job.get("id", ""),
                title=job.get("title", ""),
                company=job.get("company", ""),
                location=job.get("location", ""),
                employment_type=job.get("employment_type", ""),
                salary_min=job.get("salary_min"),
                salary_max=job.get("salary_max"),
                skills_required=job_skills,
                score=round(score, 4),
                matched_skills=matched,
                missing_skills=missing,
            ))

        recommendations.sort(key=lambda r: r.score, reverse=True)
        return recommendations[:top_n] if top_n else recommendations
