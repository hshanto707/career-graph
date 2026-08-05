"""FakeGraphService — an in-memory test double for GraphService.

Implements the exact same method signatures as `app.services.graph_service
.GraphService`, backed by plain Python dicts/lists instead of a live Neo4j
instance. Unit tests for algorithmic agents (and anything else that consumes
graph data) can depend on this instead of a real database.

Because this operates on plain Python data (no string-built queries at all),
it is inherently immune to Cypher injection — which is also exactly what the
regression test in `test_data_layer.py` exercises: a "skill name" containing
Cypher-special characters must round-trip as inert, literal data.
"""
from __future__ import annotations

from typing import Any


class FakeGraphService:
    def __init__(self):
        # student_id -> {"skills": [...], "target_roles": [...]}
        self._students: dict[str, dict[str, Any]] = {}
        # job_id -> job dict
        self._jobs: dict[str, dict[str, Any]] = {}
        # job_id -> [{"name", "importance", "frequency"}]
        self._job_skills: dict[str, list[dict[str, Any]]] = {}
        # [{"from_skill", "to_skill", "difficulty_jump"}]
        self._leads_to: list[dict[str, Any]] = []
        # [{"id", "title", "provider", "url", "duration", "free", "skill_name"}]
        self._courses: list[dict[str, Any]] = []
        # Skill.normalized_name -> node dict (mirrors the real MERGE key)
        self._skills: dict[str, dict[str, Any]] = {}
        # Category.name -> node dict
        self._categories: dict[str, dict[str, Any]] = {}
        # job_id -> set of Skill.normalized_name (mirrors REQUIRES edges,
        # deduped exactly like a real MERGE would dedupe them)
        self._requires_edges: dict[str, dict[str, dict[str, Any]]] = {}
        # job_id -> Category.name (mirrors IN_CATEGORY edges)
        self._in_category_edges: dict[str, str] = {}

    # -- seeding helpers (test setup only, not part of the GraphService API) --
    def seed_job(self, job_id: str, **fields: Any) -> None:
        self._jobs[job_id] = {"id": job_id, **fields}

    def seed_job_skills(self, job_id: str, skills: list[dict[str, Any]]) -> None:
        self._job_skills[job_id] = skills

    def seed_leads_to(self, edges: list[dict[str, Any]]) -> None:
        self._leads_to = edges

    def seed_courses(self, courses: list[dict[str, Any]]) -> None:
        self._courses = courses

    # ------------------------------------------------------------------ #
    # Student
    # ------------------------------------------------------------------ #
    def get_student_skills(self, student_id: str) -> list[dict[str, Any]]:
        student = self._students.get(student_id)
        if not student:
            return []
        return list(student.get("skills", []))

    def upsert_student_node(
        self,
        student_id: str,
        skills: list[dict[str, Any]],
        target_roles: list[str],
    ) -> None:
        # Store skills/roles as literal data -- no interpretation of their
        # contents whatsoever, mirroring the parameterized-Cypher guarantee.
        self._students[student_id] = {
            "skills": [dict(s) for s in skills],
            "target_roles": list(target_roles),
        }

    # ------------------------------------------------------------------ #
    # Jobs
    # ------------------------------------------------------------------ #
    def get_job(self, job_id: str) -> dict[str, Any] | None:
        job = self._jobs.get(job_id)
        return dict(job) if job else None

    def list_jobs(self, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        filters = filters or {}
        jobs = list(self._jobs.values())

        if filters.get("type"):
            jobs = [j for j in jobs if j.get("type") == filters["type"]]
        if filters.get("location"):
            jobs = [j for j in jobs if j.get("location") == filters["location"]]
        if filters.get("search"):
            needle = filters["search"].lower()
            jobs = [j for j in jobs if needle in (j.get("title", "") or "").lower()]

        limit = int(filters.get("limit", 50))
        return [dict(j) for j in jobs[:limit]]

    def list_job_titles(self, search: str | None = None, limit: int = 50) -> list[str]:
        titles = {j["title"] for j in self._jobs.values() if j.get("title")}
        if search:
            needle = search.lower()
            titles = {t for t in titles if needle in t.lower()}
        return sorted(titles)[:limit]

    def get_job_required_skills(self, job_id: str) -> list[dict[str, Any]]:
        return [dict(s) for s in self._job_skills.get(job_id, [])]

    def get_all_jobs_with_requires(self) -> list[dict[str, Any]]:
        return [
            {
                "job_id": job_id,
                "title": job.get("title"),
                "required_skills": [dict(s) for s in self._job_skills.get(job_id, [])],
            }
            for job_id, job in self._jobs.items()
        ]

    # ------------------------------------------------------------------ #
    # Skill graph
    # ------------------------------------------------------------------ #
    def get_leads_to_graph(self) -> list[dict[str, Any]]:
        return [dict(edge) for edge in self._leads_to]

    def get_teaches_courses(self, skill_ids: list[str]) -> list[dict[str, Any]]:
        wanted = set(skill_ids)
        return [dict(c) for c in self._courses if c.get("skill_name") in wanted]

    # ------------------------------------------------------------------ #
    # Ingestion writer — mirrors GraphService.ingest_job_posting exactly,
    # including MERGE-style idempotency (re-ingesting the same job_id /
    # skill normalized_name never creates a duplicate node or edge).
    # ------------------------------------------------------------------ #
    def ingest_job_posting(self, job: dict[str, Any], skills: list[dict[str, Any]]) -> dict[str, int]:
        job_id = job["id"]
        is_new_job = job_id not in self._jobs
        self._jobs[job_id] = {
            "id": job_id,
            "title": job.get("title"),
            "company": job.get("company"),
            "location": job.get("location"),
            "type": job.get("type"),
            "salary_min": job.get("salary_min"),
            "salary_max": job.get("salary_max"),
            "source": job.get("source", "kaggle_csv"),
        }

        edges = self._requires_edges.setdefault(job_id, {})
        for skill in skills:
            name = skill["normalized_name"]
            if name not in self._skills:
                self._skills[name] = {
                    "normalized_name": name,
                    "name": skill.get("raw_name", name),
                    "category": skill.get("category"),
                }
            self._skills[name]["flagged_for_review"] = bool(skill.get("flagged", False))
            # MERGE semantics: same (job, skill) pair collapses to one edge,
            # re-ingestion just refreshes the edge property.
            edges[name] = {"importance": skill.get("importance", "nice")}

        category = job.get("category")
        if category:
            self._categories.setdefault(category, {"name": category})
            self._in_category_edges[job_id] = category

        return {"jobs_written": 1, "skill_edges_written": len(skills)}

    def seed_course(self, course: dict[str, Any]) -> None:
        existing = next((c for c in self._courses if c.get("id") == course["id"]), None)
        for skill_name in course.get("teaches_skills", []):
            record = {
                "id": course["id"],
                "title": course.get("title"),
                "provider": course.get("provider"),
                "url": course.get("url"),
                "duration": course.get("duration"),
                "free": course.get("free", False),
                "skill_name": skill_name,
            }
            already = any(
                c.get("id") == course["id"] and c.get("skill_name") == skill_name
                for c in self._courses
            )
            if not already:
                self._courses.append(record)
        _ = existing  # kept for symmetry with the real MERGE-then-SET shape

    # -- read-back helpers for ingestion tests (not part of the real
    # GraphService surface, mirrors what a Cypher COUNT query would answer) --
    def count_jobs(self) -> int:
        return len(self._jobs)

    def count_skills(self) -> int:
        return len(self._skills)

    def count_requires_edges(self) -> int:
        return sum(len(edges) for edges in self._requires_edges.values())

    def get_skill_node(self, normalized_name: str) -> dict[str, Any] | None:
        node = self._skills.get(normalized_name)
        return dict(node) if node else None

    def list_skill_names(self, search: str | None = None, limit: int = 50) -> list[str]:
        names = {sk["name"] for sk in self._skills.values() if sk.get("name")}
        names |= {
            skill["name"]
            for skills in self._job_skills.values()
            for skill in skills
            if skill.get("name")
        }
        if search:
            needle = search.lower()
            names = {n for n in names if needle in n.lower()}
        return sorted(names)[:limit]

    # ------------------------------------------------------------------ #
    # Market
    # ------------------------------------------------------------------ #
    def get_skill_demand_counts(self) -> list[dict[str, Any]]:
        counts: dict[str, int] = {}
        for skills in self._job_skills.values():
            for skill in skills:
                name = skill["name"]
                counts[name] = counts.get(name, 0) + 1
        ranked = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)
        return [{"skill_name": name, "demand_count": count} for name, count in ranked]
