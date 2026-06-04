"""
Profile router: view and update student profile.

GET    /api/v1/profile                     — Get current user's full profile
PUT    /api/v1/profile                     — Update profile fields
POST   /api/v1/profile/skills              — Add or update a skill
DELETE /api/v1/profile/skills/{skill_name} — Remove a skill
"""
from typing import Annotated
from fastapi import APIRouter, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.postgres import get_db
from app.database.neo4j import get_neo4j
from app.dependencies import get_current_user
from app.models.user import User
from app.models.profile import StudentProfile
from app.schemas.profile import (
    ProfileResponse,
    ProfileUpdateRequest,
    AddSkillRequest,
    SkillEntry,
)
from app.schemas.common import ok

router = APIRouter(prefix="/profile")


async def _get_profile_and_skills(
    user: User,
    db: AsyncSession,
    neo4j_session,
) -> ProfileResponse:
    """Helper: load profile from PostgreSQL and skills from Neo4j."""
    result = await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == str(user.id))
    )
    profile = result.scalar_one_or_none()

    # Get skills from Neo4j — graceful degradation if unavailable
    skills: list[SkillEntry] = []
    try:
        neo4j_result = await neo4j_session.run(
            "MATCH (s:Student {user_id: $uid})-[r:HAS_SKILL]->(sk:Skill) "
            "RETURN sk.name AS name, r.proficiency AS proficiency, r.years AS years",
            uid=str(user.id),
        )
        records = await neo4j_result.data()
        skills = [
            SkillEntry(
                name=r["name"],
                proficiency=r["proficiency"] or 0,
                years=r["years"] or 0,
            )
            for r in records
        ]
    except Exception:
        skills = []

    return ProfileResponse(
        user_id=str(user.id),
        name=user.name,
        email=user.email,
        university=profile.university if profile else None,
        graduation_year=profile.graduation_year if profile else None,
        target_roles=profile.target_roles if profile else [],
        bio=profile.bio if profile else None,
        skills=skills,
    )


@router.get("")
async def get_profile(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    neo4j_session=Depends(get_neo4j),
):
    """Get the authenticated user's full profile including skills."""
    profile_data = await _get_profile_and_skills(current_user, db, neo4j_session)
    return ok(profile_data.model_dump())


@router.put("")
async def update_profile(
    body: ProfileUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    neo4j_session=Depends(get_neo4j),
):
    """Update one or more profile fields. Only provided fields are changed."""
    result = await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == str(current_user.id))
    )
    profile = result.scalar_one_or_none()

    if profile is None:
        profile = StudentProfile(user_id=str(current_user.id))
        db.add(profile)

    update_data = body.model_dump(exclude_none=True)
    if "name" in update_data:
        current_user.name = update_data.pop("name")
    for field, value in update_data.items():
        setattr(profile, field, value)

    await db.commit()
    # Refresh instances so the response reflects changes
    await db.refresh(current_user)
    await db.refresh(profile)
    profile_data = await _get_profile_and_skills(current_user, db, neo4j_session)
    return ok(profile_data.model_dump())


@router.post("/skills", status_code=status.HTTP_201_CREATED)
async def add_skill(
    body: AddSkillRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    neo4j_session=Depends(get_neo4j),
):
    """Add or update a skill in the student's Neo4j profile node."""
    await neo4j_session.run(
        """
        MERGE (s:Student {user_id: $uid})
        MERGE (sk:Skill {name: $skill_name})
        MERGE (s)-[r:HAS_SKILL]->(sk)
        SET r.proficiency = $proficiency, r.years = $years
        """,
        uid=str(current_user.id),
        skill_name=body.skill_name,
        proficiency=body.proficiency,
        years=body.years,
    )
    return ok(
        {"skill_name": body.skill_name, "proficiency": body.proficiency, "years": body.years},
        "Skill added",
    )


@router.delete("/skills/{skill_name}")
async def remove_skill(
    skill_name: str,
    current_user: Annotated[User, Depends(get_current_user)],
    neo4j_session=Depends(get_neo4j),
):
    """Remove a skill relationship from the student's Neo4j node."""
    await neo4j_session.run(
        "MATCH (s:Student {user_id: $uid})-[r:HAS_SKILL]->(sk:Skill {name: $skill_name}) DELETE r",
        uid=str(current_user.id),
        skill_name=skill_name,
    )
    return ok(None, f"Skill '{skill_name}' removed")
