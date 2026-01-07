"""Schemas for background task management."""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.canvas import ChatResponse


class TaskStatus(str, Enum):
    """Status of a background task."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskType(str, Enum):
    """Type of background task."""
    CHAT_MESSAGE = "chat_message"
    START_DECISION = "start_decision"
    CHOOSE_OPTION = "choose_option"


class BackgroundTaskCreate(BaseModel):
    """Request to create a background task."""

    task_type: TaskType = Field(..., description="Type of task")
    decision_id: uuid.UUID = Field(..., description="Decision ID")
    node_id: uuid.UUID = Field(..., description="Node ID")
    input_data: dict = Field(default_factory=dict, description="Input data for the task")


class BackgroundTaskResponse(BaseModel):
    """Response with background task information."""

    id: uuid.UUID = Field(..., description="Unique task ID")
    task_type: TaskType = Field(..., description="Type of task")
    status: TaskStatus = Field(..., description="Current task status")
    created_at: datetime = Field(..., description="When the task was created")
    started_at: Optional[datetime] = Field(None, description="When processing started")
    completed_at: Optional[datetime] = Field(None, description="When task completed")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "task_type": "chat_message",
                "status": "pending",
                "created_at": "2026-01-06T12:00:00Z",
                "started_at": None,
                "completed_at": None,
            }
        }


class TaskStatusResponse(BaseModel):
    """Detailed status response for polling."""

    id: uuid.UUID = Field(..., description="Task ID")
    status: TaskStatus = Field(..., description="Current status")
    result: Optional[ChatResponse] = Field(None, description="Result if completed")
    error: Optional[str] = Field(None, description="Error message if failed")
    progress_percentage: Optional[int] = Field(None, description="Progress percentage (0-100)")
    retry_count: int = Field(default=0, description="Number of retry attempts")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "completed",
                "result": {
                    "message": {
                        "id": "msg_1",
                        "role": "assistant",
                        "content": "Here's my analysis...",
                        "timestamp": "2026-01-06T12:00:05Z",
                    },
                    "canvas_state": {"statement": "Should I accept the job offer?"},
                    "phase": "clarify",
                },
                "error": None,
                "progress_percentage": 100,
                "retry_count": 0,
            }
        }


class PendingTasksResponse(BaseModel):
    """Response with list of pending tasks for a node."""

    tasks: list[BackgroundTaskResponse] = Field(
        default_factory=list, description="List of pending/processing tasks"
    )
