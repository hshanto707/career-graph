"""FastAPI shared dependencies."""
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from neo4j import AsyncSession as Neo4jSession

from app.database.postgres import get_db
from app.database.neo4j import get_neo4j
from app.config import settings  # noqa: F401 — re-exported for convenience

# Import deferred to avoid circular imports
security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Dependency that extracts the current authenticated user from JWT.
    Raises 401 if token is missing, expired, or invalid.
    """
    from app.services.auth_service import decode_token
    from app.models.user import User
    from sqlalchemy import select

    payload = decode_token(credentials.credentials)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user


# Type aliases for cleaner router signatures
DBDep = Annotated[AsyncSession, Depends(get_db)]
Neo4jDep = Annotated[Neo4jSession, Depends(get_neo4j)]
