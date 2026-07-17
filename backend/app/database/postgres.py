"""SQLAlchemy engine/session setup.

Swaps transparently to a local SQLite database when `TESTING=1` (or
`settings.TESTING` is True), so unit/integration tests never require a live
PostgreSQL instance. Production/deployment uses `DATABASE_URL` from `.env`
(expected to be a PostgreSQL DSN).
"""
from __future__ import annotations

import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""


def _is_testing() -> bool:
    return get_settings().TESTING or os.getenv("TESTING", "").lower() in {"1", "true", "yes"}


def build_engine(database_url: str | None = None):
    settings = get_settings()

    if database_url is None:
        if _is_testing():
            # File-based SQLite in the test run's working directory keeps
            # behavior close to a real relational DB (unlike ':memory:',
            # which drops state across connections) while needing zero setup.
            database_url = "sqlite:///./test_careergraph.db"
        else:
            database_url = settings.DATABASE_URL

    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(database_url, connect_args=connect_args, future=True)


engine = build_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a request-scoped SQLAlchemy session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
