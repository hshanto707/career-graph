"""PathFinderAgent — module B5.

Pure Python, deterministic. Given a set of missing skills and the
`LEADS_TO` skill graph, builds an ordered learning roadmap: BFS backward
from each missing skill to collect its prerequisite chain, then a
topological sort forward into a single ordered path, with `TEACHES`
courses attached per milestone, per system-design.md section 9.3.

--------------------------------------------------------------------------
Direction convention
--------------------------------------------------------------------------
`LEADS_TO` edges point from a prerequisite skill to the more advanced skill
it unlocks, e.g. `(Python)-[:LEADS_TO]->(Machine Learning)` means "Python is
a prerequisite for / leads to Machine Learning". To build a learning path
*to* a missing skill we therefore walk `LEADS_TO` edges **backward**
(advanced skill -> its prerequisites) to discover everything that should be
learned first, then reverse that into forward (prerequisite-first) order.

--------------------------------------------------------------------------
Cycle handling (test-plan.md B5#11)
--------------------------------------------------------------------------
Real-world skill graphs should be acyclic, but ingestion bugs / bad data can
introduce a cycle (e.g. A -> B -> A). A naive BFS/topsort would either loop
forever or simply stall (Kahn's algorithm: no node ever reaches in-degree
zero). This agent uses a modified Kahn's algorithm: at each step, if no
remaining node has in-degree 0 (i.e. we're stuck inside a cycle), it force-
selects the lexicographically-smallest remaining skill name, emits it, and
removes its outgoing edges to unblock the rest -- a deterministic,
reproducible tie-break rather than an undefined/order-dependent one. This
guarantees termination (the node set strictly shrinks every iteration) and
a fully defined, tested output for cyclic input, instead of raising or
hanging.

--------------------------------------------------------------------------
weeks_estimate
--------------------------------------------------------------------------
No historical learning-time data exists yet (v1), so weeks_estimate is a
simple, documented, deterministic proxy:

    weeks_estimate = BASE_WEEKS + max(difficulty_jump of any LEADS_TO edge
                                       landing on this skill from a skill
                                       already in the path, default 0)

A skill with no known prerequisite edge into it (a "root" skill, or one
whose only prerequisites fall outside the discovered path) gets just
BASE_WEEKS. This keeps the number deterministic and testable while leaving
room to be replaced by a data-driven estimate later (documented as a v1
approximation, mirroring the MarketAgent trend-calculation decision).
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Any

BASE_WEEKS = 2


def _normalize_name(name: str) -> str:
    return name.strip().lower()


@dataclass
class Milestone:
    skill_name: str
    weeks_estimate: int
    courses: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class LearningPath:
    milestones: list[Milestone] = field(default_factory=list)

    @property
    def ordered_skill_names(self) -> list[str]:
        return [m.skill_name for m in self.milestones]


class PathFinderAgent:
    """Builds an ordered learning roadmap from missing skills + the
    LEADS_TO skill graph. Pure Python -- takes plain lists/dicts fetched
    separately via GraphService.
    """

    def find_path(
        self,
        missing_skills: list[str],
        leads_to_edges: list[dict[str, Any]] | None = None,
        courses: list[dict[str, Any]] | None = None,
    ) -> LearningPath:
        """
        Args:
            missing_skills: [str, ...] canonical/display skill names the
                student needs. Duplicates (including case-insensitive dupes)
                are deduped, preserving first-seen display name.
            leads_to_edges: [{"from_skill": str, "to_skill": str,
                              "difficulty_jump": int}, ...]
            courses: [{"skill_name": str, ...}, ...] TEACHES edges,
                already resolved by GraphService for the relevant skills.

        Returns:
            LearningPath with milestones in prerequisite-first order.
            Empty input -> empty LearningPath, never raises.
        """
        courses = courses or []
        leads_to_edges = leads_to_edges or []

        # -- Dedup missing skills, case-insensitive, first-seen name kept --
        display_name_by_key: dict[str, str] = {}
        for name in missing_skills or []:
            key = _normalize_name(name)
            if key and key not in display_name_by_key:
                display_name_by_key[key] = name.strip()

        if not display_name_by_key:
            return LearningPath(milestones=[])

        # -- Build forward + backward adjacency over normalized names --
        forward_adj: dict[str, set[str]] = {}
        backward_adj: dict[str, set[str]] = {}
        difficulty: dict[tuple[str, str], int] = {}
        for edge in leads_to_edges:
            from_raw = edge.get("from_skill", "")
            to_raw = edge.get("to_skill", "")
            src = _normalize_name(from_raw)
            dst = _normalize_name(to_raw)
            if not src or not dst:
                continue
            forward_adj.setdefault(src, set()).add(dst)
            backward_adj.setdefault(dst, set()).add(src)
            difficulty[(src, dst)] = edge.get("difficulty_jump", 0) or 0
            # Preserve display casing for skills only discovered via edges
            # (ancestor prerequisites not present in the original missing list).
            display_name_by_key.setdefault(src, from_raw.strip())
            display_name_by_key.setdefault(dst, to_raw.strip())

        # -- BFS backward from every missing skill to collect all ancestor
        # prerequisites needed. Visited set makes this cycle-safe. --
        needed: set[str] = set(display_name_by_key.keys())
        visited = set(needed)
        queue: deque[str] = deque(needed)
        while queue:
            node = queue.popleft()
            for prereq in backward_adj.get(node, ()):
                if prereq not in visited:
                    visited.add(prereq)
                    needed.add(prereq)
                    queue.append(prereq)

        # -- Topological sort (Kahn's algorithm) over the induced subgraph,
        # forward direction (prerequisite -> dependent), restricted to
        # `needed` nodes only. Deterministic tie-break on cycles. --
        in_degree: dict[str, int] = {n: 0 for n in needed}
        sub_forward: dict[str, set[str]] = {n: set() for n in needed}
        for src in needed:
            for dst in forward_adj.get(src, ()):
                if dst in needed:
                    sub_forward[src].add(dst)
                    in_degree[dst] += 1

        remaining = set(needed)
        ordered: list[str] = []
        # difficulty of the edge that most directly motivated including this
        # node in the path (max over incoming edges from an already-ordered node)
        incoming_difficulty: dict[str, int] = {n: 0 for n in needed}

        while remaining:
            zero_in_degree = sorted(n for n in remaining if in_degree[n] == 0)
            if zero_in_degree:
                node = zero_in_degree[0]
            else:
                # Cycle detected: force-pick the lexicographically smallest
                # remaining node to guarantee termination deterministically.
                node = sorted(remaining)[0]

            ordered.append(node)
            remaining.remove(node)
            for dst in sub_forward.get(node, ()):
                if dst in remaining:
                    in_degree[dst] = max(0, in_degree[dst] - 1)
                    edge_diff = difficulty.get((node, dst), 0)
                    incoming_difficulty[dst] = max(incoming_difficulty[dst], edge_diff)

        # -- Attach courses + weeks estimate per milestone --
        courses_by_skill: dict[str, list[dict[str, Any]]] = {}
        for c in courses:
            key = _normalize_name(c.get("skill_name", ""))
            courses_by_skill.setdefault(key, []).append(dict(c))

        milestones: list[Milestone] = []
        for key in ordered:
            display_name = display_name_by_key.get(key, key)
            weeks = BASE_WEEKS + incoming_difficulty.get(key, 0)
            milestones.append(
                Milestone(
                    skill_name=display_name,
                    weeks_estimate=weeks,
                    courses=courses_by_skill.get(key, []),
                )
            )

        return LearningPath(milestones=milestones)
