"""API endpoints for adaptive conversational questioning."""

import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_openai_api_key
from app.models.decision_node import DecisionNode
from app.schemas.question import (
    QuestioningMode,
    Answer,
    AdaptiveQuestionResponse,
    NextQuestionResponse,
)
from app.services.adaptive_question_service import AdaptiveQuestionService

router = APIRouter(prefix="/adaptive-questions", tags=["adaptive-questions"])


@router.post(
    "/decisions/{decision_id}/nodes/{node_id}/start",
    response_model=AdaptiveQuestionResponse,
)
async def start_adaptive_questioning(
    decision_id: uuid.UUID,
    node_id: uuid.UUID,
    mode: QuestioningMode = QuestioningMode.QUICK,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(get_openai_api_key),
):
    """
    Initialize adaptive questioning for a decision node.

    This starts the conversational question flow using VoI-based selection.

    Args:
        decision_id: UUID of the decision
        node_id: UUID of the decision node
        mode: Questioning mode (quick=5 questions, deep=15 questions)

    Returns:
        - First question to ask (highest VoI)
        - Initial canvas state
        - Conversation state

    Requires X-OpenAI-Key header with your OpenAI API key.
    """
    # Get the node
    node = await db.get(DecisionNode, node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    if node.decision_id != decision_id:
        raise HTTPException(status_code=400, detail="Node doesn't belong to this decision")

    # Get situation text from node state
    situation_text = node.state_json.get("summary", "") if node.state_json else ""
    if not situation_text:
        raise HTTPException(status_code=400, detail="Node has no situation text")

    # Infer decision type from situation (simple heuristic for MVP)
    decision_type = _infer_decision_type(situation_text)

    # Initialize adaptive questioning
    service = AdaptiveQuestionService(db)
    conversation_state = await service.initialize_questioning(
        node=node,
        situation_text=situation_text,
        decision_type=decision_type,
        mode=mode,
    )

    # Save conversation state to node
    node.conversation_state_json = conversation_state.model_dump()
    node.question_history_json = []
    node.canvas_evolution_json = []
    await db.commit()

    return AdaptiveQuestionResponse(
        next_question=conversation_state.current_question,
        canvas_state=conversation_state.canvas_state,
        conversation_state=conversation_state,
    )


@router.post(
    "/decisions/{decision_id}/nodes/{node_id}/answer",
    response_model=NextQuestionResponse,
)
async def answer_question(
    decision_id: uuid.UUID,
    node_id: uuid.UUID,
    answer: Answer,
    db: AsyncSession = Depends(get_db),
):
    """
    Process an answer and get the next question.

    This is called after each answer to adaptively select the next question.

    Args:
        decision_id: UUID of the decision
        node_id: UUID of the decision node
        answer: The user's answer to the current question

    Returns:
        - Next question (or null if stopping)
        - Updated canvas state
        - Progress and status information

    Stopping occurs when:
    - Question cap reached
    - Diminishing returns detected
    - Critical information gathered
    - All remaining questions have low VoI
    """
    # Get the node
    node = await db.get(DecisionNode, node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    if node.decision_id != decision_id:
        raise HTTPException(status_code=400, detail="Node doesn't belong to this decision")

    if not node.conversation_state_json:
        raise HTTPException(
            status_code=400,
            detail="Conversation not initialized - call /start first",
        )

    # Process answer and get next question
    service = AdaptiveQuestionService(db)
    response = await service.get_next_question(node=node, previous_answer=answer)

    # Update node with new conversation state
    # (AdaptiveQuestionService modifies the node's conversation_state_json)
    await db.commit()

    return response


@router.get(
    "/decisions/{decision_id}/nodes/{node_id}/history",
)
async def get_conversation_history(
    decision_id: uuid.UUID,
    node_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get the conversation history for a node.

    Returns:
        - All questions asked
        - All answers given
        - Canvas evolution over time
    """
    # Get the node
    node = await db.get(DecisionNode, node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    if node.decision_id != decision_id:
        raise HTTPException(status_code=400, detail="Node doesn't belong to this decision")

    if not node.conversation_state_json:
        return {
            "questions_asked": [],
            "canvas_evolution": [],
            "conversation_state": None,
        }

    conversation_state = node.conversation_state_json

    return {
        "questions_asked": conversation_state.get("asked_questions", []),
        "canvas_evolution": node.canvas_evolution_json or [],
        "conversation_state": conversation_state,
    }


@router.post(
    "/decisions/{decision_id}/nodes/{node_id}/modify-answer",
)
async def modify_previous_answer(
    decision_id: uuid.UUID,
    node_id: uuid.UUID,
    question_id: str,
    new_answer: Answer,
    db: AsyncSession = Depends(get_db),
):
    """
    Modify a previous answer and recompute the canvas.

    This allows users to go back and change their answers.
    The canvas will be recomputed from that point forward.

    Args:
        decision_id: UUID of the decision
        node_id: UUID of the decision node
        question_id: ID of the question to modify
        new_answer: The new answer

    Returns:
        Updated canvas state

    Note: This is a simplified MVP implementation.
    Future: Full recomputation of subsequent questions.
    """
    # Get the node
    node = await db.get(DecisionNode, node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    if not node.conversation_state_json:
        raise HTTPException(
            status_code=400,
            detail="Conversation not initialized",
        )

    # For MVP: Simply update the answer in the history
    # Future: Recompute canvas from that point forward
    conversation_state = node.conversation_state_json
    asked_questions = conversation_state.get("asked_questions", [])

    # Find the question to modify
    question_found = False
    for qa in asked_questions:
        if qa.get("question", {}).get("id") == question_id:
            qa["answer"] = new_answer.model_dump()
            question_found = True
            break

    if not question_found:
        raise HTTPException(status_code=404, detail="Question not found in history")

    # Update node
    conversation_state["asked_questions"] = asked_questions
    node.conversation_state_json = conversation_state
    await db.commit()

    return {
        "canvas_state": conversation_state.get("canvas_state", {}),
        "message": "Answer updated successfully",
    }


def _infer_decision_type(situation_text: str) -> str:
    """
    Infer decision type from situation text.

    Simple keyword-based heuristic for MVP.
    Future: Use AI for more accurate classification.
    """
    text_lower = situation_text.lower()

    if any(word in text_lower for word in ["job", "career", "work", "offer", "position"]):
        return "career"
    elif any(word in text_lower for word in ["money", "invest", "buy", "spend", "financial", "budget"]):
        return "financial"
    elif any(word in text_lower for word in ["relationship", "partner", "dating", "marriage", "breakup"]):
        return "relationship"
    elif any(word in text_lower for word in ["business", "startup", "company", "venture"]):
        return "business"
    else:
        return "personal"
