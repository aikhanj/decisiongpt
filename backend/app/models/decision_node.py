import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class NodePhase(str, Enum):
    CLARIFY = "clarify"
    MOVES = "moves"
    EXECUTE = "execute"


class MoodState(str, Enum):
    CALM = "calm"
    ANXIOUS = "anxious"
    ANGRY = "angry"
    SAD = "sad"
    HORNY = "horny"
    TIRED = "tired"
    CONFIDENT = "confident"
    NEUTRAL = "neutral"


class DecisionNode(Base):
    """Decision node - represents a point in the decision tree."""

    __tablename__ = "decision_nodes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    decision_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("decisions.id", ondelete="CASCADE"), nullable=False
    )
    parent_node_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("decision_nodes.id"), nullable=True
    )
    phase: Mapped[str] = mapped_column(String(20), nullable=False)

    # State data
    state_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    questions_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    answers_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    moves_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    chosen_move_id: Mapped[str | None] = mapped_column(String(10), nullable=True)
    execution_plan_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Metadata
    mood_state: Mapped[str | None] = mapped_column(String(20), nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Versioning
    policy_version: Mapped[str | None] = mapped_column(String(20), nullable=True)
    prompt_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    model_version: Mapped[str | None] = mapped_column(String(50), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    # Relationships
    decision: Mapped["Decision"] = relationship("Decision", back_populates="nodes")
    parent_node: Mapped["DecisionNode | None"] = relationship(
        "DecisionNode", remote_side=[id], back_populates="child_nodes"
    )
    child_nodes: Mapped[list["DecisionNode"]] = relationship(
        "DecisionNode", back_populates="parent_node", lazy="selectin"
    )
    events: Mapped[list["DecisionEvent"]] = relationship(
        "DecisionEvent", back_populates="node", lazy="selectin"
    )
    outcome: Mapped["DecisionOutcome | None"] = relationship(
        "DecisionOutcome", back_populates="node", uselist=False
    )
    memory: Mapped["Memory | None"] = relationship(
        "Memory", back_populates="node", uselist=False
    )
