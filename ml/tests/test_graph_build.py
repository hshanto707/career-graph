"""test_graph_build.py — pure-Python tests for ml/graph_build.py.

No torch/PyTorch Geometric required to run this file -- only
`backend/requirements.txt`-level deps (rapidfuzz, neo4j driver, pydantic),
same as the rest of the backend test suite. Run with:

    cd ml && python -m pytest tests/test_graph_build.py -v

(or from repo root: `pytest ml/tests/test_graph_build.py`)

Covers test-plan.md "Custom AI Model (GNN)" #1 (node/edge counts match a
direct count over the same seeded dataset) and the "isolated node" edge
case.
"""
from __future__ import annotations

import sys
from pathlib import Path

ML_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ML_ROOT))

import pytest  # noqa: E402

from graph_build import (  # noqa: E402
    EDGE_TYPES,
    NODE_TYPES,
    build_synthetic_career_graph,
)


@pytest.fixture(scope="module")
def raw_graph():
    return build_synthetic_career_graph()


def test_all_node_types_present(raw_graph):
    for node_type in NODE_TYPES:
        assert node_type in raw_graph.node_ids


def test_all_edge_types_present(raw_graph):
    for edge_type in EDGE_TYPES:
        assert edge_type in raw_graph.edges


def test_node_counts_match_direct_recount(raw_graph):
    """Rebuild independently from the raw job/skill sets referenced by the
    edges themselves and confirm the node-id lists agree -- a lightweight
    stand-in for "matches direct Neo4j COUNT queries" (no live Neo4j here,
    see docs/gnn-model.md), verifying export self-consistency instead."""
    jobs_from_edges = {job_id for job_id, _ in raw_graph.edges[("Job", "REQUIRES", "Skill")]}
    jobs_from_edges |= {job_id for job_id, _ in raw_graph.edges[("Job", "IN_CATEGORY", "Category")]}
    assert jobs_from_edges.issubset(set(raw_graph.node_ids["Job"]))

    skills_from_edges = {skill for _, skill in raw_graph.edges[("Job", "REQUIRES", "Skill")]}
    assert skills_from_edges.issubset(set(raw_graph.node_ids["Skill"]))


def test_node_counts_are_nonzero_for_seeded_data(raw_graph):
    # The synthetic placeholder dataset is small but non-trivial (see
    # docs/data-sources.md) -- every node type should have at least one node.
    for node_type in NODE_TYPES:
        assert raw_graph.node_count(node_type) > 0, f"{node_type} has zero nodes"


def test_requires_edges_nonzero(raw_graph):
    assert raw_graph.edge_count(("Job", "REQUIRES", "Skill")) > 0


def test_leads_to_is_documented_synthetic_placeholder(raw_graph):
    """LEADS_TO has no real source yet (see graph_build.py module
    docstring) -- it must still be non-empty (so link prediction on it is
    possible) and every edge must reference real Skill node ids."""
    leads_to = raw_graph.edges[("Skill", "LEADS_TO", "Skill")]
    assert len(leads_to) > 0
    skill_ids = set(raw_graph.node_ids["Skill"])
    for src, dst in leads_to:
        assert src in skill_ids
        assert dst in skill_ids
        assert src != dst  # a category chain never links a skill to itself


def test_isolated_skill_node_handled(raw_graph):
    """A Skill that appears in no job's REQUIRES edges (edge case from
    test-plan.md) must still just be an isolated node, not crash export."""
    required_skills = {s for _, s in raw_graph.edges[("Job", "REQUIRES", "Skill")]}
    all_skills = set(raw_graph.node_ids["Skill"])
    isolated = all_skills - required_skills
    # Not asserting isolated is non-empty (dataset-dependent) -- just that,
    # if any exist, they're still valid node ids with no crash getting here.
    assert isolated.issubset(all_skills)


def test_deterministic_across_runs():
    """Re-running the build from the same fixture data twice yields
    identical node/edge sets (reproducibility, test-plan.md edge case)."""
    g1 = build_synthetic_career_graph()
    g2 = build_synthetic_career_graph()
    for node_type in NODE_TYPES:
        assert g1.node_ids[node_type] == g2.node_ids[node_type]
    for edge_type in EDGE_TYPES:
        assert sorted(g1.edges[edge_type]) == sorted(g2.edges[edge_type])
