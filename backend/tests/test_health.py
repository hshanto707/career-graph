"""B1 — backend scaffold & infra: health check, CORS, exception envelope,
config loading. Mirrors test-plan.md §B1."""
from __future__ import annotations

import importlib

import pytest


def test_health_returns_success_envelope(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert "postgres" in body["data"]
    assert "neo4j" in body["data"]


def test_health_reports_postgres_ok_in_test_mode(client):
    # The SQL layer is swapped to SQLite under TESTING=1, so Postgres
    # connectivity (i.e. the configured engine) should always report "ok"
    # here, independent of whether a real Postgres is running anywhere.
    resp = client.get("/health")
    assert resp.json()["data"]["postgres"] == "ok"


def test_health_reports_neo4j_status_without_crashing(client):
    # No live Neo4j in this sandbox -- the important assertion is that the
    # endpoint degrades to a status string instead of raising/500ing.
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["data"]["neo4j"] in {"ok", "unreachable"}


def test_cors_preflight_allows_configured_frontend_origin(client):
    # Read the actually-configured origin rather than hardcoding a literal
    # -- conftest.py only *defaults* FRONTEND_URL to localhost:5173
    # (os.environ.setdefault), so a real deployment's own FRONTEND_URL
    # (e.g. the docker-compose container's .env-derived value) takes
    # precedence and must be what this test checks against, whatever it is.
    from app.core.config import get_settings

    configured_origin = get_settings().FRONTEND_URL
    resp = client.options(
        "/health",
        headers={
            "Origin": configured_origin,
            "Access-Control-Request-Method": "GET",
        },
    )
    assert resp.status_code in (200, 204)
    assert resp.headers.get("access-control-allow-origin") == configured_origin


def test_cors_preflight_rejects_unlisted_origin(client):
    resp = client.options(
        "/health",
        headers={
            "Origin": "http://evil.example.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    # Starlette's CORS middleware responds 200 to the preflight itself but
    # omits the allow-origin header for a disallowed origin -- the browser
    # is what actually blocks the follow-up request. Assert the header is
    # absent (or doesn't match), not a hard 4xx.
    assert resp.headers.get("access-control-allow-origin") != "http://evil.example.com"


def test_unhandled_exception_returns_json_envelope(client):
    from main import app
    from starlette.testclient import TestClient

    @app.get("/__boom")
    def boom():
        raise RuntimeError("kaboom")

    # TestClient re-raises server exceptions by default (useful for normal
    # test debugging) -- disable that here since we're specifically
    # asserting on the *handled* envelope response the global exception
    # handler produces for real clients in production.
    no_raise_client = TestClient(app, raise_server_exceptions=False)
    resp = no_raise_client.get("/__boom")
    assert resp.status_code == 500
    body = resp.json()
    assert body["success"] is False
    assert body["error"] == "INTERNAL_SERVER_ERROR"
    assert "message" in body


def test_404_not_found_returns_json_envelope(client):
    resp = client.get("/this-route-does-not-exist")
    assert resp.status_code == 404
    body = resp.json()
    assert body["success"] is False
    assert body["error"] == "NOT_FOUND"


def test_validation_error_returns_json_envelope(client):
    from main import app
    from pydantic import BaseModel

    class Payload(BaseModel):
        required_field: str

    @app.post("/__validate")
    def validate(payload: Payload):
        return {"ok": True}

    resp = client.post("/__validate", json={})
    assert resp.status_code == 422
    body = resp.json()
    assert body["success"] is False
    assert body["error"] == "VALIDATION_ERROR"


def test_settings_load_with_defaults_when_env_absent(monkeypatch):
    from app.core.config import Settings

    # No .env file, no explicit env vars for these -- should fall back to
    # the documented safe local/test defaults rather than throwing.
    monkeypatch.delenv("JWT_SECRET", raising=False)
    settings = Settings(_env_file=None)
    assert settings.JWT_SECRET  # non-empty default present
    assert settings.LLM_PROVIDER == "none"
    assert settings.FRONTEND_URL.startswith("http")


def test_settings_reads_overrides_from_environment(monkeypatch):
    from app.core.config import Settings

    monkeypatch.setenv("FRONTEND_URL", "http://example.test")
    settings = Settings(_env_file=None)
    assert settings.FRONTEND_URL == "http://example.test"
