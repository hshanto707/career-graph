"""Wipes all data from Postgres and Neo4j, leaving schema/constraints intact.

Truncates every application table (cascading) and detaches/deletes every
Neo4j node, but does not touch migrations or Neo4j constraints -- run this
when you want a clean slate without tearing down containers/volumes.

Usage: python scripts/reset_db.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

from app.database.neo4j import close_driver, get_driver
from app.database.postgres import engine

POSTGRES_TABLES = ["student_profiles", "users"]


def reset_postgres() -> None:
    with engine.begin() as conn:
        tables = ", ".join(POSTGRES_TABLES)
        conn.execute(text(f"TRUNCATE TABLE {tables} RESTART IDENTITY CASCADE"))
    print(f"Postgres: truncated {', '.join(POSTGRES_TABLES)}.")


def reset_neo4j() -> None:
    driver = get_driver()
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
    close_driver()
    print("Neo4j: deleted all nodes and relationships.")


if __name__ == "__main__":
    reset_postgres()
    reset_neo4j()
    print("Done.")
