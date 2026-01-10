"""User profile model - stores persistent user context for AI personalization."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.types import UUIDType, JSONType

if TYPE_CHECKING:
    from app.models.user import User


class UserProfile(Base):
    """User profile for personalization and memory.

    Stores essential user information and extended profile data
    that gets injected into AI prompts for personalized interactions.
    """

    __tablename__ = "user_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("users.id"), nullable=False, unique=True
    )

    # Essential fields (commonly queried/displayed)
    name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    age_range: Mapped[str | None] = mapped_column(String(20), nullable=True)  # "20-25", "26-30", etc.
    occupation: Mapped[str | None] = mapped_column(String(100), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(100), nullable=True)
    specialty: Mapped[str | None] = mapped_column(String(200), nullable=True)  # major, field of study

    # Extended profile as flexible JSON
    # Structure: {
    #   "goals": ["career growth", "work-life balance"],
    #   "values": ["family", "integrity"],
    #   "recurring_themes": ["anxiety about change", "perfectionism"],
    #   "strengths": ["analytical thinking", "communication"],
    #   "growth_areas": ["delegation", "assertiveness"],
    #   "decision_styles": { "risk_tolerance": 0.4, ... },
    #   "life_context": { "relationship_status": "married", ... }
    # }
    extended_profile: Mapped[dict | None] = mapped_column(
        JSONType, nullable=True, default=dict
    )

    # AI-generated context summary for injection into prompts
    # Rebuilt periodically from profile + observations
    context_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    context_summary_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Onboarding state
    onboarding_completed: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    onboarding_step: Mapped[str | None] = mapped_column(
        String(50), default="not_started", nullable=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="profile")

    def get_display_name(self) -> str:
        """Get the user's display name, falling back to 'there' if not set."""
        return self.name or self.user.display_name or "there"

    def get_essential_summary(self) -> str:
        """Build a one-line summary of essential profile info."""
        parts = []
        if self.name:
            parts.append(f"Name: {self.name}")
        if self.age_range:
            parts.append(f"Age: {self.age_range}")
        if self.occupation:
            occ = self.occupation
            if self.industry:
                occ += f" ({self.industry})"
            parts.append(f"Occupation: {occ}")
        if self.specialty:
            parts.append(f"Specialty: {self.specialty}")
        return " | ".join(parts) if parts else ""

    def get_values(self) -> list[str]:
        """Get user's stated values from extended profile."""
        if not self.extended_profile:
            return []
        return self.extended_profile.get("values", [])

    def get_patterns(self) -> list[str]:
        """Get observed recurring themes/patterns."""
        if not self.extended_profile:
            return []
        return self.extended_profile.get("recurring_themes", [])

    def update_extended_field(self, field: str, value: any) -> None:
        """Update a specific field in the extended profile."""
        if self.extended_profile is None:
            self.extended_profile = {}
        self.extended_profile[field] = value

    def add_to_list_field(self, field: str, item: str) -> None:
        """Add an item to a list field in extended profile (deduplicated)."""
        if self.extended_profile is None:
            self.extended_profile = {}
        if field not in self.extended_profile:
            self.extended_profile[field] = []
        if item not in self.extended_profile[field]:
            self.extended_profile[field].append(item)
