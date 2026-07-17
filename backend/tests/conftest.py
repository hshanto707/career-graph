"""Shared pytest fixtures.

Forces the SQL layer onto a throwaway SQLite file (via TESTING=1) *before*
any `app.*` module is imported, so the whole test session runs standalone --
no live Postgres or Neo4j required. Each test function gets a clean set of
tables.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ["TESTING"] = "true"
os.environ.setdefault("FRONTEND_URL", "http://localhost:5173")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.database.postgres import Base, build_engine

get_settings.cache_clear()

TEST_DB_PATH = Path(__file__).resolve().parent.parent / "test_careergraph.db"


@pytest.fixture()
def db_engine():
    """A fresh SQLite-backed engine with all tables created, dropped after
    the test."""
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()
    engine = build_engine("sqlite:///./test_careergraph.db")
    Base.metadata.create_all(engine)
    try:
        yield engine
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()
        if TEST_DB_PATH.exists():
            TEST_DB_PATH.unlink()


@pytest.fixture()
def db_session(db_engine):
    from sqlalchemy.orm import sessionmaker

    SessionLocal = sessionmaker(bind=db_engine, autoflush=False, autocommit=False, future=True)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client():
    from main import app

    with TestClient(app) as test_client:
        yield test_client
