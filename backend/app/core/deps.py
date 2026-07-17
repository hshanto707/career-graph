"""Reusable FastAPI auth dependency.

`get_current_user` is the single point where `user_id`/`student_id` is
derived from the request -- always from the validated JWT's `sub` claim,
never from a request body/query param (system-design.md §15 control C4).
Every protected router imports this dependency rather than re-implementing
token handling.
"""
from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import TokenError, decode_access_token
from app.database.neo4j import get_driver
from app.database.postgres import get_db
from app.engine.orchestrator import EngineOrchestrator
from app.models.user import User
from app.services.graph_service import GraphService

# `auto_error=False` so a missing header raises our own 401 (with the shared
# envelope, via the exception handler) instead of FastAPI's default 403.
_bearer_scheme = HTTPBearer(auto_error=False)


@dataclass
class CurrentUser:
    id: str
    email: str


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> CurrentUser:
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated.")

    try:
        payload = decode_access_token(credentials.credentials)
    except TokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token.") from exc

    return CurrentUser(id=payload["sub"], email=payload.get("email", ""))


def get_current_db_user(
    current: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    """Like `get_current_user`, but also loads the full `User` row. Raises
    401 if the token is structurally valid but the user no longer exists
    (e.g. deleted account with an old, still-unexpired token)."""
    user = db.get(User, current.id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User no longer exists.")
    return user


def get_graph_service() -> GraphService:
    """Default production dependency for the student-facing routers (B7) --
    a real Neo4j-backed `GraphService`.

    Tests override this with a `FakeGraphService` via
    `app.dependency_overrides[get_graph_service]` so the whole suite runs
    without a live Neo4j instance. This is the one seam every algorithmic
    route depends on -- swap it here, and every router/orchestrator that
    takes it as a dependency follows automatically.
    """
    return GraphService(get_driver())


def get_orchestrator(
    graph_service: GraphService = Depends(get_graph_service),
) -> EngineOrchestrator:
    """Builds a per-request `EngineOrchestrator` wired to whichever
    `GraphService` is active (real or `FakeGraphService`, per
    `get_graph_service`'s override). LLM provider selection is resolved
    lazily, inside the orchestrator, from `Settings.LLM_PROVIDER`."""
    return EngineOrchestrator(graph_service)
