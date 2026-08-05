"""GNNRecommendationAgent — module B (Custom AI Model / GNN).

Optional, swappable inference layer over a trained GNN link-prediction
checkpoint (see `ml/train_gnn.py`, `ml/evaluate.py`), scoring candidate
`REQUIRES` (Job-Skill) and `LEADS_TO` (Skill-Skill) edges.

This mirrors the exact graceful-degradation pattern already used by
`LLMProvider` (system-design.md §9.4 / `app/engine/llm/base.py`): the core
backend (`backend/requirements.txt`) never needs torch/PyTorch Geometric
installed. If those packages aren't importable, or no trained checkpoint
exists on disk yet, `is_available` is `False` and every scoring method
returns `None` instead of raising — callers (e.g. `RecommendationAgent`,
`EngineOrchestrator`) must treat `None` as "fall back to the pure
algorithmic path", never as a crash.

Node ids in the checkpoint are the same string ids `ml/graph_build.py`
assigns (Job ids = `slug(company)::slug(title)`, Skill ids = O*NET
`normalized_name`). A candidate edge referencing a node id unseen at
training time also degrades to `None` (an untrained node has no learned
embedding to score with) rather than raising.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent.parent
REPO_ROOT = BACKEND_ROOT.parent
ML_ROOT = REPO_ROOT / "ml"
DEFAULT_CHECKPOINT = ML_ROOT / "checkpoints" / "gnn_link_predictor.pt"


class GNNUnavailableError(Exception):
    """Raised only by `score_or_raise`-style strict callers; the default
    scoring methods never raise this -- they return `None` instead, per the
    graceful-fallback design intent."""


class GNNRecommendationAgent:
    """Loads a trained GNN checkpoint (if present) and scores candidate
    edges. Safe to construct even when torch is not installed at all."""

    def __init__(self, checkpoint_path: str | Path = DEFAULT_CHECKPOINT):
        self._checkpoint_path = Path(checkpoint_path)
        self._model = None
        self._node_indices: dict[str, dict[str, int]] | None = None
        self._target_edge_types: list[tuple[str, str, str]] | None = None
        self._message_passing_edge_types: list[tuple[str, str, str]] | None = None
        self._edge_index_dict: Any = None
        self._z_dict: Any = None
        self._unavailable_reason: str | None = None
        self._load()

    # ------------------------------------------------------------------ #
    # Availability
    # ------------------------------------------------------------------ #
    @property
    def is_available(self) -> bool:
        return self._model is not None

    @property
    def unavailable_reason(self) -> str | None:
        """Human-readable reason scoring is unavailable, e.g. 'torch not
        installed' or 'no checkpoint found at <path>' -- useful for
        admin/status endpoints, never surfaced to the student-facing UI as
        an error (mirrors the LLM fallback UX)."""
        return self._unavailable_reason

    def _load(self) -> None:
        if not self._checkpoint_path.exists():
            self._unavailable_reason = f"no checkpoint found at {self._checkpoint_path}"
            return

        try:
            import torch
        except ImportError:
            self._unavailable_reason = "torch is not installed (see ml/requirements.txt)"
            return

        try:
            if str(ML_ROOT) not in sys.path:
                sys.path.insert(0, str(ML_ROOT))
            from model import LinkPredictor  # ml/model.py

            checkpoint = torch.load(self._checkpoint_path, weights_only=False)
            model = LinkPredictor(**checkpoint["config"])
            model.load_state_dict(checkpoint["model_state_dict"])
            model.eval()

            self._model = model
            self._node_indices = checkpoint["node_indices"]
            self._target_edge_types = checkpoint["target_edge_types"]
            self._message_passing_edge_types = checkpoint["message_passing_edge_types"]
        except Exception as exc:  # noqa: BLE001 -- any load failure must degrade, not crash
            self._model = None
            self._unavailable_reason = f"failed to load checkpoint: {exc}"

    # ------------------------------------------------------------------ #
    # Scoring
    # ------------------------------------------------------------------ #
    def score_requires(self, job_id: str, skill_name: str) -> float | None:
        """Score how plausible a (Job)-[:REQUIRES]->(Skill) edge is.
        Returns `None` (never raises) if the GNN is unavailable, or if
        `job_id`/`skill_name` weren't present in the training graph."""
        return self._score_edge("Job", "REQUIRES", "Skill", job_id, skill_name)

    def score_leads_to(self, from_skill: str, to_skill: str) -> float | None:
        """Score how plausible a (Skill)-[:LEADS_TO]->(Skill) edge is."""
        return self._score_edge("Skill", "LEADS_TO", "Skill", from_skill, to_skill)

    def _score_edge(
        self, src_type: str, relation: str, dst_type: str, src_id: str, dst_id: str
    ) -> float | None:
        if not self.is_available:
            return None

        edge_type = (src_type, relation, dst_type)
        if edge_type not in (self._target_edge_types or []):
            return None

        src_index = (self._node_indices or {}).get(src_type, {})
        dst_index = (self._node_indices or {}).get(dst_type, {})
        if src_id not in src_index or dst_id not in dst_index:
            return None

        import torch

        z_dict = self._get_z_dict()
        with torch.no_grad():
            edge_label_index = torch.tensor(
                [[src_index[src_id]], [dst_index[dst_id]]], dtype=torch.long
            )
            logit = self._model.decode(z_dict, src_type, dst_type, edge_label_index)
            return float(torch.sigmoid(logit).item())

    def _get_z_dict(self):
        """Node embeddings from one encoder forward pass, cached for the
        lifetime of this agent instance. `_score_edge` is called many times
        per recommendation request (once per candidate skill pair) -- without
        this cache, every single call would re-run the full graph encoder,
        which is the difference between scoring a rerank pool in
        milliseconds vs. minutes."""
        if self._z_dict is None:
            import torch

            edge_index_dict = self._build_message_passing_edge_index()
            with torch.no_grad():
                self._z_dict = self._model.encode(edge_index_dict)
        return self._z_dict

    def _build_message_passing_edge_index(self):
        """Rebuild the message-passing graph from the exported HeteroData.

        Unlike `train_gnn.build_training_graph` (which deliberately excludes
        val/test-split positives from message passing to avoid leakage
        during evaluation), inference here uses the FULL current graph for
        REQUIRES/LEADS_TO message passing -- standard practice once a model
        is trained and being served: a served model should see everything
        known at serving time, not a train-only subset. Cached after first
        call."""
        if self._edge_index_dict is not None:
            return self._edge_index_dict

        if str(ML_ROOT) not in sys.path:
            sys.path.insert(0, str(ML_ROOT))
        # Deliberately NOT `export_graph.export()` -- that helper always
        # writes its HeteroData to disk (a CLI/offline-pipeline concern, see
        # ml/export_graph.py's own docstring), which is both an unwanted
        # side effect for a live inference call and fails outright if ml/
        # is mounted read-only in a deployment (as it is in
        # backend/docker-compose.yml). Build the same in-memory graph
        # directly instead.
        from export_graph import to_hetero_data
        from graph_build import build_synthetic_career_graph

        hetero_data, node_indices = to_hetero_data(build_synthetic_career_graph())

        # Every message-passing relation is forward-or-reverse of one of the
        # real exported edge types -- mirrors train_gnn.build_training_graph
        # so inference uses the same bidirectional graph the model trained on.
        edge_index_dict = {}
        for edge_type in hetero_data.edge_types:
            ei = hetero_data[edge_type].edge_index
            if edge_type in (self._message_passing_edge_types or []):
                edge_index_dict[edge_type] = ei
            src_type, relation, dst_type = edge_type
            rev_type = (dst_type, f"rev_{relation}", src_type)
            if rev_type in (self._message_passing_edge_types or []):
                edge_index_dict[rev_type] = ei.flip(0)

        self._edge_index_dict = edge_index_dict
        return edge_index_dict


_default_agent: GNNRecommendationAgent | None = None


def get_default_gnn_agent() -> GNNRecommendationAgent:
    """Process-wide cached singleton. `EngineOrchestrator` is constructed
    fresh on every request (see `app/core/deps.py::get_orchestrator`) --
    without this cache, the checkpoint (a `torch.load` deserialization plus
    rebuilding the model) would reload from disk on every single API call,
    not just recommendation requests. The checkpoint is static between
    deploys/retrains, so one load per process is correct and safe."""
    global _default_agent
    if _default_agent is None:
        _default_agent = GNNRecommendationAgent()
    return _default_agent


def score_requires_with_fallback(
    agent: GNNRecommendationAgent,
    job_id: str,
    skill_name: str,
    algorithmic_fallback_score: float,
) -> tuple[float, str]:
    """Convenience helper for callers (e.g. a future `RecommendationAgent`
    integration): try the GNN, fall back to the supplied algorithmic score
    if the GNN is unavailable or has never seen this edge. Returns
    (score, source) where source is 'gnn' or 'algorithmic'."""
    score = agent.score_requires(job_id, skill_name)
    if score is None:
        return algorithmic_fallback_score, "algorithmic"
    return score, "gnn"
