"""Anthropic Claude LLM provider."""
import logging
from app.engine.llm.base import LLMProvider

logger = logging.getLogger(__name__)


class ClaudeProvider(LLMProvider):
    """
    LLM provider backed by Anthropic's Claude API.

    Uses the synchronous Anthropic SDK called from an async context.
    Model: claude-sonnet-4-6 (configurable).
    """

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-6"):
        self.api_key = api_key
        self.model = model

    async def complete(self, system_prompt: str, user_prompt: str) -> str:
        """Call Claude API and return text response."""
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.api_key)
            message = client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            return message.content[0].text if message.content else ""
        except Exception as e:
            logger.warning(f"ClaudeProvider error: {e}")
            return ""
