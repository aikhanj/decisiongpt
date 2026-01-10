"""Observation model - stores AI-generated insights about users."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING
from enum import Enum

from sqlalchemy import String, Text, DateTime, ForeignKey, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.types import UUIDType, JSONType

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.decision import Decision


class ObservationType(str, Enum):
    """Types of observations the AI can make about users."""
    PATTERN = "pattern"           # Recurring behavior or thought pattern
    VALUE = "value"               # Something the user values/prioritizes
    STRENGTH = "strength"         # Capability or positive trait
    GROWTH_AREA = "growth_area"   # Challenge or area for development
    INSIGHT = "insight"           # Connection or realization


class ObservationFeedback(str, Enum):
    """User feedback on observations."""
    HELPFUL = "helpful"
    NOT_RELEVANT = "not_relevant"
    INCORRECT = "incorrect"


class Observation(Base):
    """AI-generated observation about a user.

    Observations are insights the AI makes about user patterns,
    values, strengths, and growth areas based on conversations.
    They can be surfaced in the Observations tab or inline during chat.
    """

    __tablename__ = "user_observations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("users.id"), nullable=False
    )
    decision_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("decisions.id", ondelete="SET NULL"), nullable=True
    )

    # Observation content
    observation_text: Mapped[str] = mapped_column(Text, nullable=False)
    observation_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default=ObservationType.INSIGHT.value
    )

    # Confidence score (0.0 to 1.0)
    confidence: Mapped[float] = mapped_column(
        Numeric(3, 2), nullable=False, default=0.70
    )

    # Categorization
    tags: Mapped[list | None] = mapped_column(JSONType, nullable=True, default=list)
    related_theme: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Tracking for surfacing
    surfaced_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_surfaced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # User feedback
    user_feedback: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Source of observation
    source: Mapped[str] = mapped_column(
        String(50), default="conversation", nullable=False
    )  # 'conversation', 'onboarding', 'outcome_review'

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="observations")
    decision: Mapped["Decision | None"] = relationship(
        "Decision", back_populates="observations"
    )

    def mark_surfaced(self) -> None:
        """Mark this observation as having been shown to the user."""
        self.surfaced_count += 1
        self.last_surfaced_at = datetime.utcnow()

    def set_feedback(self, feedback: ObservationFeedback) -> None:
        """Set user feedback on this observation."""
        self.user_feedback = feedback.value

    def is_high_confidence(self) -> bool:
        """Check if this observation has high confidence (>= 0.8)."""
        return float(self.confidence) >= 0.8

    def should_surface(self) -> bool:
        """Determine if this observation should be surfaced to the user.

        Returns True if:
        - High confidence
        - Not marked as incorrect
        - Not surfaced too recently (within last 24h) unless never surfaced
        """
        if self.user_feedback == ObservationFeedback.INCORRECT.value:
            return False
        if float(self.confidence) < 0.6:
            return False
        if self.last_surfaced_at:
            hours_since = (datetime.utcnow() - self.last_surfaced_at).total_seconds() / 3600
            if hours_since < 24 and self.surfaced_count > 0:
                return False
        return True

    def to_inline_text(self) -> str:
        """Format observation for inline display in chat."""
        prefix_map = {
            ObservationType.PATTERN.value: "I've noticed",
            ObservationType.VALUE.value: "It seems like you value",
            ObservationType.STRENGTH.value: "One of your strengths appears to be",
            ObservationType.GROWTH_AREA.value: "Something you might be working on is",
            ObservationType.INSIGHT.value: "I'm observing that",
        }
        prefix = prefix_map.get(self.observation_type, "I notice")
        return f"{prefix} {self.observation_text}"
