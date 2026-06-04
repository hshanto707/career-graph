"""Custom model provider — OpenAI-compatible endpoint (vLLM / HuggingFace TGI)."""
import logging
from app.engine.llm.base import LLMProvider

logger = logging.getLogger(__name__)


class CustomModelProvider(LLMProvider):
    """
    LLM provider for OpenAI-compatible endpoints.

    Works with vLLM, HuggingFace TGI, or any server that speaks the
    /v1/chat/completions API (POST with {model, messages, max_tokens}).
    Degrades gracefully — returns empty string on any failure.
    """

    def __init__(self, base_url: str, model_name: str = "careergraph-v1"):
        self.base_url = base_url.rstrip("/")
        self.model_name = model_name

    async def complete(self, system_prompt: str, user_prompt: str) -> str:
        if not self.base_url:
            return ""
        try:
            import httpx
            payload = {
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "max_tokens": 1024,
            }
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{self.base_url}/v1/chat/completions",
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"] or ""
        except Exception as e:
            logger.warning(f"CustomModelProvider error: {e}")
            return ""
