"""FastAPI dependencies for the application."""

from typing import Optional

from fastapi import Header, HTTPException

from app.config import get_settings


async def get_llm_api_key(
    x_openai_key: Optional[str] = Header(None, alias="X-OpenAI-Key"),
    x_llm_provider: Optional[str] = Header(None, alias="X-LLM-Provider"),
) -> Optional[str]:
    """
    Extract and validate LLM API key from request header.

    For Ollama (local): No API key required
    For OpenAI (cloud): API key must be provided and start with 'sk-'

    The provider can be specified via:
    1. X-LLM-Provider header ("openai" or "ollama")
    2. Falls back to config.llm_provider setting

    Raises:
        HTTPException: 401 if using OpenAI and key is missing/invalid
    """
    settings = get_settings()

    # Determine provider from header or config
    provider = x_llm_provider or settings.llm_provider

    if provider == "ollama":
        # Ollama doesn't need an API key
        return None

    # OpenAI requires API key
    if not x_openai_key:
        raise HTTPException(
            status_code=401,
            detail="OpenAI API key required. Please provide your key in the X-OpenAI-Key header, or switch to Ollama for local inference."
        )

    if not x_openai_key.startswith("sk-"):
        raise HTTPException(
            status_code=401,
            detail="Invalid OpenAI API key format. Key must start with 'sk-'."
        )

    return x_openai_key


# Backwards compatibility alias
get_openai_api_key = get_llm_api_key
