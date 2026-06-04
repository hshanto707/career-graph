"""
Tests for SkillGapAgent — WRITTEN BEFORE IMPLEMENTATION (TDD).

SkillGapAgent computes a weighted readiness score:
  readiness = (must_matched/must_total)*0.7 + (nice_matched/nice_total)*0.3 + proficiency_bonus
"""
import pytest
from app.engine.algorithmic.skill_gap_agent import SkillGapAgent, GapResult


def test_perfect_match_gives_100():
    """Student has all must and nice skills => readiness = 100."""
    agent = SkillGapAgent()
    result = agent.compute_gap(
        student_skills={"Python": 8.0, "FastAPI": 7.0, "PostgreSQL": 6.0},
        job_required_skills=[
            {"name": "Python", "importance": "must"},
            {"name": "FastAPI", "importance": "must"},
            {"name": "PostgreSQL", "importance": "nice"},
        ]
    )
    assert result.readiness_score == pytest.approx(100.0, abs=1.0)
    assert result.missing_skills == []
    assert set(result.matched_skills) == {"Python", "FastAPI", "PostgreSQL"}


def test_no_match_gives_zero():
    """Student has none of the required skills => readiness = 0."""
    agent = SkillGapAgent()
    result = agent.compute_gap(
        student_skills={},
        job_required_skills=[
            {"name": "Java", "importance": "must"},
            {"name": "Spring Boot", "importance": "must"},
        ]
    )
    assert result.readiness_score == 0.0
    assert set(result.missing_skills) == {"Java", "Spring Boot"}
    assert result.matched_skills == []


def test_partial_match():
    """Student has 1 of 2 must skills => readiness = 0.7 * 0.5 = 35."""
    agent = SkillGapAgent()
    result = agent.compute_gap(
        student_skills={"Python": 5.0},
        job_required_skills=[
            {"name": "Python", "importance": "must"},
            {"name": "Java", "importance": "must"},
        ]
    )
    assert 30.0 <= result.readiness_score <= 45.0
    assert "Java" in result.missing_skills
    assert "Python" in result.matched_skills


def test_only_nice_skills():
    """With no must skills, score is based only on nice skills (weight 0.3)."""
    agent = SkillGapAgent()
    result = agent.compute_gap(
        student_skills={"React": 7.0},
        job_required_skills=[
            {"name": "React", "importance": "nice"},
            {"name": "TypeScript", "importance": "nice"},
        ]
    )
    # 1/2 nice matched => 0.3 * 0.5 = 15 base + proficiency bonus
    assert 10.0 <= result.readiness_score <= 30.0


def test_gap_result_has_correct_type():
    """compute_gap always returns a GapResult dataclass."""
    agent = SkillGapAgent()
    result = agent.compute_gap(student_skills={}, job_required_skills=[])
    assert isinstance(result, GapResult)
    assert hasattr(result, "readiness_score")
    assert hasattr(result, "matched_skills")
    assert hasattr(result, "missing_skills")
    assert hasattr(result, "must_total")
    assert hasattr(result, "nice_total")


def test_empty_job_requirements():
    """No requirements => readiness = 100 (nothing to miss)."""
    agent = SkillGapAgent()
    result = agent.compute_gap(student_skills={"Python": 8.0}, job_required_skills=[])
    assert result.readiness_score == 100.0


def test_proficiency_bonus_improves_score():
    """High proficiency (9-10) gives a slight bonus over low proficiency (1-2)."""
    agent = SkillGapAgent()
    low = agent.compute_gap(
        student_skills={"Python": 2.0},
        job_required_skills=[{"name": "Python", "importance": "must"}]
    )
    high = agent.compute_gap(
        student_skills={"Python": 10.0},
        job_required_skills=[{"name": "Python", "importance": "must"}]
    )
    assert high.readiness_score > low.readiness_score
