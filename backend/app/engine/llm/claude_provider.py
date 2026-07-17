"""ClaudeProvider — module B6.

Uses the `anthropic` SDK's tool-use feature to force structured JSON output:
we hand Anthropic a single synthetic tool whose `input_schema` is the target
Pydantic model's JSON schema, force `tool_choice` to that tool, and read the
model's tool-call arguments back out as JSON. This is the standard "JSON via
tool_use" pattern referenced in system-design.md §9.4.
"""
from __future__ import annotations

import json
from typing import Generator

from pydantic import BaseModel

from app.engine.llm.base import (
    LLMConfigurationError,
    LLMProvider,
    LLMProviderError,
    LLMTimeoutError,
    ModelInfo,
)

_STRUCTURED_TOOL_NAME = "emit_structured_output"


class ClaudeProvider(LLMProvider):
    """Anthropic Claude-backed `LLMProvider` implementation."""

    def __init__(
        self,
        model: str = "claude-sonnet-4-6",
        *,
        api_key: str | None = None,
        timeout: int = 30,
        max_tokens: int = 4096,
        client: object | None = None,
    ):
        super().__init__(model, timeout=timeout, max_tokens=max_tokens)

        if client is not None:
            # Test/DI seam: a pre-built (mocked) SDK client is injected
            # directly so tests never hit the real Anthropic API.
            self._client = client
            return

        if not api_key:
            raise LLMConfigurationError(
                "ClaudeProvider requires ANTHROPIC_API_KEY to be configured"
            )

        import anthropic  # imported lazily so the dependency is optional

        self._client = anthropic.Anthropic(api_key=api_key)

    def _generate(
        self,
        system_prompt: str,
        user_prompt: str,
        output_schema: type[BaseModel],
        timeout: int,
    ) -> str:
        import anthropic

        tool_schema = output_schema.model_json_schema()

        try:
            response = self._client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
                tools=[
                    {
                        "name": _STRUCTURED_TOOL_NAME,
                        "description": "Emit the structured output for this request.",
                        "input_schema": tool_schema,
                    }
                ],
                tool_choice={"type": "tool", "name": _STRUCTURED_TOOL_NAME},
                timeout=timeout,
            )
        except anthropic.APITimeoutError as exc:
            raise LLMTimeoutError(f"Claude request timed out: {exc}") from exc
        except anthropic.AnthropicError as exc:
            raise LLMProviderError(f"Claude request failed: {exc}") from exc

        for block in getattr(response, "content", []):
            if getattr(block, "type", None) == "tool_use":
                return json.dumps(block.input)

        raise LLMProviderError("Claude response contained no tool_use block")

    def stream(self, system_prompt: str, user_prompt: str) -> Generator[str, None, None]:
        import anthropic

        try:
            with self._client.messages.stream(
                model=self.model,
                max_tokens=self.max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            ) as stream:
                for text in stream.text_stream:
                    yield text
        except anthropic.APITimeoutError as exc:
            raise LLMTimeoutError(f"Claude stream timed out: {exc}") from exc
        except anthropic.AnthropicError as exc:
            raise LLMProviderError(f"Claude stream failed: {exc}") from exc

    def get_model_info(self) -> ModelInfo:
        return ModelInfo(
            provider="claude",
            model=self.model,
            supports_streaming=True,
            max_tokens=self.max_tokens,
        )
