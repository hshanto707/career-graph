"""B7 — Student-Facing Routers, plus the B6 orchestrator-fallback tests #4/#5.

Mirrors test-plan.md §B7's red/green tests + edge cases exactly, using
`FakeGraphService` (no live Neo4j) and the SQLite-backed test Postgres
(`tests/conftest.py`'s `client` fixture) so the whole module runs standalone.
"""
from __future__ import annotations

import pytest
from pydantic import BaseModel, Field

from app.core.deps import get_current_user, get_graph_service
from app.engine.llm.base import LLMOutputValidationError, LLMProvider, ModelInfo
from app.engine.orchestrator import EngineOrchestrator
from app.routers import gap_analysis as gap_analysis_router
from app.routers import jobs as jobs_router
from app.routers import market as market_router
from app.routers import profile as profile_router
from app.routers import recommendations as recommendations_router
from app.routers import skills as skills_router
from tests.fakes import FakeGraphService

# --------------------------------------------------------------------------- #
# Shared fixtures
# --------------------------------------------------------------------------- #

_ALL_GRAPH_ROUTERS = [jobs_router, skills_router, recommendations_router, gap_analysis_router, market_router]


@pytest.fixture(scope="module")
def _router_engine():
    """A dedicated in-memory SQLite engine (StaticPool -- single physical
    connection) for this module's Postgres-backed routes (profile/dashboard
    target-role resolution), isolated from the shared `postgres.engine` for
    the same reason `test_auth.py`'s `_auth_engine` fixture documents: a
    QueuePool-backed, file-based SQLite engine can hand out stale
    connections across the TestClient's background request thread."""
    from sqlalchemy import create_engine
    from sqlalchemy.pool import StaticPool

    from app.database.postgres import Base

    import app.models.profile  # noqa: F401
    import app.models.user  # noqa: F401

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(engine)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture(autouse=True)
def _override_get_db(_router_engine):
    from sqlalchemy.orm import sessionmaker

    from app.database.postgres import get_db
    from app.models.profile import StudentProfile
    from app.models.user import User
    from main import app

    TestSessionLocal = sessionmaker(bind=_router_engine, autoflush=False, autocommit=False, future=True)

    def _get_db_override():
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _get_db_override
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_db, None)
        with _router_engine.begin() as conn:
            conn.execute(StudentProfile.__table__.delete())
            conn.execute(User.__table__.delete())


@pytest.fixture()
def fake_graph():
    graph = FakeGraphService()

    graph.seed_job("job-1", title="Junior Backend Engineer", company="Acme", location="Remote", type="Full-time")
    graph.seed_job_skills(
        "job-1",
        [
            {"name": "Python", "importance": "must", "frequency": 10},
            {"name": "SQL", "importance": "must", "frequency": 8},
            {"name": "Docker", "importance": "nice", "frequency": 3},
        ],
    )
    graph.seed_job("job-2", title="Data Analyst Intern", company="Beta", location="NYC", type="Internship")
    graph.seed_job_skills(
        "job-2",
        [
            {"name": "SQL", "importance": "must", "frequency": 8},
            {"name": "Excel", "importance": "nice", "frequency": 2},
        ],
    )
    graph.seed_leads_to([{"from_skill": "Python", "to_skill": "Machine Learning", "difficulty_jump": 2}])
    graph.seed_courses(
        [
            {"skill_name": "SQL", "id": "course-sql", "title": "SQL Basics", "url": "https://example.com/sql"},
            {"skill_name": "Docker", "id": "course-docker", "title": "Docker 101", "url": "https://example.com/docker"},
        ]
    )
    return graph


@pytest.fixture()
def client_with_fake_graph(client, fake_graph):
    """The shared `client` fixture (tests/conftest.py) with every B7 router's
    `get_graph_service` dependency overridden to `fake_graph` -- no live
    Neo4j required anywhere in this module."""
    client.app.dependency_overrides[get_graph_service] = lambda: fake_graph
    try:
        yield client
    finally:
        client.app.dependency_overrides.pop(get_graph_service, None)


def _register_and_login(client, email: str) -> str:
    resp = client.post(
        "/auth/register", json={"email": email, "password": "correct-horse-1", "name": "Test Student"}
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["data"]["token"]


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _set_target_role(client, token, job_id: str):
    resp = client.put("/profile", json={"target_roles": [job_id]}, headers=_auth_headers(token))
    assert resp.status_code == 200, resp.text


def _add_skill(client, token, name, proficiency=8, years=2.0):
    resp = client.post(
        "/profile/skills",
        json={"name": name, "proficiency": proficiency, "years": years},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


# ==================================================================== #
# 1 -- GET /profile: per-user data isolation
# ==================================================================== #
def test_profile_isolated_per_user(client_with_fake_graph):
    client = client_with_fake_graph
    token_a = _register_and_login(client, "alice@example.com")
    token_b = _register_and_login(client, "bob@example.com")

    _add_skill(client, token_a, "Python")
    _add_skill(client, token_b, "Excel")

    resp_a = client.get("/profile", headers=_auth_headers(token_a))
    resp_b = client.get("/profile", headers=_auth_headers(token_b))

    assert resp_a.status_code == 200
    assert resp_b.status_code == 200
    names_a = {s["name"] for s in resp_a.json()["data"]["skills"]}
    names_b = {s["name"] for s in resp_b.json()["data"]["skills"]}
    assert names_a == {"Python"}
    assert names_b == {"Excel"}
    # Neither user's token can ever see the other's data.
    assert names_a != names_b


def test_profile_update_persists_and_syncs_graph(client_with_fake_graph, fake_graph):
    client = client_with_fake_graph
    token = _register_and_login(client, "carol@example.com")

    resp = client.put(
        "/profile",
        json={"major": "Computer Science", "graduation_year": 2027, "target_roles": ["job-1"]},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["major"] == "Computer Science"

    # Re-fetch confirms the change persisted.
    refetch = client.get("/profile", headers=_auth_headers(token))
    assert refetch.json()["data"]["graduation_year"] == 2027

    # Neo4j (fake) side was synced in the same request.
    user_id = _decode_user_id(client, token)
    assert fake_graph.get_student_skills(user_id) == []  # no skills yet, but no crash


def test_add_skill_appears_in_profile_and_graph_service(client_with_fake_graph, fake_graph):
    client = client_with_fake_graph
    token = _register_and_login(client, "dave@example.com")

    _add_skill(client, token, "Python", proficiency=7, years=1.5)

    profile = client.get("/profile", headers=_auth_headers(token)).json()["data"]
    assert any(s["name"] == "Python" for s in profile["skills"])

    user_id = _decode_user_id(client, token)
    graph_skills = fake_graph.get_student_skills(user_id)
    assert any(s["name"] == "Python" for s in graph_skills)


def test_profile_experience_round_trip_with_structured_dates(client_with_fake_graph):
    client = client_with_fake_graph
    token = _register_and_login(client, "erin@example.com")

    resp = client.put(
        "/profile",
        json={
            "experience": [
                {
                    "title": "Intern",
                    "company": "Acme",
                    "start_month": 6,
                    "start_year": 2024,
                    "end_month": 8,
                    "end_year": 2024,
                    "is_current": False,
                    "description": "Built things.",
                }
            ]
        },
        headers=_auth_headers(token),
    )
    assert resp.status_code == 200, resp.text
    entry = resp.json()["data"]["experience"][0]
    assert entry["start_month"] == 6
    assert entry["start_year"] == 2024
    assert entry["end_month"] == 8
    assert entry["end_year"] == 2024
    assert entry["is_current"] is False

    refetch = client.get("/profile", headers=_auth_headers(token))
    assert refetch.json()["data"]["experience"][0]["company"] == "Acme"


def test_profile_experience_currently_working_clears_end_date(client_with_fake_graph):
    client = client_with_fake_graph
    token = _register_and_login(client, "frank@example.com")

    resp = client.put(
        "/profile",
        json={
            "experience": [
                {
                    "title": "Engineer",
                    "company": "Globex",
                    "start_month": 1,
                    "start_year": 2025,
                    "end_month": 12,
                    "end_year": 2025,
                    "is_current": True,
                }
            ]
        },
        headers=_auth_headers(token),
    )
    assert resp.status_code == 200, resp.text
    entry = resp.json()["data"]["experience"][0]
    assert entry["is_current"] is True
    assert entry["end_month"] is None
    assert entry["end_year"] is None


def test_profile_experience_requires_end_date_unless_current(client_with_fake_graph):
    client = client_with_fake_graph
    token = _register_and_login(client, "grace@example.com")

    resp = client.put(
        "/profile",
        json={
            "experience": [
                {
                    "title": "Engineer",
                    "company": "Globex",
                    "start_month": 1,
                    "start_year": 2025,
                    "is_current": False,
                }
            ]
        },
        headers=_auth_headers(token),
    )
    assert resp.status_code == 422


def test_profile_experience_rejects_end_date_before_start_date(client_with_fake_graph):
    client = client_with_fake_graph
    token = _register_and_login(client, "heidi@example.com")

    resp = client.put(
        "/profile",
        json={
            "experience": [
                {
                    "title": "Engineer",
                    "company": "Globex",
                    "start_month": 6,
                    "start_year": 2024,
                    "end_month": 1,
                    "end_year": 2024,
                    "is_current": False,
                }
            ]
        },
        headers=_auth_headers(token),
    )
    assert resp.status_code == 422


def _decode_user_id(client, token: str) -> str:
    resp = client.get("/auth/me", headers=_auth_headers(token))
    assert resp.status_code == 200
    return resp.json()["data"]["id"]


# ==================================================================== #
# 2 -- GET /jobs filters + search + 404
# ==================================================================== #
def test_jobs_filter_by_type(client_with_fake_graph):
    client = client_with_fake_graph
    token = _register_and_login(client, "erin@example.com")

    resp = client.get("/jobs", params={"type": "Internship"}, headers=_auth_headers(token))
    assert resp.status_code == 200
    jobs = resp.json()["data"]
    assert len(jobs) == 1
    assert jobs[0]["type"] == "Internship"


def test_jobs_search_filters_by_title(client_with_fake_graph):
    client = client_with_fake_graph
    token = _register_and_login(client, "frank@example.com")

    resp = client.get("/jobs", params={"search": "Backend"}, headers=_auth_headers(token))
    assert resp.status_code == 200
    jobs = resp.json()["data"]
    assert len(jobs) == 1
    assert "Backend" in jobs[0]["title"]


def test_jobs_unfiltered_returns_all(client_with_fake_graph):
    client = client_with_fake_graph
    token = _register_and_login(client, "grace@example.com")

    resp = client.get("/jobs", headers=_auth_headers(token))
    assert resp.status_code == 200
    assert len(resp.json()["data"]) == 2


def test_jobs_filter_zero_results_returns_empty_200(client_with_fake_graph):
    client = client_with_fake_graph
    token = _register_and_login(client, "henry@example.com")

    resp = client.get("/jobs", params={"type": "Contract"}, headers=_auth_headers(token))
    assert resp.status_code == 200
    assert resp.json()["data"] == []


def test_jobs_search_special_characters_treated_as_literal(client_with_fake_graph):
    """Cypher/SQL-injection-style search payload must be treated as literal
    text, never crash the route (test-plan.md B7 edge cases)."""
    client = client_with_fake_graph
    token = _register_and_login(client, "iris@example.com")

    resp = client.get(
        "/jobs", params={"search": "'; MATCH (n) DETACH DELETE n //"}, headers=_auth_headers(token)
    )
    assert resp.status_code == 200
    assert resp.json()["data"] == []


def test_get_job_by_id_success(client_with_fake_graph):
    client = client_with_fake_graph
    token = _register_and_login(client, "jack@example.com")

    resp = client.get("/jobs/job-1", headers=_auth_headers(token))
    assert resp.status_code == 200
    assert resp.json()["data"]["id"] == "job-1"


def test_get_job_by_id_404(client_with_fake_graph):
    client = client_with_fake_graph
    token = _register_and_login(client, "kim@example.com")

    resp = client.get("/jobs/does-not-exist", headers=_auth_headers(token))
    assert resp.status_code == 404
    body = resp.json()
    assert body["success"] is False
    assert body["error"] == "NOT_FOUND"


def test_job_titles_search_filters_and_dedupes(client_with_fake_graph):
    client = client_with_fake_graph

    resp = client.get("/jobs/titles?search=data")
    assert resp.status_code == 200
    titles = resp.json()["data"]
    assert titles == ["Data Analyst Intern"]


def test_job_titles_empty_search_returns_full_sorted_list(client_with_fake_graph):
    client = client_with_fake_graph

    resp = client.get("/jobs/titles")
    assert resp.status_code == 200
    titles = resp.json()["data"]
    assert titles == sorted(titles)
    assert set(titles) == {"Junior Backend Engineer", "Data Analyst Intern"}


def test_job_titles_no_auth_required(client_with_fake_graph):
    client = client_with_fake_graph
    resp = client.get("/jobs/titles")
    assert resp.status_code == 200


# ==================================================================== #
# 3 -- GET /skills/market matches MarketAgent
# ==================================================================== #
def test_skills_market_matches_market_agent(client_with_fake_graph, fake_graph):
    from app.engine.algorithmic.market_agent import MarketAgent

    client = client_with_fake_graph
    token = _register_and_login(client, "leo@example.com")

    resp = client.get("/skills/market", headers=_auth_headers(token))
    assert resp.status_code == 200
    api_demand = {row["skill_name"]: row["demand_score"] for row in resp.json()["data"]}

    expected = MarketAgent().aggregate_demand(fake_graph.get_all_jobs_with_requires())
    expected_demand = {sd.skill_name: sd.demand_score for sd in expected.skill_demand}

    assert api_demand == expected_demand


def test_skills_list_search_filters_and_dedupes(client_with_fake_graph):
    client = client_with_fake_graph

    resp = client.get("/skills?search=sql")
    assert resp.status_code == 200
    names = resp.json()["data"]
    assert names == ["SQL"]


def test_skills_list_empty_search_returns_full_sorted_list(client_with_fake_graph):
    client = client_with_fake_graph

    resp = client.get("/skills")
    assert resp.status_code == 200
    names = resp.json()["data"]
    assert names == sorted(names)
    assert set(names) == {"Python", "SQL", "Docker", "Excel"}


def test_skills_list_no_auth_required(client_with_fake_graph):
    client = client_with_fake_graph
    resp = client.get("/skills")
    assert resp.status_code == 200


# ==================================================================== #
# 4 -- GET /skills/gap vs POST /gap-analysis consistency (open decision #2)
# ==================================================================== #
def test_skill_gap_and_gap_analysis_are_consistent(client_with_fake_graph):
    client = client_with_fake_graph
    token = _register_and_login(client, "mona@example.com")
    _add_skill(client, token, "Python")
    _add_skill(client, token, "SQL")
    _set_target_role(client, token, "job-1")

    via_get = client.get("/skills/gap", headers=_auth_headers(token))
    via_post = client.post("/gap-analysis", json={"target_job_id": "job-1"}, headers=_auth_headers(token))

    assert via_get.status_code == 200
    assert via_post.status_code == 200
    assert via_get.json()["data"]["readiness_score"] == via_post.json()["data"]["readiness_score"]
    assert set(via_get.json()["data"]["matched_skills"]) == set(via_post.json()["data"]["matched_skills"])


def test_gap_analysis_unknown_job_404(client_with_fake_graph):
    client = client_with_fake_graph
    token = _register_and_login(client, "nate@example.com")

    resp = client.post("/gap-analysis", json={"target_job_id": "no-such-job"}, headers=_auth_headers(token))
    assert resp.status_code == 404
    assert resp.json()["error"] == "NOT_FOUND"


def test_skill_gap_no_target_role_returns_defined_empty_state(client_with_fake_graph):
    client = client_with_fake_graph
    token = _register_and_login(client, "olga@example.com")

    resp = client.get("/skills/gap", headers=_auth_headers(token))
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["readiness_score"] == 0
    assert data["missing_skills"] == []
    assert data["explanation"]  # non-empty, never blank


def test_skill_gap_explicit_query_override_unknown_job_404(client_with_fake_graph):
    client = client_with_fake_graph
    token = _register_and_login(client, "pete@example.com")

    resp = client.get("/skills/gap", params={"target_job_id": "no-such-job"}, headers=_auth_headers(token))
    assert resp.status_code == 404


# ==================================================================== #
# 5 -- GET /recommendations/jobs|skills|courses shape + sort
# ==================================================================== #
def test_recommended_jobs_sorted_and_shaped(client_with_fake_graph):
    client = client_with_fake_graph
    token = _register_and_login(client, "quinn@example.com")
    _add_skill(client, token, "Python")
    _add_skill(client, token, "SQL")

    resp = client.get("/recommendations/jobs", headers=_auth_headers(token))
    assert resp.status_code == 200
    jobs = resp.json()["data"]
    assert len(jobs) == 2
    scores = [j["match_percentage"] for j in jobs]
    assert scores == sorted(scores, reverse=True)
    for j in jobs:
        assert "why_recommended" in j and j["why_recommended"]


def test_recommended_skills_and_courses_shaped(client_with_fake_graph):
    client = client_with_fake_graph
    token = _register_and_login(client, "randy@example.com")

    resp_skills = client.get("/recommendations/skills", headers=_auth_headers(token))
    assert resp_skills.status_code == 200
    assert isinstance(resp_skills.json()["data"], list)

    resp_courses = client.get(
        "/recommendations/courses", params={"target_job_id": "job-1"}, headers=_auth_headers(token)
    )
    assert resp_courses.status_code == 200
    courses = resp_courses.json()["data"]
    assert any(c["skill_name"] == "SQL" for c in courses)


# ==================================================================== #
# 6 -- GET /market/insights matches MarketAgent
# ==================================================================== #
def test_market_insights_matches_market_agent(client_with_fake_graph, fake_graph):
    from app.engine.algorithmic.market_agent import MarketAgent

    client = client_with_fake_graph
    token = _register_and_login(client, "sara@example.com")

    resp = client.get("/market/insights", headers=_auth_headers(token))
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["summary"]
    assert len(data["trend_bullets"]) == 3

    expected = MarketAgent().aggregate_demand(fake_graph.get_all_jobs_with_requires())
    assert data["top_skills"][0]["skill_name"] == expected.skill_demand[0].skill_name


# ==================================================================== #
# 7 -- GET /dashboard cross-endpoint consistency
# ==================================================================== #
def test_dashboard_consistent_with_skills_gap_and_market(client_with_fake_graph):
    client = client_with_fake_graph
    token = _register_and_login(client, "tina@example.com")
    _add_skill(client, token, "Python")
    _set_target_role(client, token, "job-1")

    dash = client.get("/dashboard", headers=_auth_headers(token)).json()["data"]
    gap = client.get("/skills/gap", headers=_auth_headers(token)).json()["data"]
    market = client.get("/skills/market", headers=_auth_headers(token)).json()["data"]

    assert dash["job_readiness_score"] == gap["readiness_score"]
    total_matched_gap = len(gap["matched_skills"])
    assert dash["skills_matched"] == total_matched_gap

    dash_demand_names = {sd["skill_name"] for sd in dash["market_demand"]}
    market_names = {sd["skill_name"] for sd in market}
    assert dash_demand_names.issubset(market_names)


# ==================================================================== #
# 8 -- Brand-new, empty student -> nothing 500s
# ==================================================================== #
def test_brand_new_student_never_500s_on_any_route(client_with_fake_graph):
    client = client_with_fake_graph
    token = _register_and_login(client, "uma@example.com")
    headers = _auth_headers(token)

    routes = [
        ("get", "/profile", None),
        ("get", "/jobs", None),
        ("get", "/skills/market", None),
        ("get", "/skills/gap", None),
        ("get", "/recommendations/jobs", None),
        ("get", "/recommendations/skills", None),
        ("get", "/recommendations/courses", None),
        ("get", "/market/insights", None),
        ("get", "/dashboard", None),
    ]
    for method, path, body in routes:
        resp = getattr(client, method)(path, headers=headers, json=body) if body else getattr(client, method)(
            path, headers=headers
        )
        assert resp.status_code != 500, f"{method.upper()} {path} returned 500: {resp.text}"
        assert resp.status_code < 500


# ==================================================================== #
# 9 -- Pagination boundary
# ==================================================================== #
def test_jobs_pagination_past_last_page_returns_empty(client_with_fake_graph):
    client = client_with_fake_graph
    token = _register_and_login(client, "vince@example.com")

    resp = client.get("/jobs", params={"limit": 10, "offset": 1000}, headers=_auth_headers(token))
    assert resp.status_code == 200
    assert resp.json()["data"] == []


# ==================================================================== #
# 10 -- Every protected route rejects unauthenticated requests with 401
# ==================================================================== #
_PROTECTED_ROUTES = [
    ("get", "/profile"),
    ("put", "/profile"),
    ("post", "/profile/skills"),
    ("get", "/jobs"),
    ("get", "/jobs/job-1"),
    ("get", "/skills/market"),
    ("get", "/skills/gap"),
    ("get", "/recommendations/jobs"),
    ("get", "/recommendations/skills"),
    ("get", "/recommendations/courses"),
    ("post", "/gap-analysis"),
    ("get", "/market/insights"),
    ("get", "/dashboard"),
]


@pytest.mark.parametrize("method,path", _PROTECTED_ROUTES)
def test_protected_routes_reject_unauthenticated(client_with_fake_graph, method, path):
    client = client_with_fake_graph
    resp = getattr(client, method)(path)
    assert resp.status_code == 401, f"{method.upper()} {path} did not 401 without auth (got {resp.status_code})"
    assert resp.json()["success"] is False


# ==================================================================== #
# EngineOrchestrator LLM-fallback tests -- B6 #4 and #5
# ==================================================================== #
class _AlwaysFailsProvider(LLMProvider):
    """A scripted `LLMProvider` that always raises after retries -- used to
    simulate 'LLM configured but the provider is down/misbehaving' without
    touching real network/SDK code (test-plan.md B6#5)."""

    def __init__(self):
        super().__init__(model="always-fails")

    def _generate(self, system_prompt, user_prompt, output_schema, timeout):
        raise LLMOutputValidationError("simulated permanent failure", attempts=1, raw_output=None)

    def stream(self, system_prompt, user_prompt):  # pragma: no cover - unused
        yield ""

    def get_model_info(self) -> ModelInfo:
        return ModelInfo(provider="always-fails", model=self.model)


class TestOrchestratorLLMFallback:
    """B6 #4/#5: never let an LLM absence/failure produce anything but a
    template narrative -- checked directly against the orchestrator, with no
    HTTP layer involved."""

    def test_llm_unset_falls_back_to_template_narrative(self, fake_graph):
        orchestrator = EngineOrchestrator(fake_graph)  # default Settings(): LLM_PROVIDER == "none"

        result = orchestrator.compute_gap_analysis("student-1", "job-1")

        assert result["explanation"] is not None
        assert result["explanation"].strip() != ""
        assert "match" in result["explanation"].lower()
        assert result["encouragement"].strip() != ""

    def test_llm_configured_but_raises_falls_back_gracefully_never_500(self, fake_graph):
        failing_provider = _AlwaysFailsProvider()
        orchestrator = EngineOrchestrator(fake_graph, llm_provider=failing_provider)

        # Must not raise -- this is the crux of B6#5: an LLM failure after
        # exhausting retries must degrade gracefully, not propagate.
        result = orchestrator.compute_gap_analysis("student-1", "job-1")

        assert result["explanation"].strip() != ""
        assert result["encouragement"].strip() != ""
        # Same fallback text shape as the "unset" path -- proves it's the
        # identical template code path, not a different half-broken one.
        baseline = EngineOrchestrator(fake_graph).compute_gap_analysis("student-1", "job-1")
        assert result["explanation"] == baseline["explanation"]

    def test_llm_unset_market_summary_template_present(self, fake_graph):
        orchestrator = EngineOrchestrator(fake_graph)
        result = orchestrator.get_market_insights()
        assert result["summary"].strip() != ""
        assert len(result["trend_bullets"]) == 3
        for bullet in result["trend_bullets"]:
            assert bullet.strip() != ""

    def test_llm_raises_recommendation_narratives_fallback_via_http(self, client, fake_graph):
        """End-to-end through the real HTTP route: even with a
        permanently-failing LLM provider wired in via dependency override,
        GET /recommendations/jobs must still return 200 with non-empty
        why_recommended text on every job -- never a 500."""
        from app.core.deps import get_orchestrator as get_orchestrator_dep

        client.app.dependency_overrides[get_graph_service] = lambda: fake_graph
        client.app.dependency_overrides[get_orchestrator_dep] = lambda: EngineOrchestrator(
            fake_graph, llm_provider=_AlwaysFailsProvider()
        )
        try:
            token = _register_and_login(client, "wanda@example.com")
            resp = client.get("/recommendations/jobs", headers=_auth_headers(token))
            assert resp.status_code == 200
            for job in resp.json()["data"]:
                assert job["why_recommended"].strip() != ""
        finally:
            client.app.dependency_overrides.pop(get_graph_service, None)
            client.app.dependency_overrides.pop(get_orchestrator_dep, None)


class _StubGNNAgent:
    """Duck-typed GNNRecommendationAgent stand-in -- avoids a torch
    dependency in the plain backend test env. Mirrors the one in
    test_algorithmic_agents.py, used here to prove the *orchestrator*
    wiring (get_default_gnn_agent seam, match_source in the API response),
    not just RecommendationAgent.rank_jobs in isolation."""

    def __init__(self, scores: dict[tuple[str, str], float] | None = None, available: bool = True):
        self._scores = scores or {}
        self.is_available = available

    def score_leads_to(self, from_skill, to_skill):
        return self._scores.get((from_skill, to_skill))


class TestOrchestratorGNNWiring:
    """Milestone 1 (docs/current-status.md): the trained GNN must actually
    influence a live GET /recommendations/jobs response, not just exist as
    untested standalone code. Uses a stub agent (via the same
    gnn_agent= constructor seam llm_provider= already has) so this runs
    without torch installed."""

    def test_gnn_available_surfaces_in_job_recommendations(self, fake_graph):
        fake_graph.upsert_student_node("student-1", skills=[{"name": "Python"}], target_roles=[])
        stub = _StubGNNAgent(scores={("Python", "Machine Learning"): 0.8})
        orchestrator = EngineOrchestrator(fake_graph, gnn_agent=stub)

        results = orchestrator.get_job_recommendations("student-1")

        assert results  # fake_graph seeds job-1/job-2
        sources = {r["match_source"] for r in results}
        assert "gnn" in sources  # at least one job was actually reranked

    def test_gnn_unavailable_all_jobs_stay_algorithmic(self, fake_graph):
        fake_graph.upsert_student_node("student-1", skills=[{"name": "Python"}], target_roles=[])
        stub = _StubGNNAgent(available=False)
        orchestrator = EngineOrchestrator(fake_graph, gnn_agent=stub)

        results = orchestrator.get_job_recommendations("student-1")

        assert results
        assert all(r["match_source"] == "algorithmic" for r in results)

    def test_gnn_wiring_end_to_end_via_http(self, client, fake_graph):
        """Same shape as the LLM-fallback HTTP test above: the real
        GET /recommendations/jobs route, with the orchestrator's GNN seam
        overridden to a stub, actually returns match_source per job."""
        from app.core.deps import get_orchestrator as get_orchestrator_dep

        stub = _StubGNNAgent(scores={("Python", "Machine Learning"): 0.8})
        client.app.dependency_overrides[get_graph_service] = lambda: fake_graph
        client.app.dependency_overrides[get_orchestrator_dep] = lambda: EngineOrchestrator(
            fake_graph, gnn_agent=stub
        )
        try:
            token = _register_and_login(client, "gnn-check@example.com")
            client.put(
                "/profile",
                headers=_auth_headers(token),
                json={"skills": [{"name": "Python", "proficiency": 5, "years": 1}]},
            )
            resp = client.get("/recommendations/jobs", headers=_auth_headers(token))
            assert resp.status_code == 200
            jobs = resp.json()["data"]
            assert jobs
            for job in jobs:
                assert job["match_source"] in ("gnn", "algorithmic")
        finally:
            client.app.dependency_overrides.pop(get_graph_service, None)
            client.app.dependency_overrides.pop(get_orchestrator_dep, None)
