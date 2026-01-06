from pydantic import BaseModel, Field
from typing import Optional, Literal

from app.schemas.question import Question
from app.schemas.canvas import Option


# Decision Canvas - generalized decision types
DecisionType = Literal[
    "career",
    "financial",
    "business",
    "personal",
    "relationship",
    "health",
    "education",
    "major_purchase",
    "other",
]


class Phase1Response(BaseModel):
    """Expected response from AI for Phase 1 - Decision Canvas."""

    summary: str = Field(..., description="Brief summary of the decision situation")
    situation_type: DecisionType = Field(
        default="other",
        description="Type of decision being made"
    )
    mood_detected: Literal[
        "calm", "anxious", "stressed", "excited", "uncertain", "confident", "neutral"
    ] = Field(default="neutral", description="Detected emotional state")
    questions: list[Question] = Field(
        ..., min_length=3, max_length=10, description="Clarifying questions to ask"
    )

    # Decision Canvas additions
    decision_statement: Optional[str] = Field(
        None, description="Clear statement of the decision to be made"
    )
    context_bullets: list[str] = Field(
        default_factory=list, description="Key context points extracted"
    )
    initial_constraints: list[dict] = Field(
        default_factory=list, description="Initial constraints identified"
    )


class Phase2Response(BaseModel):
    """Expected response from AI for Phase 2."""

    options: list[Option] = Field(
        ..., min_length=2, max_length=3, description="Decision options"
    )
    canvas_state_update: Optional[dict] = Field(
        None, description="Updates to canvas state (risks, next_action)"
    )


class ExecutionPlanResponse(BaseModel):
    """Expected response from AI for execution plan generation."""

    steps: list[str] = Field(..., min_length=3, max_length=6)
    exact_message: str
    exit_line: str
    boundary_rule: str
