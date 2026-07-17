"""CareerGraph FastAPI application entrypoint.

Wires together CORS, the response-envelope exception handlers, and router
registration (per system-design.md \xa76). Phase 1 scope: scaffold + data
layer only — routers are mounted but largely placeholder until later phases
implement their route handlers.
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.responses import envelope, register_exception_handlers
from app.database.postgres import engine as postgres_engine
from app.database.neo4j import close_driver, verify_connectivity
from app.routers import (
    admin,
    auth,
    dashboard,
    gap_analysis,
    jobs,
    market,
    profile,
    recommendations,
    skills,
)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    close_driver()


app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION, lifespan=lifespan)

# --- CORS: restrict to the configured frontend origin only. Auth is header
# based (Bearer JWT), not cookie based, so credentials are not required. ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

# --- Router registration ---
app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(jobs.router)
app.include_router(skills.router)
app.include_router(recommendations.router)
app.include_router(gap_analysis.router)
app.include_router(market.router)
app.include_router(dashboard.router)
app.include_router(admin.router)


@app.get("/health")
def health():
    """Liveness/readiness check. Reports each dependency independently so a
    single down service doesn't mask the status of the other."""
    postgres_status = "ok"
    try:
        with postgres_engine.connect():
            pass
    except Exception:
        postgres_status = "unreachable"

    neo4j_status = "ok" if verify_connectivity() else "unreachable"

    return envelope(
        data={"postgres": postgres_status, "neo4j": neo4j_status},
        message="CareerGraph API is running.",
    )
