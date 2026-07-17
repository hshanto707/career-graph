"""Provider factory — routes `LLM_PROVIDER` (env-configured) to the correct
concrete `LLMProvider` subclass with zero call-site branching.

Per system-design.md §9.4: "Provider selection purely via `.env`
(`LLM_PROVIDER=claude|openai|ollama`), swappable without code changes."
"""
from __future__ import annotations

from app.engine.llm.base import LLMConfigurationError, LLMProvider

_PROVIDER_NAMES = ("claude", "openai", "ollama")


def create_llm_provider(
    provider: str,
    *,
    model: str | None = None,
    api_key: str | None = None,
    base_url: str = "http://localhost:11434",
    timeout: int = 30,
    max_tokens: int = 4096,
) -> LLMProvider:
    """Construct the `LLMProvider` implementation named by `provider`.

    `provider` is expected to be the raw `LLM_PROVIDER` env value
    (`"claude"`, `"openai"`, or `"ollama"`, case-insensitive). Raises
    `LLMConfigurationError` for `"none"`/empty/unrecognized values so callers
    (the EngineOrchestrator, in a later phase) can treat "no provider
    configured" and "misconfigured provider" the same way: skip the LLM call
    and fall back to template narratives.
    """
    normalized = (provider or "").strip().lower()

    if normalized == "claude":
        from app.engine.llm.claude_provider import ClaudeProvider

        return ClaudeProvider(model=model or "claude-sonnet-4-6", api_key=api_key, timeout=timeout, max_tokens=max_tokens)

    if normalized == "openai":
        from app.engine.llm.openai_provider import OpenAIProvider

        return OpenAIProvider(model=model or "gpt-4o", api_key=api_key, timeout=timeout, max_tokens=max_tokens)

    if normalized == "ollama":
        from app.engine.llm.ollama_provider import OllamaProvider

        return OllamaProvider(model=model or "llama3", base_url=base_url, timeout=timeout, max_tokens=max_tokens)

    raise LLMConfigurationError(
        f"Unknown or unconfigured LLM_PROVIDER {provider!r} "
        f"(expected one of {_PROVIDER_NAMES}, or 'none' to disable the LLM)"
    )
