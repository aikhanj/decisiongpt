from pydantic import BaseModel, Field
from typing import Optional, Literal

from app.schemas.question import Question
from app.schemas.move import Move


class Phase1Response(BaseModel):
    """Expected response from AI for Phase 1."""

    summary: str = Field(..., description="Brief summary of the situation")
    situation_type: Literal[
        "gym_approach",
        "double_text",
        "kiss_timing",
        "first_date_plan",
        "generic_relationship_next_step",
    ] = Field(..., description="Detected situation type")
    mood_detected: Literal[
        "calm", "anxious", "angry", "sad", "horny", "tired", "confident", "neutral"
    ] = Field(..., description="Detected mood state")
    questions: list[Question] = Field(
        ..., min_length=5, max_length=15, description="Questions to ask the user"
    )


class Phase2Response(BaseModel):
    """Expected response from AI for Phase 2."""

    moves: list[Move] = Field(
        ..., min_length=2, max_length=3, description="Move options"
    )
    cooldown_recommended: bool = Field(
        False, description="Whether a cooldown is recommended"
    )
    cooldown_reason: Optional[str] = Field(
        None, description="Reason for cooldown recommendation"
    )


class ExecutionPlanResponse(BaseModel):
    """Expected response from AI for execution plan generation."""

    steps: list[str] = Field(..., min_length=3, max_length=6)
    exact_message: str
    exit_line: str
    boundary_rule: str
