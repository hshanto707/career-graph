"""RecommendationAgent — module B5.

Pure Python, deterministic. Ranks jobs for a student by combining an exact
Jaccard-similarity score over skill sets with a "partial credit" score
derived from `LEADS_TO` graph proximity (depth <= 2), per
system-design.md section 9.3:

    exact_score   = |student_skills ∩ job_skills| / |student_skills ∪ job_skills|
    partial_score = graph proximity via LEADS_TO within depth 2
    final_score   = exact_score * 0.8 + partial_score * 0.2

--------------------------------------------------------------------------
Optional GNN rerank stage (Custom AI Model integration)
--------------------------------------------------------------------------
`rank_jobs` always computes the pure-algorithmic scores above first, over
every job -- this is cheap (no model inference) and is the retrieval stage.
If a `gnn_agent` (`GNNRecommendationAgent`) is supplied and available, the
top `gnn_rerank_pool_size` candidates by algorithmic score are then
reranked with a learned signal: for each of a job's still-missing required
skills, the trained model's `score_leads_to` is queried against every
skill the student already owns, taking the best (max) plausibility per
missing skill -- a learned generalization of the same depth<=2 BFS idea
`partial_score` already uses, but not limited to skill pairs an explicit
(synthetic) LEADS_TO edge happens to connect. This is a standard
retrieve-then-rerank pattern: bounding the (expensive, model-inference)
rerank stage to a small top-N pool keeps a 9,000+ job catalog tractable
instead of scoring every job with the GNN. Jobs outside the pool keep
their algorithmic-only score (`score_source="algorithmic"`); reranked jobs
get `score_source="gnn"`. When no GNN is supplied/available, or a job has
no missing skills to score, behavior is identical to the pure-algorithmic
path -- this is an additive, gracefully-degrading stage, never a
replacement for it.

--------------------------------------------------------------------------
Partial-match scoring via LEADS_TO
--------------------------------------------------------------------------
A student who knows Python gets partial credit toward a job requiring
Machine Learning because `Python -[:LEADS_TO]-> Machine Learning` exists in
the skill graph (system-design.md's worked example). Concretely:

    - For each job-required skill the student does NOT already have exactly,
      check whether any student skill reaches it via LEADS_TO edges within
      2 hops (depth 1 = direct edge, depth 2 = one intermediate skill).
    - depth-1 reachability contributes full partial credit for that skill
      (weight 1.0); depth-2 reachability contributes half credit (weight
      0.5) since it represents a more distant, less certain prerequisite
      relationship. This asymmetry is what makes "Disjoint exact match but
      a depth-1 LEADS_TO path exists" (test-plan.md B5#7) contribute a
      strictly larger partial_score than an equivalent depth-2-only path.
    - partial_score = (sum of per-skill partial credit) / |job_skills|,
      i.e. normalized 0-1 like exact_score, and only counts skills that
      weren't already exact matches (no double-counting).

This keeps partial_score in the same [0, 1] range as exact_score so the
0.8/0.2 weighted blend is well-defined and bounded to [0, 1].
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Any

EXACT_WEIGHT = 0.8
PARTIAL_WEIGHT = 0.2
DEPTH1_CREDIT = 1.0
DEPTH2_CREDIT = 0.5
MAX_DEPTH = 2

# Weights when a GNN score is available for a job (must sum to 1.0, same as
# EXACT_WEIGHT + PARTIAL_WEIGHT above). Exact match still dominates -- the
# GNN contributes a meaningful but bounded learned signal on top of it.
GNN_EXACT_WEIGHT = 0.6
GNN_PARTIAL_WEIGHT = 0.15
GNN_WEIGHT = 0.25
GNN_RERANK_POOL_SIZE = 50


def _normalize_name(name: str) -> str:
    return name.strip().lower()


@dataclass
class RankedJob:
    job_id: str
    title: str
    exact_score: float
    partial_score: float
    final_score: float
    matched_skills: list[str] = field(default_factory=list)
    gnn_score: float | None = None
    score_source: str = "algorithmic"


def _build_leads_to_adjacency(leads_to_edges: list[dict[str, Any]]) -> dict[str, set[str]]:
    """LEADS_TO is directional (from_skill -> to_skill). Build an adjacency
    map keyed by normalized `from_skill` name."""
    adjacency: dict[str, set[str]] = {}
    for edge in leads_to_edges or []:
        src = _normalize_name(edge.get("from_skill", ""))
        dst = _normalize_name(edge.get("to_skill", ""))
        if not src or not dst:
            continue
        adjacency.setdefault(src, set()).add(dst)
    return adjacency


def _reachable_within_depth(
    start_nodes: set[str], adjacency: dict[str, set[str]], max_depth: int
) -> dict[str, int]:
    """BFS from every node in `start_nodes` simultaneously over `adjacency`,
    capped at `max_depth` hops. Returns {reached_node: shortest_depth}.
    Cycle-safe: a `visited` set prevents revisiting nodes / infinite loops.
    """
    depths: dict[str, int] = {}
    visited: set[str] = set(start_nodes)
    queue: deque[tuple[str, int]] = deque((n, 0) for n in start_nodes)

    while queue:
        node, depth = queue.popleft()
        if depth >= max_depth:
            continue
        for neighbor in adjacency.get(node, ()):
            if neighbor in visited:
                continue
            visited.add(neighbor)
            new_depth = depth + 1
            depths[neighbor] = new_depth
            queue.append((neighbor, new_depth))
    return depths


class RecommendationAgent:
    """Ranks jobs for a student using Jaccard exact match + LEADS_TO partial
    credit. Pure Python -- takes plain lists/dicts fetched separately via
    GraphService.
    """

    def rank_jobs(
        self,
        student_skills: list[dict[str, Any]],
        all_jobs: list[dict[str, Any]],
        leads_to_edges: list[dict[str, Any]] | None = None,
        gnn_agent: Any = None,
        gnn_rerank_pool_size: int = GNN_RERANK_POOL_SIZE,
    ) -> list[RankedJob]:
        """
        Args:
            student_skills: [{"name": str, ...}, ...]
            all_jobs: [{"job_id": str, "title": str,
                        "required_skills": [{"name": str, ...}, ...]}, ...]
            leads_to_edges: [{"from_skill": str, "to_skill": str, "difficulty_jump": int}, ...]
            gnn_agent: optional `GNNRecommendationAgent` (duck-typed --
                anything with `.is_available` and `.score_leads_to`).
                See module docstring for the rerank stage this enables.
            gnn_rerank_pool_size: how many top algorithmic candidates get
                rescored by the GNN.

        Returns:
            RankedJob list sorted strictly descending by final_score. Ties
            are broken deterministically by job_id (ascending) so ordering
            is stable and reproducible across runs.
        """
        student_names = {
            _normalize_name(s.get("name", "")) for s in (student_skills or []) if s.get("name")
        }
        # Original-cased display names, keyed by normalized name -- the GNN
        # checkpoint's node ids are the canonical `normalized_name` strings
        # from ingestion (mixed case), not this agent's internal lowercase
        # matching keys, so GNN queries must use these, never `student_names`.
        student_name_display: dict[str, str] = {}
        for s in student_skills or []:
            raw = s.get("name", "")
            if raw:
                student_name_display.setdefault(_normalize_name(raw), raw)

        adjacency = _build_leads_to_adjacency(leads_to_edges or [])
        reachable = _reachable_within_depth(student_names, adjacency, MAX_DEPTH) if student_names else {}

        ranked: list[RankedJob] = []
        # job_id -> (unmatched required skill names, normalized -> display).
        # Cheap to keep for every job (plain lists/dicts, no model calls);
        # only looked up for the small GNN rerank pool below.
        unmatched_by_job: dict[str, tuple[list[str], dict[str, str]]] = {}

        for job in all_jobs or []:
            required = job.get("required_skills", []) or []
            job_names_raw = [s.get("name", "") for s in required if s.get("name")]
            # Defensive dedup of required-skill names within a single job.
            job_names = list(dict.fromkeys(_normalize_name(n) for n in job_names_raw))
            job_name_display: dict[str, str] = {}
            for raw in job_names_raw:
                job_name_display.setdefault(_normalize_name(raw), raw)

            if not job_names and not student_names:
                exact_score = 0.0
            else:
                job_name_set = set(job_names)
                intersection = student_names & job_name_set
                union = student_names | job_name_set
                exact_score = (len(intersection) / len(union)) if union else 0.0

            if job_names:
                exact_matched = student_names & set(job_names)
                unmatched_required = [n for n in job_names if n not in exact_matched]
                partial_credit_sum = 0.0
                for skill_name in unmatched_required:
                    depth = reachable.get(skill_name)
                    if depth == 1:
                        partial_credit_sum += DEPTH1_CREDIT
                    elif depth == 2:
                        partial_credit_sum += DEPTH2_CREDIT
                partial_score = partial_credit_sum / len(job_names)
            else:
                unmatched_required = []
                partial_score = 0.0

            final_score = exact_score * EXACT_WEIGHT + partial_score * PARTIAL_WEIGHT

            matched_names = [
                s.get("name", "") for s in required
                if s.get("name") and _normalize_name(s.get("name", "")) in student_names
            ]

            job_id = job.get("job_id", "")
            unmatched_by_job[job_id] = (unmatched_required, job_name_display)

            ranked.append(
                RankedJob(
                    job_id=job_id,
                    title=job.get("title", ""),
                    exact_score=round(exact_score, 6),
                    partial_score=round(partial_score, 6),
                    final_score=round(final_score, 6),
                    matched_skills=matched_names,
                )
            )

        ranked.sort(key=lambda r: (-r.final_score, r.job_id))

        if gnn_agent is not None and getattr(gnn_agent, "is_available", False) and student_name_display:
            for r in ranked[:gnn_rerank_pool_size]:
                unmatched_required, job_name_display = unmatched_by_job.get(r.job_id, ([], {}))
                gnn_score = self._score_gnn_fit(
                    gnn_agent, unmatched_required, job_name_display, student_name_display
                )
                r.gnn_score = round(gnn_score, 6)
                r.score_source = "gnn"
                r.final_score = round(
                    r.exact_score * GNN_EXACT_WEIGHT
                    + r.partial_score * GNN_PARTIAL_WEIGHT
                    + gnn_score * GNN_WEIGHT,
                    6,
                )
            ranked.sort(key=lambda r: (-r.final_score, r.job_id))

        return ranked

    @staticmethod
    def _score_gnn_fit(
        gnn_agent: Any,
        unmatched_required: list[str],
        job_name_display: dict[str, str],
        student_name_display: dict[str, str],
    ) -> float:
        """For each of a job's still-missing required skills, the best
        (max) learned plausibility that some skill the student already
        owns progresses toward it (`Skill -[:LEADS_TO]-> Skill`), averaged
        over the missing skills. 0.0 if there's nothing missing to score,
        or the GNN has no learned signal for any of the pairs (unseen
        skill names at training time) -- never raises, matching
        `GNNRecommendationAgent`'s own graceful-degradation contract."""
        if not unmatched_required:
            return 0.0

        per_skill_best: list[float] = []
        for missing_key in unmatched_required:
            missing_display = job_name_display.get(missing_key, missing_key)
            best: float | None = None
            for owned_display in student_name_display.values():
                score = gnn_agent.score_leads_to(owned_display, missing_display)
                if score is not None and (best is None or score > best):
                    best = score
            per_skill_best.append(best if best is not None else 0.0)

        return sum(per_skill_best) / len(unmatched_required)
