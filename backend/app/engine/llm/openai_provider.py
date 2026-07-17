"""OpenAIProvider — module B6.

Uses the `openai` SDK's structured-outputs feature (`response_format={"type":
"json_schema", ...}`) to force the model to emit JSON that already matches
the target Pydantic model's shape, per system-design.md §9.4 ("JSON via
response_format").
"""
from __future__ import annotations

from typing import Generator

from pydantic import BaseModel

from app.engine.llm.base import (
    LLMConfigurationError,
    LLMProvider,
    LLMProviderError,
    LLMTimeoutError,
    ModelInfo,
)


class OpenAIProvider(LLMProvider):
    """OpenAI GPT-backed `LLMProvider` implementation."""

    def __init__(
        self,
        model: str = "gpt-4o",
        *,
        api_key: str | None = None,
        timeout: int = 30,
        max_tokens: int = 4096,
        client: object | None = None,
    ):
        super().__init__(model, timeout=timeout, max_tokens=max_tokens)

        if client is not None:
            self._client = client
            return

        if not api_key:
            raise LLMConfigurationError(
                "OpenAIProvider requires OPENAI_API_KEY to be configured"
            )

        import openai  # imported lazily so the dependency is optional

        self._client = openai.OpenAI(api_key=api_key)

    def _generate(
        self,
        system_prompt: str,
        user_prompt: str,
        output_schema: type[BaseModel],
        timeout: int,
    ) -> str:
        import openai

        json_schema = output_schema.model_json_schema()
        json_schema["additionalProperties"] = False

        try:
            response = self._client.chat.completions.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": output_schema.__name__,
                        "schema": json_schema,
                        "strict": True,
                    },
                },
                timeout=timeout,
            )
        except openai.APITimeoutError as exc:
            raise LLMTimeoutError(f"OpenAI request timed out: {exc}") from exc
        except openai.OpenAIError as exc:
            raise LLMProviderError(f"OpenAI request failed: {exc}") from exc

        choices = getattr(response, "choices", None) or []
        if not choices or not getattr(choices[0].message, "content", None):
            raise LLMProviderError("OpenAI response contained no message content")

        return choices[0].message.content

    def stream(self, system_prompt: str, user_prompt: str) -> Generator[str, None, None]:
        import openai

        try:
            stream = self._client.chat.completions.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                stream=True,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta
                if getattr(delta, "content", None):
                    yield delta.content
        except openai.APITimeoutError as exc:
            raise LLMTimeoutError(f"OpenAI stream timed out: {exc}") from exc
        except openai.OpenAIError as exc:
            raise LLMProviderError(f"OpenAI stream failed: {exc}") from exc

    def get_model_info(self) -> ModelInfo:
        return ModelInfo(
            provider="openai",
            model=self.model,
            supports_streaming=True,
            max_tokens=self.max_tokens,
        )
