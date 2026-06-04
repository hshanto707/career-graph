"""Student profile model (one-to-one with User)."""
import uuid
from datetime import datetime
from sqlalchemy import String, Integer, ForeignKey, DateTime, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.database.postgres import Base


class StudentProfile(Base):
    """Extended profile data for student users."""
    __tablename__ = "student_profiles"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id"),
        unique=True,
        nullable=False,
        index=True,
    )
    university: Mapped[str | None] = mapped_column(String(200), nullable=True)
    graduation_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    target_roles: Mapped[list] = mapped_column(JSON, default=list)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
