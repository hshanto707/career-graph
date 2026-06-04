"""
CareerGraph API — FastAPI application entry point.

Mounts all routers under /api/v1 prefix. Handles CORS, startup/shutdown lifecycle.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database.neo4j import close_driver

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_DEFAULT_JWT_SECRET = "change-me-in-production-use-256-bit-key"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown lifecycle."""
    # B-01: LLM Provider — lazy import so factory.py can be missing without crash
    try:
        from app.engine.llm.factory import create_llm_provider
        app.state.llm_provider = create_llm_provider(settings)
        if app.state.llm_provider:
            logger.info(f"LLM provider initialized: {settings.llm_provider}")
        else:
            logger.info("LLM provider: none (running in algorithmic-only mode)")
    except ImportError:
        app.state.llm_provider = None
        logger.info("LLM factory not found — running without LLM")

    # B-08: Startup validation warnings (non-fatal)
    if settings.jwt_secret == _DEFAULT_JWT_SECRET:
        logger.warning("WARNING: JWT_SECRET is using placeholder value. Set a secure key in production.")

    if settings.llm_provider not in ("none", "ollama", ""):
        if settings.llm_provider == "claude" and not settings.anthropic_api_key:
            logger.warning("WARNING: LLM_PROVIDER=claude but ANTHROPIC_API_KEY is not set.")
        elif settings.llm_provider == "openai" and not settings.openai_api_key:
            logger.warning("WARNING: LLM_PROVIDER=openai but OPENAI_API_KEY is not set.")

    # Check if Neo4j has data (warn only, don't fail)
    try:
        from app.database.neo4j import get_driver
        driver = get_driver()
        async with driver.session() as session:
            result = await session.run("MATCH (j:Job) RETURN count(j) AS cnt LIMIT 1")
            records = await result.data()
            job_count = records[0]["cnt"] if records else 0
            if job_count == 0:
                logger.warning("WARNING: No jobs in graph. Run POST /api/v1/admin/ingest/csv to load data.")
    except Exception:
        pass  # DB not yet connected — handled by health check

    logger.info("CareerGraph API starting up...")
    yield
    logger.info("CareerGraph API shutting down...")
    await close_driver()


app = FastAPI(
    title="CareerGraph API",
    description="Agent-Based Labor Market Intelligence Platform for Student Career Guidance",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and mount all routers
from app.routers import auth, profile, jobs, skills, recommendations, gap_analysis, market, dashboard, admin  # noqa: E402

PREFIX = "/api/v1"
app.include_router(auth.router,            prefix=PREFIX, tags=["Authentication"])
app.include_router(profile.router,         prefix=PREFIX, tags=["Profile"])
app.include_router(jobs.router,            prefix=PREFIX, tags=["Jobs"])
app.include_router(skills.router,          prefix=PREFIX, tags=["Skills"])
app.include_router(recommendations.router, prefix=PREFIX, tags=["Recommendations"])
app.include_router(gap_analysis.router,    prefix=PREFIX, tags=["Gap Analysis"])
app.include_router(market.router,          prefix=PREFIX, tags=["Market"])
app.include_router(dashboard.router,       prefix=PREFIX, tags=["Dashboard"])
app.include_router(admin.router,           prefix=PREFIX, tags=["Admin"])

# Model inference router (created separately — loads only if file exists)
try:
    from app.routers import model as model_router
    app.include_router(model_router.router, prefix=PREFIX, tags=["Model"])
except ImportError:
    pass


# I-04: Enriched health check
@app.get("/api/v1/health", tags=["Health"])
async def health_check(request: Request):
    """Health check with database connectivity and LLM provider status."""
    from app.database.postgres import engine
    from sqlalchemy import text

    neo4j_status = "disconnected"
    jobs_in_graph = 0
    try:
        from app.database.neo4j import get_driver
        driver = get_driver()
        async with driver.session() as session:
            result = await session.run("MATCH (j:Job) RETURN count(j) AS cnt")
            records = await result.data()
            jobs_in_graph = records[0]["cnt"] if records else 0
            neo4j_status = "connected"
    except Exception:
        pass

    postgres_status = "disconnected"
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        postgres_status = "connected"
    except Exception:
        pass

    llm_obj = getattr(request.app.state, "llm_provider", None)
    llm_label = settings.llm_provider if llm_obj else "none"

    return {
        "success": True,
        "data": {
            "status": "healthy",
            "version": "1.0.0",
            "databases": {
                "postgres": postgres_status,
                "neo4j": neo4j_status,
            },
            "llm_provider": llm_label,
            "jobs_in_graph": jobs_in_graph,
        },
        "message": "CareerGraph API is running",
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"success": False, "data": None, "message": "Internal server error"},
    )
