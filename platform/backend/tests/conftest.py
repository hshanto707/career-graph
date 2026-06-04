"""
Pytest fixtures for the CareerGraph test suite.

Uses an in-memory SQLite database for PostgreSQL tests and mocks for Neo4j.
This ensures tests run without any external service dependencies.
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from unittest.mock import AsyncMock, MagicMock

# Override settings BEFORE importing the app
import os
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("NEO4J_URI", "bolt://localhost:7687")
os.environ.setdefault("JWT_SECRET", "test-secret-key-for-testing-only")

from app.database.postgres import Base, get_db  # noqa: E402
from app.database.neo4j import get_neo4j          # noqa: E402
from main import app                               # noqa: E402


@pytest_asyncio.fixture(scope="function")
async def db_engine():
    """Create in-memory SQLite engine for tests."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine):
    """Async database session for tests."""
    factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with factory() as session:
        yield session


@pytest.fixture
def mock_neo4j():
    """Mock Neo4j session for tests."""
    mock = AsyncMock()
    mock.run = AsyncMock()
    mock.run.return_value = MagicMock()
    return mock


@pytest_asyncio.fixture(scope="function")
async def async_client(db_session, mock_neo4j):
    """HTTP client for API tests with mocked database dependencies."""
    app.dependency_overrides[get_db] = lambda: db_session  # type: ignore
    app.dependency_overrides[get_neo4j] = lambda: mock_neo4j  # type: ignore

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def registered_user(async_client):
    """Register a test user and return the response data."""
    response = await async_client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "name": "Test User",
        "password": "testpassword123",
    })
    return response.json()["data"]


@pytest_asyncio.fixture
async def auth_headers(async_client, registered_user):
    """Return auth headers for a registered test user."""
    response = await async_client.post("/api/v1/auth/login", json={
        "email": "test@example.com",
        "password": "testpassword123",
    })
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}
