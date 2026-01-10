"""Observations API router - AI observations about users."""

import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.dependencies import get_openai_api_key
from app.services.observation_service import ObservationService
from app.models.observation import ObservationFeedback

router = APIRouter(prefix="/observations", tags=["observations"])


# Request/Response schemas
class ObservationResponse(BaseModel):
    """Single observation response."""
    id: str
    observation_text: str
    observation_type: str
    confidence: float
    related_theme: Optional[str] = None
    tags: list[str] = []
    surfaced_count: int = 0
    user_feedback: Optional[str] = None
    created_at: str
    decision_id: Optional[str] = None


class ObservationsGrouped(BaseModel):
    """Observations grouped by type."""
    patterns: list[ObservationResponse] = []
    values: list[ObservationResponse] = []
    strengths: list[ObservationResponse] = []
    growth_areas: list[ObservationResponse] = []
    insights: list[ObservationResponse] = []


class FeedbackRequest(BaseModel):
    """Feedback on an observation."""
    feedback: str  # "helpful", "not_relevant", "incorrect"


def _observation_to_response(obs) -> ObservationResponse:
    """Convert Observation model to response schema."""
    return ObservationResponse(
        id=str(obs.id),
        observation_text=obs.observation_text,
        observation_type=obs.observation_type,
        confidence=float(obs.confidence),
        related_theme=obs.related_theme,
        tags=obs.tags or [],
        surfaced_count=obs.surfaced_count,
        user_feedback=obs.user_feedback,
        created_at=obs.created_at.isoformat() if obs.created_at else "",
        decision_id=str(obs.decision_id) if obs.decision_id else None,
    )


@router.get("/me", response_model=list[ObservationResponse])
async def get_my_observations(
    observation_type: Optional[str] = None,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """Get observations about the current user.

    Optionally filter by type: pattern, value, strength, growth_area, insight
    """
    settings = get_settings()
    user_id = uuid.UUID(settings.default_user_id)

    service = ObservationService(db)
    observations = await service.get_observations_for_display(
        user_id,
        limit=limit,
        observation_type=observation_type,
    )

    return [_observation_to_response(obs) for obs in observations]


@router.get("/me/grouped", response_model=ObservationsGrouped)
async def get_observations_grouped(
    db: AsyncSession = Depends(get_db),
):
    """Get observations grouped by type for the Observations tab."""
    settings = get_settings()
    user_id = uuid.UUID(settings.default_user_id)

    service = ObservationService(db)
    grouped = await service.get_observations_grouped(user_id)

    return ObservationsGrouped(
        patterns=[_observation_to_response(o) for o in grouped.get("pattern", [])],
        values=[_observation_to_response(o) for o in grouped.get("value", [])],
        strengths=[_observation_to_response(o) for o in grouped.get("strength", [])],
        growth_areas=[_observation_to_response(o) for o in grouped.get("growth_area", [])],
        insights=[_observation_to_response(o) for o in grouped.get("insight", [])],
    )


@router.get("/me/recent", response_model=list[ObservationResponse])
async def get_recent_insights(
    days: int = 7,
    limit: int = 5,
    db: AsyncSession = Depends(get_db),
):
    """Get recent high-confidence insights."""
    settings = get_settings()
    user_id = uuid.UUID(settings.default_user_id)

    service = ObservationService(db)
    observations = await service.get_recent_insights(user_id, days=days, limit=limit)

    return [_observation_to_response(obs) for obs in observations]


@router.post("/{observation_id}/feedback")
async def submit_feedback(
    observation_id: uuid.UUID,
    data: FeedbackRequest,
    db: AsyncSession = Depends(get_db),
):
    """Submit feedback on an observation.

    Feedback options: helpful, not_relevant, incorrect
    """
    settings = get_settings()
    user_id = uuid.UUID(settings.default_user_id)

    # Validate feedback value
    try:
        feedback = ObservationFeedback(data.feedback)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid feedback. Must be one of: {[f.value for f in ObservationFeedback]}"
        )

    service = ObservationService(db)
    observation = await service.set_feedback(observation_id, user_id, feedback)

    if not observation:
        raise HTTPException(status_code=404, detail="Observation not found")

    return {"status": "feedback_recorded", "observation_id": str(observation_id)}


@router.get("/decision/{decision_id}", response_model=list[ObservationResponse])
async def get_decision_observations(
    decision_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get observations generated from a specific decision."""
    from sqlalchemy import select
    from app.models.observation import Observation

    settings = get_settings()
    user_id = uuid.UUID(settings.default_user_id)

    result = await db.execute(
        select(Observation)
        .where(
            Observation.user_id == user_id,
            Observation.decision_id == decision_id,
        )
        .order_by(Observation.confidence.desc())
    )
    observations = result.scalars().all()

    return [_observation_to_response(obs) for obs in observations]


@router.post("/generate/{decision_id}")
async def generate_observations(
    decision_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(get_openai_api_key),
):
    """Manually trigger observation generation for a decision.

    This analyzes the conversation history and generates new observations.
    Usually called automatically, but can be triggered manually.
    """
    from app.services.decision_service import DecisionService

    settings = get_settings()
    user_id = uuid.UUID(settings.default_user_id)

    # Get the decision and its chat messages
    decision_service = DecisionService(db)
    decision = await decision_service.get_decision(decision_id)

    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")

    if decision.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Get the latest node's chat messages
    if not decision.nodes:
        raise HTTPException(status_code=400, detail="Decision has no conversation history")

    node = decision.nodes[-1]
    chat_messages = node.chat_messages_json or []

    if len(chat_messages) < 3:
        raise HTTPException(status_code=400, detail="Not enough conversation history")

    # Generate observations
    service = ObservationService(db, api_key)
    new_observations = await service.generate_observations_from_conversation(
        user_id=user_id,
        decision_id=decision_id,
        chat_messages=chat_messages,
    )

    return {
        "status": "generated",
        "count": len(new_observations),
        "observations": [_observation_to_response(obs) for obs in new_observations],
    }
