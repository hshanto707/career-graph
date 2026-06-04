"""OpenAI GPT LLM provider."""
import logging
from app.engine.llm.base import LLMProvider

logger = logging.getLogger(__name__)


class OpenAIProvider(LLMProvider):
    """LLM provider backed by OpenAI's GPT API."""

    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.api_key = api_key
        self.model = model

    async def complete(self, system_prompt: str, user_prompt: str) -> str:
        """Call OpenAI API and return text response."""
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=1024,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.warning(f"OpenAIProvider error: {e}")
            return ""
