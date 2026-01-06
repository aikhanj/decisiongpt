"""FastAPI dependencies for the application."""

from fastapi import Header, HTTPException


async def get_openai_api_key(
    x_openai_key: str = Header(..., alias="X-OpenAI-Key")
) -> str:
    """
    Extract and validate OpenAI API key from request header.

    The API key must be provided in the X-OpenAI-Key header and must
    start with 'sk-' (standard OpenAI key format).

    Raises:
        HTTPException: 401 if key is missing or invalid format
    """
    if not x_openai_key:
        raise HTTPException(
            status_code=401,
            detail="OpenAI API key required. Please provide your key in the X-OpenAI-Key header."
        )

    if not x_openai_key.startswith("sk-"):
        raise HTTPException(
            status_code=401,
            detail="Invalid OpenAI API key format. Key must start with 'sk-'."
        )

    return x_openai_key
