import hashlib
import json
import logging
from typing import TypeVar, Type

from openai import OpenAI
from pydantic import BaseModel, ValidationError

from app.config import get_settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class AIGateway:
    """Gateway for OpenAI API calls with JSON validation (BYOK - Bring Your Own Key)."""

    def __init__(self, api_key: str):
        """
        Initialize the AI gateway with user-provided API key.

        Args:
            api_key: User's OpenAI API key (from X-OpenAI-Key header)
        """
        settings = get_settings()
        self.client = OpenAI(api_key=api_key)
        self.model = settings.openai_model
        self.embedding_model = settings.openai_embedding_model

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
        """
        Generate a response from OpenAI and validate against Pydantic model.

        Args:
            system_prompt: System prompt for the AI
            user_prompt: User prompt/input
            response_model: Pydantic model to validate response against
            temperature: Sampling temperature (default 0.3 for structured output)
            max_retries: Number of retries on validation failure

        Returns:
            Tuple of (validated response, metadata dict with model_version, prompt_hash, tokens)
        """
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
                }

                # Parse JSON
                try:
                    data = json.loads(content)
                except json.JSONDecodeError as e:
                    logger.warning(f"JSON parse error (attempt {attempt + 1}): {e}")
                    if attempt < max_retries:
                        # Ask model to fix the JSON
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
                        # Ask model to fix the response
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
