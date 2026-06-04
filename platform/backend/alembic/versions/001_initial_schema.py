"""Initial schema: users and student_profiles tables.

Revision ID: 001
Revises:
Create Date: 2026-04-13
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True, nullable=False),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "student_profiles",
        sa.Column("id", sa.String(36), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            unique=True,
            nullable=False,
        ),
        sa.Column("university", sa.String(200), nullable=True),
        sa.Column("graduation_year", sa.Integer(), nullable=True),
        sa.Column("target_roles", sa.JSON(), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_student_profiles_user_id", "student_profiles", ["user_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_student_profiles_user_id", table_name="student_profiles")
    op.drop_table("student_profiles")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
