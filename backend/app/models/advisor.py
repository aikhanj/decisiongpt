"""Advisor model for custom AI personas."""
import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.types import UUIDType, JSONType


class Advisor(Base):
    """Custom advisor persona created by users."""

    __tablename__ = "advisors"

    id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, primary_key=True, default=uuid.uuid4
    )

    # Owner (null for system advisors)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("users.id"), nullable=True
    )

    # Identity
    slug: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    avatar: Mapped[str] = mapped_column(String(50), nullable=False, default="🤖")
    description: Mapped[str] = mapped_column(String(500), nullable=False)

    # Classification (stored as JSON arrays for cross-database compatibility)
    expertise_keywords: Mapped[list[str]] = mapped_column(
        JSONType, nullable=False, default=list
    )
    personality_traits: Mapped[list[str]] = mapped_column(
        JSONType, nullable=False, default=list
    )

    # Prompt
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)

    # Flags
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    user: Mapped["User"] = relationship("User", lazy="selectin")
