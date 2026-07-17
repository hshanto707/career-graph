"""B4 — Ingestion Pipeline (IngestionAgent + NormalizationAgent).
Mirrors test-plan.md §B4: every red/green test + documented edge case.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.engine.ingestion.ingestion_agent import IngestionAgent
from app.engine.ingestion.normalization_agent import NormalizationAgent
from app.routers import admin as admin_router
from tests.fakes import FakeGraphService

BACKEND_ROOT = Path(__file__).resolve().parent.parent
REAL_DATA_DIR = BACKEND_ROOT / "data"

CSV_HEADER = "title,company,location,type,skills_required,salary_min,salary_max,category\n"


# ------------------------------------------------------------------ #
# Fixtures
# ------------------------------------------------------------------ #
@pytest.fixture()
def synonyms_path(tmp_path) -> Path:
    path = tmp_path / "synonyms.json"
    path.write_text(json.dumps({"ReactJS": "React", "Node": "Node.js"}), encoding="utf-8")
    return path


@pytest.fixture()
def onet_path(tmp_path) -> Path:
    path = tmp_path / "onet_skills.csv"
    path.write_text(
        "skill_name,category\n"
        "Python,Programming Languages\n"
        "JavaScript,Programming Languages\n"
        "React,Web Frameworks\n"
        "Node.js,Web Frameworks\n"
        "SQL,Databases\n"
        "Docker,Cloud & DevOps\n"
        "Kubernetes,Cloud & DevOps\n",
        encoding="utf-8",
    )
    return path


@pytest.fixture()
def normalizer(synonyms_path, onet_path) -> NormalizationAgent:
    return NormalizationAgent(
        graph_service=FakeGraphService(),
        synonyms_path=synonyms_path,
        onet_skills_path=onet_path,
    )


@pytest.fixture()
def graph() -> FakeGraphService:
    return FakeGraphService()


@pytest.fixture()
def normalizer_for(synonyms_path, onet_path):
    def _build(graph_service) -> NormalizationAgent:
        return NormalizationAgent(
            graph_service=graph_service,
            synonyms_path=synonyms_path,
            onet_skills_path=onet_path,
        )

    return _build


# ------------------------------------------------------------------ #
# IngestionAgent — CSV read/validate/parse
# ------------------------------------------------------------------ #
def test_valid_csv_row_parsed_into_record():
    csv_text = (
        CSV_HEADER
        + 'Backend Developer,Acme Inc,Remote,Full-time,"Python, SQL, Docker",70000,90000,Engineering\n'
    )
    result = IngestionAgent().read_csv(csv_text)

    assert result.stats.rows_read == 1
    assert result.stats.rows_dropped == 0
    record = result.records[0]
    assert record["title"] == "Backend Developer"
    assert record["company"] == "Acme Inc"
    assert record["skills_required"] == ["Python", "SQL", "Docker"]
    assert record["salary_min"] == 70000
    assert record["salary_max"] == 90000
    assert record["location"] == "Remote"
    assert record["type"] == "Full-time"


def test_malformed_row_missing_title_is_dropped_not_crashed():
    csv_text = (
        CSV_HEADER
        + ',Ghost Corp,Remote,Full-time,"Python, SQL",50000,70000,Engineering\n'
        + "Data Analyst,RealCo,Remote,Full-time,\"SQL, Excel\",60000,80000,Data\n"
    )
    result = IngestionAgent().read_csv(csv_text)

    assert result.stats.rows_read == 2
    assert result.stats.rows_dropped == 1
    assert "missing title" in result.stats.drop_reasons
    assert len(result.records) == 1
    assert result.records[0]["title"] == "Data Analyst"


def test_malformed_row_missing_company_is_dropped():
    csv_text = (
        CSV_HEADER
        + 'Data Analyst,,Remote,Full-time,"SQL, Excel",60000,80000,Data\n'
    )
    result = IngestionAgent().read_csv(csv_text)
    assert result.stats.rows_dropped == 1
    assert result.records == []


def test_missing_required_columns_raises():
    csv_text = "title,company\nFoo,Bar\n"
    with pytest.raises(ValueError):
        IngestionAgent().read_csv(csv_text)


def test_empty_csv_only_header_row_produces_no_records_no_crash():
    result = IngestionAgent().read_csv(CSV_HEADER)
    assert result.stats.rows_read == 0
    assert result.records == []


def test_csv_whitespace_and_empty_entries_in_skills_are_cleaned():
    csv_text = (
        CSV_HEADER
        + 'Backend Developer,Acme Inc,Remote,Full-time," Python, , SQL ",70000,90000,Engineering\n'
    )
    result = IngestionAgent().read_csv(csv_text)
    assert result.records[0]["skills_required"] == ["Python", "SQL"]


def test_csv_duplicate_skills_in_one_row_are_deduped():
    csv_text = (
        CSV_HEADER
        + 'Backend Developer,Acme Inc,Remote,Full-time,"Python, Python, SQL",70000,90000,Engineering\n'
    )
    result = IngestionAgent().read_csv(csv_text)
    assert result.records[0]["skills_required"] == ["Python", "SQL"]


def test_csv_case_insensitive_duplicate_skills_deduped():
    csv_text = (
        CSV_HEADER
        + 'Backend Developer,Acme Inc,Remote,Full-time,"python, Python, SQL",70000,90000,Engineering\n'
    )
    result = IngestionAgent().read_csv(csv_text)
    assert result.records[0]["skills_required"] == ["python", "SQL"]


def test_csv_bom_and_crlf_line_endings_do_not_choke_parser():
    csv_bytes = (CSV_HEADER + 'Backend Developer,Acme Inc,Remote,Full-time,"Python, SQL",70000,90000,Engineering\r\n').encode(
        "utf-8-sig"
    )
    result = IngestionAgent().read_csv(csv_bytes)
    assert result.stats.rows_read == 1
    assert result.records[0]["title"] == "Backend Developer"


def test_large_skills_list_on_one_row_parses_correctly():
    skills = ", ".join(f"Skill{i}" for i in range(50))
    csv_text = CSV_HEADER + f'Backend Developer,Acme Inc,Remote,Full-time,"{skills}",70000,90000,Engineering\n'
    result = IngestionAgent().read_csv(csv_text)
    assert len(result.records[0]["skills_required"]) == 50


def test_salary_min_greater_than_max_is_dropped():
    csv_text = (
        CSV_HEADER
        + 'Backend Developer,Acme Inc,Remote,Full-time,"Python, SQL",90000,70000,Engineering\n'
    )
    result = IngestionAgent().read_csv(csv_text)
    assert result.stats.rows_dropped == 1
    assert result.records == []


# ------------------------------------------------------------------ #
# NormalizationAgent — exact synonym / fuzzy match / flag-for-review
# ------------------------------------------------------------------ #
def test_exact_synonym_match_reactjs_to_react(normalizer):
    resolved = normalizer.normalize_skill("ReactJS")
    assert resolved.normalized_name == "React"
    assert resolved.flagged is False
    assert resolved.match_type == "exact_synonym"


def test_exact_synonym_match_node_to_node_js(normalizer):
    resolved = normalizer.normalize_skill("Node")
    assert resolved.normalized_name == "Node.js"
    assert resolved.flagged is False


def test_already_canonical_name_passes_through_unflagged(normalizer):
    resolved = normalizer.normalize_skill("Python")
    assert resolved.normalized_name == "Python"
    assert resolved.flagged is False
    assert resolved.match_type == "already_canonical"


def test_fuzzy_match_at_or_above_threshold_resolves_to_canonical(normalizer):
    # "Pythonn" is a one-letter typo of the canonical O*NET name "Python";
    # WRatio scores this at ~92, comfortably >= the 90 threshold.
    resolved = normalizer.normalize_skill("Pythonn")
    assert resolved.normalized_name == "Python"
    assert resolved.flagged is False
    assert resolved.match_type == "fuzzy"


def test_fuzzy_match_below_threshold_keeps_raw_and_flags(normalizer):
    # "Pythom" only scores ~83 against "Python" -- below the 90 cutoff.
    resolved = normalizer.normalize_skill("Pythom")
    assert resolved.normalized_name == "Pythom"
    assert resolved.flagged is True
    assert resolved.match_type == "unmatched"


def test_completely_unrelated_skill_is_flagged_not_silently_dropped(normalizer):
    resolved = normalizer.normalize_skill("Xyzzyqux12345")
    assert resolved.flagged is True
    assert resolved.normalized_name == "Xyzzyqux12345"


def test_fuzzy_match_tie_is_broken_deterministically(normalizer, monkeypatch):
    """Two O*NET names tie at the same top fuzzy score -- the tie-breaker
    must be deterministic (alphabetically-first canonical name), never
    'whatever the library returns first'."""
    tied_matches = [("Zeta Skill", 95.0, 0), ("Alpha Skill", 95.0, 1), ("Beta Skill", 80.0, 2)]

    def fake_extract(*args, **kwargs):
        return tied_matches

    monkeypatch.setattr(
        "app.engine.ingestion.normalization_agent.process.extract", fake_extract
    )
    resolved = normalizer.normalize_skill("Something Close")
    assert resolved.normalized_name == "Alpha Skill"
    assert resolved.match_type == "fuzzy"


def test_importance_derived_from_position_first_half_is_must(normalizer_for):
    graph = FakeGraphService()
    agent = normalizer_for(graph)
    records = [
        {
            "title": "Backend Developer",
            "company": "Acme Inc",
            "location": "Remote",
            "type": "Full-time",
            "skills_required": ["Python", "SQL", "Docker", "Kubernetes"],
            "salary_min": 70000,
            "salary_max": 90000,
            "category": "Engineering",
        }
    ]
    agent.process_and_write(records)

    job_id = agent._job_id("Acme Inc", "Backend Developer")
    edges = graph._requires_edges[job_id]
    assert edges["Python"]["importance"] == "must"
    assert edges["SQL"]["importance"] == "must"
    assert edges["Docker"]["importance"] == "nice"
    assert edges["Kubernetes"]["importance"] == "nice"


# ------------------------------------------------------------------ #
# Neo4j MERGE idempotency (via FakeGraphService)
# ------------------------------------------------------------------ #
def test_reingesting_same_csv_twice_does_not_duplicate_nodes_or_edges(normalizer_for):
    graph = FakeGraphService()
    agent = normalizer_for(graph)
    records = [
        {
            "title": "Backend Developer",
            "company": "Acme Inc",
            "location": "Remote",
            "type": "Full-time",
            "skills_required": ["Python", "SQL"],
            "salary_min": 70000,
            "salary_max": 90000,
            "category": "Engineering",
        },
        {
            "title": "Data Analyst",
            "company": "Acme Inc",
            "location": "Remote",
            "type": "Full-time",
            "skills_required": ["SQL", "Python"],
            "salary_min": 60000,
            "salary_max": 80000,
            "category": "Data",
        },
    ]

    agent.process_and_write(records)
    jobs_after_first = graph.count_jobs()
    skills_after_first = graph.count_skills()
    edges_after_first = graph.count_requires_edges()

    # Run again on identical input.
    agent.process_and_write(records)

    assert graph.count_jobs() == jobs_after_first == 2
    assert graph.count_skills() == skills_after_first == 2
    assert graph.count_requires_edges() == edges_after_first == 4


def test_reingesting_after_synonym_added_reresolves_a_previously_flagged_skill(tmp_path, onet_path):
    """If synonyms.json gains a new mapping between runs, re-running
    normalization must re-resolve (and un-flag) the previously-flagged
    skill rather than sticking with the stale flag forever."""
    synonyms_path = tmp_path / "synonyms.json"
    synonyms_path.write_text(json.dumps({}), encoding="utf-8")

    graph = FakeGraphService()
    agent = NormalizationAgent(graph_service=graph, synonyms_path=synonyms_path, onet_skills_path=onet_path)

    record = {
        "title": "Backend Developer",
        "company": "Acme Inc",
        "location": "Remote",
        "type": "Full-time",
        "skills_required": ["ReactJS"],
        "salary_min": 70000,
        "salary_max": 90000,
        "category": "Engineering",
    }
    agent.process_and_write([record])
    assert graph.get_skill_node("ReactJS")["flagged_for_review"] is True

    # Update the synonym map to add the mapping, then re-run.
    synonyms_path.write_text(json.dumps({"ReactJS": "React"}), encoding="utf-8")
    agent2 = NormalizationAgent(graph_service=graph, synonyms_path=synonyms_path, onet_skills_path=onet_path)
    agent2.process_and_write([record])

    assert graph.get_skill_node("React")["flagged_for_review"] is False


# ------------------------------------------------------------------ #
# Admin endpoint — POST /admin/ingest/csv, GET /admin/ingest/status
# ------------------------------------------------------------------ #
@pytest.fixture()
def admin_client(client):
    fake_graph = FakeGraphService()
    client.app.dependency_overrides[admin_router.get_graph_service] = lambda: fake_graph
    admin_router._last_run_stats = None
    yield client, fake_graph
    client.app.dependency_overrides.pop(admin_router.get_graph_service, None)


def _upload_csv(client, token, content: bytes = None):
    content = content or (
        CSV_HEADER
        + 'Backend Developer,Acme Inc,Remote,Full-time,"Python, SQL",70000,90000,Engineering\n'
        + ',Ghost Corp,Remote,Full-time,"Python",50000,70000,Engineering\n'
    ).encode("utf-8")
    headers = {"X-Admin-Token": token} if token is not None else {}
    return client.post(
        "/admin/ingest/csv",
        files={"file": ("jobs.csv", content, "text/csv")},
        headers=headers,
    )


def test_ingest_csv_rejected_without_admin_token(admin_client):
    client, _ = admin_client
    response = _upload_csv(client, token=None)
    assert response.status_code == 401
    assert response.json()["success"] is False


def test_ingest_csv_rejected_with_wrong_admin_token(admin_client):
    client, _ = admin_client
    response = _upload_csv(client, token="totally-wrong-token")
    assert response.status_code == 401


def test_ingest_status_rejected_without_admin_token(admin_client):
    client, _ = admin_client
    response = client.get("/admin/ingest/status")
    assert response.status_code == 401


def test_ingest_csv_end_to_end_with_valid_admin_token(admin_client):
    from app.core.config import get_settings

    client, fake_graph = admin_client
    token = get_settings().ADMIN_TOKEN

    response = _upload_csv(client, token=token)
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    stats = body["data"]
    assert stats["rows_read"] == 2
    assert stats["rows_dropped"] == 1
    assert "missing title" in stats["drop_reasons"]
    assert stats["jobs_written"] == 1
    assert fake_graph.count_jobs() == 1


def test_ingest_status_no_runs_yet_before_any_ingestion(admin_client):
    from app.core.config import get_settings

    client, _ = admin_client
    token = get_settings().ADMIN_TOKEN
    response = client.get("/admin/ingest/status", headers={"X-Admin-Token": token})
    assert response.status_code == 200
    assert response.json()["data"]["has_run"] is False


def test_ingest_status_reflects_last_run_after_ingestion(admin_client):
    from app.core.config import get_settings

    client, _ = admin_client
    token = get_settings().ADMIN_TOKEN

    _upload_csv(client, token=token)
    response = client.get("/admin/ingest/status", headers={"X-Admin-Token": token})

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["has_run"] is True
    assert data["rows_read"] == 2


# ------------------------------------------------------------------ #
# Real placeholder fixtures sanity (data/kaggle_jobs.csv, onet_skills.csv,
# synonyms.json actually load and are internally consistent)
# ------------------------------------------------------------------ #
def test_real_placeholder_fixtures_load_and_ingest_without_error():
    ingestion_result = IngestionAgent().read_csv(REAL_DATA_DIR / "kaggle_jobs.csv")
    assert ingestion_result.stats.rows_read >= 190
    assert len(ingestion_result.records) >= 190
    # The dataset (now ~10k realistic-scale rows) is expected to be clean at
    # the row-structure level — malformed-row handling is covered separately
    # by the synthetic-fixture tests above; this near-zero bound just guards
    # against a future data refresh silently reintroducing bulk breakage.
    assert ingestion_result.stats.rows_dropped <= 0.01 * ingestion_result.stats.rows_read

    agent = NormalizationAgent(
        graph_service=FakeGraphService(),
        synonyms_path=REAL_DATA_DIR / "synonyms.json",
        onet_skills_path=REAL_DATA_DIR / "onet_skills.csv",
    )
    stats = agent.process_and_write(ingestion_result.records[:20])
    assert stats.jobs_written == 20
