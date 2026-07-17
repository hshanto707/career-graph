"""graph_build.py — pure-Python graph construction (no torch dependency).

Builds the CareerGraph knowledge graph as plain Python data structures
(node id lists + edge id-pair lists) from the synthetic seed data checked
into `backend/data/` (see `docs/data-sources.md` — these are hand-generated
placeholder fixtures pending the real Kaggle/O*NET datasets).

This module deliberately has ZERO dependency on torch/PyTorch Geometric so
it can be unit-tested in any environment (node/edge counting, determinism,
split disjointness) without the heavy ML stack installed. `export_graph.py`
is the thin layer on top that turns this into a PyG `HeteroData` object.

No live Neo4j instance is required or used — this reuses the exact same
`IngestionAgent` / `NormalizationAgent` pipeline and `FakeGraphService` the
backend test-suite already uses, so the exported graph is faithful to what
a real ingestion run against Neo4j would produce, just captured in-memory.

--------------------------------------------------------------------------
Node types
--------------------------------------------------------------------------
Student, Skill, Job, Course, Category — matching system-design.md §7.2.

--------------------------------------------------------------------------
Edge types
--------------------------------------------------------------------------
(Student, HAS_SKILL, Skill), (Job, REQUIRES, Skill), (Skill, LEADS_TO, Skill),
(Course, TEACHES, Skill), (Job, IN_CATEGORY, Category)

--------------------------------------------------------------------------
LEADS_TO — synthetic placeholder (documented, not real prerequisite data)
--------------------------------------------------------------------------
Neither the real nor the placeholder ingestion pipeline populates LEADS_TO
edges (no source of "skill A is a prerequisite of skill B" data exists yet
— see docs/data-sources.md). For the GNN to have a LEADS_TO link-prediction
task at all, this module deterministically synthesizes a small prerequisite
graph: within each O*NET skill category, skills are sorted alphabetically
and chained (skill[i] -[:LEADS_TO]-> skill[i+1]) with difficulty_jump=1.
This is a clearly-labeled synthetic stand-in — a real system would derive
LEADS_TO from curriculum/course-sequencing data or historical career-
progression data (tracked as Future Work per project-roadmap.md).
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ML_ROOT = Path(__file__).resolve().parent
REPO_ROOT = ML_ROOT.parent
BACKEND_ROOT = REPO_ROOT / "backend"
DATA_DIR = BACKEND_ROOT / "data"

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

EdgeType = tuple[str, str, str]  # (src_node_type, relation, dst_node_type)

NODE_TYPES = ["Student", "Skill", "Job", "Course", "Category"]
EDGE_TYPES: list[EdgeType] = [
    ("Student", "HAS_SKILL", "Skill"),
    ("Job", "REQUIRES", "Skill"),
    ("Skill", "LEADS_TO", "Skill"),
    ("Course", "TEACHES", "Skill"),
    ("Job", "IN_CATEGORY", "Category"),
]


@dataclass
class RawGraph:
    """Plain-Python graph: ordered node ids per type + (src_id, dst_id)
    edge pairs per edge type. No tensors, no torch import anywhere here."""

    node_ids: dict[str, list[str]] = field(default_factory=dict)
    edges: dict[EdgeType, list[tuple[str, str]]] = field(default_factory=dict)

    def node_count(self, node_type: str) -> int:
        return len(self.node_ids.get(node_type, []))

    def edge_count(self, edge_type: EdgeType) -> int:
        return len(self.edges.get(edge_type, []))

    def node_index(self, node_type: str) -> dict[str, int]:
        return {nid: i for i, nid in enumerate(self.node_ids.get(node_type, []))}


def _synthesize_leads_to(
    skill_categories: dict[str, str | None],
) -> list[tuple[str, str]]:
    """Deterministic placeholder LEADS_TO chain, one per O*NET category
    (see module docstring). Categories with < 2 skills produce no edges."""
    by_category: dict[str, list[str]] = {}
    for skill_name, category in skill_categories.items():
        if not category:
            continue
        by_category.setdefault(category, []).append(skill_name)

    edges: list[tuple[str, str]] = []
    for category in sorted(by_category):
        names = sorted(by_category[category])
        for a, b in zip(names, names[1:]):
            edges.append((a, b))
    return edges


def build_synthetic_career_graph(
    data_dir: Path | str = DATA_DIR,
    include_demo_seed: bool = True,
) -> RawGraph:
    """Build the full RawGraph from the synthetic Kaggle/O*NET placeholder
    CSVs, run through the real Ingestion + Normalization pipeline, plus the
    curated demo students/courses (`app.etl.seed_demo_data`) and a
    synthesized LEADS_TO chain.
    """
    from app.engine.ingestion.ingestion_agent import IngestionAgent
    from app.engine.ingestion.normalization_agent import NormalizationAgent
    from tests.fakes import FakeGraphService  # backend test double, reused deliberately

    data_dir = Path(data_dir)
    graph = FakeGraphService()

    ingestion = IngestionAgent()
    result = ingestion.read_csv(data_dir / "kaggle_jobs.csv")

    normalizer = NormalizationAgent(
        graph_service=graph,
        synonyms_path=data_dir / "synonyms.json",
        onet_skills_path=data_dir / "onet_skills.csv",
    )
    normalizer.process_and_write(result.records)

    if include_demo_seed:
        from app.etl.seed_demo_data import DEMO_COURSES, DEMO_STUDENTS

        for course in DEMO_COURSES:
            graph.seed_course(course)
        for student in DEMO_STUDENTS:
            graph.upsert_student_node(
                student["id"], student["skills"], student["target_roles"]
            )

    return _raw_graph_from_fake_service(graph, normalizer)


def _raw_graph_from_fake_service(graph: Any, normalizer: Any) -> RawGraph:
    student_ids = sorted(graph._students.keys())
    job_ids = sorted(graph._jobs.keys())
    skill_ids = sorted(graph._skills.keys())
    course_ids = sorted({c["id"] for c in graph._courses})
    category_ids = sorted(graph._categories.keys())

    raw = RawGraph(
        node_ids={
            "Student": student_ids,
            "Skill": skill_ids,
            "Job": job_ids,
            "Course": course_ids,
            "Category": category_ids,
        }
    )

    # (Student, HAS_SKILL, Skill) — student skill "name" isn't guaranteed to
    # already be normalized (profile-entered free text), so resolve via the
    # same normalizer used for job postings, falling back to raw name if
    # unmatched (still a valid node key, just not O*NET-canonical).
    has_skill: list[tuple[str, str]] = []
    skill_id_set = set(skill_ids)
    for sid in student_ids:
        for skill in graph._students[sid]["skills"]:
            raw_name = skill.get("name", "")
            normalized = normalizer.normalize_skill(raw_name).normalized_name
            target = normalized if normalized in skill_id_set else raw_name
            if target not in skill_id_set:
                skill_id_set.add(target)
                raw.node_ids["Skill"].append(target)
            has_skill.append((sid, target))
    raw.node_ids["Skill"] = sorted(set(raw.node_ids["Skill"]))

    # (Job, REQUIRES, Skill)
    requires: list[tuple[str, str]] = []
    for job_id, edges in graph._requires_edges.items():
        for skill_name in edges:
            requires.append((job_id, skill_name))

    # (Course, TEACHES, Skill) -- a course can teach a skill that never
    # appeared in any job posting's REQUIRES edges (e.g. a course-only
    # skill like "NumPy"); such skills still need a node id so the edge
    # isn't silently dropped at export time.
    teaches = [(c["id"], c["skill_name"]) for c in graph._courses]
    for _, skill_name in teaches:
        if skill_name not in skill_id_set:
            skill_id_set.add(skill_name)
            raw.node_ids["Skill"].append(skill_name)

    # (Job, IN_CATEGORY, Category)
    in_category = [(job_id, cat) for job_id, cat in graph._in_category_edges.items()]

    # (Skill, LEADS_TO, Skill) — synthesized placeholder, see module docstring.
    skill_categories = {name: node.get("category") for name, node in graph._skills.items()}
    leads_to = [
        (a, b)
        for a, b in _synthesize_leads_to(skill_categories)
        if a in skill_id_set and b in skill_id_set
    ]

    raw.node_ids["Skill"] = sorted(skill_id_set)

    raw.edges = {
        ("Student", "HAS_SKILL", "Skill"): has_skill,
        ("Job", "REQUIRES", "Skill"): requires,
        ("Skill", "LEADS_TO", "Skill"): leads_to,
        ("Course", "TEACHES", "Skill"): teaches,
        ("Job", "IN_CATEGORY", "Category"): in_category,
    }
    return raw
