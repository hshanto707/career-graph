"""Tests for admin endpoints — written BEFORE implementation (TDD)."""
import pytest
from httpx import AsyncClient
import io


async def test_ingest_csv_requires_auth(async_client: AsyncClient):
    """CSV ingestion requires authentication."""
    resp = await async_client.post("/api/v1/admin/ingest/csv",
        files={"file": ("jobs.csv", b"id,title\nJ1,Dev", "text/csv")})
    assert resp.status_code in (401, 403)


async def test_ingest_csv_authenticated(async_client: AsyncClient, auth_headers):
    """Authenticated user can upload a valid CSV."""
    csv_content = (
        "id,title,company,location,employment_type,salary_min,salary_max,skills_required,description,posted_date\n"
        "JOB_001,Backend Dev,TechCo,Remote,Full-time,80000,120000,\"Python,FastAPI\",Great role,2024-01-15\n"
    )
    resp = await async_client.post(
        "/api/v1/admin/ingest/csv",
        headers=auth_headers,
        files={"file": ("jobs.csv", csv_content.encode(), "text/csv")}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert "valid_rows" in body["data"]


async def test_ingest_csv_invalid_file(async_client: AsyncClient, auth_headers):
    """Invalid CSV with missing columns returns 400."""
    resp = await async_client.post(
        "/api/v1/admin/ingest/csv",
        headers=auth_headers,
        files={"file": ("jobs.csv", b"id,title\nJOB_001,Dev", "text/csv")}
    )
    assert resp.status_code == 400


async def test_seed_prerequisites_success(async_client: AsyncClient, auth_headers, mock_neo4j, tmp_path, monkeypatch):
    """Seeding prerequisites returns count of seeded edges."""
    import json as _json
    from unittest.mock import AsyncMock

    prereq_data = {
        "prerequisites": [
            {"from": "Machine Learning", "to": "Python", "difficulty_jump": 2},
            {"from": "Deep Learning", "to": "Machine Learning", "difficulty_jump": 3},
        ]
    }
    test_file = tmp_path / "prerequisites.json"
    test_file.write_text(_json.dumps(prereq_data))

    # Patch the _PREREQ_FILE constant in the admin module
    import app.routers.admin as admin_mod
    monkeypatch.setattr(admin_mod, "_PREREQ_FILE", test_file)

    mock_neo4j.run.return_value.data = AsyncMock(return_value=[])

    resp = await async_client.post("/api/v1/admin/seed/prerequisites", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["seeded"] == 2


async def test_admin_stats_returns_counts(async_client: AsyncClient, auth_headers, mock_neo4j):
    """Admin stats endpoint returns node/edge counts."""
    from unittest.mock import AsyncMock
    mock_neo4j.run.return_value.data = AsyncMock(side_effect=[
        [{"label": "Job", "cnt": 120}, {"label": "Skill", "cnt": 80}],
        [{"rel_type": "REQUIRES", "cnt": 450}, {"rel_type": "LEADS_TO", "cnt": 40}],
    ])

    resp = await async_client.get("/api/v1/admin/stats", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "node_counts" in data
    assert "edge_counts" in data
    assert "graph_density" in data
