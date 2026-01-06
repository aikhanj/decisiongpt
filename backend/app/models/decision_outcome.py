import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import String, Boolean, Integer, DateTime, ForeignKey, Numeric, Text, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DecisionOutcome(Base):
    """Decision outcome - user feedback on move execution."""

    __tablename__ = "decision_outcomes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    node_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("decision_nodes.id", ondelete="CASCADE"), nullable=False
    )
    progress_yesno: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    sentiment_2h: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sentiment_24h: Mapped[int | None] = mapped_column(Integer, nullable=True)
    brier_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    __table_args__ = (
        CheckConstraint("sentiment_2h BETWEEN -2 AND 2", name="check_sentiment_2h_range"),
        CheckConstraint("sentiment_24h BETWEEN -2 AND 2", name="check_sentiment_24h_range"),
    )

    # Relationships
    node: Mapped["DecisionNode"] = relationship("DecisionNode", back_populates="outcome")
