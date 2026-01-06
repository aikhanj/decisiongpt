from pydantic import BaseModel, Field
from typing import Optional, Literal


class CriteriaScores(BaseModel):
    """Scoring breakdown for a move."""

    self_respect: int = Field(..., ge=0, le=10)
    respect_for_her: int = Field(..., ge=0, le=10)
    clarity: int = Field(..., ge=0, le=10)
    leadership: int = Field(..., ge=0, le=10)
    warmth: int = Field(..., ge=0, le=10)
    progress: int = Field(..., ge=0, le=10)
    risk_management: int = Field(..., ge=0, le=10)


class Scripts(BaseModel):
    """Script variants for a move."""

    direct: str = Field(..., description="Direct, confident script")
    softer: str = Field(..., description="Softer, more cautious script")


class BranchResponse(BaseModel):
    """What to do based on her response."""

    next_move: str = Field(..., description="Suggested next action")
    script: str = Field(..., description="Suggested script for this branch")


class Branches(BaseModel):
    """Response branches for different reactions."""

    warm: BranchResponse
    neutral: BranchResponse
    cold: BranchResponse


class Move(BaseModel):
    """A move option from Phase 2."""

    move_id: Literal["A", "B", "C"] = Field(..., description="Move identifier")
    title: str = Field(..., description="Short title for the move")
    when_to_use: str = Field(..., description="1-2 line description of when to use")
    tradeoff: str = Field(..., description="1 line description of the tradeoff")
    gentleman_score: int = Field(
        ..., ge=0, le=100, description="Overall gentleman score"
    )
    risk_level: Literal["low", "med", "high"] = Field(..., description="Risk level")
    p_raw_progress: float = Field(
        ..., ge=0, le=1, description="Raw probability of progress"
    )
    p_calibrated_progress: float = Field(
        ..., ge=0, le=1, description="Calibrated probability of progress"
    )
    criteria_scores: CriteriaScores
    scripts: Scripts
    timing: str = Field(..., description="When to execute this move")
    branches: Branches


class MoveList(BaseModel):
    """List of moves from Phase 2."""

    moves: list[Move]
    cooldown_recommended: bool = False
    cooldown_reason: Optional[str] = None


class ExecutionPlan(BaseModel):
    """Execution plan for a chosen move."""

    steps: list[str] = Field(..., min_length=3, max_length=6)
    exact_message: str = Field(..., description="The exact message/opener to use")
    exit_line: str = Field(..., description="Exit line if not receptive")
    boundary_rule: str = Field(..., description="One boundary rule to follow")
