"""Application configuration.

Reads settings from environment variables / a `.env` file via pydantic-settings.
All fields have sane local/test defaults so the app (and the test suite) can
boot without a real Postgres/Neo4j/LLM key present. In a real deployment,
`.env` overrides these defaults.
"""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- App ---
    APP_NAME: str = "CareerGraph API"
    APP_VERSION: str = "0.1.0"
    ENV: str = "development"

    # Set to true by the test suite (or TESTING=1 in the environment) to force
    # the SQL layer onto an in-memory/local SQLite database instead of Postgres.
    TESTING: bool = False

    # --- PostgreSQL ---
    DATABASE_URL: str = "postgresql+psycopg2://careergraph:careergraph@localhost:5432/careergraph"

    # --- Neo4j ---
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "careergraph"

    # --- Auth ---
    JWT_SECRET: str = "dev-only-insecure-secret-change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 24

    # --- Admin (module B4) ---
    # Capstone-scope decision (features-todo.md "Open decisions" #1): a
    # single fixed admin token via .env, checked against the `X-Admin-Token`
    # header, rather than a full admin-role/user system.
    ADMIN_TOKEN: str = "dev-admin-token-change-me"

    # --- LLM ---
    LLM_PROVIDER: str = "none"  # none | claude | openai | ollama
    LLM_MODEL: str = "claude-sonnet-4-6"
    ANTHROPIC_API_KEY: str | None = None
    OPENAI_API_KEY: str | None = None
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    # --- CORS ---
    FRONTEND_URL: str = "http://localhost:5173"


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor. Use `get_settings.cache_clear()` in tests
    that mutate environment variables between cases."""
    return Settings()
