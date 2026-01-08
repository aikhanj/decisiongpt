"""AI Gateway - Factory for LLM providers with unified interface."""

import logging
from typing import TypeVar, Type, Optional

from pydantic import BaseModel

from app.config import get_settings
from app.ai.providers import LLMProvider, OpenAIProvider, OllamaProvider

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class AIGateway:
    """
    Gateway for LLM API calls with JSON validation.

    Supports multiple providers:
    - OpenAI (BYOK - Bring Your Own Key)
    - Ollama (local, no key required)
    """

    def __init__(self, api_key: Optional[str] = None, provider: Optional[str] = None):
        """
        Initialize the AI gateway with appropriate provider.

        Args:
            api_key: API key (required for OpenAI, ignored for Ollama)
            provider: Override provider from config ("openai" or "ollama")
        """
        settings = get_settings()
        provider_name = provider or settings.llm_provider

        self._provider = self._create_provider(provider_name, api_key, settings)

    def _create_provider(self, provider_name: str, api_key: Optional[str], settings) -> LLMProvider:
        """Factory method to create the appropriate LLM provider."""
        if provider_name == "ollama":
            logger.info(f"Using Ollama provider with model: {settings.ollama_model}")
            return OllamaProvider(
                base_url=settings.ollama_base_url,
                model=settings.ollama_model,
                embedding_model=settings.ollama_embedding_model,
            )
        elif provider_name == "openai":
            if not api_key:
                raise ValueError("OpenAI API key is required when using OpenAI provider")
            logger.info(f"Using OpenAI provider with model: {settings.openai_model}")
            return OpenAIProvider(
                api_key=api_key,
                model=settings.openai_model,
                embedding_model=settings.openai_embedding_model,
            )
        else:
            raise ValueError(f"Unknown LLM provider: {provider_name}")

    @property
    def provider_name(self) -> str:
        """Return the name of the current provider."""
        return self._provider.provider_name

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: Type[T],
        temperature: float = 0.3,
        max_retries: int = 1,
    ) -> tuple[T, dict]:
        """
        Generate a response and validate against Pydantic model.

        Args:
            system_prompt: System prompt for the AI
            user_prompt: User prompt/input
            response_model: Pydantic model to validate response against
            temperature: Sampling temperature (default 0.3 for structured output)
            max_retries: Number of retries on validation failure

        Returns:
            Tuple of (validated response, metadata dict with model_version, prompt_hash, tokens)
        """
        return await self._provider.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_model=response_model,
            temperature=temperature,
            max_retries=max_retries,
        )

    async def get_embedding(self, text: str) -> list[float]:
        """Get embedding vector for text."""
        return await self._provider.get_embedding(text)
