"""
Tests for RecommendationAgent — WRITTEN BEFORE IMPLEMENTATION (TDD).

RecommendationAgent ranks jobs for a student using:
  score = Jaccard(student_skills ∩ job_skills) / |union| * 0.8 + partial_score * 0.2
"""
import pytest
from app.engine.algorithmic.recommendation_agent import RecommendationAgent, JobRecommendation


SAMPLE_JOBS = [
    {
        "id": "JOB_001",
        "title": "Python Developer",
        "company": "TechCorp",
        "location": "San Francisco CA",
        "employment_type": "Full-time",
        "salary_min": 80000,
        "salary_max": 120000,
        "skills_required": ["Python", "FastAPI", "PostgreSQL"],
    },
    {
        "id": "JOB_002",
        "title": "Frontend Engineer",
        "company": "WebCo",
        "location": "Remote",
        "employment_type": "Full-time",
        "salary_min": 70000,
        "salary_max": 100000,
        "skills_required": ["React", "TypeScript", "CSS"],
    },
    {
        "id": "JOB_003",
        "title": "Full Stack Developer",
        "company": "StartupX",
        "location": "New York NY",
        "employment_type": "Full-time",
        "salary_min": 90000,
        "salary_max": 130000,
        "skills_required": ["Python", "React", "PostgreSQL", "Docker"],
    },
]


def test_ranks_best_match_first():
    """Job with most skill overlap ranks first."""
    agent = RecommendationAgent()
    student_skills = {"Python", "FastAPI", "PostgreSQL"}
    results = agent.rank_jobs(student_skills, SAMPLE_JOBS)
    assert results[0].job_id == "JOB_001"  # 3/3 match


def test_returns_list_of_job_recommendations():
    """rank_jobs returns a list of JobRecommendation objects."""
    agent = RecommendationAgent()
    results = agent.rank_jobs({"Python"}, SAMPLE_JOBS)
    assert isinstance(results, list)
    assert all(isinstance(r, JobRecommendation) for r in results)


def test_score_between_0_and_1():
    """All recommendation scores are in [0, 1]."""
    agent = RecommendationAgent()
    results = agent.rank_jobs({"Python", "React"}, SAMPLE_JOBS)
    for r in results:
        assert 0.0 <= r.score <= 1.0


def test_no_overlap_gives_lowest_score():
    """No overlap job has the lowest score."""
    agent = RecommendationAgent()
    results = agent.rank_jobs({"Java", "Spring Boot"}, SAMPLE_JOBS)
    scores = [r.score for r in results]
    # All should be low since student has completely different skills
    assert max(scores) < 0.5


def test_empty_student_skills():
    """Empty student skills returns jobs with zero scores."""
    agent = RecommendationAgent()
    results = agent.rank_jobs(set(), SAMPLE_JOBS)
    assert all(r.score == 0.0 for r in results)


def test_empty_jobs_list():
    """Empty jobs list returns empty results."""
    agent = RecommendationAgent()
    results = agent.rank_jobs({"Python"}, [])
    assert results == []


def test_results_sorted_descending():
    """Results are always sorted by score descending."""
    agent = RecommendationAgent()
    results = agent.rank_jobs({"Python", "React", "PostgreSQL"}, SAMPLE_JOBS)
    scores = [r.score for r in results]
    assert scores == sorted(scores, reverse=True)
