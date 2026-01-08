"""FastAPI dependencies for the application."""

from typing import Optional

from fastapi import Header, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import get_settings
from app.database import get_db


async def get_llm_api_key(
    db: AsyncSession = Depends(get_db),
    x_openai_key: Optional[str] = Header(None, alias="X-OpenAI-Key"),
    x_llm_provider: Optional[str] = Header(None, alias="X-LLM-Provider"),
) -> Optional[str]:
    """
    Extract and validate LLM API key.

    For Ollama (local): No API key required
    For OpenAI (cloud): API key from header or saved settings

    Priority:
    1. X-OpenAI-Key header (per-request override)
    2. Saved settings in database
    3. Environment config fallback

    Raises:
        HTTPException: 401 if using OpenAI and key is missing/invalid
    """
    config = get_settings()

    # Try to get saved settings from DB
    from app.models.app_settings import AppSettings
    result = await db.execute(select(AppSettings).limit(1))
    app_settings = result.scalar_one_or_none()

    # Determine provider (header > saved settings > config)
    if x_llm_provider:
        provider = x_llm_provider
    elif app_settings and app_settings.setup_completed:
        provider = app_settings.llm_provider
    else:
        provider = config.llm_provider

    if provider == "ollama":
        # Ollama doesn't need an API key
        return None

    # OpenAI requires API key - check header first, then saved settings
    api_key = x_openai_key

    if not api_key and app_settings and app_settings.openai_api_key:
        api_key = app_settings.openai_api_key

    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="OpenAI API key required. Please configure it in Settings, or switch to Ollama for local inference."
        )

    if not api_key.startswith("sk-"):
        raise HTTPException(
            status_code=401,
            detail="Invalid OpenAI API key format. Key must start with 'sk-'."
        )

    return api_key


# Backwards compatibility alias
get_openai_api_key = get_llm_api_key
