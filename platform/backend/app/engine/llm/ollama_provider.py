"""Ollama local LLM provider."""
import logging
from app.engine.llm.base import LLMProvider

logger = logging.getLogger(__name__)


class OllamaProvider(LLMProvider):
    """LLM provider backed by a local Ollama server."""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3"):
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def complete(self, system_prompt: str, user_prompt: str) -> str:
        """POST to Ollama /api/generate and return text response."""
        try:
            import requests
            payload = {
                "model": self.model,
                "prompt": f"{system_prompt}\n\n{user_prompt}",
                "stream": False,
            }
            resp = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=30)
            resp.raise_for_status()
            return resp.json().get("response", "")
        except Exception as e:
            logger.warning(f"OllamaProvider error: {e}")
            return ""
