"""Abstract base class for LLM providers."""

from abc import ABC, abstractmethod
from typing import TypeVar, Type

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMProvider(ABC):
    """Abstract base class for LLM providers (OpenAI, Ollama, etc.)."""

    @abstractmethod
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: Type[T],
        temperature: float = 0.3,
        max_retries: int = 1,
        call_location: str = "unknown",
    ) -> tuple[T, dict]:
        """
        Generate a response and validate against a Pydantic model.

        Args:
            system_prompt: System prompt for the AI
            user_prompt: User prompt/input
            response_model: Pydantic model to validate response against
            temperature: Sampling temperature
            max_retries: Number of retries on validation failure
            call_location: Location in code where this call originated (for logging)

        Returns:
            Tuple of (validated response, metadata dict)
        """
        pass

    @abstractmethod
    async def get_embedding(self, text: str) -> list[float]:
        """
        Get embedding vector for text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector as list of floats
        """
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the name of the provider (e.g., 'openai', 'ollama')."""
        pass
