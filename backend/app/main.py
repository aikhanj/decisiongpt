from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import decisions_router, nodes_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events."""
    # Startup
    settings = get_settings()
    print(f"Starting Gentleman Coach API")
    print(f"Vector Memory: {'enabled' if settings.use_vector_memory else 'disabled'}")
    yield
    # Shutdown
    print("Shutting down Gentleman Coach API")


app = FastAPI(
    title="Gentleman Coach API",
    description="API for the Gentleman Coach romantic decision advisor",
    version="1.0.0",
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


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "gentleman-coach"}


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": "Gentleman Coach API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }
