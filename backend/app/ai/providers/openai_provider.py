"""OpenAI LLM provider implementation."""

import hashlib
import json
import logging
from typing import TypeVar, Type

from openai import OpenAI
from pydantic import BaseModel, ValidationError

from .base import LLMProvider

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class OpenAIProvider(LLMProvider):
    """OpenAI API provider with JSON validation."""

    def __init__(self, api_key: str, model: str = "gpt-4o", embedding_model: str = "text-embedding-ada-002"):
        """
        Initialize the OpenAI provider.

        Args:
            api_key: OpenAI API key
            model: Model name for chat completions
            embedding_model: Model name for embeddings
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.embedding_model = embedding_model

    @property
    def provider_name(self) -> str:
        return "openai"

    def _hash_prompt(self, prompt: str) -> str:
        """Generate SHA-256 hash of the prompt."""
        return hashlib.sha256(prompt.encode()).hexdigest()[:16]

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: Type[T],
        temperature: float = 0.3,
        max_retries: int = 1,
    ) -> tuple[T, dict]:
        """Generate a response from OpenAI and validate against Pydantic model."""
        prompt_hash = self._hash_prompt(system_prompt + user_prompt)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        for attempt in range(max_retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    response_format={"type": "json_object"},
                )

                content = response.choices[0].message.content
                metadata = {
                    "model_version": response.model,
                    "prompt_hash": prompt_hash,
                    "input_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "output_tokens": response.usage.completion_tokens if response.usage else 0,
                    "provider": self.provider_name,
                }

                # Parse JSON
                try:
                    data = json.loads(content)
                except json.JSONDecodeError as e:
                    logger.warning(f"JSON parse error (attempt {attempt + 1}): {e}")
                    if attempt < max_retries:
                        messages.append({"role": "assistant", "content": content})
                        messages.append({
                            "role": "user",
                            "content": f"Your response was not valid JSON. Error: {e}. Please fix and return valid JSON.",
                        })
                        continue
                    raise ValueError(f"Failed to parse JSON after {max_retries + 1} attempts")

                # Validate against Pydantic model
                try:
                    validated = response_model.model_validate(data)
                    logger.info(
                        f"AI response validated successfully",
                        extra={
                            "model": self.model,
                            "prompt_hash": prompt_hash,
                            "tokens": metadata.get("output_tokens", 0),
                        },
                    )
                    return validated, metadata
                except ValidationError as e:
                    logger.warning(f"Validation error (attempt {attempt + 1}): {e}")
                    if attempt < max_retries:
                        messages.append({"role": "assistant", "content": content})
                        messages.append({
                            "role": "user",
                            "content": f"Your response did not match the expected schema. Error: {e}. Please fix and return a valid response.",
                        })
                        continue
                    raise ValueError(f"Validation failed after {max_retries + 1} attempts: {e}")

            except Exception as e:
                logger.error(f"AI generation error: {e}")
                raise

        raise ValueError("AI generation failed after all retries")

    async def get_embedding(self, text: str) -> list[float]:
        """Get embedding vector for text using OpenAI."""
        response = self.client.embeddings.create(
            model=self.embedding_model,
            input=text,
        )
        return response.data[0].embedding
