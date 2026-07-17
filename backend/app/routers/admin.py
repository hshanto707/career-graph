"""admin router — module B4.

Exposes the ingestion pipeline trigger + status endpoints per
system-design.md §8:

    POST /admin/ingest/csv     -- upload a jobs CSV, runs Ingestion +
                                   Normalization synchronously, returns stats.
    GET  /admin/ingest/status  -- returns the most recent run's stats, or an
                                   explicit "no runs yet" state.

Auth: gated by a fixed shared secret (`X-Admin-Token` header, compared to
`Settings.ADMIN_TOKEN`) — the capstone-scope decision documented in
features-todo.md's "Open decisions" list (#1): a full admin-role system is
out of scope, but the endpoint must never be reachable unauthenticated.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, Header, UploadFile

from app.core.config import Settings, get_settings
from app.core.responses import AppError, envelope
from app.database.neo4j import get_driver
from app.engine.ingestion.ingestion_agent import IngestionAgent
from app.engine.ingestion.normalization_agent import NormalizationAgent
from app.services.graph_service import GraphService

router = APIRouter(prefix="/admin", tags=["admin"])

BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BACKEND_ROOT / "data"
DEFAULT_SYNONYMS_PATH = DATA_DIR / "synonyms.json"
DEFAULT_ONET_PATH = DATA_DIR / "onet_skills.csv"

# In-memory "last ingestion run" store. A single-process capstone deployment
# does not need this durable across restarts; if that changes, persist it to
# Postgres instead of adding new ingestion-unrelated infra here.
_last_run_stats: dict[str, Any] | None = None


def get_graph_service() -> GraphService:
    """Default production dependency — a real Neo4j-backed GraphService.

    Tests override this with a `FakeGraphService` via
    `app.dependency_overrides[get_graph_service]` so the whole suite runs
    without a live Neo4j instance.
    """
    return GraphService(get_driver())


def require_admin(x_admin_token: str | None = Header(default=None)) -> None:
    settings = get_settings()
    if not x_admin_token or x_admin_token != settings.ADMIN_TOKEN:
        raise AppError("UNAUTHORIZED", "Missing or invalid admin token.", status_code=401)


@router.post("/ingest/csv", dependencies=[Depends(require_admin)])
async def ingest_csv(
    file: UploadFile = File(...),
    graph_service: GraphService = Depends(get_graph_service),
    settings: Settings = Depends(get_settings),
) -> dict:
    global _last_run_stats

    raw_bytes = await file.read()

    ingestion_agent = IngestionAgent()
    try:
        ingestion_result = ingestion_agent.read_csv(raw_bytes)
    except ValueError as exc:
        raise AppError("VALIDATION_ERROR", str(exc), status_code=422) from exc

    normalization_agent = NormalizationAgent(
        graph_service=graph_service,
        synonyms_path=DEFAULT_SYNONYMS_PATH,
        onet_skills_path=DEFAULT_ONET_PATH,
    )
    normalization_stats = normalization_agent.process_and_write(ingestion_result.records)

    run_stats = {
        "filename": file.filename,
        **ingestion_result.stats.as_dict(),
        **normalization_stats.as_dict(),
    }
    _last_run_stats = run_stats

    return envelope(data=run_stats, message="Ingestion complete.")


@router.get("/ingest/status", dependencies=[Depends(require_admin)])
def ingest_status() -> dict:
    if _last_run_stats is None:
        return envelope(data={"has_run": False}, message="No ingestion runs yet.")
    return envelope(data={"has_run": True, **_last_run_stats}, message="Last ingestion run.")
