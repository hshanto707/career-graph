"""Small helpers shared across the B7 student-facing routers.

Not a router itself -- no `router = APIRouter()` here, so nothing in this
module is ever registered with `main.py`.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.profile import StudentProfile


def resolve_target_job_id(db: Session, user_id: str) -> str | None:
    """Resolves "the student's current target role" for routes that don't
    take an explicit `target_job_id` (`GET /skills/gap`'s default,
    `GET /dashboard`) -- the student's most-recently-added `target_roles`
    entry (list is treated as append-ordered; last entry wins).

    Returns `None` if the student has no profile yet or no target roles set
    at all -- callers must treat that as a defined empty/zero state, never
    an error (test-plan.md B7 edge cases: brand-new student must not 500).

    See docs/algorithmic-agents-decisions.md for the full write-up of this
    resolution (features-todo.md open decision #2: reconciling
    `GET /skills/gap` vs `POST /gap-analysis`).
    """
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == user_id).one_or_none()
    if profile is None or not profile.target_roles:
        return None
    return profile.target_roles[-1]


def get_profile_or_404(db: Session, user_id: str) -> StudentProfile:
    from app.core.responses import AppError

    profile = db.query(StudentProfile).filter(StudentProfile.user_id == user_id).one_or_none()
    if profile is None:
        raise AppError("NOT_FOUND", "Profile not found.", 404)
    return profile
