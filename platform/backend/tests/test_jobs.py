"""Tests for jobs endpoints — written BEFORE implementation (TDD)."""
import pytest
from httpx import AsyncClient


async def test_list_jobs_no_auth_required(async_client: AsyncClient):
    """Job listing is publicly accessible (no auth needed)."""
    resp = await async_client.get("/api/v1/jobs")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert "jobs" in body["data"]
    assert isinstance(body["data"]["jobs"], list)


async def test_list_jobs_returns_pagination_info(async_client: AsyncClient):
    """Job list response includes total count and pagination info."""
    resp = await async_client.get("/api/v1/jobs?limit=10&offset=0")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "total" in data
    assert "limit" in data
    assert "offset" in data


async def test_get_job_by_id_not_found(async_client: AsyncClient):
    """Requesting non-existent job returns 404."""
    resp = await async_client.get("/api/v1/jobs/NONEXISTENT")
    assert resp.status_code == 404
