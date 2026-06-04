"""Tests for market insights endpoint — written BEFORE implementation (TDD)."""
import pytest
from httpx import AsyncClient


async def test_market_insights_public(async_client: AsyncClient):
    """Market insights is publicly accessible."""
    resp = await async_client.get("/api/v1/market/insights")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert "total_jobs" in body["data"]
    assert "top_skills" in body["data"]


async def test_market_insights_returns_correct_shape(async_client: AsyncClient):
    """Market insights data has required fields."""
    resp = await async_client.get("/api/v1/market/insights")
    data = resp.json()["data"]
    assert "total_jobs" in data
    assert "top_skills" in data
    assert "top_categories" in data
    assert isinstance(data["top_skills"], list)
