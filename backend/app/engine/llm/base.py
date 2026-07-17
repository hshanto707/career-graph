"""LLMProvider ABC — module B6 (Pluggable LLM Provider Abstraction).

Per system-design.md §9.4, every concrete provider (Claude, OpenAI, Ollama)
implements the same `complete()` contract and returns a **validated Pydantic
model** — never raw text/dict. `ReasoningAgent` (and anything downstream of
it) never touches unvalidated LLM output.

This module owns the shared retry/timeout/validation machinery so each
concrete provider only has to implement the single SDK call that produces a
raw JSON string.
"""
from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Generator

from pydantic import BaseModel, ValidationError


# --------------------------------------------------------------------------- #
# Exceptions
# --------------------------------------------------------------------------- #
class LLMProviderError(Exception):
    """Base class for all LLM-provider-layer errors.

    The EngineOrchestrator (module B6, later phase) catches this family and
    falls back to template narratives rather than ever surfacing a raw
    provider/network error (or a 500) to the frontend.
    """


class LLMConfigurationError(LLMProviderError):
    """Raised when a provider cannot be constructed (e.g. missing API key)."""


class LLMTimeoutError(LLMProviderError):
    """Raised when every retry attempt timed out."""


class LLMOutputValidationError(LLMProviderError):
    """Raised when the model never produced schema-valid JSON within the
    configured number of retries (malformed JSON, or JSON that fails Pydantic
    field validation, e.g. a negative `estimated_learning_weeks`)."""

    def __init__(self, message: str, *, attempts: int, raw_output: str | None = None):
        super().__init__(message)
        self.attempts = attempts
        self.raw_output = raw_output


# --------------------------------------------------------------------------- #
# Shared value objects
# --------------------------------------------------------------------------- #
class ModelInfo(BaseModel):
    """Metadata describing the concrete model/provider in use."""

    provider: str
    model: str
    supports_streaming: bool = True
    max_tokens: int = 4096


# --------------------------------------------------------------------------- #
# LLMProvider ABC
# --------------------------------------------------------------------------- #
class LLMProvider(ABC):
    """Pluggable LLM provider contract.

    Concrete subclasses (ClaudeProvider, OpenAIProvider, OllamaProvider) only
    need to implement `_generate()` — the single call into the underlying SDK
    that returns a raw JSON string — plus `stream()` and `get_model_info()`.
    `complete()` itself is implemented once here so retry/timeout/validation
    behavior is identical (and identically tested) across every provider.
    """

    def __init__(self, model: str, *, timeout: int = 30, max_tokens: int = 4096):
        self.model = model
        self.default_timeout = timeout
        self.max_tokens = max_tokens

    # ------------------------------------------------------------------ #
    # Public contract
    # ------------------------------------------------------------------ #
    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        output_schema: type[BaseModel],
        timeout: int = 30,
        retries: int = 2,
    ) -> BaseModel:
        """Call the model and return a validated instance of `output_schema`.

        Retries up to `retries` additional times (so `retries + 1` total
        attempts) on any of: a provider/network error, a timeout, malformed
        JSON, or JSON that is schema-shaped but fails Pydantic field
        validation. If every attempt fails, raises `LLMTimeoutError` (if the
        last failure was a timeout) or `LLMOutputValidationError` (for every
        other failure mode) — never a generic/unhandled exception, and the
        raw LLM text never escapes this method.
        """
        total_attempts = max(1, retries + 1)
        last_error: Exception | None = None
        last_raw: str | None = None
        timed_out = False

        for _ in range(total_attempts):
            try:
                raw = self._generate(system_prompt, user_prompt, output_schema, timeout)
            except LLMTimeoutError as exc:
                last_error = exc
                timed_out = True
                continue
            except LLMProviderError as exc:
                last_error = exc
                timed_out = False
                continue

            last_raw = raw
            timed_out = False
            try:
                data = json.loads(raw)
            except (json.JSONDecodeError, TypeError) as exc:
                last_error = exc
                continue

            try:
                return output_schema.model_validate(data)
            except ValidationError as exc:
                last_error = exc
                continue

        if timed_out:
            raise LLMTimeoutError(
                f"{self.__class__.__name__} timed out after {total_attempts} attempt(s)"
            ) from last_error

        raise LLMOutputValidationError(
            f"{self.__class__.__name__} failed to produce schema-valid output "
            f"after {total_attempts} attempt(s): {last_error}",
            attempts=total_attempts,
            raw_output=last_raw,
        ) from last_error

    # ------------------------------------------------------------------ #
    # Subclass hooks
    # ------------------------------------------------------------------ #
    @abstractmethod
    def _generate(
        self,
        system_prompt: str,
        user_prompt: str,
        output_schema: type[BaseModel],
        timeout: int,
    ) -> str:
        """Make one call to the underlying SDK/HTTP endpoint and return the
        raw JSON text it produced. Must raise `LLMTimeoutError` on a timeout
        and `LLMProviderError` (or a subclass) on any other provider failure.
        Must never raise a raw SDK exception past this boundary."""

    @abstractmethod
    def stream(self, system_prompt: str, user_prompt: str) -> Generator[str, None, None]:
        """Yield incremental text chunks from the model. Used for endpoints
        that want to stream a narrative rather than wait for the full
        response (not schema-validated — callers that need a validated
        model must use `complete()` instead)."""

    @abstractmethod
    def get_model_info(self) -> ModelInfo:
        """Return metadata about the concrete model/provider in use."""

    def __repr__(self) -> str:  # pragma: no cover - cosmetic
        return f"{self.__class__.__name__}(model={self.model!r})"
