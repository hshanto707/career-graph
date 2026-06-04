"""Application configuration loaded from environment variables / .env file."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ─── PostgreSQL ───────────────────────────────────────────────────────────
    database_url: str = "postgresql+asyncpg://careergraph:careergraph@localhost:5432/careergraph"

    # ─── Neo4j ────────────────────────────────────────────────────────────────
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "careergraph"

    # ─── JWT Authentication ───────────────────────────────────────────────────
    jwt_secret: str = "change-me-in-production-use-256-bit-key"
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24

    # ─── LLM Providers ───────────────────────────────────────────────────────
    anthropic_api_key: str = ""
    openai_api_key: str = ""

    # ─── LLM Configuration ───────────────────────────────────────────────────
    llm_provider: str = "claude"
    llm_model: str = "claude-sonnet-4-6"

    # ─── CORS / Frontend ─────────────────────────────────────────────────────
    frontend_url: str = "http://localhost:5173"

    # ─── Ollama (local LLM fallback) ─────────────────────────────────────────
    ollama_base_url: str = "http://localhost:11434"

    # ─── Custom / Fine-tuned Model ────────────────────────────────────────────
    custom_model_url: str = ""         # vLLM or TGI endpoint, e.g. http://localhost:8080
    custom_model_name: str = "careergraph-v1"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


settings = Settings()
