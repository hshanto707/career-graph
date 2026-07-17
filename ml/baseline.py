"""baseline.py — algorithmic (non-GNN) edge-scoring baselines, reusing the
existing `RecommendationAgent`/`PathFinderAgent` signal so `evaluate.py` can
score the GNN and the algorithmic baseline on the IDENTICAL held-out edges
(test-plan.md GNN #6).

Neither `RecommendationAgent` nor `PathFinderAgent` was originally designed
to score a single candidate edge in isolation (they rank whole job lists /
build ordered paths for one student), so this module adapts their exact
underlying signal to the edge-prediction task, documented per relation:

  - REQUIRES (Job -> Skill): "would `skill` plausibly be required by
    `job`?" is scored via the same Jaccard-similarity mechanism
    `RecommendationAgent` uses to compare a student's skill set against a
    job's skill set — here applied job-to-job: the score is the best
    Jaccard overlap between `job`'s other required skills and any other
    job (in the training graph) that requires `skill`. This is a
    legitimate, off-the-shelf collaborative-filtering reuse of the same
    exact_score formula, not a new algorithm.

  - LEADS_TO (Skill -> Skill): scored with `RecommendationAgent`'s own
    depth-1/depth-2 LEADS_TO reachability credit (`DEPTH1_CREDIT`,
    `DEPTH2_CREDIT`), applied directly: is `dst` reachable from `src` within
    2 hops over the TRAIN-split LEADS_TO edges?
"""
from __future__ import annotations

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.engine.algorithmic.recommendation_agent import (  # noqa: E402
    DEPTH1_CREDIT,
    DEPTH2_CREDIT,
    _build_leads_to_adjacency,
    _normalize_name,
    _reachable_within_depth,
)


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 0.0
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)


def build_requires_baseline(train_requires_edges: list[tuple[str, str]]):
    """Returns a `score_fn(job_id, skill_name) -> float in [0, 1]` closure
    built once from the TRAIN-split REQUIRES edges (never val/test — the
    baseline must not see held-out edges any more than the GNN's message
    passing graph does)."""
    job_skills: dict[str, set[str]] = {}
    skill_jobs: dict[str, set[str]] = {}
    for job_id, skill in train_requires_edges:
        job_skills.setdefault(job_id, set()).add(skill)
        skill_jobs.setdefault(skill, set()).add(job_id)

    def score(job_id: str, skill_name: str) -> float:
        this_job_skills = job_skills.get(job_id, set())
        candidate_jobs = skill_jobs.get(skill_name, set()) - {job_id}
        if not candidate_jobs:
            return 0.0
        best = 0.0
        for other_job in candidate_jobs:
            best = max(best, _jaccard(this_job_skills, job_skills.get(other_job, set())))
        return best

    return score


def build_leads_to_baseline(train_leads_to_edges: list[tuple[str, str]]):
    """Returns a `score_fn(src_skill, dst_skill) -> float in [0, 1]` closure
    reusing RecommendationAgent's depth-1/2 LEADS_TO reachability credit,
    built once from the TRAIN-split LEADS_TO edges."""
    edge_dicts = [{"from_skill": a, "to_skill": b} for a, b in train_leads_to_edges]
    adjacency = _build_leads_to_adjacency(edge_dicts)

    def score(src_skill: str, dst_skill: str) -> float:
        start = {_normalize_name(src_skill)}
        reachable = _reachable_within_depth(start, adjacency, max_depth=2)
        depth = reachable.get(_normalize_name(dst_skill))
        if depth == 1:
            return DEPTH1_CREDIT
        if depth == 2:
            return DEPTH2_CREDIT
        return 0.0

    return score
