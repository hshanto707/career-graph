"""Neo4j driver singleton.

A single shared `neo4j.Driver` is created lazily on first use and reused for
the lifetime of the process, per the neo4j-driver best practice (the driver
manages its own connection pool internally — do not create one per request).
"""
from __future__ import annotations

from neo4j import Driver, GraphDatabase

from app.core.config import get_settings

_driver: Driver | None = None


def get_driver() -> Driver:
    global _driver
    if _driver is None:
        settings = get_settings()
        _driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
        )
    return _driver


def close_driver() -> None:
    global _driver
    if _driver is not None:
        _driver.close()
        _driver = None


def verify_connectivity() -> bool:
    """Best-effort connectivity check used by /health. Never raises."""
    try:
        get_driver().verify_connectivity()
        return True
    except Exception:
        return False
