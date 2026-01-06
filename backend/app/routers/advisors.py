"""Advisors router for managing custom AI personas."""
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field
from typing import Optional

from app.database import get_db
from app.models.advisor import Advisor as AdvisorModel
from app.ai.advisors.registry import get_all_advisors, get_advisor, get_registry, Advisor as AdvisorData

router = APIRouter(prefix="/advisors", tags=["advisors"])


class AdvisorResponse(BaseModel):
    """Response model for an advisor."""
    id: str
    name: str
    avatar: str
    description: str
    expertise_keywords: list[str]
    personality_traits: list[str]
    is_system: bool

    class Config:
        from_attributes = True


class CreateAdvisorRequest(BaseModel):
    """Request to create a custom advisor."""
    slug: str = Field(..., min_length=2, max_length=50, pattern="^[a-z0-9-]+$")
    name: str = Field(..., min_length=2, max_length=100)
    avatar: str = Field(..., min_length=1, max_length=50)
    description: str = Field(..., min_length=10, max_length=500)
    expertise_keywords: list[str] = Field(..., min_items=1, max_items=50)
    personality_traits: list[str] = Field(default_factory=list, max_items=10)
    system_prompt: str = Field(..., min_length=50, max_length=10000)


class UpdateAdvisorRequest(BaseModel):
    """Request to update a custom advisor."""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    avatar: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = Field(None, min_length=10, max_length=500)
    expertise_keywords: Optional[list[str]] = Field(None, min_items=1, max_items=50)
    personality_traits: Optional[list[str]] = Field(None, max_items=10)
    system_prompt: Optional[str] = Field(None, min_length=50, max_length=10000)
    is_active: Optional[bool] = None


@router.get("", response_model=list[AdvisorResponse])
async def list_advisors(
    include_custom: bool = True,
    db: AsyncSession = Depends(get_db),
):
    """List all available advisors.

    Returns both system (pre-built) advisors and custom advisors.
    """
    advisors = []

    # Add system advisors from registry
    for advisor in get_all_advisors():
        advisors.append(AdvisorResponse(
            id=advisor.id,
            name=advisor.name,
            avatar=advisor.avatar,
            description=advisor.description,
            expertise_keywords=advisor.expertise_keywords,
            personality_traits=advisor.personality_traits,
            is_system=advisor.is_system,
        ))

    # Add custom advisors from database
    if include_custom:
        result = await db.execute(
            select(AdvisorModel).where(AdvisorModel.is_active == True)
        )
        custom_advisors = result.scalars().all()

        for advisor in custom_advisors:
            # Skip if already in system advisors (shouldn't happen, but safety check)
            if not any(a.id == advisor.slug for a in advisors):
                advisors.append(AdvisorResponse(
                    id=advisor.slug,
                    name=advisor.name,
                    avatar=advisor.avatar,
                    description=advisor.description,
                    expertise_keywords=advisor.expertise_keywords,
                    personality_traits=advisor.personality_traits,
                    is_system=advisor.is_system,
                ))

    return advisors


@router.get("/{advisor_id}", response_model=AdvisorResponse)
async def get_advisor_by_id(
    advisor_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific advisor by ID."""
    # First check system advisors
    advisor = get_advisor(advisor_id)
    if advisor:
        return AdvisorResponse(
            id=advisor.id,
            name=advisor.name,
            avatar=advisor.avatar,
            description=advisor.description,
            expertise_keywords=advisor.expertise_keywords,
            personality_traits=advisor.personality_traits,
            is_system=advisor.is_system,
        )

    # Then check custom advisors
    result = await db.execute(
        select(AdvisorModel).where(AdvisorModel.slug == advisor_id)
    )
    custom_advisor = result.scalar_one_or_none()

    if not custom_advisor:
        raise HTTPException(status_code=404, detail="Advisor not found")

    return AdvisorResponse(
        id=custom_advisor.slug,
        name=custom_advisor.name,
        avatar=custom_advisor.avatar,
        description=custom_advisor.description,
        expertise_keywords=custom_advisor.expertise_keywords,
        personality_traits=custom_advisor.personality_traits,
        is_system=custom_advisor.is_system,
    )


@router.post("", response_model=AdvisorResponse)
async def create_advisor(
    request: CreateAdvisorRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create a new custom advisor."""
    # Check if slug already exists in system advisors
    if get_advisor(request.slug):
        raise HTTPException(
            status_code=400,
            detail=f"Advisor with slug '{request.slug}' already exists as a system advisor"
        )

    # Check if slug already exists in custom advisors
    result = await db.execute(
        select(AdvisorModel).where(AdvisorModel.slug == request.slug)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail=f"Advisor with slug '{request.slug}' already exists"
        )

    # Create the advisor
    advisor = AdvisorModel(
        slug=request.slug,
        name=request.name,
        avatar=request.avatar,
        description=request.description,
        expertise_keywords=request.expertise_keywords,
        personality_traits=request.personality_traits,
        system_prompt=request.system_prompt,
        is_system=False,
        is_active=True,
    )

    db.add(advisor)
    await db.commit()
    await db.refresh(advisor)

    # Add to the registry for immediate use
    registry = get_registry()
    registry.add_custom_advisor(AdvisorData(
        id=advisor.slug,
        name=advisor.name,
        avatar=advisor.avatar,
        description=advisor.description,
        expertise_keywords=advisor.expertise_keywords,
        personality_traits=advisor.personality_traits,
        system_prompt=advisor.system_prompt,
        is_system=False,
    ))

    return AdvisorResponse(
        id=advisor.slug,
        name=advisor.name,
        avatar=advisor.avatar,
        description=advisor.description,
        expertise_keywords=advisor.expertise_keywords,
        personality_traits=advisor.personality_traits,
        is_system=advisor.is_system,
    )


@router.patch("/{advisor_id}", response_model=AdvisorResponse)
async def update_advisor(
    advisor_id: str,
    request: UpdateAdvisorRequest,
    db: AsyncSession = Depends(get_db),
):
    """Update a custom advisor."""
    # Cannot update system advisors
    if get_advisor(advisor_id) and get_advisor(advisor_id).is_system:
        raise HTTPException(
            status_code=400,
            detail="Cannot modify system advisors"
        )

    # Find the custom advisor
    result = await db.execute(
        select(AdvisorModel).where(AdvisorModel.slug == advisor_id)
    )
    advisor = result.scalar_one_or_none()

    if not advisor:
        raise HTTPException(status_code=404, detail="Advisor not found")

    # Update fields
    if request.name is not None:
        advisor.name = request.name
    if request.avatar is not None:
        advisor.avatar = request.avatar
    if request.description is not None:
        advisor.description = request.description
    if request.expertise_keywords is not None:
        advisor.expertise_keywords = request.expertise_keywords
    if request.personality_traits is not None:
        advisor.personality_traits = request.personality_traits
    if request.system_prompt is not None:
        advisor.system_prompt = request.system_prompt
    if request.is_active is not None:
        advisor.is_active = request.is_active

    await db.commit()
    await db.refresh(advisor)

    # Update in registry
    registry = get_registry()
    if advisor.is_active:
        registry.add_custom_advisor(AdvisorData(
            id=advisor.slug,
            name=advisor.name,
            avatar=advisor.avatar,
            description=advisor.description,
            expertise_keywords=advisor.expertise_keywords,
            personality_traits=advisor.personality_traits,
            system_prompt=advisor.system_prompt,
            is_system=False,
        ))
    else:
        registry.remove_custom_advisor(advisor.slug)

    return AdvisorResponse(
        id=advisor.slug,
        name=advisor.name,
        avatar=advisor.avatar,
        description=advisor.description,
        expertise_keywords=advisor.expertise_keywords,
        personality_traits=advisor.personality_traits,
        is_system=advisor.is_system,
    )


@router.delete("/{advisor_id}")
async def delete_advisor(
    advisor_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a custom advisor."""
    # Cannot delete system advisors
    if get_advisor(advisor_id) and get_advisor(advisor_id).is_system:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete system advisors"
        )

    # Find the custom advisor
    result = await db.execute(
        select(AdvisorModel).where(AdvisorModel.slug == advisor_id)
    )
    advisor = result.scalar_one_or_none()

    if not advisor:
        raise HTTPException(status_code=404, detail="Advisor not found")

    # Remove from registry
    registry = get_registry()
    registry.remove_custom_advisor(advisor_id)

    # Delete from database
    await db.delete(advisor)
    await db.commit()

    return {"message": f"Advisor '{advisor_id}' deleted successfully"}
