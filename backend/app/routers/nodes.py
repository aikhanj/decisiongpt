import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_openai_api_key
from app.models.decision_node import NodePhase
from app.schemas.decision import (
    AnswerRequest,
    ChooseMoveRequest,
    DecisionNodeResponse,
    Phase2APIResponse,
    ExecutionAPIResponse,
)
from app.schemas.outcome import OutcomeCreate, OutcomeResponse
from app.services.decision_service import DecisionService
from app.services.phase2_service import Phase2Service
from app.services.calibration_service import CalibrationService
from app.services.memory_service import MemoryService

router = APIRouter(prefix="/decisions/{decision_id}/nodes", tags=["nodes"])


@router.get("/{node_id}", response_model=DecisionNodeResponse)
async def get_node(
    decision_id: uuid.UUID,
    node_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a decision node by ID."""
    service = DecisionService(db)
    node = await service.get_node(node_id)

    if not node or node.decision_id != decision_id:
        raise HTTPException(status_code=404, detail="Node not found")

    return DecisionNodeResponse.model_validate(node)


@router.post("/{node_id}/answer", response_model=Phase2APIResponse)
async def answer_questions(
    decision_id: uuid.UUID,
    node_id: uuid.UUID,
    data: AnswerRequest,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(get_openai_api_key),
):
    """
    Submit answers to Phase 1 questions and run Phase 2 (Moves).

    Returns 2-3 move options with scripts and branches.

    Requires X-OpenAI-Key header with your OpenAI API key.
    """
    decision_service = DecisionService(db)
    node = await decision_service.get_node(node_id)

    if not node or node.decision_id != decision_id:
        raise HTTPException(status_code=404, detail="Node not found")

    if node.phase != NodePhase.CLARIFY.value:
        raise HTTPException(
            status_code=400,
            detail=f"Node is in {node.phase} phase, expected clarify",
        )

    service = Phase2Service(db)
    updated_node, response = await service.run_phase2(node, data.answers, api_key)

    return Phase2APIResponse(
        node=DecisionNodeResponse.model_validate(updated_node),
        moves=response.moves,
        cooldown_recommended=response.cooldown_recommended,
        cooldown_reason=response.cooldown_reason,
    )


@router.post("/{node_id}/choose", response_model=ExecutionAPIResponse)
async def choose_move(
    decision_id: uuid.UUID,
    node_id: uuid.UUID,
    data: ChooseMoveRequest,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(get_openai_api_key),
):
    """
    Choose a move (A, B, or C) and generate execution plan.

    Returns a concrete execution plan with steps and scripts.

    Requires X-OpenAI-Key header with your OpenAI API key.
    """
    decision_service = DecisionService(db)
    node = await decision_service.get_node(node_id)

    if not node or node.decision_id != decision_id:
        raise HTTPException(status_code=404, detail="Node not found")

    if node.phase != NodePhase.MOVES.value:
        raise HTTPException(
            status_code=400,
            detail=f"Node is in {node.phase} phase, expected moves",
        )

    service = Phase2Service(db)
    updated_node, execution_plan = await service.generate_execution_plan(
        node, data.move_id, api_key
    )

    return ExecutionAPIResponse(
        node=DecisionNodeResponse.model_validate(updated_node),
        execution_plan=execution_plan,
    )


@router.post("/{node_id}/branch", response_model=DecisionNodeResponse)
async def create_branch(
    decision_id: uuid.UUID,
    node_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a branch from an existing node to explore alternatives.

    Clones the node state and allows re-running Phase 2 with modifications.
    """
    decision_service = DecisionService(db)
    node = await decision_service.get_node(node_id)

    if not node or node.decision_id != decision_id:
        raise HTTPException(status_code=404, detail="Node not found")

    # Create a child node with same state but allowing new answers/moves
    branch_node = await decision_service.create_node(
        decision_id=decision_id,
        phase=NodePhase.CLARIFY,
        parent_node_id=node_id,
        state_json=node.state_json,
        questions_json=node.questions_json,
        mood_state=node.mood_state,
        metadata_json=node.metadata_json,
        policy_version=node.policy_version,
    )

    # Log event
    await decision_service.log_event(
        decision_id=decision_id,
        node_id=branch_node.id,
        event_type="branched",
        payload={"parent_node_id": str(node_id)},
    )

    return DecisionNodeResponse.model_validate(branch_node)


@router.post("/{node_id}/resolve", response_model=OutcomeResponse)
async def resolve_outcome(
    decision_id: uuid.UUID,
    node_id: uuid.UUID,
    data: OutcomeCreate,
    db: AsyncSession = Depends(get_db),
    x_openai_key: Optional[str] = Header(None, alias="X-OpenAI-Key"),
):
    """
    Record the outcome of a decision and compute Brier score.

    This marks the decision as resolved.

    Optionally provide X-OpenAI-Key header if vector memory is enabled.
    """
    decision_service = DecisionService(db)
    node = await decision_service.get_node(node_id)

    if not node or node.decision_id != decision_id:
        raise HTTPException(status_code=404, detail="Node not found")

    if node.phase != NodePhase.EXECUTE.value:
        raise HTTPException(
            status_code=400,
            detail=f"Node is in {node.phase} phase, expected execute",
        )

    calibration_service = CalibrationService(db)
    outcome = await calibration_service.record_outcome(
        node_id=node_id,
        progress_yesno=data.progress_yesno,
        sentiment_2h=data.sentiment_2h,
        sentiment_24h=data.sentiment_24h,
        notes=data.notes,
    )

    # Create memory if vector memory is enabled and API key provided
    memory_service = MemoryService(db)
    if memory_service.is_enabled and x_openai_key:
        await memory_service.create_memory_from_node(node, x_openai_key)

    return OutcomeResponse.model_validate(outcome)
