"""BackgroundTask model for tracking async task processing."""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import String, DateTime, ForeignKey, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.types import UUIDType, JSONType


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


class BackgroundTask(Base):
    """Background task - tracks async job processing for AI operations."""

    __tablename__ = "background_tasks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, primary_key=True, default=uuid.uuid4
    )
    celery_task_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True, index=True
    )
    task_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=TaskStatus.PENDING.value, index=True
    )

    # References
    decision_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("decisions.id", ondelete="CASCADE"), nullable=False
    )
    node_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("decision_nodes.id", ondelete="CASCADE"), nullable=False
    )

    # Data storage
    input_data: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    result_data: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Retry tracking
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    decision: Mapped["Decision"] = relationship("Decision")
    node: Mapped["DecisionNode"] = relationship("DecisionNode")
