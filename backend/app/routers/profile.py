"""Profile API router - user profile management and onboarding."""

import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.services.user_context_service import UserContextService

router = APIRouter(prefix="/users/me", tags=["profile"])


# Request/Response schemas
class ProfileEssentials(BaseModel):
    """Essential profile fields for onboarding."""
    name: Optional[str] = None
    age_range: Optional[str] = None
    occupation: Optional[str] = None
    industry: Optional[str] = None
    specialty: Optional[str] = None


class ProfileExtended(BaseModel):
    """Extended profile fields."""
    values: Optional[list[str]] = None
    goals: Optional[list[str]] = None
    recurring_themes: Optional[list[str]] = None
    strengths: Optional[list[str]] = None
    growth_areas: Optional[list[str]] = None


class ProfileResponse(BaseModel):
    """Full profile response."""
    id: str
    user_id: str
    name: Optional[str] = None
    age_range: Optional[str] = None
    occupation: Optional[str] = None
    industry: Optional[str] = None
    specialty: Optional[str] = None
    extended_profile: dict = {}
    onboarding_completed: bool = False
    onboarding_step: Optional[str] = None
    context_summary: Optional[str] = None


class OnboardingStatus(BaseModel):
    """Onboarding status response."""
    completed: bool
    step: Optional[str] = None


class TopicSuggestion(BaseModel):
    """Suggested topic based on past conversations."""
    topic: str
    count: int
    recent: bool = False


@router.get("/profile", response_model=ProfileResponse)
async def get_profile(
    db: AsyncSession = Depends(get_db),
):
    """Get the current user's profile."""
    settings = get_settings()
    user_id = uuid.UUID(settings.default_user_id)

    service = UserContextService(db)
    profile = await service.get_or_create_profile(user_id)

    return ProfileResponse(
        id=str(profile.id),
        user_id=str(profile.user_id),
        name=profile.name,
        age_range=profile.age_range,
        occupation=profile.occupation,
        industry=profile.industry,
        specialty=profile.specialty,
        extended_profile=profile.extended_profile or {},
        onboarding_completed=profile.onboarding_completed,
        onboarding_step=profile.onboarding_step,
        context_summary=profile.context_summary,
    )


@router.put("/profile", response_model=ProfileResponse)
async def update_profile(
    data: ProfileEssentials,
    db: AsyncSession = Depends(get_db),
):
    """Update the current user's profile essentials."""
    settings = get_settings()
    user_id = uuid.UUID(settings.default_user_id)

    service = UserContextService(db)
    profile = await service.get_or_create_profile(user_id)

    # Update fields if provided
    if data.name is not None:
        profile.name = data.name
    if data.age_range is not None:
        profile.age_range = data.age_range
    if data.occupation is not None:
        profile.occupation = data.occupation
    if data.industry is not None:
        profile.industry = data.industry
    if data.specialty is not None:
        profile.specialty = data.specialty

    # Invalidate cached context
    profile.context_summary_updated_at = None

    await db.commit()
    await db.refresh(profile)

    return ProfileResponse(
        id=str(profile.id),
        user_id=str(profile.user_id),
        name=profile.name,
        age_range=profile.age_range,
        occupation=profile.occupation,
        industry=profile.industry,
        specialty=profile.specialty,
        extended_profile=profile.extended_profile or {},
        onboarding_completed=profile.onboarding_completed,
        onboarding_step=profile.onboarding_step,
        context_summary=profile.context_summary,
    )


@router.patch("/profile/extended")
async def update_extended_profile(
    data: ProfileExtended,
    db: AsyncSession = Depends(get_db),
):
    """Update the current user's extended profile (values, goals, etc.)."""
    settings = get_settings()
    user_id = uuid.UUID(settings.default_user_id)

    service = UserContextService(db)

    # Convert to dict for the update function
    learned_data = {}
    if data.values:
        learned_data["values"] = data.values
    if data.goals:
        learned_data["goals"] = data.goals
    if data.recurring_themes:
        learned_data["recurring_themes"] = data.recurring_themes
    if data.strengths:
        learned_data["strengths"] = data.strengths
    if data.growth_areas:
        learned_data["growth_areas"] = data.growth_areas

    await service.update_profile_from_conversation(user_id, learned_data)

    return {"status": "updated"}


@router.get("/onboarding/status", response_model=OnboardingStatus)
async def get_onboarding_status(
    db: AsyncSession = Depends(get_db),
):
    """Check if the user has completed onboarding."""
    settings = get_settings()
    user_id = uuid.UUID(settings.default_user_id)

    service = UserContextService(db)
    profile = await service.get_or_create_profile(user_id)

    return OnboardingStatus(
        completed=profile.onboarding_completed,
        step=profile.onboarding_step,
    )


@router.post("/onboarding/complete")
async def complete_onboarding(
    db: AsyncSession = Depends(get_db),
):
    """Mark onboarding as complete."""
    settings = get_settings()
    user_id = uuid.UUID(settings.default_user_id)

    service = UserContextService(db)
    profile = await service.get_or_create_profile(user_id)

    profile.onboarding_completed = True
    profile.onboarding_step = "completed"

    # Refresh context summary now that onboarding is done
    await service.refresh_context_summary(user_id)

    await db.commit()

    return {"status": "completed"}


@router.get("/suggested-topics", response_model=list[TopicSuggestion])
async def get_suggested_topics(
    db: AsyncSession = Depends(get_db),
):
    """Get topic suggestions based on past decisions.

    Returns topics like "Career", "Relationships", "Startups" with counts
    based on the user's decision history.
    """
    settings = get_settings()
    user_id = uuid.UUID(settings.default_user_id)

    # Query decisions and group by situation_type
    from sqlalchemy import select, func
    from app.models.decision import Decision

    result = await db.execute(
        select(
            Decision.situation_type,
            func.count(Decision.id).label("count"),
        )
        .where(Decision.user_id == user_id)
        .group_by(Decision.situation_type)
        .order_by(func.count(Decision.id).desc())
        .limit(5)
    )
    rows = result.fetchall()

    # Map situation types to display names
    type_display = {
        "career": "Career",
        "financial": "Finance",
        "business": "Business",
        "personal": "Personal",
        "relationship": "Relationships",
        "health": "Health",
        "education": "Education",
        "other": "General",
    }

    suggestions = []
    for row in rows:
        if row.situation_type:
            suggestions.append(TopicSuggestion(
                topic=type_display.get(row.situation_type, row.situation_type.title()),
                count=row.count,
                recent=False,  # Could enhance to check recency
            ))

    return suggestions


@router.post("/context/refresh")
async def refresh_context(
    db: AsyncSession = Depends(get_db),
):
    """Force refresh the user's context summary."""
    settings = get_settings()
    user_id = uuid.UUID(settings.default_user_id)

    service = UserContextService(db)
    context = await service.refresh_context_summary(user_id)

    return {"status": "refreshed", "context_length": len(context) if context else 0}
