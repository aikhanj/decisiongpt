from pydantic import BaseModel, Field
from typing import Optional, Literal


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
