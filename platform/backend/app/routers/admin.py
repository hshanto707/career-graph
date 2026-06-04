"""
Admin router — data ingestion, prerequisite seeding, and graph statistics.

POST /api/v1/admin/ingest/csv        — Upload job postings CSV (triggers pipeline)
GET  /api/v1/admin/ingest/status     — Get status of last ingestion
POST /api/v1/admin/seed/prerequisites — Seed LEADS_TO edges from prerequisites.json
GET  /api/v1/admin/stats             — Graph statistics (node/edge counts)
"""
import json
import logging
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from app.database.neo4j import get_neo4j
from app.dependencies import get_current_user
from app.services.graph_service import GraphService
from app.engine.ingestion.ingestion_agent import IngestionAgent
from app.engine.ingestion.normalization_agent import NormalizationAgent
from app.schemas.common import ok

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin")

_PREREQ_FILE = Path(__file__).parent.parent.parent / "data" / "prerequisites.json"

# In-memory ingestion status (would be a Redis job queue in production)
_last_ingest_status: dict = {
    "status": "idle",
    "total_rows": 0,
    "valid_rows": 0,
    "failed_rows": 0,
    "message": "No ingestion has run yet",
}


@router.post("/ingest/csv")
async def ingest_csv(
    file: UploadFile = File(..., description="CSV file with job postings"),
    current_user=Depends(get_current_user),
    neo4j_session=Depends(get_neo4j),
):
    """
    Upload a job postings CSV and run the ingestion pipeline.

    Pipeline:
    1. IngestionAgent validates and parses the CSV
    2. NormalizationAgent resolves skill synonyms
    3. GraphService writes jobs and skills to Neo4j
    """
    global _last_ingest_status

    content = await file.read()
    csv_text = content.decode("utf-8")

    try:
        ingest_agent = IngestionAgent()
        result = ingest_agent.ingest_csv(csv_text)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    norm_agent = NormalizationAgent()
    jobs = norm_agent.normalize_jobs(result.jobs)

    svc = GraphService(neo4j_session)
    written = 0
    for job in jobs:
        try:
            await svc.upsert_job(job)
            written += 1
        except Exception as e:
            logger.warning(f"Failed to write job {job.get('id')}: {e}")

    _last_ingest_status = {
        "status": "completed",
        "total_rows": result.total_rows,
        "valid_rows": result.valid_rows,
        "failed_rows": result.failed_rows,
        "message": f"Ingested {written}/{result.valid_rows} jobs into Neo4j",
    }

    return ok(_last_ingest_status)


@router.get("/ingest/status")
async def ingest_status(current_user=Depends(get_current_user)):
    """Get the status of the last ingestion operation."""
    return ok(_last_ingest_status)


@router.post("/seed/prerequisites")
async def seed_prerequisites(
    current_user=Depends(get_current_user),
    neo4j_session=Depends(get_neo4j),
):
    """Seed LEADS_TO skill prerequisite edges from prerequisites.json."""
    if not _PREREQ_FILE.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="prerequisites.json not found. Ensure data/prerequisites.json exists.",
        )

    try:
        data = json.loads(_PREREQ_FILE.read_text())
        edges = data.get("prerequisites", [])
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to read prerequisites: {e}")

    svc = GraphService(neo4j_session)
    count = await svc.upsert_prereq_edges(edges)
    return ok({"seeded": count, "message": f"Created/updated {count} LEADS_TO edges"})


@router.get("/stats")
async def graph_stats(
    current_user=Depends(get_current_user),
    neo4j_session=Depends(get_neo4j),
):
    """Get graph statistics: node counts, edge counts, and density."""
    svc = GraphService(neo4j_session)
    try:
        stats = await svc.get_graph_stats()
    except Exception as e:
        logger.error(f"Error fetching graph stats: {e}")
        stats = {"node_counts": {}, "edge_counts": {}, "graph_density": 0.0}
    return ok(stats)
