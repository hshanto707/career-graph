"""RecommendationAgent — module B5.

Pure Python, deterministic. Ranks jobs for a student by combining an exact
Jaccard-similarity score over skill sets with a "partial credit" score
derived from `LEADS_TO` graph proximity (depth <= 2), per
system-design.md section 9.3:

    exact_score   = |student_skills ∩ job_skills| / |student_skills ∪ job_skills|
    partial_score = graph proximity via LEADS_TO within depth 2
    final_score   = exact_score * 0.8 + partial_score * 0.2

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
    ) -> list[RankedJob]:
        """
        Args:
            student_skills: [{"name": str, ...}, ...]
            all_jobs: [{"job_id": str, "title": str,
                        "required_skills": [{"name": str, ...}, ...]}, ...]
            leads_to_edges: [{"from_skill": str, "to_skill": str, "difficulty_jump": int}, ...]

        Returns:
            RankedJob list sorted strictly descending by final_score. Ties
            are broken deterministically by job_id (ascending) so ordering
            is stable and reproducible across runs.
        """
        student_names = {
            _normalize_name(s.get("name", "")) for s in (student_skills or []) if s.get("name")
        }
        adjacency = _build_leads_to_adjacency(leads_to_edges or [])
        reachable = _reachable_within_depth(student_names, adjacency, MAX_DEPTH) if student_names else {}

        ranked: list[RankedJob] = []
        for job in all_jobs or []:
            required = job.get("required_skills", []) or []
            job_names_raw = [s.get("name", "") for s in required if s.get("name")]
            # Defensive dedup of required-skill names within a single job.
            job_names = list(dict.fromkeys(_normalize_name(n) for n in job_names_raw))

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
                partial_score = 0.0

            final_score = exact_score * EXACT_WEIGHT + partial_score * PARTIAL_WEIGHT

            matched_names = [
                s.get("name", "") for s in required
                if s.get("name") and _normalize_name(s.get("name", "")) in student_names
            ]

            ranked.append(
                RankedJob(
                    job_id=job.get("job_id", ""),
                    title=job.get("title", ""),
                    exact_score=round(exact_score, 6),
                    partial_score=round(partial_score, 6),
                    final_score=round(final_score, 6),
                    matched_skills=matched_names,
                )
            )

        ranked.sort(key=lambda r: (-r.final_score, r.job_id))
        return ranked
