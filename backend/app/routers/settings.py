"""Settings router for app configuration and onboarding."""

import asyncio
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field
import httpx

from app.database import get_db
from app.models.app_settings import AppSettings
from app.config import get_settings

router = APIRouter(prefix="/settings", tags=["settings"])


# === Pydantic Schemas ===

class SetupStatusResponse(BaseModel):
    """Response for setup status check."""
    setup_completed: bool
    llm_provider: Optional[str] = None
    ollama_model: Optional[str] = None
    has_openai_key: bool = False


class OllamaStatusResponse(BaseModel):
    """Response for Ollama status check."""
    status: str  # "running", "not_running", "not_installed"
    installed_models: list[dict] = []
    current_model: Optional[str] = None
    help: Optional[str] = None


class AvailableModel(BaseModel):
    """A model available for download."""
    name: str
    description: str
    size: str
    parameters: str


class SaveSettingsRequest(BaseModel):
    """Request to save settings."""
    llm_provider: str = Field(..., pattern="^(ollama|openai)$")
    ollama_model: Optional[str] = None
    openai_api_key: Optional[str] = None
    openai_model: Optional[str] = "gpt-4o"


class PullModelRequest(BaseModel):
    """Request to pull/download an Ollama model."""
    model_name: str = Field(..., min_length=1)


# === Helper Functions ===

async def get_or_create_settings(db: AsyncSession) -> AppSettings:
    """Get existing settings or create default ones."""
    result = await db.execute(select(AppSettings).limit(1))
    settings = result.scalar_one_or_none()

    if not settings:
        settings = AppSettings()
        db.add(settings)
        await db.commit()
        await db.refresh(settings)

    return settings


# === Endpoints ===

@router.get("/setup-status", response_model=SetupStatusResponse)
async def get_setup_status(db: AsyncSession = Depends(get_db)):
    """Check if initial setup has been completed."""
    settings = await get_or_create_settings(db)

    return SetupStatusResponse(
        setup_completed=settings.setup_completed,
        llm_provider=settings.llm_provider if settings.setup_completed else None,
        ollama_model=settings.ollama_model if settings.setup_completed else None,
        has_openai_key=bool(settings.openai_api_key) if settings.setup_completed else False,
    )


@router.get("/ollama/status", response_model=OllamaStatusResponse)
async def get_ollama_status(db: AsyncSession = Depends(get_db)):
    """Check Ollama status and list installed models."""
    config = get_settings()
    app_settings = await get_or_create_settings(db)
    base_url = config.ollama_base_url.replace("/v1", "")

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{base_url}/api/tags")

            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])

                # Format model info
                installed_models = []
                for m in models:
                    size_bytes = m.get("size", 0)
                    size_gb = size_bytes / (1024 ** 3)
                    installed_models.append({
                        "name": m.get("name"),
                        "size": f"{size_gb:.1f} GB" if size_gb >= 1 else f"{size_bytes / (1024**2):.0f} MB",
                        "modified_at": m.get("modified_at"),
                        "family": m.get("details", {}).get("family", "unknown"),
                        "parameter_size": m.get("details", {}).get("parameter_size", "unknown"),
                    })

                return OllamaStatusResponse(
                    status="running",
                    installed_models=installed_models,
                    current_model=app_settings.ollama_model,
                )

    except httpx.ConnectError:
        return OllamaStatusResponse(
            status="not_running",
            installed_models=[],
            current_model=None,
            help="Ollama is not running. Please start it with 'ollama serve' or launch the Ollama app.",
        )
    except Exception as e:
        return OllamaStatusResponse(
            status="not_installed",
            installed_models=[],
            current_model=None,
            help=f"Could not connect to Ollama. Please install it from https://ollama.ai. Error: {str(e)}",
        )


@router.get("/ollama/available-models")
async def get_available_models():
    """Get list of popular models available for download."""
    # Curated list of recommended models
    models = [
        {
            "name": "llama3.2",
            "display_name": "Llama 3.2 (3B)",
            "description": "Meta's latest small model. Fast and capable.",
            "size": "2.0 GB",
            "parameters": "3B",
            "recommended": True,
        },
        {
            "name": "llama3.2:1b",
            "display_name": "Llama 3.2 (1B)",
            "description": "Smallest Llama model. Very fast, good for basic tasks.",
            "size": "1.3 GB",
            "parameters": "1B",
            "recommended": False,
        },
        {
            "name": "llama3.1:8b",
            "display_name": "Llama 3.1 (8B)",
            "description": "Larger model with better reasoning. Needs more RAM.",
            "size": "4.7 GB",
            "parameters": "8B",
            "recommended": False,
        },
        {
            "name": "mistral",
            "display_name": "Mistral (7B)",
            "description": "Excellent general-purpose model from Mistral AI.",
            "size": "4.1 GB",
            "parameters": "7B",
            "recommended": False,
        },
        {
            "name": "phi3:mini",
            "display_name": "Phi-3 Mini",
            "description": "Microsoft's efficient small model. Great for limited hardware.",
            "size": "2.3 GB",
            "parameters": "3.8B",
            "recommended": False,
        },
        {
            "name": "gemma2:2b",
            "display_name": "Gemma 2 (2B)",
            "description": "Google's lightweight model. Fast and efficient.",
            "size": "1.6 GB",
            "parameters": "2B",
            "recommended": False,
        },
        {
            "name": "qwen2.5:7b",
            "display_name": "Qwen 2.5 (7B)",
            "description": "Alibaba's capable multilingual model.",
            "size": "4.4 GB",
            "parameters": "7B",
            "recommended": False,
        },
    ]
    return {"models": models}


@router.post("/ollama/pull")
async def pull_ollama_model(request: PullModelRequest):
    """Pull/download an Ollama model. Returns a streaming response with progress."""
    config = get_settings()
    base_url = config.ollama_base_url.replace("/v1", "")

    async def stream_progress():
        try:
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream(
                    "POST",
                    f"{base_url}/api/pull",
                    json={"name": request.model_name},
                ) as response:
                    async for line in response.aiter_lines():
                        if line:
                            yield f"data: {line}\n\n"

            yield 'data: {"status": "success"}\n\n'

        except httpx.ConnectError:
            yield 'data: {"error": "Ollama is not running"}\n\n'
        except Exception as e:
            yield f'data: {{"error": "{str(e)}"}}\n\n'

    return StreamingResponse(
        stream_progress(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@router.post("/ollama/pull-sync")
async def pull_ollama_model_sync(request: PullModelRequest):
    """Pull/download an Ollama model synchronously (for simpler clients)."""
    config = get_settings()
    base_url = config.ollama_base_url.replace("/v1", "")

    try:
        async with httpx.AsyncClient(timeout=600.0) as client:  # 10 min timeout for large models
            response = await client.post(
                f"{base_url}/api/pull",
                json={"name": request.model_name},
            )

            if response.status_code == 200:
                return {"status": "success", "model": request.model_name}
            else:
                return {"status": "error", "message": response.text}

    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Ollama is not running")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("")
async def get_settings_endpoint(db: AsyncSession = Depends(get_db)):
    """Get current app settings."""
    settings = await get_or_create_settings(db)

    return {
        "llm_provider": settings.llm_provider,
        "ollama_model": settings.ollama_model,
        "ollama_base_url": settings.ollama_base_url,
        "openai_model": settings.openai_model,
        "has_openai_key": bool(settings.openai_api_key),
        "setup_completed": settings.setup_completed,
    }


@router.put("")
async def save_settings(
    request: SaveSettingsRequest,
    db: AsyncSession = Depends(get_db),
):
    """Save app settings and complete setup."""
    settings = await get_or_create_settings(db)

    # Update settings
    settings.llm_provider = request.llm_provider

    if request.llm_provider == "ollama":
        if request.ollama_model:
            settings.ollama_model = request.ollama_model
    elif request.llm_provider == "openai":
        if request.openai_api_key:
            settings.openai_api_key = request.openai_api_key
        if request.openai_model:
            settings.openai_model = request.openai_model

    settings.setup_completed = True

    await db.commit()
    await db.refresh(settings)

    return {
        "status": "success",
        "llm_provider": settings.llm_provider,
        "ollama_model": settings.ollama_model if settings.llm_provider == "ollama" else None,
        "openai_model": settings.openai_model if settings.llm_provider == "openai" else None,
    }


@router.post("/test-openai-key")
async def test_openai_key(api_key: str = Query(..., description="OpenAI API key to test")):
    """Test if an OpenAI API key is valid."""

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://api.openai.com/v1/models",
                headers={"Authorization": f"Bearer {api_key}"},
            )

            if response.status_code == 200:
                return {"valid": True, "message": "API key is valid"}
            elif response.status_code == 401:
                return {"valid": False, "message": "Invalid API key"}
            else:
                return {"valid": False, "message": f"Error: {response.status_code}"}

    except Exception as e:
        return {"valid": False, "message": f"Connection error: {str(e)}"}
