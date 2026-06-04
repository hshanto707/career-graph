"""Tests for NormalizationAgent — WRITTEN BEFORE IMPLEMENTATION (TDD)."""
import pytest
from app.engine.ingestion.normalization_agent import NormalizationAgent

SYNONYMS = {
    "reactjs": "React",
    "nodejs": "Node.js",
    "python3": "Python",
    "ml": "Machine Learning",
    "javascript": "JavaScript",
}

def test_exact_synonym_resolved():
    """Exact synonym match resolves to canonical name."""
    agent = NormalizationAgent(synonyms=SYNONYMS)
    assert agent.normalize("ReactJS") == "React"
    assert agent.normalize("NodeJS") == "Node.js"

def test_case_insensitive_match():
    """Synonym lookup is case-insensitive."""
    agent = NormalizationAgent(synonyms=SYNONYMS)
    assert agent.normalize("PYTHON3") == "Python"
    assert agent.normalize("python3") == "Python"

def test_unknown_skill_returns_original():
    """Unknown skill with no synonym match returns itself."""
    agent = NormalizationAgent(synonyms=SYNONYMS)
    result = agent.normalize("Kubernetes")
    assert result == "Kubernetes"

def test_normalize_list():
    """normalize_list resolves all skills in a list."""
    agent = NormalizationAgent(synonyms=SYNONYMS)
    result = agent.normalize_list(["ReactJS", "NodeJS", "Docker"])
    assert "React" in result
    assert "Node.js" in result
    assert "Docker" in result

def test_deduplicate_after_normalization():
    """After normalization, duplicate canonical names are deduplicated."""
    agent = NormalizationAgent(synonyms=SYNONYMS)
    result = agent.normalize_list(["ReactJS", "React", "react"])
    # All resolve to "React" — should appear only once
    assert result.count("React") == 1

def test_fuzzy_match_close_spelling():
    """Fuzzy matching resolves near-misspellings (score >= 85)."""
    # "Machne Learning" is close to "Machine Learning"
    agent = NormalizationAgent(synonyms=SYNONYMS, known_skills=["Machine Learning", "React", "Python"])
    result = agent.normalize("Machne Learning")
    assert result == "Machine Learning"

def test_jobs_normalized_in_bulk():
    """normalize_jobs processes a list of job dicts in place."""
    agent = NormalizationAgent(synonyms=SYNONYMS)
    jobs = [
        {"id": "J1", "skills_required": ["ReactJS", "NodeJS"]},
        {"id": "J2", "skills_required": ["python3", "ML"]},
    ]
    normalized = agent.normalize_jobs(jobs)
    assert "React" in normalized[0]["skills_required"]
    assert "Node.js" in normalized[0]["skills_required"]
    assert "Python" in normalized[1]["skills_required"]
    assert "Machine Learning" in normalized[1]["skills_required"]
