"""OpenAI LLM provider implementation."""

import hashlib
import json
import logging
import time
from typing import TypeVar, Type

from openai import OpenAI
from pydantic import BaseModel, ValidationError

from .base import LLMProvider
from app.config import get_settings
from app.logging_config import sanitize_api_key, truncate_text

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
        self._api_key = api_key  # Store for logging (will be sanitized)

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
        call_location: str = "unknown",
    ) -> tuple[T, dict]:
        """Generate a response from OpenAI and validate against Pydantic model."""
        start_time = time.time()
        settings = get_settings()
        prompt_hash = self._hash_prompt(system_prompt + user_prompt)

        # DEBUG: Log request details if debug logging enabled
        if settings.ai_debug_logging:
            logger.debug(
                f"AI Request\n"
                f"  Location: {call_location}\n"
                f"  Provider: {self.provider_name} | Model: {self.model} | Temp: {temperature}\n"
                f"  System Prompt: {truncate_text(system_prompt)}\n"
                f"  User Prompt: {truncate_text(user_prompt)}\n"
                f"  API Key: {sanitize_api_key(self._api_key)}"
            )

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

                    duration = time.time() - start_time
                    input_tokens = metadata.get("input_tokens", 0)
                    output_tokens = metadata.get("output_tokens", 0)
                    total_tokens = input_tokens + output_tokens

                    # INFO: Always log success with key metrics
                    logger.info(
                        f"AI Response ✓\n"
                        f"  Location: {call_location}\n"
                        f"  Duration: {duration:.2f}s | Tokens: {input_tokens} in / {output_tokens} out ({total_tokens} total)\n"
                        f"  Response: {truncate_text(str(validated.model_dump()))}"
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
                duration = time.time() - start_time
                logger.error(
                    f"AI Response ✗\n"
                    f"  Location: {call_location}\n"
                    f"  Duration: {duration:.2f}s\n"
                    f"  Error: {str(e)}",
                    exc_info=True
                )
                raise

        raise ValueError("AI generation failed after all retries")

    async def get_embedding(self, text: str) -> list[float]:
        """Get embedding vector for text using OpenAI."""
        response = self.client.embeddings.create(
            model=self.embedding_model,
            input=text,
        )
        return response.data[0].embedding
