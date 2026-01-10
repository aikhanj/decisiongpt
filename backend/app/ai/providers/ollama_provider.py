"""Ollama LLM provider implementation using OpenAI-compatible API."""

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


class OllamaProvider(LLMProvider):
    """
    Ollama provider using the OpenAI-compatible API.

    Ollama exposes an OpenAI-compatible endpoint at /v1, allowing us to
    reuse the OpenAI SDK with a different base URL.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434/v1",
        model: str = "llama3.2",
        embedding_model: str = "nomic-embed-text",
    ):
        """
        Initialize the Ollama provider.

        Args:
            base_url: Ollama API base URL (default: http://localhost:11434/v1)
            model: Model name for chat completions
            embedding_model: Model name for embeddings
        """
        # Ollama doesn't need an API key, but OpenAI SDK requires one
        self.client = OpenAI(
            base_url=base_url,
            api_key="ollama",  # Dummy key - Ollama ignores this
        )
        self.model = model
        self.embedding_model = embedding_model
        self.base_url = base_url
        self._api_key = "ollama"  # Store for logging

    @property
    def provider_name(self) -> str:
        return "ollama"

    def _hash_prompt(self, prompt: str) -> str:
        """Generate SHA-256 hash of the prompt."""
        return hashlib.sha256(prompt.encode()).hexdigest()[:16]

    def _build_json_prompt(self, system_prompt: str) -> str:
        """
        Enhance the system prompt to request JSON output.

        Ollama models respond better when explicitly asked for JSON in the prompt.
        """
        json_instruction = (
            "\n\nIMPORTANT: You must respond with valid JSON only. "
            "Do not include any text before or after the JSON object. "
            "Do not use markdown code blocks. Just output the raw JSON."
        )
        return system_prompt + json_instruction

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: Type[T],
        temperature: float = 0.3,
        max_retries: int = 1,
        call_location: str = "unknown",
    ) -> tuple[T, dict]:
        """Generate a response from Ollama and validate against Pydantic model."""
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

        # Enhance system prompt for JSON output
        enhanced_system_prompt = self._build_json_prompt(system_prompt)

        messages = [
            {"role": "system", "content": enhanced_system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        for attempt in range(max_retries + 1):
            try:
                # Try with JSON format if supported by the model
                try:
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        temperature=temperature,
                        response_format={"type": "json_object"},
                    )
                except Exception:
                    # Fall back to regular completion if JSON format not supported
                    logger.info(f"JSON format not supported for {self.model}, using regular completion")
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        temperature=temperature,
                    )

                content = response.choices[0].message.content

                # Clean up response - remove markdown code blocks if present
                content = self._clean_json_response(content)

                metadata = {
                    "model_version": self.model,
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
                            "content": (
                                f"Your response was not valid JSON. Error: {e}. "
                                "Please fix and return ONLY valid JSON, no other text."
                            ),
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
                            "content": (
                                f"Your response did not match the expected schema. Error: {e}. "
                                "Please fix and return a valid JSON response."
                            ),
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

    def _clean_json_response(self, content: str) -> str:
        """Remove markdown code blocks and extra whitespace from response."""
        content = content.strip()

        # Remove markdown code blocks
        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]

        if content.endswith("```"):
            content = content[:-3]

        return content.strip()

    async def get_embedding(self, text: str) -> list[float]:
        """Get embedding vector for text using Ollama."""
        try:
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=text,
            )
            return response.data[0].embedding
        except Exception as e:
            logger.warning(f"Ollama embedding failed: {e}. Returning empty vector.")
            # Return empty embedding if Ollama doesn't support the embedding model
            # This allows the app to work without embeddings
            return []
