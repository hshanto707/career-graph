"""Neo4j async graph database connection."""
from neo4j import AsyncGraphDatabase, AsyncDriver
from app.config import settings

_driver: AsyncDriver | None = None


def get_driver() -> AsyncDriver:
    """Get or create the Neo4j driver (singleton)."""
    global _driver
    if _driver is None:
        _driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )
    return _driver


async def close_driver() -> None:
    """Close the Neo4j driver on app shutdown."""
    global _driver
    if _driver is not None:
        await _driver.close()
        _driver = None


async def get_neo4j():
    """FastAPI dependency: yields a Neo4j async session."""
    driver = get_driver()
    async with driver.session() as session:
        yield session
