"""
Authentication router: register and login endpoints.

POST /api/v1/auth/register — Create account, return JWT
POST /api/v1/auth/login    — Verify credentials, return JWT
"""
from typing import Annotated
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.postgres import get_db
from app.models.user import User
from app.models.profile import StudentProfile
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse
from app.schemas.common import ok
from app.services.auth_service import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth")


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    body: RegisterRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Register a new user account and return a JWT token."""
    # Check duplicate email
    result = await db.execute(select(User).where(User.email == body.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # Create user
    user = User(
        email=body.email,
        name=body.name,
        hashed_password=hash_password(body.password),
    )
    db.add(user)
    await db.flush()  # Get user.id before commit

    # Create linked profile
    profile = StudentProfile(user_id=str(user.id))
    db.add(profile)
    await db.commit()

    token = create_access_token(str(user.id), user.email)
    return ok(
        TokenResponse(
            access_token=token,
            user_id=str(user.id),
            name=user.name,
            email=user.email,
        ).model_dump()
    )


@router.post("/login")
async def login(
    body: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Login with email/password and receive a JWT token."""
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_access_token(str(user.id), user.email)
    return ok(
        TokenResponse(
            access_token=token,
            user_id=str(user.id),
            name=user.name,
            email=user.email,
        ).model_dump()
    )
