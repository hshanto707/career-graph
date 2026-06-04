"""Tests for authentication endpoints. Written BEFORE implementation (TDD)."""
import pytest
from httpx import AsyncClient

# ─── Registration Tests ───────────────────────────────────────────────────────

async def test_register_success(async_client: AsyncClient):
    """A new user can register with valid data."""
    resp = await async_client.post("/api/v1/auth/register", json={
        "email": "alice@example.com", "name": "Alice", "password": "securepass123"
    })
    assert resp.status_code == 201
    body = resp.json()
    assert body["success"] is True
    assert "access_token" in body["data"]
    assert body["data"]["email"] == "alice@example.com"
    assert body["data"]["name"] == "Alice"
    assert "password" not in str(body)  # Never expose passwords

async def test_register_duplicate_email(async_client: AsyncClient):
    """Registering with an already-used email returns 409."""
    payload = {"email": "bob@example.com", "name": "Bob", "password": "securepass123"}
    await async_client.post("/api/v1/auth/register", json=payload)
    resp = await async_client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 409

async def test_register_short_password(async_client: AsyncClient):
    """Password shorter than 8 characters is rejected with 422."""
    resp = await async_client.post("/api/v1/auth/register", json={
        "email": "carol@example.com", "name": "Carol", "password": "short"
    })
    assert resp.status_code == 422

async def test_register_invalid_email(async_client: AsyncClient):
    """Invalid email format is rejected with 422."""
    resp = await async_client.post("/api/v1/auth/register", json={
        "email": "not-an-email", "name": "Dave", "password": "securepass123"
    })
    assert resp.status_code == 422

# ─── Login Tests ──────────────────────────────────────────────────────────────

async def test_login_success(async_client: AsyncClient, registered_user):
    """Registered user can log in and receives a JWT."""
    resp = await async_client.post("/api/v1/auth/login", json={
        "email": "test@example.com", "password": "testpassword123"
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert "access_token" in body["data"]
    assert body["data"]["token_type"] == "bearer"

async def test_login_wrong_password(async_client: AsyncClient, registered_user):
    """Wrong password returns 401."""
    resp = await async_client.post("/api/v1/auth/login", json={
        "email": "test@example.com", "password": "wrongpassword"
    })
    assert resp.status_code == 401

async def test_login_unknown_email(async_client: AsyncClient):
    """Login with non-existent email returns 401."""
    resp = await async_client.post("/api/v1/auth/login", json={
        "email": "nobody@example.com", "password": "somepassword"
    })
    assert resp.status_code == 401
