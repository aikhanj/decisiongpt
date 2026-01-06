from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
    print(f"Vector Memory: {'enabled' if settings.use_vector_memory else 'disabled'}")
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

# Include routers
app.include_router(decisions_router, prefix="/api")
app.include_router(nodes_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(advisors_router, prefix="/api")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "decision-canvas"}


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": "Decision Canvas API",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/health",
    }
