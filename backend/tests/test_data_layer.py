"""B2 — data layer: Postgres models + GraphService/FakeGraphService.
Mirrors test-plan.md §B2."""
from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.profile import StudentProfile
from app.models.user import User
from tests.fakes import FakeGraphService

BACKEND_ROOT = Path(__file__).resolve().parent.parent


# ------------------------------------------------------------------ #
# User email uniqueness
# ------------------------------------------------------------------ #
def test_user_email_uniqueness_enforced(db_session):
    db_session.add(User(email="dupe@example.com", hashed_password="x", name="A"))
    db_session.commit()

    db_session.add(User(email="dupe@example.com", hashed_password="y", name="B"))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_user_distinct_emails_both_succeed(db_session):
    db_session.add(User(email="a@example.com", hashed_password="x", name="A"))
    db_session.add(User(email="b@example.com", hashed_password="y", name="B"))
    db_session.commit()

    assert db_session.query(User).count() == 2


# ------------------------------------------------------------------ #
# StudentProfile one-to-one with User
# ------------------------------------------------------------------ #
def test_student_profile_one_to_one_enforced(db_session):
    user = User(email="student@example.com", hashed_password="x", name="Student")
    db_session.add(user)
    db_session.commit()

    db_session.add(
        StudentProfile(user_id=user.id, major="CS", skills=[], target_roles=[], experience=[])
    )
    db_session.commit()

    # A second profile for the *same* user must be rejected by the unique
    # constraint on student_profiles.user_id.
    db_session.add(
        StudentProfile(user_id=user.id, major="Math", skills=[], target_roles=[], experience=[])
    )
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_student_profile_created_empty_is_valid(db_session):
    user = User(email="empty@example.com", hashed_password="x", name="Empty")
    db_session.add(user)
    db_session.commit()

    profile = StudentProfile(user_id=user.id, skills=[], target_roles=[], experience=[])
    db_session.add(profile)
    db_session.commit()

    fetched = db_session.query(StudentProfile).filter_by(user_id=user.id).one()
    assert fetched.skills == []
    assert fetched.major is None


# ------------------------------------------------------------------ #
# Alembic migration round-trip
# ------------------------------------------------------------------ #
def test_alembic_migration_round_trip():
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import create_engine, inspect

    db_path = BACKEND_ROOT / "test_alembic.db"
    if db_path.exists():
        db_path.unlink()
    db_url = f"sqlite:///{db_path}"

    cfg = Config(str(BACKEND_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_ROOT / "alembic"))
    cfg.set_main_option("sqlalchemy.url", db_url)
    # env.py overrides sqlalchemy.url via get_settings() when TESTING=1 is
    # set (which conftest already does for the whole test session), so this
    # engine and env.py's engine resolve to the same on-disk SQLite file
    # only if we point TESTING settings at it explicitly here instead.
    import os

    os.environ["DATABASE_URL"] = db_url

    try:
        command.upgrade(cfg, "head")

        engine = create_engine(db_url)
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())
        assert "users" in tables
        assert "student_profiles" in tables

        command.downgrade(cfg, "base")

        inspector = inspect(create_engine(db_url))
        tables_after = set(inspector.get_table_names())
        assert "users" not in tables_after
        assert "student_profiles" not in tables_after
    finally:
        if db_path.exists():
            db_path.unlink()


# ------------------------------------------------------------------ #
# FakeGraphService — mirrors GraphService's method signatures
# ------------------------------------------------------------------ #
def test_get_student_skills_returns_seeded_skills():
    graph = FakeGraphService()
    graph.upsert_student_node(
        "student-1",
        skills=[{"name": "Python", "proficiency": 8, "years": 3}],
        target_roles=["job-1"],
    )
    skills = graph.get_student_skills("student-1")
    assert skills == [{"name": "Python", "proficiency": 8, "years": 3}]


def test_get_student_skills_empty_for_unknown_student():
    graph = FakeGraphService()
    assert graph.get_student_skills("does-not-exist") == []


def test_get_job_and_list_jobs():
    graph = FakeGraphService()
    graph.seed_job("job-1", title="Backend Engineer", company="Acme", location="Remote", type="Full-time")
    graph.seed_job("job-2", title="Data Analyst", company="Acme", location="NYC", type="Internship")

    assert graph.get_job("job-1")["title"] == "Backend Engineer"
    assert graph.get_job("nonexistent") is None

    all_jobs = graph.list_jobs()
    assert len(all_jobs) == 2

    interns = graph.list_jobs({"type": "Internship"})
    assert len(interns) == 1
    assert interns[0]["id"] == "job-2"

    searched = graph.list_jobs({"search": "backend"})
    assert len(searched) == 1
    assert searched[0]["id"] == "job-1"


def test_get_job_required_skills_and_all_jobs_with_requires():
    graph = FakeGraphService()
    graph.seed_job("job-1", title="Backend Engineer")
    graph.seed_job_skills(
        "job-1",
        [
            {"name": "Python", "importance": "must", "frequency": 10},
            {"name": "Docker", "importance": "nice", "frequency": 3},
        ],
    )

    required = graph.get_job_required_skills("job-1")
    assert {s["name"] for s in required} == {"Python", "Docker"}

    all_with_requires = graph.get_all_jobs_with_requires()
    assert all_with_requires[0]["job_id"] == "job-1"
    assert len(all_with_requires[0]["required_skills"]) == 2


def test_get_leads_to_graph_and_teaches_courses():
    graph = FakeGraphService()
    graph.seed_leads_to([{"from_skill": "Python", "to_skill": "Machine Learning", "difficulty_jump": 2}])
    graph.seed_courses(
        [{"id": "c1", "title": "ML 101", "provider": "X", "url": "", "duration": "4w", "free": True, "skill_name": "Machine Learning"}]
    )

    leads_to = graph.get_leads_to_graph()
    assert leads_to[0]["to_skill"] == "Machine Learning"

    courses = graph.get_teaches_courses(["Machine Learning"])
    assert len(courses) == 1
    assert courses[0]["title"] == "ML 101"

    assert graph.get_teaches_courses(["Nonexistent Skill"]) == []


def test_get_skill_demand_counts():
    graph = FakeGraphService()
    graph.seed_job("job-1", title="A")
    graph.seed_job("job-2", title="B")
    graph.seed_job_skills("job-1", [{"name": "Python", "importance": "must", "frequency": 1}])
    graph.seed_job_skills("job-2", [{"name": "Python", "importance": "must", "frequency": 1}, {"name": "SQL", "importance": "nice", "frequency": 1}])

    demand = graph.get_skill_demand_counts()
    demand_by_name = {d["skill_name"]: d["demand_count"] for d in demand}
    assert demand_by_name["Python"] == 2
    assert demand_by_name["SQL"] == 1


# ------------------------------------------------------------------ #
# Cypher-injection-safety regression test
# ------------------------------------------------------------------ #
CYPHER_PAYLOAD = "Skill' MATCH (n) DETACH DELETE n //"


def test_cypher_injection_payload_round_trips_as_literal_data():
    """A skill name containing Cypher-special syntax must be stored and
    returned as inert literal data, never interpreted/executed. The real
    GraphService achieves this via parameterized `$param` Cypher (never
    string interpolation); FakeGraphService achieves the same invariant
    trivially by never building query strings from input at all -- both
    must produce the same observable behavior: the payload round-trips
    unchanged and no other data is destroyed."""
    graph = FakeGraphService()
    graph.seed_job("job-1", title="Test Job")
    graph.seed_job("job-2", title="Untouched Job")
    graph.seed_job_skills("job-1", [{"name": CYPHER_PAYLOAD, "importance": "must", "frequency": 1}])

    required = graph.get_job_required_skills("job-1")
    assert required[0]["name"] == CYPHER_PAYLOAD

    # If the payload had somehow been "executed", job-2 would be gone.
    assert graph.get_job("job-2") is not None

    graph.upsert_student_node("student-1", skills=[{"name": CYPHER_PAYLOAD, "proficiency": 5, "years": 1}], target_roles=[])
    skills = graph.get_student_skills("student-1")
    assert skills[0]["name"] == CYPHER_PAYLOAD


def test_graph_service_search_filter_never_interpolates_values_into_query_text():
    """Static regression guard over the real GraphService (not the fake):
    the only f-string in `list_jobs` interpolates fixed clause *fragments*
    like `j.type = $type` (constructed from param *names*, never from the
    caller-supplied *values*). Every value -- including `search` -- must be
    passed through `session.run(query, **params)` as a bound parameter, so
    grep for the tell-tale sign of a real vulnerability: a value variable
    embedded directly inside the query f-string itself.
    """
    source = (BACKEND_ROOT / "app" / "services" / "graph_service.py").read_text()

    assert "params['search']" not in source
    assert '{filters["search"]}' not in source
    assert '{filters.get("search")}' not in source
    # The parameter is bound via **params / keyword args to session.run(...),
    # never spliced into the query text.
    assert "params[\"search\"] = filters[\"search\"]" in source
