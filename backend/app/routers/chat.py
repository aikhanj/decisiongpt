"""Chat router for Decision Canvas API."""
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import Optional

from app.database import get_db
from app.dependencies import get_openai_api_key
from app.services.chat_service import ChatService
from app.services.decision_service import DecisionService
from app.schemas.canvas import ChatRequest, ChatResponse, CanvasState, Option, CommitPlan, ChatMessage
from app.schemas.decision import DecisionResponse, DecisionNodeResponse

router = APIRouter(prefix="/decisions", tags=["chat"])


class StartDecisionRequest(BaseModel):
    """Request to start a new decision."""
    situation_text: str = Field(..., min_length=10, max_length=5000)


class StartDecisionResponse(BaseModel):
    """Response after starting a new decision."""
    decision: DecisionResponse
    node: DecisionNodeResponse
    initial_message: ChatMessage
    canvas_state: CanvasState
    questions: list[dict] = []


class ChooseOptionRequest(BaseModel):
    """Request to choose an option."""
    option_id: str = Field(..., min_length=1, max_length=10)  # Allow A, B, C or other formats


@router.post("", response_model=StartDecisionResponse)
async def start_decision(
    request: StartDecisionRequest,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(get_openai_api_key),
):
    """Start a new decision and get initial analysis.

    This creates a new decision, runs Phase 1 analysis, and returns
    the initial chat message with clarifying questions.
    """
    chat_service = ChatService(db, api_key)

    # Use a default user ID for MVP (no auth)
    default_user_id = uuid.UUID("00000000-0000-0000-0000-000000000001")

    decision, node, phase1_response = await chat_service.start_decision(
        user_id=default_user_id,
        situation_text=request.situation_text,
    )

    # Get the assistant's initial message
    chat_messages = node.chat_messages_json or []
    assistant_msg = next(
        (m for m in reversed(chat_messages) if m.get("role") == "assistant"),
        {"id": "msg_0", "role": "assistant", "content": "Hello!", "timestamp": "2026-01-06T00:00:00Z"}
    )

    return StartDecisionResponse(
        decision=DecisionResponse.model_validate(decision),
        node=DecisionNodeResponse.model_validate(node),
        initial_message=ChatMessage(
            id=assistant_msg["id"],
            role="assistant",
            content=assistant_msg["content"],
            timestamp=assistant_msg["timestamp"],
        ),
        canvas_state=CanvasState(**(node.canvas_state_json or {})),
        questions=phase1_response.get("questions", []),
    )


@router.post("/{decision_id}/nodes/{node_id}/chat", response_model=ChatResponse)
async def send_chat_message(
    decision_id: uuid.UUID,
    node_id: uuid.UUID,
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(get_openai_api_key),
):
    """Send a chat message and get AI response.

    This processes the user's message, updates the canvas state,
    and returns the assistant's response.
    """
    decision_service = DecisionService(db)
    chat_service = ChatService(db, api_key)

    # Get decision and node
    decision = await decision_service.get_decision(decision_id)
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")

    node = await decision_service.get_node(node_id)
    if not node or node.decision_id != decision_id:
        raise HTTPException(status_code=404, detail="Node not found")

    # Process message
    response = await chat_service.send_message(node, request.message)

    return response


@router.post("/{decision_id}/nodes/{node_id}/choose", response_model=ChatResponse)
async def choose_option(
    decision_id: uuid.UUID,
    node_id: uuid.UUID,
    request: ChooseOptionRequest,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(get_openai_api_key),
):
    """Choose an option and generate commit plan.

    This explicitly selects an option and generates the action plan.
    """
    print(f"[DEBUG] choose_option called with option_id: {request.option_id}")
    decision_service = DecisionService(db)
    chat_service = ChatService(db, api_key)

    # Get decision and node
    decision = await decision_service.get_decision(decision_id)
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")

    node = await decision_service.get_node(node_id)
    if not node or node.decision_id != decision_id:
        raise HTTPException(status_code=404, detail="Node not found")

    # Check node is in options phase
    if node.phase != "moves":
        raise HTTPException(
            status_code=400,
            detail=f"Can only choose option during options phase. Current phase: {node.phase}"
        )

    # Get available options
    options = (node.moves_json or {}).get("options", [])
    option_ids = [o.get("id") for o in options]

    if request.option_id not in option_ids:
        raise HTTPException(
            status_code=400,
            detail=f"Option '{request.option_id}' not found. Available: {option_ids}"
        )

    # Choose option
    try:
        response = await chat_service.choose_option(node, request.option_id)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate commit plan: {str(e)}")


@router.get("/{decision_id}/nodes/{node_id}/chat-history")
async def get_chat_history(
    decision_id: uuid.UUID,
    node_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get full chat history for a node."""
    decision_service = DecisionService(db)

    decision = await decision_service.get_decision(decision_id)
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")

    node = await decision_service.get_node(node_id)
    if not node or node.decision_id != decision_id:
        raise HTTPException(status_code=404, detail="Node not found")

    chat_messages = node.chat_messages_json or []
    canvas_state = node.canvas_state_json or {}
    options = (node.moves_json or {}).get("options", [])
    commit_plan = node.execution_plan_json

    return {
        "messages": [ChatMessage(**m) for m in chat_messages],
        "canvas_state": CanvasState(**canvas_state) if canvas_state else None,
        "phase": node.phase,
        "options": [Option(**o) for o in options] if options else None,
        "commit_plan": CommitPlan(**commit_plan) if commit_plan else None,
    }


@router.post("/{decision_id}/nodes/{node_id}/submit-answers")
async def submit_answers(
    decision_id: uuid.UUID,
    node_id: uuid.UUID,
    answers: dict,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(get_openai_api_key),
):
    """Submit answers to clarifying questions.

    This stores the answers and optionally triggers options generation.
    """
    decision_service = DecisionService(db)
    chat_service = ChatService(db, api_key)

    decision = await decision_service.get_decision(decision_id)
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")

    node = await decision_service.get_node(node_id)
    if not node or node.decision_id != decision_id:
        raise HTTPException(status_code=404, detail="Node not found")

    # Store answers
    node.answers_json = answers
    await db.commit()

    # Send a message to trigger potential phase transition
    response = await chat_service.send_message(
        node,
        "I've answered the questions. Can you generate options for me?"
    )

    return response
