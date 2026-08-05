"""GraphService — the single point of contact for all Cypher queries.

Per system-design.md §15 (control C6), every query here uses parameterized
Cypher (`$param` syntax) exclusively — never string interpolation/f-strings
into a query body — so arbitrary user input (skill names, search terms, ids)
can never be interpreted as Cypher.

Algorithmic agents (SkillGapAgent, RecommendationAgent, PathFinderAgent,
MarketAgent) call these methods and never talk to the neo4j driver directly.
"""
from __future__ import annotations

from typing import Any

from neo4j import Driver


class GraphService:
    """Thin, fully-parameterized query layer over the Neo4j knowledge graph."""

    def __init__(self, driver: Driver):
        self._driver = driver

    # ------------------------------------------------------------------ #
    # Student
    # ------------------------------------------------------------------ #
    def get_student_skills(self, student_id: str) -> list[dict[str, Any]]:
        """Return [{name, proficiency, years}] for a student's HAS_SKILL edges.

        Returns an empty list if the student has no such edges, or does not
        exist in Neo4j at all (e.g. registered in Postgres but never synced).
        """
        query = """
        MATCH (s:Student {id: $student_id})-[r:HAS_SKILL]->(sk:Skill)
        RETURN sk.name AS name, r.proficiency AS proficiency, r.years AS years
        """
        with self._driver.session() as session:
            result = session.run(query, student_id=student_id)
            return [dict(record) for record in result]

    def upsert_student_node(
        self,
        student_id: str,
        skills: list[dict[str, Any]],
        target_roles: list[str],
    ) -> None:
        """MERGE the Student node and (re)write its HAS_SKILL / TARGETS edges.

        `skills` is a list of {name, proficiency, years}. `target_roles` is a
        list of job ids the student is targeting.
        """
        with self._driver.session() as session:
            session.execute_write(self._upsert_student_tx, student_id, skills, target_roles)

    @staticmethod
    def _upsert_student_tx(tx, student_id: str, skills: list[dict[str, Any]], target_roles: list[str]):
        tx.run("MERGE (s:Student {id: $student_id})", student_id=student_id)

        # Clear and rewrite HAS_SKILL edges so removed skills don't linger.
        tx.run(
            """
            MATCH (s:Student {id: $student_id})-[r:HAS_SKILL]->()
            DELETE r
            """,
            student_id=student_id,
        )
        for skill in skills:
            tx.run(
                """
                MATCH (s:Student {id: $student_id})
                MERGE (sk:Skill {normalized_name: $name})
                ON CREATE SET sk.name = $name
                MERGE (s)-[r:HAS_SKILL]->(sk)
                SET r.proficiency = $proficiency, r.years = $years
                """,
                student_id=student_id,
                name=skill["name"],
                proficiency=skill.get("proficiency", 0),
                years=skill.get("years", 0.0),
            )

        tx.run(
            """
            MATCH (s:Student {id: $student_id})-[r:TARGETS]->()
            DELETE r
            """,
            student_id=student_id,
        )
        for job_id in target_roles:
            tx.run(
                """
                MATCH (s:Student {id: $student_id})
                MERGE (j:Job {id: $job_id})
                MERGE (s)-[:TARGETS]->(j)
                """,
                student_id=student_id,
                job_id=job_id,
            )

    # ------------------------------------------------------------------ #
    # Jobs
    # ------------------------------------------------------------------ #
    def get_job(self, job_id: str) -> dict[str, Any] | None:
        query = """
        MATCH (j:Job {id: $job_id})
        RETURN j.id AS id, j.title AS title, j.company AS company,
               j.location AS location, j.type AS type, j.source AS source,
               j.salary_min AS salary_min, j.salary_max AS salary_max
        """
        with self._driver.session() as session:
            record = session.run(query, job_id=job_id).single()
            return dict(record) if record else None

    def list_jobs(self, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """List jobs, optionally filtered by `type`, `location`, or a `search`
        substring against the title. All filter values are bound parameters —
        even a `search` value containing Cypher-special characters is treated
        as a literal string by `CONTAINS`.
        """
        filters = filters or {}
        clauses: list[str] = []
        params: dict[str, Any] = {}

        if filters.get("type"):
            clauses.append("j.type = $type")
            params["type"] = filters["type"]
        if filters.get("location"):
            clauses.append("j.location = $location")
            params["location"] = filters["location"]
        if filters.get("search"):
            clauses.append("toLower(j.title) CONTAINS toLower($search)")
            params["search"] = filters["search"]

        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        limit = int(filters.get("limit", 50))
        params["limit"] = limit

        query = f"""
        MATCH (j:Job)
        {where}
        RETURN j.id AS id, j.title AS title, j.company AS company,
               j.location AS location, j.type AS type
        ORDER BY j.id
        LIMIT $limit
        """
        with self._driver.session() as session:
            result = session.run(query, **params)
            return [dict(record) for record in result]

    def list_job_titles(self, search: str | None = None, limit: int = 50) -> list[str]:
        """Distinct, sorted Job titles, optionally filtered by a case-insensitive
        substring match. Backs target-role autocomplete suggestions."""
        query = """
        MATCH (j:Job)
        WHERE j.title IS NOT NULL AND ($search IS NULL OR toLower(j.title) CONTAINS toLower($search))
        RETURN DISTINCT j.title AS title
        ORDER BY j.title
        LIMIT $limit
        """
        with self._driver.session() as session:
            result = session.run(query, search=search, limit=limit)
            return [record["title"] for record in result]

    def get_job_required_skills(self, job_id: str) -> list[dict[str, Any]]:
        query = """
        MATCH (j:Job {id: $job_id})-[r:REQUIRES]->(sk:Skill)
        RETURN sk.name AS name, r.importance AS importance, r.frequency AS frequency
        """
        with self._driver.session() as session:
            result = session.run(query, job_id=job_id)
            return [dict(record) for record in result]

    def get_all_jobs_with_requires(self) -> list[dict[str, Any]]:
        """Return every Job with its REQUIRES edges, for RecommendationAgent."""
        query = """
        MATCH (j:Job)
        OPTIONAL MATCH (j)-[r:REQUIRES]->(sk:Skill)
        RETURN j.id AS job_id, j.title AS title,
               [x IN collect({name: sk.name, importance: r.importance}) WHERE x.name IS NOT NULL]
                 AS required_skills
        """
        with self._driver.session() as session:
            result = session.run(query)
            return [dict(record) for record in result]

    # ------------------------------------------------------------------ #
    # Skill graph (PathFinderAgent)
    # ------------------------------------------------------------------ #
    def get_leads_to_graph(self) -> list[dict[str, Any]]:
        query = """
        MATCH (a:Skill)-[r:LEADS_TO]->(b:Skill)
        RETURN a.name AS from_skill, b.name AS to_skill, r.difficulty_jump AS difficulty_jump
        """
        with self._driver.session() as session:
            result = session.run(query)
            return [dict(record) for record in result]

    def get_teaches_courses(self, skill_ids: list[str]) -> list[dict[str, Any]]:
        query = """
        MATCH (c:Course)-[:TEACHES]->(sk:Skill)
        WHERE sk.name IN $skill_ids
        RETURN c.id AS id, c.title AS title, c.provider AS provider,
               c.url AS url, c.duration AS duration, c.free AS free,
               sk.name AS skill_name
        """
        with self._driver.session() as session:
            result = session.run(query, skill_ids=skill_ids)
            return [dict(record) for record in result]

    def list_skill_names(self, search: str | None = None, limit: int = 50) -> list[str]:
        """Distinct, sorted Skill names, optionally filtered by a case-insensitive
        substring match. Backs skill-name autocomplete suggestions."""
        query = """
        MATCH (s:Skill)
        WHERE s.name IS NOT NULL AND ($search IS NULL OR toLower(s.name) CONTAINS toLower($search))
        RETURN DISTINCT s.name AS name
        ORDER BY s.name
        LIMIT $limit
        """
        with self._driver.session() as session:
            result = session.run(query, search=search, limit=limit)
            return [record["name"] for record in result]

    # ------------------------------------------------------------------ #
    # Market (MarketAgent)
    # ------------------------------------------------------------------ #
    def get_skill_demand_counts(self) -> list[dict[str, Any]]:
        query = """
        MATCH (j:Job)-[:REQUIRES]->(sk:Skill)
        RETURN sk.name AS skill_name, count(j) AS demand_count
        ORDER BY demand_count DESC
        """
        with self._driver.session() as session:
            result = session.run(query)
            return [dict(record) for record in result]

    # ------------------------------------------------------------------ #
    # Ingestion writer (IngestionAgent / NormalizationAgent — module B4)
    # ------------------------------------------------------------------ #
    def ingest_job_posting(self, job: dict[str, Any], skills: list[dict[str, Any]]) -> dict[str, int]:
        """MERGE a single job posting + its normalized required skills into
        the graph. Idempotent: re-running this with the same `job["id"]` and
        the same skill `normalized_name`s does not create duplicate nodes or
        edges — every write below is a `MERGE`, never a bare `CREATE`, keyed
        on the same identity every agent/test uses.

        `job` must include a stable `id` (see `NormalizationAgent._job_id`,
        derived from company+title) plus title/company/location/type/salary
        fields and an optional `category`.

        `skills` is a list of
        `{raw_name, normalized_name, category, flagged, importance}`.
        """
        with self._driver.session() as session:
            return session.execute_write(self._ingest_job_posting_tx, job, skills)

    @staticmethod
    def _ingest_job_posting_tx(tx, job: dict[str, Any], skills: list[dict[str, Any]]) -> dict[str, int]:
        tx.run(
            """
            MERGE (j:Job {id: $id})
            SET j.title = $title, j.company = $company, j.location = $location,
                j.type = $type, j.salary_min = $salary_min, j.salary_max = $salary_max,
                j.source = $source
            """,
            id=job["id"],
            title=job.get("title"),
            company=job.get("company"),
            location=job.get("location"),
            type=job.get("type"),
            salary_min=job.get("salary_min"),
            salary_max=job.get("salary_max"),
            source=job.get("source", "kaggle_csv"),
        )

        for skill in skills:
            tx.run(
                """
                MATCH (j:Job {id: $job_id})
                MERGE (sk:Skill {normalized_name: $normalized_name})
                SET sk.name = $normalized_name,
                    sk.category = coalesce(sk.category, $category),
                    sk.flagged_for_review = $flagged
                MERGE (j)-[r:REQUIRES]->(sk)
                SET r.importance = $importance
                """,
                job_id=job["id"],
                normalized_name=skill["normalized_name"],
                category=skill.get("category"),
                flagged=bool(skill.get("flagged", False)),
                importance=skill.get("importance", "nice"),
            )

        category = job.get("category")
        if category:
            tx.run(
                """
                MATCH (j:Job {id: $job_id})
                MERGE (c:Category {name: $category})
                MERGE (j)-[:IN_CATEGORY]->(c)
                """,
                job_id=job["id"],
                category=category,
            )

        return {
            "jobs_written": 1,
            "skill_edges_written": len(skills),
        }

    def seed_course(self, course: dict[str, Any]) -> None:
        """MERGE a Course node + its `TEACHES` edges onto existing Skill
        nodes (by `normalized_name`). Used by `app/etl/seed_demo_data.py`;
        idempotent like every other write in this class."""
        with self._driver.session() as session:
            session.execute_write(self._seed_course_tx, course)

    @staticmethod
    def _seed_course_tx(tx, course: dict[str, Any]) -> None:
        tx.run(
            """
            MERGE (c:Course {id: $id})
            SET c.title = $title, c.provider = $provider, c.url = $url,
                c.duration = $duration, c.free = $free
            """,
            id=course["id"],
            title=course.get("title"),
            provider=course.get("provider"),
            url=course.get("url"),
            duration=course.get("duration"),
            free=course.get("free", False),
        )
        for skill_name in course.get("teaches_skills", []):
            tx.run(
                """
                MATCH (c:Course {id: $id})
                MERGE (sk:Skill {normalized_name: $skill_name})
                SET sk.name = $skill_name
                MERGE (c)-[:TEACHES]->(sk)
                """,
                id=course["id"],
                skill_name=skill_name,
            )

    # ------------------------------------------------------------------ #
    # Bootstrap
    # ------------------------------------------------------------------ #
    def ensure_constraints(self) -> None:
        """Idempotent constraint/index bootstrap — safe to call on every
        startup; `IF NOT EXISTS` means re-running never errors."""
        statements = [
            "CREATE CONSTRAINT skill_normalized_name IF NOT EXISTS "
            "FOR (s:Skill) REQUIRE s.normalized_name IS UNIQUE",
            "CREATE CONSTRAINT job_id IF NOT EXISTS "
            "FOR (j:Job) REQUIRE j.id IS UNIQUE",
            "CREATE CONSTRAINT student_id IF NOT EXISTS "
            "FOR (s:Student) REQUIRE s.id IS UNIQUE",
            "CREATE CONSTRAINT course_id IF NOT EXISTS "
            "FOR (c:Course) REQUIRE c.id IS UNIQUE",
            "CREATE CONSTRAINT category_name IF NOT EXISTS "
            "FOR (c:Category) REQUIRE c.name IS UNIQUE",
            "CREATE INDEX job_type IF NOT EXISTS FOR (j:Job) ON (j.type)",
            "CREATE INDEX job_location IF NOT EXISTS FOR (j:Job) ON (j.location)",
            "CREATE INDEX skill_category IF NOT EXISTS FOR (s:Skill) ON (s.category)",
        ]
        with self._driver.session() as session:
            for statement in statements:
                session.run(statement)
