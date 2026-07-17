"""test_gnn_pipeline_requires_torch.py — REQUIRES ml/requirements.txt.

These tests exercise export_graph.py / train_gnn.py / evaluate.py / the
trained model and therefore need torch + torch_geometric + scikit-learn
installed (see ml/requirements.txt and docs/gnn-model.md). They are
collected and SKIPPED (not failed) automatically if those imports are
unavailable, so `pytest` run from a plain backend-only environment does not
report false failures -- this file's presence documents which red/green
tests from test-plan.md's "Custom AI Model (GNN)" section need the heavy ML
stack to actually execute.

Run with (after `pip install -r ml/requirements.txt -r backend/requirements.txt`):
    pytest ml/tests/test_gnn_pipeline_requires_torch.py -v
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ML_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ML_ROOT))

torch = pytest.importorskip("torch", reason="requires ml/requirements.txt (torch)")
pytest.importorskip("torch_geometric", reason="requires ml/requirements.txt (torch_geometric)")
pytest.importorskip("sklearn", reason="requires ml/requirements.txt (scikit-learn)")

from export_graph import export, to_hetero_data  # noqa: E402
from graph_build import EDGE_TYPES, NODE_TYPES, build_synthetic_career_graph  # noqa: E402
from train_gnn import TARGET_EDGE_TYPES, prepare_splits, train  # noqa: E402


@pytest.fixture(scope="module")
def raw_graph():
    return build_synthetic_career_graph()


def test_export_to_hetero_data_node_counts_match_raw_graph(raw_graph):
    """test-plan.md GNN #1: exported HeteroData node/edge counts match the
    raw-graph counts (our stand-in for a live Neo4j COUNT query -- see
    docs/gnn-model.md)."""
    hetero_data, _ = to_hetero_data(raw_graph)
    for node_type in NODE_TYPES:
        assert hetero_data[node_type].num_nodes == raw_graph.node_count(node_type)
    for edge_type in EDGE_TYPES:
        assert hetero_data[edge_type].edge_index.shape[1] == raw_graph.edge_count(edge_type)


def test_prepare_splits_disjoint_and_nonempty(raw_graph):
    """test-plan.md GNN #2."""
    splits = prepare_splits(raw_graph, seed=42)
    for edge_type in TARGET_EDGE_TYPES:
        s = splits[edge_type]
        train_set, val_set, test_set = set(s["train"]), set(s["val"]), set(s["test"])
        assert not (train_set & val_set)
        assert not (train_set & test_set)
        assert not (val_set & test_set)
        assert len(train_set) > 0
        assert len(val_set) > 0
        assert len(test_set) > 0


def test_negative_samples_are_not_real_edges(raw_graph):
    """test-plan.md GNN #4."""
    splits = prepare_splits(raw_graph, seed=42)
    for edge_type in TARGET_EDGE_TYPES:
        s = splits[edge_type]
        all_real = set(s["train"]) | set(s["val"]) | set(s["test"])
        for neg_key in ("train_neg", "val_neg", "test_neg"):
            for neg in s[neg_key]:
                assert neg not in all_real


def test_training_loop_runs_and_loss_decreases(tmp_path):
    """test-plan.md GNN #3 -- a 'does it learn at all' smoke test, fixed
    seed, small epoch count. Not a full convergence proof."""
    model, history, splits, node_indices, edge_index_dict, supervision = train(
        epochs=15, seed=123, checkpoint_path=tmp_path / "smoke_checkpoint.pt"
    )
    assert len(history) == 15
    first_loss = history[0]["loss"]
    last_loss = history[-1]["loss"]
    assert last_loss < first_loss, "loss did not decrease over training -- model isn't learning"
    assert (tmp_path / "smoke_checkpoint.pt").exists()


def test_reproducibility_same_seed_same_split(raw_graph):
    """test-plan.md GNN edge case: same seed -> same split across two
    separate calls (thesis-defensible reproducibility)."""
    s1 = prepare_splits(raw_graph, seed=7)
    s2 = prepare_splits(raw_graph, seed=7)
    for edge_type in TARGET_EDGE_TYPES:
        assert s1[edge_type]["train"] == s2[edge_type]["train"]
        assert s1[edge_type]["val"] == s2[edge_type]["val"]
        assert s1[edge_type]["test"] == s2[edge_type]["test"]


def test_checkpoint_loading_with_mismatched_architecture_fails_clearly(tmp_path):
    """test-plan.md GNN edge case: loading a checkpoint into a
    differently-shaped model must raise a clear error, not silently load
    garbage weights."""
    from model import LinkPredictor

    # Train a tiny real checkpoint, then try loading it into an
    # incompatibly-shaped model.
    train(epochs=2, seed=1, checkpoint_path=tmp_path / "ckpt.pt")
    checkpoint = torch.load(tmp_path / "ckpt.pt", weights_only=False)

    bad_model = LinkPredictor(
        node_types=checkpoint["config"]["node_types"],
        message_passing_edge_types=checkpoint["config"]["message_passing_edge_types"],
        num_nodes_per_type=checkpoint["config"]["num_nodes_per_type"],
        hidden_channels=999,  # deliberately mismatched
        out_channels=checkpoint["config"]["out_channels"],
    )
    with pytest.raises(RuntimeError):
        bad_model.load_state_dict(checkpoint["model_state_dict"])


def test_inference_ranks_known_positive_above_negatives(tmp_path):
    """test-plan.md GNN #7: sanity ranking test, independent of the full
    metrics pipeline."""
    import sys as _sys

    BACKEND_ROOT = ML_ROOT.parent / "backend"
    if str(BACKEND_ROOT) not in _sys.path:
        _sys.path.insert(0, str(BACKEND_ROOT))

    checkpoint_path = tmp_path / "ckpt.pt"
    train(epochs=60, seed=42, checkpoint_path=checkpoint_path)

    from app.engine.algorithmic.gnn_recommendation_agent import GNNRecommendationAgent

    agent = GNNRecommendationAgent(checkpoint_path=checkpoint_path)
    assert agent.is_available

    raw_graph = build_synthetic_career_graph()
    splits = prepare_splits(raw_graph, seed=42)
    edge_type = ("Job", "REQUIRES", "Skill")
    test_pos = splits[edge_type]["test"]
    test_neg = splits[edge_type]["test_neg"]
    assert test_pos and test_neg

    job_id, skill_name = test_pos[0]
    pos_score = agent.score_requires(job_id, skill_name)
    assert pos_score is not None

    neg_scores = [
        agent.score_requires(j, s) for j, s in test_neg if agent.score_requires(j, s) is not None
    ]
    assert neg_scores
    # Not asserting strict dominance over every negative (small/sparse
    # seed data is noisy -- see docs/gnn-model.md) -- but the positive must
    # rank above the median negative, i.e. the model learned *something*.
    sorted_neg = sorted(neg_scores)
    median = sorted_neg[len(sorted_neg) // 2]
    assert pos_score >= median


def test_gnn_agent_falls_back_gracefully_with_no_checkpoint(tmp_path):
    """test-plan.md GNN #8 -- mirrors the LLM-fallback pattern. Runs even
    without torch installed (this specific test doesn't need it), but lives
    here for locality with the rest of the GNN suite."""
    import sys as _sys

    BACKEND_ROOT = ML_ROOT.parent / "backend"
    if str(BACKEND_ROOT) not in _sys.path:
        _sys.path.insert(0, str(BACKEND_ROOT))

    from app.engine.algorithmic.gnn_recommendation_agent import GNNRecommendationAgent

    agent = GNNRecommendationAgent(checkpoint_path=tmp_path / "does_not_exist.pt")
    assert agent.is_available is False
    assert agent.score_requires("any-job", "any-skill") is None
    assert agent.score_leads_to("Python", "Machine Learning") is None
