from app.routers.decisions import router as decisions_router
from app.routers.nodes import router as nodes_router
from app.routers.adaptive_questions import router as adaptive_questions_router
from app.routers.profile import router as profile_router
from app.routers.observations import router as observations_router

__all__ = [
    "decisions_router",
    "nodes_router",
    "adaptive_questions_router",
    "profile_router",
    "observations_router",
]
