"""Tests for the LLM provider factory (B-01)."""
import pytest
from unittest.mock import MagicMock


def _settings(**kwargs):
    s = MagicMock()
    s.llm_provider = kwargs.get("llm_provider", "none")
    s.anthropic_api_key = kwargs.get("anthropic_api_key", "")
    s.openai_api_key = kwargs.get("openai_api_key", "")
    s.ollama_base_url = kwargs.get("ollama_base_url", "http://localhost:11434")
    s.llm_model = kwargs.get("llm_model", "claude-sonnet-4-6")
    s.custom_model_url = kwargs.get("custom_model_url", "")
    s.custom_model_name = kwargs.get("custom_model_name", "careergraph-v1")
    return s


def test_factory_none_provider_returns_none():
    from app.engine.llm.factory import create_llm_provider
    assert create_llm_provider(_settings(llm_provider="none")) is None


def test_factory_empty_provider_returns_none():
    from app.engine.llm.factory import create_llm_provider
    assert create_llm_provider(_settings(llm_provider="")) is None


def test_factory_claude_without_key_returns_none():
    from app.engine.llm.factory import create_llm_provider
    assert create_llm_provider(_settings(llm_provider="claude", anthropic_api_key="")) is None


def test_factory_claude_with_key_returns_claude_provider():
    from app.engine.llm.factory import create_llm_provider
    from app.engine.llm.claude_provider import ClaudeProvider
    provider = create_llm_provider(_settings(llm_provider="claude", anthropic_api_key="sk-ant-test"))
    assert isinstance(provider, ClaudeProvider)


def test_factory_openai_without_key_returns_none():
    from app.engine.llm.factory import create_llm_provider
    assert create_llm_provider(_settings(llm_provider="openai", openai_api_key="")) is None


def test_factory_ollama_returns_ollama_provider():
    from app.engine.llm.factory import create_llm_provider
    from app.engine.llm.ollama_provider import OllamaProvider
    provider = create_llm_provider(_settings(llm_provider="ollama"))
    assert isinstance(provider, OllamaProvider)


def test_factory_custom_without_url_returns_none():
    from app.engine.llm.factory import create_llm_provider
    assert create_llm_provider(_settings(llm_provider="custom", custom_model_url="")) is None


def test_factory_custom_with_url_returns_custom_provider():
    from app.engine.llm.factory import create_llm_provider
    from app.engine.llm.custom_provider import CustomModelProvider
    provider = create_llm_provider(_settings(llm_provider="custom", custom_model_url="http://localhost:8080"))
    assert isinstance(provider, CustomModelProvider)


def test_factory_unknown_provider_returns_none():
    from app.engine.llm.factory import create_llm_provider
    assert create_llm_provider(_settings(llm_provider="mystery_llm")) is None
