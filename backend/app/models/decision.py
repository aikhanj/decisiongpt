import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DecisionStatus(str, Enum):
    ACTIVE = "active"
    RESOLVED = "resolved"
    ARCHIVED = "archived"


class SituationType(str, Enum):
    GYM_APPROACH = "gym_approach"
    DOUBLE_TEXT = "double_text"
    KISS_TIMING = "kiss_timing"
    FIRST_DATE_PLAN = "first_date_plan"
    GENERIC = "generic_relationship_next_step"


class Decision(Base):
    """Decision model - represents a user's decision-making session."""

    __tablename__ = "decisions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    situation_text: Mapped[str] = mapped_column(Text, nullable=False)
    situation_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), default=DecisionStatus.ACTIVE.value
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="decisions")
    nodes: Mapped[list["DecisionNode"]] = relationship(
        "DecisionNode", back_populates="decision", lazy="selectin"
    )
    events: Mapped[list["DecisionEvent"]] = relationship(
        "DecisionEvent", back_populates="decision", lazy="selectin"
    )
