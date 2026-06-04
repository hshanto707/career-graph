"""Abstract base class for all LLM providers."""
from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """
    Abstract LLM provider interface.

    All concrete providers (Claude, OpenAI, Ollama) must implement
    the complete() method with the same signature. This allows the
    ReasoningAgent to swap providers without changing its logic.
    """

    @abstractmethod
    async def complete(self, system_prompt: str, user_prompt: str) -> str:
        """
        Send a completion request to the LLM.

        Args:
            system_prompt: Instructions for the model.
            user_prompt: The user's input to process.

        Returns:
            The model's text response as a string.
            Returns empty string on failure (graceful degradation).
        """
