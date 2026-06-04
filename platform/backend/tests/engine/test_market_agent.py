"""
Tests for MarketAgent — WRITTEN BEFORE IMPLEMENTATION (TDD).

MarketAgent aggregates skill demand from job postings.
"""
import pytest
from app.engine.algorithmic.market_agent import MarketAgent, MarketInsights


SAMPLE_JOBS_DATA = [
    {"id": "J1", "title": "Backend Dev", "skills_required": ["Python", "FastAPI", "PostgreSQL", "Docker"]},
    {"id": "J2", "title": "Frontend Dev", "skills_required": ["React", "TypeScript", "CSS", "Docker"]},
    {"id": "J3", "title": "Full Stack",   "skills_required": ["Python", "React", "PostgreSQL"]},
    {"id": "J4", "title": "Data Scientist", "skills_required": ["Python", "Machine Learning", "Pandas"]},
    {"id": "J5", "title": "DevOps",       "skills_required": ["Docker", "Kubernetes", "Linux"]},
]


def test_returns_market_insights():
    """aggregate returns a MarketInsights object."""
    agent = MarketAgent()
    result = agent.aggregate(SAMPLE_JOBS_DATA)
    assert isinstance(result, MarketInsights)


def test_python_is_most_demanded():
    """Python appears in 3/5 jobs so it should rank first."""
    agent = MarketAgent()
    result = agent.aggregate(SAMPLE_JOBS_DATA)
    top_skill = result.top_skills[0]
    assert top_skill["name"] == "Python"
    assert top_skill["demand_count"] == 3


def test_demand_score_normalized_0_to_100():
    """All demand scores are in [0, 100]."""
    agent = MarketAgent()
    result = agent.aggregate(SAMPLE_JOBS_DATA)
    for skill in result.top_skills:
        assert 0 <= skill["demand_score"] <= 100


def test_top_skills_sorted_by_demand():
    """Skills are sorted by demand_count descending."""
    agent = MarketAgent()
    result = agent.aggregate(SAMPLE_JOBS_DATA)
    counts = [s["demand_count"] for s in result.top_skills]
    assert counts == sorted(counts, reverse=True)


def test_total_jobs_count():
    """total_jobs equals the number of input jobs."""
    agent = MarketAgent()
    result = agent.aggregate(SAMPLE_JOBS_DATA)
    assert result.total_jobs == 5


def test_empty_jobs():
    """Empty job list returns empty insights."""
    agent = MarketAgent()
    result = agent.aggregate([])
    assert result.top_skills == []
    assert result.total_jobs == 0


def test_docker_appears_in_multiple():
    """Docker appears in 3 jobs (J1, J2, J5)."""
    agent = MarketAgent()
    result = agent.aggregate(SAMPLE_JOBS_DATA)
    docker = next((s for s in result.top_skills if s["name"] == "Docker"), None)
    assert docker is not None
    assert docker["demand_count"] == 3
