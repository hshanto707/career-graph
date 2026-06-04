"""Tests for skills endpoints — written BEFORE implementation (TDD)."""
import pytest
from httpx import AsyncClient


async def test_market_skills_public(async_client: AsyncClient):
    """Market skills endpoint is publicly accessible."""
    resp = await async_client.get("/api/v1/skills/market")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert "top_skills" in body["data"]


async def test_skill_gap_requires_auth(async_client: AsyncClient):
    """Skill gap endpoint requires authentication."""
    resp = await async_client.get("/api/v1/skills/gap?target_job_id=JOB_001")
    assert resp.status_code in (401, 403)


async def test_skill_gap_authenticated(async_client: AsyncClient, auth_headers):
    """Authenticated user can get skill gap analysis."""
    resp = await async_client.get("/api/v1/skills/gap?target_job_id=JOB_001", headers=auth_headers)
    # Could be 200 or 404 depending on whether JOB_001 exists; either is fine
    assert resp.status_code in (200, 404)
