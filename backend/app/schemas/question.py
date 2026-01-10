from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
from enum import Enum


class Question(BaseModel):
    """A question for the user to answer."""

    id: str = Field(..., description="Unique identifier for the question")
    question: str = Field(..., description="The question text")
    answer_type: Literal["yes_no", "text", "number", "single_select"] = Field(
        ..., description="Type of answer expected"
    )
    choices: Optional[list[str]] = Field(
        None, description="Options for single_select type"
    )
    why_this_question: str = Field(
        ..., description="Tooltip explaining why this question is asked"
    )
    what_it_changes: str = Field(
        ..., description="Tooltip explaining what this answer affects"
    )
    priority: int = Field(
        ..., ge=0, le=100, description="Priority score for ordering questions"
    )


class QuestionList(BaseModel):
    """List of questions from Phase 1."""

    questions: list[Question]


# ============================================================================
# Adaptive Questioning Schemas
# ============================================================================


class QuestioningMode(str, Enum):
    """Mode for adaptive questioning."""

    QUICK = "quick"  # 5 questions max
    DEEP = "deep"  # 15 questions max


class CandidateQuestion(Question):
    """A question with VoI (Value of Information) scoring."""

    voi_score: float = Field(default=0.0, ge=0.0, le=100.0, description="Value of Information score (0-100)")
    targets_canvas_field: str = Field(..., description="Canvas field this question targets (e.g., 'criteria', 'constraints')")
    uncertainty_reduction_estimate: float = Field(default=0.0, ge=0.0, le=1.0, description="Estimated uncertainty reduction (0-1)")
    critical_variable: bool = Field(default=False, description="Whether this targets a critical missing variable")
    heuristic_trigger: Optional[str] = Field(None, description="Heuristic that triggered this question (if any)")


class Answer(BaseModel):
    """An answer to a question."""

    question_id: str = Field(..., description="ID of the question being answered")
    value: str | int | bool = Field(..., description="The answer value")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="User's confidence in their answer (0-1)")


class QuestionWithAnswer(BaseModel):
    """A question that has been answered."""

    question: CandidateQuestion = Field(..., description="The question")
    answer: Answer = Field(..., description="The answer")
    answered_at: datetime = Field(default_factory=datetime.utcnow, description="When the question was answered")
    canvas_impact: list[str] = Field(default_factory=list, description="Canvas fields updated by this answer")


class ConversationState(BaseModel):
    """Tracks state of conversational adaptive questioning."""

    mode: QuestioningMode = Field(..., description="Questioning mode (quick or deep)")
    question_cap: int = Field(..., ge=1, le=20, description="Maximum number of questions")
    questions_asked: int = Field(default=0, ge=0, description="Number of questions asked so far")

    # Question pools
    candidate_questions: list[CandidateQuestion] = Field(default_factory=list, description="Pool of candidate questions")
    asked_questions: list[QuestionWithAnswer] = Field(default_factory=list, description="Questions that have been asked and answered")
    current_question: Optional[CandidateQuestion] = Field(None, description="Current question being asked")

    # Canvas state (imported dynamically to avoid circular import)
    canvas_state: dict = Field(default_factory=dict, description="Current canvas state")

    # VoI tracking
    last_canvas_uncertainty: float = Field(default=1.0, ge=0.0, le=1.0, description="Last measured canvas uncertainty")
    uncertainty_reduction_history: list[float] = Field(default_factory=list, description="History of uncertainty reductions")

    # Stopping logic
    ready_for_options: bool = Field(default=False, description="Whether ready to generate options")
    stop_reason: Optional[str] = Field(None, description="Reason for stopping (if stopped)")


class NextQuestionResponse(BaseModel):
    """Response from answering a question."""

    next_question: Optional[CandidateQuestion] = Field(None, description="Next question (null if stopping)")
    canvas_update: dict = Field(..., description="Updated canvas state")
    ready_for_options: bool = Field(..., description="Whether ready to proceed to options")
    questions_remaining: Optional[int] = Field(None, description="Estimated questions remaining")
    progress: float = Field(..., ge=0.0, le=1.0, description="Progress toward completion (0-1)")
    stop_reason: Optional[str] = Field(None, description="Reason for stopping (if stopping)")


class AdaptiveQuestionResponse(BaseModel):
    """Response from starting adaptive questioning."""

    next_question: CandidateQuestion = Field(..., description="First question to ask")
    canvas_state: dict = Field(..., description="Initial canvas state")
    conversation_state: ConversationState = Field(..., description="Conversation state")
