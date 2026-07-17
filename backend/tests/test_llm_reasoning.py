"""B6 — LLM Provider Abstraction + Reasoning Agent. Mirrors test-plan.md §B6.

Covers every B6 red/green test + edge case EXCEPT tests #4 and #5
(EngineOrchestrator fallback-to-template-narrative behavior when
`LLM_PROVIDER` is unset, or when the provider raises after exhausting
retries) -- the EngineOrchestrator itself is built in a later phase and will
own those two tests.

No real network calls are made anywhere in this file: the `anthropic` /
`openai` SDK clients and the `httpx` client used by `OllamaProvider` are all
replaced with hand-built fakes/mocks.
"""
from __future__ import annotations

import json
import time
from types import SimpleNamespace

import httpx
import pytest
from pydantic import BaseModel, Field, ValidationError

from app.engine.llm.base import (
    LLMConfigurationError,
    LLMOutputValidationError,
    LLMProvider,
    LLMProviderError,
    LLMTimeoutError,
    ModelInfo,
)
from app.engine.llm.claude_provider import ClaudeProvider
from app.engine.llm.factory import create_llm_provider
from app.engine.llm.ollama_provider import OllamaProvider
from app.engine.llm.openai_provider import OpenAIProvider
from app.engine.reasoning.reasoning_agent import (
    GapExplanation,
    MarketSummary,
    Milestone,
    MissingSkillExplanation,
    ReasoningAgent,
    RecommendationNarratives,
    RoadmapPlan,
)


# --------------------------------------------------------------------------- #
# Shared test fixtures / helpers
# --------------------------------------------------------------------------- #


class _EchoSchema(BaseModel):
    """A minimal, generic output schema used to test the base retry/timeout
    machinery independent of any particular provider's wire format."""

    message: str
    count: int = Field(ge=0)


class _ScriptedProvider(LLMProvider):
    """A bare-bones `LLMProvider` whose `_generate()` plays back a scripted
    sequence of behaviors, one per call -- lets us test `complete()`'s
    shared retry/timeout/validation logic without any real SDK involved."""

    def __init__(self, script: list):
        super().__init__(model="scripted-model")
        self._script = list(script)
        self.calls = 0

    def _generate(self, system_prompt, user_prompt, output_schema, timeout):
        self.calls += 1
        step = self._script[self.calls - 1]
        if isinstance(step, Exception):
            raise step
        return step

    def stream(self, system_prompt, user_prompt):  # pragma: no cover - unused here
        yield ""

    def get_model_info(self) -> ModelInfo:
        return ModelInfo(provider="scripted", model=self.model)


# --------------------------------------------------------------------------- #
# 1. LLMProvider.complete() contract -- schema-valid parse, per provider
# --------------------------------------------------------------------------- #


def test_claude_provider_returns_validated_model_on_valid_tool_use():
    fake_block = SimpleNamespace(type="tool_use", input={"message": "hi", "count": 3})
    fake_response = SimpleNamespace(content=[fake_block])
    fake_client = SimpleNamespace(
        messages=SimpleNamespace(create=lambda **kwargs: fake_response)
    )

    provider = ClaudeProvider(client=fake_client)
    result = provider.complete("system", "user", _EchoSchema)

    assert isinstance(result, _EchoSchema)
    assert result.message == "hi"
    assert result.count == 3


def test_openai_provider_returns_validated_model_on_valid_json_content():
    fake_message = SimpleNamespace(content=json.dumps({"message": "hi", "count": 5}))
    fake_choice = SimpleNamespace(message=fake_message)
    fake_response = SimpleNamespace(choices=[fake_choice])
    fake_client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **kwargs: fake_response))
    )

    provider = OpenAIProvider(client=fake_client)
    result = provider.complete("system", "user", _EchoSchema)

    assert isinstance(result, _EchoSchema)
    assert result.message == "hi"
    assert result.count == 5


def test_ollama_provider_returns_validated_model_on_valid_json_response():
    def fake_post(path, json=None, timeout=None):
        return httpx.Response(200, json={"response": '{"message": "hi", "count": 7}'})

    fake_client = SimpleNamespace(post=fake_post)
    provider = OllamaProvider(client=fake_client)
    result = provider.complete("system", "user", _EchoSchema)

    assert isinstance(result, _EchoSchema)
    assert result.message == "hi"
    assert result.count == 7


# --------------------------------------------------------------------------- #
# 2. Malformed LLM JSON response -- retry then raise a specific exception
# --------------------------------------------------------------------------- #


def test_malformed_json_retries_then_raises_output_validation_error():
    provider = _ScriptedProvider(["not json {{{", "still not json", "nope"])

    with pytest.raises(LLMOutputValidationError) as exc_info:
        provider.complete("system", "user", _EchoSchema, retries=2)

    # retries=2 => 3 total attempts, one per scripted response.
    assert provider.calls == 3
    assert exc_info.value.attempts == 3
    assert exc_info.value.raw_output == "nope"


def test_provider_recovers_if_a_later_retry_succeeds():
    provider = _ScriptedProvider(
        ["not json", json.dumps({"message": "ok", "count": 1})]
    )

    result = provider.complete("system", "user", _EchoSchema, retries=2)

    assert provider.calls == 2
    assert result == _EchoSchema(message="ok", count=1)


def test_retries_zero_means_a_single_attempt():
    provider = _ScriptedProvider(["not json"])

    with pytest.raises(LLMOutputValidationError):
        provider.complete("system", "user", _EchoSchema, retries=0)

    assert provider.calls == 1


# --------------------------------------------------------------------------- #
# 3. ReasoningAgent passes structured data through faithfully
# --------------------------------------------------------------------------- #


class _StubLLMProvider(LLMProvider):
    """Returns a fixed, pre-validated response and records exactly what
    prompts/schema it was called with, so we can assert the ReasoningAgent
    forwards structured input in and structured output out unmodified."""

    def __init__(self, fixed_response: BaseModel):
        super().__init__(model="stub-model")
        self._fixed_response = fixed_response
        self.last_call = None

    def complete(self, system_prompt, user_prompt, output_schema, timeout=30, retries=2):
        self.last_call = {
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "output_schema": output_schema,
            "timeout": timeout,
            "retries": retries,
        }
        assert output_schema is type(self._fixed_response)
        return self._fixed_response

    def _generate(self, *a, **kw):  # pragma: no cover - complete() overridden above
        raise NotImplementedError

    def stream(self, system_prompt, user_prompt):  # pragma: no cover - unused
        yield ""

    def get_model_info(self) -> ModelInfo:
        return ModelInfo(provider="stub", model=self.model)


def test_explain_gap_returns_llm_response_unmodified():
    fixed = GapExplanation(
        explanation="You're close on backend skills but missing cloud experience.",
        encouragement="You've already got the hardest parts down.",
        missing_skills=[
            MissingSkillExplanation(skill_name="AWS", importance="must", estimated_learning_weeks=4)
        ],
    )
    provider = _StubLLMProvider(fixed)
    agent = ReasoningAgent(provider)

    gap_result = {
        "readiness_score": 62,
        "matched_skills": ["Python", "SQL"],
        "missing_skills": ["AWS"],
    }
    result = agent.explain_gap(gap_result)

    assert result is fixed
    assert provider.last_call["output_schema"] is GapExplanation
    assert "AWS" in provider.last_call["user_prompt"]
    assert "62" in provider.last_call["user_prompt"]


def test_narrate_recommendations_returns_llm_response_unmodified():
    fixed = RecommendationNarratives(narratives=[])
    provider = _StubLLMProvider(fixed)
    agent = ReasoningAgent(provider)

    ranked_jobs = [{"job_id": "job-1", "final_score": 0.83}]
    result = agent.narrate_recommendations(ranked_jobs)

    assert result is fixed
    assert provider.last_call["output_schema"] is RecommendationNarratives
    assert "job-1" in provider.last_call["user_prompt"]


def test_write_roadmap_returns_llm_response_unmodified():
    fixed = RoadmapPlan(
        weekly_milestones=[
            Milestone(week_range="1-2", skill_name="Python", goal="Finish basics")
        ]
    )
    provider = _StubLLMProvider(fixed)
    agent = ReasoningAgent(provider)

    result = agent.write_roadmap({"ordered_skills": ["Python"]})

    assert result is fixed
    assert provider.last_call["output_schema"] is RoadmapPlan


def test_summarize_market_returns_llm_response_unmodified():
    fixed = MarketSummary(
        trend_bullets=["a", "b", "c"], market_summary="Solid growth.", highlight_skills=["Python"]
    )
    provider = _StubLLMProvider(fixed)
    agent = ReasoningAgent(provider)

    result = agent.summarize_market({"skill_demand": [{"name": "Python", "demand_score": 90}]})

    assert result is fixed
    assert provider.last_call["output_schema"] is MarketSummary


# --------------------------------------------------------------------------- #
# 4/5. Orchestrator fallback tests -- NOT this phase.
# --------------------------------------------------------------------------- #
# TODO(orchestrator-phase): test-plan.md B6 #4 ("Orchestrator with
# LLM_PROVIDER unset returns algorithmic result + template narratives") and
# #5 ("Orchestrator with LLM_PROVIDER set but the provider raises after
# exhausting retries falls back to the same template path, still 200") both
# depend on `EngineOrchestrator`, which is not implemented until a later
# phase. Add them to a dedicated `test_orchestrator.py` alongside that work.


# --------------------------------------------------------------------------- #
# 6. Provider switch via env var -- factory/construction test
# --------------------------------------------------------------------------- #


def test_factory_routes_claude_to_claude_provider():
    provider = create_llm_provider("claude", api_key="fake-key")
    assert isinstance(provider, ClaudeProvider)
    assert provider.get_model_info().provider == "claude"


def test_factory_routes_openai_to_openai_provider():
    provider = create_llm_provider("openai", api_key="fake-key")
    assert isinstance(provider, OpenAIProvider)
    assert provider.get_model_info().provider == "openai"


def test_factory_routes_ollama_to_ollama_provider_no_api_key_required():
    provider = create_llm_provider("ollama")
    assert isinstance(provider, OllamaProvider)
    assert provider.get_model_info().provider == "ollama"


def test_factory_is_case_insensitive_and_switches_via_env_style_string():
    for name, expected in [("Claude", ClaudeProvider), ("OPENAI", OpenAIProvider), ("ollama", OllamaProvider)]:
        kwargs = {} if expected is OllamaProvider else {"api_key": "fake-key"}
        provider = create_llm_provider(name, **kwargs)
        assert isinstance(provider, expected)


def test_factory_rejects_none_or_unknown_provider():
    with pytest.raises(LLMConfigurationError):
        create_llm_provider("none")
    with pytest.raises(LLMConfigurationError):
        create_llm_provider("")
    with pytest.raises(LLMConfigurationError):
        create_llm_provider("not-a-real-provider")


def test_claude_and_openai_providers_require_api_key_when_no_client_injected():
    with pytest.raises(LLMConfigurationError):
        ClaudeProvider(api_key=None)
    with pytest.raises(LLMConfigurationError):
        OpenAIProvider(api_key=None)


# --------------------------------------------------------------------------- #
# Timeout handling
# --------------------------------------------------------------------------- #


def test_timeout_mid_request_retries_then_raises_llm_timeout_error():
    provider = _ScriptedProvider(
        [LLMTimeoutError("slow"), LLMTimeoutError("slow"), LLMTimeoutError("slow")]
    )

    with pytest.raises(LLMTimeoutError):
        provider.complete("system", "user", _EchoSchema, retries=2)

    assert provider.calls == 3


def test_timeout_does_not_hang_and_returns_promptly(monkeypatch):
    """A mocked 'slow' call must fail fast into the timeout path rather than
    actually blocking for real wall-clock time."""

    class _SlowThenTimeout(LLMProvider):
        def __init__(self):
            super().__init__(model="slow-model")
            self.calls = 0

        def _generate(self, system_prompt, user_prompt, output_schema, timeout):
            self.calls += 1
            raise LLMTimeoutError(f"exceeded {timeout}s")

        def stream(self, system_prompt, user_prompt):
            yield ""

        def get_model_info(self) -> ModelInfo:
            return ModelInfo(provider="slow", model=self.model)

    provider = _SlowThenTimeout()
    start = time.monotonic()
    with pytest.raises(LLMTimeoutError):
        provider.complete("system", "user", _EchoSchema, timeout=1, retries=1)
    elapsed = time.monotonic() - start

    assert provider.calls == 2
    assert elapsed < 1.0  # no real sleeping/blocking happened


def test_ollama_provider_raises_llm_timeout_error_on_httpx_timeout():
    def fake_post(path, json=None, timeout=None):
        raise httpx.TimeoutException("timed out")

    fake_client = SimpleNamespace(post=fake_post)
    provider = OllamaProvider(client=fake_client)

    with pytest.raises(LLMTimeoutError):
        provider.complete("system", "user", _EchoSchema, retries=0)


def test_claude_provider_raises_llm_timeout_error_on_sdk_timeout():
    import anthropic

    def raise_timeout(**kwargs):
        raise anthropic.APITimeoutError(request=httpx.Request("POST", "https://api.anthropic.com"))

    fake_client = SimpleNamespace(messages=SimpleNamespace(create=raise_timeout))
    provider = ClaudeProvider(client=fake_client)

    with pytest.raises(LLMTimeoutError):
        provider.complete("system", "user", _EchoSchema, retries=0)


def test_openai_provider_raises_llm_timeout_error_on_sdk_timeout():
    import openai

    def raise_timeout(**kwargs):
        raise openai.APITimeoutError(request=httpx.Request("POST", "https://api.openai.com"))

    fake_client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=raise_timeout))
    )
    provider = OpenAIProvider(client=fake_client)

    with pytest.raises(LLMTimeoutError):
        provider.complete("system", "user", _EchoSchema, retries=0)


# --------------------------------------------------------------------------- #
# Semantically-invalid fields -- Pydantic field validators reject them
# --------------------------------------------------------------------------- #


def test_negative_estimated_learning_weeks_rejected_by_field_validator():
    with pytest.raises(ValidationError):
        MissingSkillExplanation(skill_name="AWS", importance="must", estimated_learning_weeks=-3)


def test_negative_estimated_learning_weeks_from_llm_causes_output_validation_error():
    # Schema-shaped JSON (all expected keys present) but semantically invalid
    # (negative weeks) must still be rejected -- retried, then raised as the
    # same LLMOutputValidationError as malformed JSON, never silently accepted.
    bad_payload = json.dumps(
        {
            "explanation": "You're close.",
            "encouragement": "Keep going.",
            "missing_skills": [
                {"skill_name": "AWS", "importance": "must", "estimated_learning_weeks": -1}
            ],
        }
    )
    provider = _ScriptedProvider([bad_payload, bad_payload])

    with pytest.raises(LLMOutputValidationError) as exc_info:
        provider.complete("system", "user", GapExplanation, retries=1)

    assert provider.calls == 2
    assert exc_info.value.attempts == 2


def test_negative_count_in_echo_schema_rejected():
    provider = _ScriptedProvider([json.dumps({"message": "hi", "count": -5})])

    with pytest.raises(LLMOutputValidationError):
        provider.complete("system", "user", _EchoSchema, retries=0)


# --------------------------------------------------------------------------- #
# Concurrent / no-shared-state sanity check
# --------------------------------------------------------------------------- #


def test_independent_provider_instances_do_not_share_call_state():
    provider_a = _ScriptedProvider([json.dumps({"message": "a", "count": 1})])
    provider_b = _ScriptedProvider([json.dumps({"message": "b", "count": 2})])

    result_a = provider_a.complete("s", "u", _EchoSchema)
    result_b = provider_b.complete("s", "u", _EchoSchema)

    assert result_a.message == "a"
    assert result_b.message == "b"
    assert provider_a.calls == 1
    assert provider_b.calls == 1
