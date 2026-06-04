"""
GraphService — Centralizes all Neo4j Cypher queries.

All Neo4j interactions go through this service class.
This makes queries easy to test, audit, and modify in one place.
"""
import logging
from neo4j import AsyncSession

logger = logging.getLogger(__name__)


class GraphService:
    """
    Provides high-level methods for all Neo4j graph operations.

    Each method wraps a Cypher query. Parameter binding ($param) is
    used everywhere to prevent Cypher injection attacks.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    # ─── Student Operations ──────────────────────────────────────────────────

    async def get_student_skills(self, user_id: str) -> list[dict]:
        """Get all skills for a student with proficiency and years."""
        result = await self.session.run(
            """
            MATCH (s:Student {user_id: $uid})-[r:HAS_SKILL]->(sk:Skill)
            RETURN sk.name AS name, r.proficiency AS proficiency, r.years AS years
            ORDER BY r.proficiency DESC
            """,
            uid=user_id,
        )
        records = await result.data()
        return [{"name": r["name"], "proficiency": r["proficiency"] or 0, "years": r["years"] or 0} for r in records]

    async def upsert_student_skill(self, user_id: str, skill_name: str, proficiency: float, years: float) -> None:
        """Add or update a skill for a student."""
        await self.session.run(
            """
            MERGE (s:Student {user_id: $uid})
            MERGE (sk:Skill {name: $skill_name})
            MERGE (s)-[r:HAS_SKILL]->(sk)
            SET r.proficiency = $proficiency, r.years = $years
            """,
            uid=user_id,
            skill_name=skill_name,
            proficiency=proficiency,
            years=years,
        )

    async def remove_student_skill(self, user_id: str, skill_name: str) -> None:
        """Remove a skill relationship from a student."""
        await self.session.run(
            """
            MATCH (s:Student {user_id: $uid})-[r:HAS_SKILL]->(sk:Skill {name: $skill_name})
            DELETE r
            """,
            uid=user_id,
            skill_name=skill_name,
        )

    # ─── Job Operations ───────────────────────────────────────────────────────

    async def get_all_jobs(self, limit: int = 1000) -> list[dict]:
        """Retrieve all job postings from the graph."""
        result = await self.session.run(
            """
            MATCH (j:Job)
            OPTIONAL MATCH (j)-[:REQUIRES]->(sk:Skill)
            WITH j, collect(sk.name) AS skills
            RETURN j.id AS id, j.title AS title, j.company AS company,
                   j.location AS location, j.employment_type AS employment_type,
                   j.salary_min AS salary_min, j.salary_max AS salary_max,
                   j.description AS description, j.posted_date AS posted_date,
                   skills AS skills_required
            ORDER BY j.id
            LIMIT $limit
            """,
            limit=limit,
        )
        return await result.data()

    async def get_jobs_filtered(
        self,
        search: str | None = None,
        location: str | None = None,
        employment_type: str | None = None,
        skill: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        """
        Get paginated jobs with optional filters.
        Returns (jobs, total_count).
        """
        conditions = ["1=1"]
        params: dict = {"limit": limit, "skip": offset}

        if search:
            conditions.append("(toLower(j.title) CONTAINS toLower($search) OR toLower(j.company) CONTAINS toLower($search))")
            params["search"] = search
        if location:
            conditions.append("toLower(j.location) CONTAINS toLower($location)")
            params["location"] = location
        if employment_type:
            conditions.append("j.employment_type = $employment_type")
            params["employment_type"] = employment_type

        where_clause = " AND ".join(conditions)
        skill_match = "OPTIONAL MATCH (j)-[:REQUIRES]->(sk:Skill)" if not skill else f"MATCH (j)-[:REQUIRES]->(sk:Skill {{name: $skill}})"
        if skill:
            params["skill"] = skill

        query = f"""
            MATCH (j:Job) WHERE {where_clause}
            {skill_match}
            WITH j, collect(DISTINCT sk.name) AS skills_required
            RETURN j.id AS id, j.title AS title, j.company AS company,
                   j.location AS location, j.employment_type AS employment_type,
                   j.salary_min AS salary_min, j.salary_max AS salary_max,
                   j.description AS description, j.posted_date AS posted_date,
                   skills_required
            ORDER BY j.id
            SKIP $skip LIMIT $limit
        """
        count_query = f"""
            MATCH (j:Job) WHERE {where_clause}
            RETURN count(j) AS total
        """

        result = await self.session.run(query, **params)
        jobs = await result.data()

        count_params = {k: v for k, v in params.items() if k not in ("limit", "skip")}
        count_result = await self.session.run(count_query, **count_params)
        count_data = await count_result.data()
        total = count_data[0]["total"] if count_data else 0

        return jobs, total

    async def get_job_by_id(self, job_id: str) -> dict | None:
        """Get a single job by ID including structured skill requirements."""
        result = await self.session.run(
            """
            MATCH (j:Job {id: $job_id})
            OPTIONAL MATCH (j)-[r:REQUIRES]->(sk:Skill)
            WITH j, collect({name: sk.name, importance: coalesce(r.importance, 'must')}) AS skills
            RETURN j.id AS id, j.title AS title, j.company AS company,
                   j.location AS location, j.employment_type AS employment_type,
                   j.salary_min AS salary_min, j.salary_max AS salary_max,
                   j.description AS description, j.posted_date AS posted_date,
                   skills AS skills_required
            """,
            job_id=job_id,
        )
        records = await result.data()
        return records[0] if records else None

    # ─── Market & Graph Operations ────────────────────────────────────────────

    async def get_prereq_graph(self) -> dict[str, list[str]]:
        """
        Get the skill prerequisite graph as a dict.
        Returns {skill_name: [prerequisite_skill_names]}.
        """
        result = await self.session.run(
            "MATCH (a:Skill)-[:LEADS_TO]->(b:Skill) RETURN a.name AS skill, b.name AS prereq"
        )
        records = await result.data()
        graph: dict[str, list[str]] = {}
        for row in records:
            graph.setdefault(row["skill"], []).append(row["prereq"])
        return graph

    async def get_courses_for_skills(self, skill_names: list[str]) -> list[dict]:
        """Find courses that teach the given skills."""
        result = await self.session.run(
            """
            MATCH (c:Course)-[:TEACHES]->(sk:Skill)
            WHERE sk.name IN $skill_names
            RETURN c.id AS id, c.title AS title, c.provider AS provider,
                   c.url AS url, c.duration AS duration, c.free AS free,
                   collect(sk.name) AS teaches_skills
            """,
            skill_names=skill_names,
        )
        return await result.data()

    # ─── Ingestion Operations ─────────────────────────────────────────────────

    async def upsert_job(self, job: dict) -> None:
        """Insert or update a job node and its REQUIRES skill relationships."""
        await self.session.run(
            """
            MERGE (j:Job {id: $id})
            SET j.title = $title, j.company = $company, j.location = $location,
                j.employment_type = $employment_type, j.salary_min = $salary_min,
                j.salary_max = $salary_max, j.description = $description,
                j.posted_date = $posted_date
            WITH j
            UNWIND $skills AS skill_name
            MERGE (sk:Skill {name: skill_name})
            MERGE (j)-[:REQUIRES {importance: 'must'}]->(sk)
            """,
            id=job["id"],
            title=job.get("title", ""),
            company=job.get("company", ""),
            location=job.get("location", ""),
            employment_type=job.get("employment_type", "Full-time"),
            salary_min=job.get("salary_min"),
            salary_max=job.get("salary_max"),
            description=job.get("description", ""),
            posted_date=job.get("posted_date", ""),
            skills=job.get("skills_required", []),
        )

    async def get_all_skills(self) -> list[dict]:
        """Get all skill nodes."""
        result = await self.session.run(
            "MATCH (sk:Skill) RETURN sk.name AS name, sk.category AS category ORDER BY sk.name"
        )
        return await result.data()

    # ─── Prerequisite Operations ──────────────────────────────────────────────

    async def upsert_prereq_edges(self, edges: list[dict]) -> int:
        """
        Create or update LEADS_TO edges between skills (prerequisites).

        Each edge dict: {"from": str, "to": str, "difficulty_jump": int}
        Returns the number of edges processed.
        """
        count = 0
        for edge in edges:
            await self.session.run(
                """
                MERGE (a:Skill {name: $from_skill})
                MERGE (b:Skill {name: $to_skill})
                MERGE (a)-[r:LEADS_TO]->(b)
                SET r.difficulty_jump = $difficulty_jump
                """,
                from_skill=edge["from"],
                to_skill=edge["to"],
                difficulty_jump=edge.get("difficulty_jump", 1),
            )
            count += 1
        return count

    async def get_graph_stats(self) -> dict:
        """Return node and relationship counts from the graph."""
        node_result = await self.session.run(
            "MATCH (n) WHERE size(labels(n)) > 0 RETURN labels(n)[0] AS label, count(n) AS cnt"
        )
        node_records = await node_result.data()
        node_counts = {r["label"]: r["cnt"] for r in node_records}

        rel_result = await self.session.run(
            "MATCH ()-[r]->() RETURN type(r) AS rel_type, count(r) AS cnt"
        )
        rel_records = await rel_result.data()
        edge_counts = {r["rel_type"]: r["cnt"] for r in rel_records}

        total_nodes = sum(node_counts.values()) or 1
        total_edges = sum(edge_counts.values())
        density = total_edges / (total_nodes * (total_nodes - 1)) if total_nodes > 1 else 0.0

        return {
            "node_counts": node_counts,
            "edge_counts": edge_counts,
            "graph_density": round(density, 4),
        }
