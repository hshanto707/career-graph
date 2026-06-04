"""LLM Provider Factory — instantiates the correct provider from settings."""
import logging
from app.engine.llm.base import LLMProvider

logger = logging.getLogger(__name__)


def create_llm_provider(settings) -> "LLMProvider | None":
    """
    Create an LLM provider from the given settings object.

    Returns None when provider is 'none', key is missing, or provider unknown.
    Safe to call in tests — returns None when no API key present.
    """
    provider = (getattr(settings, "llm_provider", "") or "").lower().strip()

    if provider in ("none", "", "null"):
        return None

    if provider == "claude":
        key = getattr(settings, "anthropic_api_key", "")
        if not key:
            logger.warning("LLM_PROVIDER=claude but ANTHROPIC_API_KEY not set — no LLM")
            return None
        from app.engine.llm.claude_provider import ClaudeProvider
        return ClaudeProvider(key, getattr(settings, "llm_model", "claude-sonnet-4-6"))

    if provider == "openai":
        key = getattr(settings, "openai_api_key", "")
        if not key:
            logger.warning("LLM_PROVIDER=openai but OPENAI_API_KEY not set — no LLM")
            return None
        from app.engine.llm.openai_provider import OpenAIProvider
        return OpenAIProvider(key, getattr(settings, "llm_model", "gpt-4o"))

    if provider == "ollama":
        base_url = getattr(settings, "ollama_base_url", "http://localhost:11434")
        from app.engine.llm.ollama_provider import OllamaProvider
        return OllamaProvider(base_url, getattr(settings, "llm_model", "llama3"))

    if provider == "custom":
        custom_url = getattr(settings, "custom_model_url", "")
        if not custom_url:
            logger.warning("LLM_PROVIDER=custom but CUSTOM_MODEL_URL not set — no LLM")
            return None
        try:
            from app.engine.llm.custom_provider import CustomModelProvider
            return CustomModelProvider(
                custom_url,
                getattr(settings, "custom_model_name", "careergraph-v1"),
            )
        except ImportError:
            logger.warning("CustomModelProvider not found — no LLM")
            return None

    logger.warning(f"Unknown LLM_PROVIDER='{provider}' — no LLM")
    return None
