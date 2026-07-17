"""test_gnn_recommendation_agent.py — module B (GNN inference integration).

Runs in the plain backend test environment (no torch required): verifies
the graceful-degradation contract of `GNNRecommendationAgent` mirrors the
LLM-provider fallback pattern (system-design.md §9.4, test-plan.md GNN #8).
The "GNN actually scores an edge correctly" tests live in
`ml/tests/test_gnn_pipeline_requires_torch.py` since they need the full
ml/requirements.txt stack.
"""
from __future__ import annotations

from pathlib import Path

from app.engine.algorithmic.gnn_recommendation_agent import (
    GNNRecommendationAgent,
    score_requires_with_fallback,
)


def test_unavailable_when_checkpoint_missing(tmp_path):
    agent = GNNRecommendationAgent(checkpoint_path=tmp_path / "no_such_checkpoint.pt")
    assert agent.is_available is False
    assert "no checkpoint found" in agent.unavailable_reason


def test_scoring_methods_return_none_when_unavailable(tmp_path):
    agent = GNNRecommendationAgent(checkpoint_path=tmp_path / "missing.pt")
    assert agent.score_requires("some-job", "Python") is None
    assert agent.score_leads_to("Python", "Machine Learning") is None


def test_score_requires_with_fallback_uses_algorithmic_score_when_gnn_unavailable(tmp_path):
    agent = GNNRecommendationAgent(checkpoint_path=tmp_path / "missing.pt")
    score, source = score_requires_with_fallback(agent, "job-1", "Python", algorithmic_fallback_score=0.73)
    assert source == "algorithmic"
    assert score == 0.73


def test_corrupt_checkpoint_degrades_gracefully_instead_of_raising(tmp_path):
    """A checkpoint file that exists but isn't a valid torch/PyG checkpoint
    (or torch isn't installed in this environment at all) must never raise
    out of the constructor -- it must degrade to unavailable, exactly like
    an LLM provider with a bad API key falls back rather than 500ing."""
    bad_checkpoint = tmp_path / "corrupt.pt"
    bad_checkpoint.write_bytes(b"not a real checkpoint")

    agent = GNNRecommendationAgent(checkpoint_path=bad_checkpoint)
    assert agent.is_available is False
    assert agent.unavailable_reason  # some explanatory string, not empty


def test_default_checkpoint_path_points_at_ml_directory():
    """Sanity check that the default checkpoint path resolves under the
    repo's ml/ directory (sibling of backend/), not inside backend/ itself
    -- keeping the heavy-ML artifact out of the API's own tree."""
    from app.engine.algorithmic.gnn_recommendation_agent import DEFAULT_CHECKPOINT

    assert Path(DEFAULT_CHECKPOINT).parts[-3:] == ("ml", "checkpoints", "gnn_link_predictor.pt")
