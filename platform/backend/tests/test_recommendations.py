"""Tests for recommendations endpoints — written BEFORE implementation (TDD)."""
import pytest
from httpx import AsyncClient


async def test_job_recommendations_requires_auth(async_client: AsyncClient):
    """Job recommendations endpoint requires authentication."""
    resp = await async_client.get("/api/v1/recommendations/jobs")
    assert resp.status_code in (401, 403)


async def test_job_recommendations_authenticated(async_client: AsyncClient, auth_headers):
    """Authenticated user can get job recommendations."""
    resp = await async_client.get("/api/v1/recommendations/jobs", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert "recommendations" in body["data"]
    assert isinstance(body["data"]["recommendations"], list)


async def test_skill_recommendations_requires_auth(async_client: AsyncClient):
    """Skill recommendations require authentication."""
    resp = await async_client.get("/api/v1/recommendations/skills")
    assert resp.status_code in (401, 403)
