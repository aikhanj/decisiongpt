from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field
from typing import Optional, Literal

from app.schemas.question import Question
from app.schemas.move import Move, ExecutionPlan


class DecisionCreate(BaseModel):
    """Request to create a new decision."""

    situation_text: str = Field(..., min_length=10, max_length=5000)


class Answer(BaseModel):
    """User's answer to a question."""

    question_id: str
    value: str | int | bool


class AnswerRequest(BaseModel):
    """Request to submit answers."""

    answers: list[Answer]


class ChooseMoveRequest(BaseModel):
    """Request to choose a move."""

    move_id: str = Field(..., pattern="^[ABC]$")


class DecisionNodeResponse(BaseModel):
    """Response for a decision node."""

    id: UUID
    decision_id: UUID
    parent_node_id: Optional[UUID] = None
    phase: str
    questions_json: Optional[dict] = None
    answers_json: Optional[dict] = None
    moves_json: Optional[dict] = None
    chosen_move_id: Optional[str] = None
    execution_plan_json: Optional[dict] = None
    mood_state: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DecisionResponse(BaseModel):
    """Response for a decision."""

    id: UUID
    user_id: UUID
    title: Optional[str] = None
    situation_text: str
    situation_type: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime
    nodes: list[DecisionNodeResponse] = []

    class Config:
        from_attributes = True


class DecisionListResponse(BaseModel):
    """Response for listing decisions."""

    decisions: list[DecisionResponse]


class Phase1APIResponse(BaseModel):
    """API response for Phase 1."""

    decision: DecisionResponse
    node: DecisionNodeResponse
    summary: str
    situation_type: str
    mood_detected: str
    questions: list[Question]


class Phase2APIResponse(BaseModel):
    """API response for Phase 2."""

    node: DecisionNodeResponse
    moves: list[Move]
    cooldown_recommended: bool
    cooldown_reason: Optional[str] = None


class ExecutionAPIResponse(BaseModel):
    """API response for execution plan."""

    node: DecisionNodeResponse
    execution_plan: ExecutionPlan
