from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import httpx

from app.config import get_settings
from app.routers import decisions_router, nodes_router
from app.routers.chat import router as chat_router
from app.routers.advisors import router as advisors_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events."""
    # Startup
    settings = get_settings()
    print(f"Starting Decision Canvas API")
    print(f"Database: {settings.database_type}")
    print(f"LLM Provider: {settings.llm_provider}")
    print(f"Desktop Mode: {settings.desktop_mode}")
    print(f"Vector Memory: {'enabled' if settings.use_vector_memory else 'disabled'}")

    # Initialize database tables for SQLite (desktop mode)
    if settings.database_type == "sqlite":
        from app.database import init_db
        print(f"Initializing SQLite database at: {settings.sqlite_path}")
        await init_db()
        print("Database initialized")

    yield
    # Shutdown
    print("Shutting down Decision Canvas API")


app = FastAPI(
    title="Decision Canvas API",
    description="API for Decision Canvas - structured decision making with AI",
    version="2.0.0",
    lifespan=lifespan,
)

# Configure CORS
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include core routers
app.include_router(decisions_router, prefix="/api")
app.include_router(nodes_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(advisors_router, prefix="/api")

# Include tasks router only when Celery is available (web mode)
if not settings.desktop_mode:
    try:
        from app.routers.tasks import router as tasks_router
        app.include_router(tasks_router, prefix="/api")
        print("Tasks router enabled (Celery mode)")
    except ImportError:
        print("Tasks router disabled (Celery not available)")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "decision-canvas"}


@app.get("/")
async def root():
    """Root endpoint with API info."""
    settings = get_settings()
    return {
        "name": "Decision Canvas API",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/health",
        "llm_provider": settings.llm_provider,
        "database_type": settings.database_type,
        "desktop_mode": settings.desktop_mode,
    }


@app.get("/api/ollama/status")
async def ollama_status():
    """Check if Ollama is running and get available models."""
    settings = get_settings()
    base_url = settings.ollama_base_url.replace("/v1", "")  # Remove /v1 suffix

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Check Ollama API
            response = await client.get(f"{base_url}/api/tags")
            if response.status_code == 200:
                data = response.json()
                models = [m.get("name") for m in data.get("models", [])]
                return {
                    "status": "running",
                    "models": models,
                    "current_model": settings.ollama_model,
                    "model_available": settings.ollama_model in models or any(
                        settings.ollama_model in m for m in models
                    ),
                }
    except Exception as e:
        pass

    return {
        "status": "not_running",
        "models": [],
        "current_model": settings.ollama_model,
        "model_available": False,
        "help": "Please install and start Ollama from https://ollama.ai",
    }
