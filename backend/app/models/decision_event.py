import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.types import UUIDType, JSONType


class EventType(str, Enum):
    CREATED = "created"
    ANSWERED = "answered"
    MOVED = "moved"
    CHOSEN = "chosen"
    BRANCHED = "branched"
    RESOLVED = "resolved"


class DecisionEvent(Base):
    """Decision event - append-only audit log for decision changes."""

    __tablename__ = "decision_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, primary_key=True, default=uuid.uuid4
    )
    decision_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("decisions.id", ondelete="CASCADE"), nullable=False
    )
    node_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("decision_nodes.id"), nullable=True
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    payload_json: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    # Relationships
    decision: Mapped["Decision"] = relationship("Decision", back_populates="events")
    node: Mapped["DecisionNode | None"] = relationship(
        "DecisionNode", back_populates="events"
    )
