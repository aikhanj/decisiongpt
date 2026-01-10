"""Schemas for Decision Canvas chat and canvas state."""
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """A single chat message."""

    id: str = Field(..., description="Unique message ID")
    role: Literal["user", "assistant", "system"] = Field(..., description="Message role")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    # Optional fields for assistant messages with questions
    question_reason: Optional[str] = Field(
        None, description="Why this question matters (shown as tooltip)"
    )
    suggested_options: Optional[list[str]] = Field(
        None, description="Quick reply options for the user to click"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "msg_1",
                "role": "user",
                "content": "I'm trying to decide whether to accept a job offer...",
                "timestamp": "2026-01-06T12:00:00Z",
            }
        }


class Constraint(BaseModel):
    """A decision constraint (hard or soft)."""

    id: str = Field(..., description="Unique constraint ID")
    text: str = Field(..., description="Constraint description")
    type: Literal["hard", "soft"] = Field(..., description="Constraint type")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "c1",
                "text": "Must be able to work remotely at least 2 days per week",
                "type": "hard",
            }
        }


class Criterion(BaseModel):
    """A decision criterion with weight."""

    id: str = Field(..., description="Unique criterion ID")
    name: str = Field(..., description="Criterion name")
    weight: int = Field(ge=1, le=10, default=5, description="Weight 1-10")
    description: Optional[str] = Field(None, description="Optional description")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "cr1",
                "name": "Work-life balance",
                "weight": 8,
                "description": "Time for family and hobbies",
            }
        }


class Risk(BaseModel):
    """A risk associated with an option."""

    id: str = Field(..., description="Unique risk ID")
    description: str = Field(..., description="Risk description")
    severity: Literal["low", "medium", "high"] = Field(..., description="Risk severity")
    mitigation: Optional[str] = Field(None, description="How to mitigate this risk")
    option_id: Optional[str] = Field(None, description="Associated option ID")


class CanvasState(BaseModel):
    """The current state of the decision canvas."""

    statement: Optional[str] = Field(None, description="Decision statement")
    context_bullets: list[str] = Field(default_factory=list, description="Context bullet points")
    constraints: list[Constraint] = Field(default_factory=list, description="Constraints")
    criteria: list[Criterion] = Field(default_factory=list, description="Decision criteria")
    risks: list[Risk] = Field(default_factory=list, description="Identified risks")
    next_action: Optional[str] = Field(None, description="Next action to take")

    class Config:
        json_schema_extra = {
            "example": {
                "statement": "Should I accept the senior engineer role at TechCorp?",
                "context_bullets": [
                    "Currently employed at StartupXYZ for 3 years",
                    "TechCorp offers 30% salary increase",
                    "Would require relocation to Austin",
                ],
                "constraints": [
                    {"id": "c1", "text": "Must maintain healthcare coverage", "type": "hard"},
                    {"id": "c2", "text": "Prefer to stay in current city", "type": "soft"},
                ],
                "criteria": [
                    {"id": "cr1", "name": "Salary", "weight": 7},
                    {"id": "cr2", "name": "Growth potential", "weight": 9},
                ],
                "risks": [],
                "next_action": "Answer clarifying questions about role responsibilities",
            }
        }


class Option(BaseModel):
    """A decision option."""

    id: str = Field(..., description="Option ID (A, B, C)")
    title: str = Field(..., description="Option title")
    good_if: str = Field(..., description="This option is good if...")
    bad_if: str = Field(..., description="This option is bad if...")
    pros: list[str] = Field(default_factory=list, description="Pros")
    cons: list[str] = Field(default_factory=list, description="Cons")
    risks: list[str] = Field(default_factory=list, description="Risk tags")
    steps: list[str] = Field(default_factory=list, description="Implementation steps")
    confidence: Literal["low", "medium", "high"] = Field(..., description="Confidence level")
    confidence_reasoning: Optional[str] = Field(None, description="Why this confidence level")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "A",
                "title": "Accept the offer",
                "good_if": "Growth and salary are top priorities",
                "bad_if": "Location flexibility is critical",
                "pros": ["30% salary increase", "Larger team", "Better benefits"],
                "cons": ["Requires relocation", "Unknown team culture"],
                "risks": ["culture_fit", "relocation_stress"],
                "steps": [
                    "Negotiate start date",
                    "Request relocation assistance",
                    "Give 2-week notice",
                ],
                "confidence": "medium",
                "confidence_reasoning": "Limited information about team dynamics",
            }
        }


class IfThenBranch(BaseModel):
    """An if-then branch in the commit plan."""

    condition: str = Field(..., description="The condition (e.g., 'success', 'failure')")
    action: str = Field(..., description="What to do if condition is met")


class CommitStep(BaseModel):
    """A step in the commit plan."""

    number: int = Field(..., description="Step number")
    title: str = Field(..., description="Step title")
    description: Optional[str] = Field(None, description="Step description")
    branches: list[IfThenBranch] = Field(default_factory=list, description="If-then branches")
    completed: bool = Field(default=False, description="Whether step is completed")


class CommitPlan(BaseModel):
    """The commit plan after choosing an option."""

    chosen_option_id: str = Field(..., description="ID of chosen option")
    chosen_option_title: str = Field(..., description="Title of chosen option")
    steps: list[CommitStep] = Field(default_factory=list, description="Steps to execute")

    class Config:
        json_schema_extra = {
            "example": {
                "chosen_option_id": "A",
                "chosen_option_title": "Accept the offer",
                "steps": [
                    {
                        "number": 1,
                        "title": "Negotiate start date and relocation package",
                        "description": "Call HR to discuss flexibility",
                        "branches": [
                            {"condition": "success", "action": "Proceed to step 2"},
                            {
                                "condition": "failure",
                                "action": "Consider counter-offer or decline",
                            },
                        ],
                        "completed": False,
                    }
                ],
            }
        }


class ChatRequest(BaseModel):
    """Request to send a chat message."""

    message: str = Field(..., min_length=1, max_length=5000, description="User message")


class AdvisorInfo(BaseModel):
    """Information about the advisor responding."""

    id: str = Field(..., description="Advisor ID")
    name: str = Field(..., description="Advisor display name")
    avatar: str = Field(..., description="Advisor avatar emoji or URL")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "dating",
                "name": "The Gentleman",
                "avatar": "🎩",
            }
        }


class ChatResponse(BaseModel):
    """Response from chat endpoint."""

    message: ChatMessage = Field(..., description="Assistant's response message")
    canvas_state: CanvasState = Field(..., description="Updated canvas state")
    phase: str = Field(..., description="Current phase (clarify/options/committed/resolved)")
    questions: Optional[list] = Field(None, description="Questions if in clarify phase")
    options: Optional[list[Option]] = Field(None, description="Options if in options phase")
    commit_plan: Optional[CommitPlan] = Field(None, description="Commit plan if committed")
    advisor: Optional[AdvisorInfo] = Field(None, description="The advisor who responded")
