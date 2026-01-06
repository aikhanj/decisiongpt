import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.dependencies import get_openai_api_key
from app.schemas.decision import (
    DecisionCreate,
    DecisionResponse,
    Phase1APIResponse,
)
from app.schemas.question import Question
from app.services.phase1_service import Phase1Service
from app.services.decision_service import DecisionService

router = APIRouter(prefix="/decisions", tags=["decisions"])


@router.post("", response_model=Phase1APIResponse)
async def create_decision(
    data: DecisionCreate,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(get_openai_api_key),
):
    """
    Create a new decision and run Phase 1 (Clarify).

    Returns structured questions for the user to answer.

    Requires X-OpenAI-Key header with your OpenAI API key.
    """
    settings = get_settings()
    user_id = uuid.UUID(settings.default_user_id)

    service = Phase1Service(db)
    node, response = await service.run_phase1(
        user_id=user_id,
        situation_text=data.situation_text,
        api_key=api_key,
    )

    # Get the decision
    decision_service = DecisionService(db)
    decision = await decision_service.get_decision(node.decision_id)

    return Phase1APIResponse(
        decision=DecisionResponse.model_validate(decision),
        node=node,
        summary=response.summary,
        situation_type=response.situation_type,
        mood_detected=response.mood_detected,
        questions=[Question.model_validate(q) for q in response.questions],
    )


@router.get("", response_model=list[DecisionResponse])
async def list_decisions(
    db: AsyncSession = Depends(get_db),
):
    """Get recent decisions for the current user."""
    settings = get_settings()
    user_id = uuid.UUID(settings.default_user_id)

    service = DecisionService(db)
    decisions = await service.get_decisions_for_user(user_id)

    return [DecisionResponse.model_validate(d) for d in decisions]


@router.get("/{decision_id}", response_model=DecisionResponse)
async def get_decision(
    decision_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a decision by ID with all nodes."""
    service = DecisionService(db)
    decision = await service.get_decision(decision_id)

    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")

    return DecisionResponse.model_validate(decision)
