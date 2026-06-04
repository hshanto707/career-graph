"""Tests for ReasoningAgent — WRITTEN BEFORE IMPLEMENTATION (TDD)."""
import pytest
from unittest.mock import AsyncMock, patch
from app.engine.reasoning.reasoning_agent import ReasoningAgent
from app.engine.algorithmic.skill_gap_agent import GapResult


GAP_RESULT = GapResult(
    readiness_score=62.5,
    matched_skills=["Python", "PostgreSQL"],
    missing_skills=["Docker", "Kubernetes"],
    must_total=4, nice_total=0, must_matched=2, nice_matched=0
)


@pytest.mark.asyncio
async def test_explain_gap_returns_dict():
    """explain_gap returns a dict with explanation and encouragement keys."""
    mock_provider = AsyncMock()
    mock_provider.complete = AsyncMock(return_value='{"explanation": "You need Docker.", "encouragement": "Keep going!", "weeks_to_learn": 4}')

    agent = ReasoningAgent(llm_provider=mock_provider)
    result = await agent.explain_gap(GAP_RESULT, target_job_title="DevOps Engineer")

    assert isinstance(result, dict)
    assert "explanation" in result
    assert "encouragement" in result


@pytest.mark.asyncio
async def test_explain_gap_graceful_degradation_on_llm_failure():
    """If LLM returns empty string, explain_gap falls back to template response."""
    mock_provider = AsyncMock()
    mock_provider.complete = AsyncMock(return_value="")

    agent = ReasoningAgent(llm_provider=mock_provider)
    result = await agent.explain_gap(GAP_RESULT, target_job_title="DevOps Engineer")

    assert isinstance(result, dict)
    assert "explanation" in result  # Should have fallback text


@pytest.mark.asyncio
async def test_explain_gap_without_provider():
    """ReasoningAgent with no provider returns template response."""
    agent = ReasoningAgent(llm_provider=None)
    result = await agent.explain_gap(GAP_RESULT, target_job_title="DevOps Engineer")

    assert isinstance(result, dict)
    assert "explanation" in result


@pytest.mark.asyncio
async def test_narrate_recommendations_returns_list():
    """narrate_recommendations returns a list of dicts with why_recommended."""
    mock_provider = AsyncMock()
    mock_provider.complete = AsyncMock(return_value='{"why_recommended": "Strong Python match."}')

    agent = ReasoningAgent(llm_provider=mock_provider)
    jobs = [{"job_id": "J1", "title": "Backend Dev", "score": 0.8, "matched_skills": ["Python"]}]
    result = await agent.narrate_recommendations(jobs)

    assert isinstance(result, list)
    assert len(result) == 1
    assert "why_recommended" in result[0]
