"""Tests for LLM provider abstraction — WRITTEN BEFORE IMPLEMENTATION (TDD)."""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from app.engine.llm.base import LLMProvider
from app.engine.llm.claude_provider import ClaudeProvider
from app.engine.llm.openai_provider import OpenAIProvider
from app.engine.llm.ollama_provider import OllamaProvider


def test_llm_provider_is_abstract():
    """LLMProvider cannot be instantiated directly (abstract base class)."""
    with pytest.raises(TypeError):
        LLMProvider()


def test_claude_provider_implements_interface():
    """ClaudeProvider implements the complete() method."""
    provider = ClaudeProvider(api_key="test-key")
    assert hasattr(provider, "complete")
    assert callable(provider.complete)


def test_openai_provider_implements_interface():
    """OpenAIProvider implements the complete() method."""
    provider = OpenAIProvider(api_key="test-key")
    assert hasattr(provider, "complete")
    assert callable(provider.complete)


def test_ollama_provider_implements_interface():
    """OllamaProvider implements the complete() method."""
    provider = OllamaProvider(base_url="http://localhost:11434")
    assert hasattr(provider, "complete")
    assert callable(provider.complete)


@pytest.mark.asyncio
async def test_claude_provider_returns_string():
    """ClaudeProvider.complete returns a non-empty string."""
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text='{"explanation": "test"}')]

    with patch("anthropic.Anthropic") as MockAnthropic:
        MockAnthropic.return_value.messages.create.return_value = mock_response
        provider = ClaudeProvider(api_key="test-key")
        result = await provider.complete("system prompt", "user prompt")
        assert isinstance(result, str)
        assert len(result) > 0


@pytest.mark.asyncio
async def test_ollama_provider_handles_connection_error():
    """OllamaProvider returns empty string on connection error (graceful degradation)."""
    with patch("requests.post", side_effect=ConnectionError("refused")):
        provider = OllamaProvider(base_url="http://localhost:11434")
        result = await provider.complete("system", "user")
        assert result == ""
