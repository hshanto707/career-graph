"""profile router — module B7.

GET /profile, PUT /profile, POST /profile/skills. Postgres is the source of
truth for account/profile data; every write here also (re)syncs the
corresponding `Student` node + `HAS_SKILL`/`TARGETS` edges into Neo4j via
`GraphService`, in the same request, per system-design.md §7.1's sync note.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser, get_current_user, get_graph_service
from app.core.responses import envelope
from app.database.postgres import get_db
from app.models.profile import StudentProfile
from app.routers._shared import get_profile_or_404
from app.schemas.profile import ProfileOut, ProfileUpdate, SkillEntry
from app.services.graph_service import GraphService

router = APIRouter(prefix="/profile", tags=["profile"])


def _sync_graph(graph_service: GraphService, user_id: str, profile: StudentProfile) -> None:
    """Best-effort Neo4j sync. Never raises out of a route -- the
    PostgreSQL write is the source of truth and must never be rolled back
    just because the graph store is briefly unreachable."""
    try:
        graph_service.upsert_student_node(
            student_id=user_id,
            skills=list(profile.skills or []),
            target_roles=list(profile.target_roles or []),
        )
    except Exception:  # noqa: BLE001 - see docstring
        pass


@router.get("")
def get_profile(
    current: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = get_profile_or_404(db, current.id)
    return envelope(data=ProfileOut.model_validate(profile).model_dump())


@router.put("")
def update_profile(
    payload: ProfileUpdate,
    current: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    graph_service: GraphService = Depends(get_graph_service),
):
    profile = get_profile_or_404(db, current.id)

    data = payload.model_dump(exclude_unset=True)
    if "major" in data:
        profile.major = data["major"]
    if "graduation_year" in data:
        profile.graduation_year = data["graduation_year"]
    if "skills" in data:
        profile.skills = data["skills"]
    if "target_roles" in data:
        profile.target_roles = data["target_roles"]
    if "experience" in data:
        profile.experience = data["experience"]

    db.commit()
    db.refresh(profile)
    _sync_graph(graph_service, current.id, profile)

    return envelope(data=ProfileOut.model_validate(profile).model_dump(), message="Profile updated.")


@router.post("/skills", status_code=201)
def add_or_update_skill(
    payload: SkillEntry,
    current: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    graph_service: GraphService = Depends(get_graph_service),
):
    """Adds a new skill, or updates an existing one (matched case-
    insensitively by name) rather than creating a duplicate entry."""
    profile = get_profile_or_404(db, current.id)

    skills = list(profile.skills or [])
    new_entry = payload.model_dump()
    match_idx = next(
        (i for i, s in enumerate(skills) if s.get("name", "").strip().lower() == payload.name.strip().lower()),
        None,
    )
    if match_idx is not None:
        skills[match_idx] = new_entry
    else:
        skills.append(new_entry)

    profile.skills = skills
    db.commit()
    db.refresh(profile)
    _sync_graph(graph_service, current.id, profile)

    return envelope(data=ProfileOut.model_validate(profile).model_dump(), message="Skill saved.")
