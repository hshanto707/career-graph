"""auth router — B3.

POST /auth/register, POST /auth/login. Both return the shared envelope
wrapping a `TokenResponse` (`{token, user}`) per system-design.md §8.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core import login_lockout
from app.core.deps import CurrentUser, get_current_user
from app.core.responses import AppError, envelope
from app.core.security import create_access_token, hash_password, verify_password
from app.database.postgres import get_db
from app.models.profile import StudentProfile
from app.models.user import User
from app.schemas.auth import TokenResponse, UserCreate, UserLogin, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])

# Generic message for any login failure -- deliberately identical whether the
# email doesn't exist or the password is wrong, so the response never leaks
# which case occurred (test-plan.md §B3 #4).
_INVALID_CREDENTIALS_MESSAGE = "Invalid email or password."


def _normalize_email(email: str) -> str:
    # Emails are case-insensitive per RFC convention for the domain, and in
    # practice for the local part too for virtually every real provider --
    # normalize to lowercase consistently for storage + lookup.
    return email.strip().lower()


@router.post("/register", status_code=201)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    email = _normalize_email(payload.email)
    name = payload.name.strip()

    if not name:
        raise AppError("VALIDATION_ERROR", "Name must not be empty.", 422)

    user = User(email=email, hashed_password=hash_password(payload.password), name=name)
    db.add(user)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise AppError("CONFLICT", "An account with this email already exists.", 409)

    # Every registered student gets an empty profile immediately -- callers
    # (dashboard, gap-analysis, etc.) can always assume a profile row exists.
    db.add(StudentProfile(user_id=user.id, skills=[], target_roles=[], experience=[]))
    db.commit()
    db.refresh(user)

    token = create_access_token(user_id=user.id, email=user.email)
    return envelope(
        data=TokenResponse(token=token, user=UserOut.model_validate(user)).model_dump(),
        message="Registration successful.",
    )


@router.post("/login")
def login(payload: UserLogin, db: Session = Depends(get_db)):
    email = _normalize_email(payload.email)

    locked_for = login_lockout.seconds_until_unlocked(email)
    if locked_for > 0:
        raise AppError(
            "TOO_MANY_ATTEMPTS",
            f"Too many failed login attempts. Try again in {int(locked_for) + 1} seconds.",
            429,
        )

    user = db.query(User).filter(User.email == email).one_or_none()

    if user is None or not verify_password(payload.password, user.hashed_password):
        login_lockout.record_failure(email)
        raise AppError("UNAUTHORIZED", _INVALID_CREDENTIALS_MESSAGE, 401)

    login_lockout.record_success(email)
    token = create_access_token(user_id=user.id, email=user.email)
    return envelope(
        data=TokenResponse(token=token, user=UserOut.model_validate(user)).model_dump(),
        message="Login successful.",
    )


@router.get("/me")
def me(current: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """Small convenience route exercising `get_current_user` end-to-end --
    also useful for the frontend to validate a stored token on load."""
    user = db.get(User, current.id)
    if user is None:
        raise AppError("NOT_FOUND", "User not found.", 404)
    return envelope(data=UserOut.model_validate(user).model_dump())
