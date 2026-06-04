"""Tests for dashboard endpoint — written BEFORE implementation (TDD)."""
import pytest
from httpx import AsyncClient


async def test_dashboard_requires_auth(async_client: AsyncClient):
    """Dashboard requires authentication."""
    resp = await async_client.get("/api/v1/dashboard")
    assert resp.status_code in (401, 403)


async def test_dashboard_authenticated(async_client: AsyncClient, auth_headers):
    """Authenticated user gets dashboard stats."""
    resp = await async_client.get("/api/v1/dashboard", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    data = body["data"]
    assert "skills_count" in data
    assert "total_jobs_in_market" in data
