"""Tests for EngineOrchestrator — WRITTEN BEFORE IMPLEMENTATION (TDD)."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.engine.orchestrator import EngineOrchestrator


@pytest.fixture
def mock_graph_service():
    svc = AsyncMock()
    svc.get_student_skills = AsyncMock(return_value=[
        {"name": "Python", "proficiency": 8.0, "years": 3.0},
        {"name": "FastAPI", "proficiency": 7.0, "years": 1.5},
    ])
    svc.get_all_jobs = AsyncMock(return_value=[
        {"id": "J1", "title": "Backend Dev", "company": "TechCorp", "location": "Remote",
         "employment_type": "Full-time", "salary_min": 80000, "salary_max": 120000,
         "skills_required": ["Python", "FastAPI", "PostgreSQL"]},
    ])
    svc.get_job_by_id = AsyncMock(return_value={
        "id": "J1", "title": "Backend Dev",
        "skills_required": [{"name": "Python", "importance": "must"}, {"name": "Docker", "importance": "nice"}]
    })
    svc.get_prereq_graph = AsyncMock(return_value={"FastAPI": ["Python"], "Docker": []})
    return svc


@pytest.mark.asyncio
async def test_get_recommendations(mock_graph_service):
    """get_recommendations returns a list of job recommendations."""
    orch = EngineOrchestrator(graph_service=mock_graph_service)
    result = await orch.get_recommendations(user_id="user-123")
    assert isinstance(result, list)
    assert len(result) >= 1
    assert "job_id" in result[0] or "id" in result[0]


@pytest.mark.asyncio
async def test_analyze_gap(mock_graph_service):
    """analyze_gap returns a gap result with readiness_score."""
    orch = EngineOrchestrator(graph_service=mock_graph_service)
    result = await orch.analyze_gap(user_id="user-123", target_job_id="J1")
    assert "readiness_score" in result
    assert 0 <= result["readiness_score"] <= 100


@pytest.mark.asyncio
async def test_get_learning_path(mock_graph_service):
    """get_learning_path returns milestones list."""
    orch = EngineOrchestrator(graph_service=mock_graph_service)
    result = await orch.get_learning_path(user_id="user-123", target_job_id="J1")
    assert "milestones" in result
    assert isinstance(result["milestones"], list)


@pytest.mark.asyncio
async def test_get_market_insights(mock_graph_service):
    """get_market_insights returns top_skills."""
    orch = EngineOrchestrator(graph_service=mock_graph_service)
    result = await orch.get_market_insights()
    assert "top_skills" in result


@pytest.mark.asyncio
async def test_orchestrator_works_without_llm(mock_graph_service):
    """Orchestrator functions correctly when no LLM provider is configured."""
    orch = EngineOrchestrator(graph_service=mock_graph_service, llm_provider=None)
    result = await orch.analyze_gap(user_id="user-123", target_job_id="J1")
    assert "readiness_score" in result
