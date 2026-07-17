"""OllamaProvider — module B6.

Talks HTTP to a local Ollama daemon (`localhost:11434` by default). Ollama
has no native structured-output/tool-use API, so the target JSON schema is
embedded directly in the system prompt and Ollama's `"format": "json"` mode
is used to constrain decoding to valid JSON, per system-design.md §9.4
("JSON schema in system prompt").

Uses `httpx` rather than the `requests` package referenced in the design doc
narrative — `httpx` is already a project dependency (pulled in transitively
by FastAPI/anthropic) and gives us a drop-in sync client without adding a new
dependency, with identical timeout/error semantics.
"""
from __future__ import annotations

import json
from typing import Generator

import httpx
from pydantic import BaseModel

from app.engine.llm.base import (
    LLMProvider,
    LLMProviderError,
    LLMTimeoutError,
    ModelInfo,
)


class OllamaProvider(LLMProvider):
    """Local Ollama-backed `LLMProvider` implementation."""

    def __init__(
        self,
        model: str = "llama3",
        *,
        base_url: str = "http://localhost:11434",
        timeout: int = 30,
        max_tokens: int = 4096,
        client: httpx.Client | None = None,
    ):
        super().__init__(model, timeout=timeout, max_tokens=max_tokens)
        self.base_url = base_url.rstrip("/")
        # `httpx.Client` is safe to construct even with no daemon running --
        # nothing is dialed until a request is actually made -- so, unlike
        # the API-key-backed providers, there is no eager configuration
        # error here. A test can inject a mocked client via `client=`.
        self._client = client or httpx.Client(base_url=self.base_url)

    def _build_prompt(self, system_prompt: str, output_schema: type[BaseModel]) -> str:
        schema_json = json.dumps(output_schema.model_json_schema())
        return (
            f"{system_prompt}\n\n"
            "Respond with ONLY a single JSON object matching this JSON Schema "
            "exactly -- no prose, no markdown fences, no extra keys:\n"
            f"{schema_json}"
        )

    def _generate(
        self,
        system_prompt: str,
        user_prompt: str,
        output_schema: type[BaseModel],
        timeout: int,
    ) -> str:
        payload = {
            "model": self.model,
            "system": self._build_prompt(system_prompt, output_schema),
            "prompt": user_prompt,
            "stream": False,
            "format": "json",
        }
        try:
            response = self._client.post("/api/generate", json=payload, timeout=timeout)
        except httpx.TimeoutException as exc:
            raise LLMTimeoutError(f"Ollama request timed out: {exc}") from exc
        except httpx.HTTPError as exc:
            raise LLMProviderError(f"Ollama request failed: {exc}") from exc

        if response.status_code != 200:
            raise LLMProviderError(
                f"Ollama returned HTTP {response.status_code}: {response.text}"
            )

        try:
            body = response.json()
        except ValueError as exc:
            raise LLMProviderError(f"Ollama returned a non-JSON envelope: {exc}") from exc

        text = body.get("response")
        if not text:
            raise LLMProviderError("Ollama response contained no 'response' field")
        return text

    def stream(self, system_prompt: str, user_prompt: str) -> Generator[str, None, None]:
        payload = {
            "model": self.model,
            "system": system_prompt,
            "prompt": user_prompt,
            "stream": True,
        }
        try:
            with self._client.stream(
                "POST", "/api/generate", json=payload, timeout=self.default_timeout
            ) as response:
                for line in response.iter_lines():
                    if not line:
                        continue
                    chunk = json.loads(line)
                    if chunk.get("response"):
                        yield chunk["response"]
        except httpx.TimeoutException as exc:
            raise LLMTimeoutError(f"Ollama stream timed out: {exc}") from exc
        except httpx.HTTPError as exc:
            raise LLMProviderError(f"Ollama stream failed: {exc}") from exc

    def get_model_info(self) -> ModelInfo:
        return ModelInfo(
            provider="ollama",
            model=self.model,
            supports_streaming=True,
            max_tokens=self.max_tokens,
        )
