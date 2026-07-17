from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import get_settings
from app.database.postgres import Base
from app.models import StudentProfile, User  # noqa: F401 - registers models on Base.metadata

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


_PLACEHOLDER_URL = "driver://user:pass@localhost/dbname"


def _database_url() -> str:
    # Honor an explicit sqlalchemy.url from the Alembic Config (e.g. set
    # programmatically by a test that wants an isolated on-disk SQLite file)
    # over the settings-derived default, falling back to the latter only
    # when the config still has alembic.ini's placeholder value.
    configured = config.get_main_option("sqlalchemy.url")
    if configured and configured != _PLACEHOLDER_URL:
        return configured

    settings = get_settings()
    if settings.TESTING:
        return "sqlite:///./test_careergraph.db"
    return settings.DATABASE_URL


def run_migrations_offline() -> None:
    url = _database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = _database_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
