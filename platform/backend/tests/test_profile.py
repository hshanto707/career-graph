"""Tests for profile endpoints. Written BEFORE implementation (TDD)."""
import pytest
from httpx import AsyncClient

async def test_get_profile_authenticated(async_client: AsyncClient, auth_headers, registered_user):
    """Authenticated user can retrieve their profile."""
    resp = await async_client.get("/api/v1/profile", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    data = body["data"]
    assert data["email"] == "test@example.com"
    assert data["name"] == "Test User"
    assert "skills" in data
    assert isinstance(data["skills"], list)

async def test_get_profile_unauthenticated(async_client: AsyncClient):
    """Unauthenticated request to profile returns 403."""
    resp = await async_client.get("/api/v1/profile")
    assert resp.status_code in (401, 403)

async def test_update_profile(async_client: AsyncClient, auth_headers):
    """User can update their profile fields."""
    resp = await async_client.put("/api/v1/profile", headers=auth_headers, json={
        "university": "BRAC University",
        "graduation_year": 2026,
        "target_roles": ["Software Engineer", "Backend Developer"],
        "bio": "Aspiring software engineer"
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"]["university"] == "BRAC University"
    assert body["data"]["graduation_year"] == 2026

async def test_update_profile_partial(async_client: AsyncClient, auth_headers):
    """Partial profile update only changes provided fields."""
    await async_client.put("/api/v1/profile", headers=auth_headers, json={
        "university": "BUET"
    })
    resp = await async_client.get("/api/v1/profile", headers=auth_headers)
    assert resp.json()["data"]["university"] == "BUET"

async def test_add_skill(async_client: AsyncClient, auth_headers, mock_neo4j):
    """User can add a skill to their profile."""
    resp = await async_client.post("/api/v1/profile/skills", headers=auth_headers, json={
        "skill_name": "Python",
        "proficiency": 8.0,
        "years": 3.0
    })
    assert resp.status_code == 201
    body = resp.json()
    assert body["success"] is True

async def test_add_skill_invalid_proficiency(async_client: AsyncClient, auth_headers):
    """Proficiency outside 0-10 range is rejected with 422."""
    resp = await async_client.post("/api/v1/profile/skills", headers=auth_headers, json={
        "skill_name": "Python", "proficiency": 15.0, "years": 2.0
    })
    assert resp.status_code == 422
