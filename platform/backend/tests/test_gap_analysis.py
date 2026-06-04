"""Tests for gap analysis endpoint — written BEFORE implementation (TDD)."""
import pytest
from httpx import AsyncClient


async def test_gap_analysis_requires_auth(async_client: AsyncClient):
    """Gap analysis endpoint requires authentication."""
    resp = await async_client.post("/api/v1/gap-analysis", json={"target_job_id": "JOB_001"})
    assert resp.status_code in (401, 403)


async def test_gap_analysis_authenticated(async_client: AsyncClient, auth_headers):
    """Authenticated user can request gap analysis."""
    resp = await async_client.post("/api/v1/gap-analysis",
        headers=auth_headers, json={"target_job_id": "JOB_001"})
    # 200 with data, or 404 if JOB_001 not in Neo4j mock
    assert resp.status_code in (200, 404)
    if resp.status_code == 200:
        data = resp.json()["data"]
        assert "readiness_score" in data


async def test_gap_analysis_missing_job_id(async_client: AsyncClient, auth_headers):
    """Gap analysis without target_job_id returns 422."""
    resp = await async_client.post("/api/v1/gap-analysis", headers=auth_headers, json={})
    assert resp.status_code == 422


async def test_gap_analysis_returns_roadmap(async_client: AsyncClient, auth_headers, mock_neo4j):
    """Gap analysis response includes roadmap field with milestones."""
    from unittest.mock import AsyncMock

    student_skills = [{"name": "Python", "proficiency": 8, "years": 2}]
    job_data = [{
        "id": "JOB_TEST", "title": "Data Engineer", "company": "Acme",
        "location": "Remote", "employment_type": "Full-time",
        "salary_min": None, "salary_max": None, "description": "", "posted_date": "",
        "skills_required": [
            {"name": "Python", "importance": "must"},
            {"name": "Spark", "importance": "must"},
        ],
    }]
    prereq_data = []

    mock_neo4j.run.return_value.data = AsyncMock(side_effect=[
        student_skills,
        job_data,
        prereq_data,
    ])

    resp = await async_client.post(
        "/api/v1/gap-analysis",
        headers=auth_headers,
        json={"target_job_id": "JOB_TEST"},
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "readiness_score" in data
    assert "roadmap" in data
    assert "milestones" in data["roadmap"]
    assert isinstance(data["roadmap"]["milestones"], list)
