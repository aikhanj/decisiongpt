"""User Context Service - Builds compact user context for AI prompt injection."""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.user_profile import UserProfile
from app.models.observation import Observation, ObservationType
from app.models.decision import Decision


class UserContextService:
    """Service for building and managing user context for AI personalization.

    This service builds a compact context string (~400 tokens) that gets
    prepended to AI system prompts, enabling personalized interactions
    without requiring RAG/vector search on every request.
    """

    TOKEN_BUDGET = 400  # Approximate token limit for context

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_profile(self, user_id: uuid.UUID) -> UserProfile:
        """Get existing profile or create a new one for the user."""
        result = await self.db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()

        if not profile:
            profile = UserProfile(user_id=user_id)
            self.db.add(profile)
            await self.db.commit()
            await self.db.refresh(profile)

        return profile

    async def build_user_context(
        self,
        user_id: uuid.UUID,
        decision_context: Optional[str] = None,
        include_recent_decisions: bool = True,
    ) -> str:
        """Build a compact context string for the current user.

        Args:
            user_id: The user's ID
            decision_context: Optional current decision text for relevance matching
            include_recent_decisions: Whether to include recent decision summaries

        Returns:
            Formatted context string like:
            ---
            USER CONTEXT:
            Name: Alex | Age: 26-30 | Occupation: Product Manager (Tech/Startup)
            Values: Growth, family, financial security
            Patterns: Tends to overthink decisions, values data, struggles with saying no
            Recent: Made decision about job offer (chose to stay), working on delegation
            ---
        """
        profile = await self.get_or_create_profile(user_id)

        # If we have a cached summary and it's recent, use it
        if profile.context_summary and profile.context_summary_updated_at:
            age = datetime.now(timezone.utc) - profile.context_summary_updated_at
            if age < timedelta(hours=24):
                return profile.context_summary

        # Build fresh context
        context_parts = []

        # Essential info
        essential = profile.get_essential_summary()
        if essential:
            context_parts.append(essential)

        # Values
        values = profile.get_values()
        if values:
            context_parts.append(f"Values: {', '.join(values[:5])}")

        # Patterns from observations
        patterns = await self._get_pattern_summary(user_id)
        if patterns:
            context_parts.append(f"Patterns: {patterns}")

        # Recent decisions
        if include_recent_decisions:
            recent = await self._get_recent_decisions_summary(user_id)
            if recent:
                context_parts.append(f"Recent: {recent}")

        # Relevant context if decision text provided
        if decision_context:
            relevant = await self._get_relevant_observations(user_id, decision_context)
            if relevant:
                context_parts.append(f"Relevant: {relevant}")

        if not context_parts:
            return ""

        return "USER CONTEXT:\n" + "\n".join(context_parts)

    async def _get_pattern_summary(self, user_id: uuid.UUID, limit: int = 3) -> str:
        """Get a summary of observed patterns for the user."""
        result = await self.db.execute(
            select(Observation)
            .where(
                Observation.user_id == user_id,
                Observation.observation_type.in_([
                    ObservationType.PATTERN.value,
                    ObservationType.GROWTH_AREA.value,
                ]),
                Observation.user_feedback != "incorrect",
            )
            .order_by(Observation.confidence.desc())
            .limit(limit)
        )
        observations = result.scalars().all()

        if not observations:
            return ""

        patterns = [obs.observation_text for obs in observations]
        return "; ".join(patterns)

    async def _get_recent_decisions_summary(
        self, user_id: uuid.UUID, limit: int = 2
    ) -> str:
        """Get a summary of recent decisions."""
        result = await self.db.execute(
            select(Decision)
            .where(Decision.user_id == user_id)
            .order_by(Decision.created_at.desc())
            .limit(limit)
        )
        decisions = result.scalars().all()

        if not decisions:
            return ""

        summaries = []
        for decision in decisions:
            title = decision.title or decision.situation_text[:50]
            status = decision.status
            summaries.append(f"{title} ({status})")

        return "; ".join(summaries)

    async def _get_relevant_observations(
        self, user_id: uuid.UUID, context: str, limit: int = 2
    ) -> str:
        """Get observations potentially relevant to the current context.

        This is a simple keyword-based approach. For production, you might
        use embeddings/vector similarity if available.
        """
        # Extract key topics from context (simple approach)
        keywords = self._extract_keywords(context)
        if not keywords:
            return ""

        # Find observations with matching tags or themes
        result = await self.db.execute(
            select(Observation)
            .where(
                Observation.user_id == user_id,
                Observation.user_feedback != "incorrect",
                Observation.confidence >= 0.6,
            )
            .order_by(Observation.confidence.desc())
            .limit(20)
        )
        observations = result.scalars().all()

        # Simple relevance scoring
        relevant = []
        for obs in observations:
            text_lower = obs.observation_text.lower()
            tags = obs.tags or []
            theme = (obs.related_theme or "").lower()

            score = 0
            for keyword in keywords:
                if keyword in text_lower:
                    score += 2
                if keyword in theme:
                    score += 1
                if keyword in [t.lower() for t in tags]:
                    score += 1

            if score > 0:
                relevant.append((obs, score))

        relevant.sort(key=lambda x: x[1], reverse=True)
        top = [obs.observation_text for obs, _ in relevant[:limit]]

        return "; ".join(top)

    def _extract_keywords(self, text: str) -> list[str]:
        """Extract potential keywords from text for matching.

        Simple approach - in production, consider using NLP.
        """
        # Common decision-related keywords
        keyword_categories = {
            "career": ["job", "career", "work", "promotion", "salary", "boss", "colleague"],
            "startup": ["startup", "business", "founder", "invest", "equity", "product"],
            "relationship": ["relationship", "dating", "partner", "marriage", "love"],
            "health": ["health", "fitness", "diet", "exercise", "weight", "gym"],
            "finance": ["money", "invest", "save", "budget", "debt", "financial"],
            "education": ["school", "degree", "study", "course", "learn", "university"],
        }

        text_lower = text.lower()
        found = []

        for category, words in keyword_categories.items():
            for word in words:
                if word in text_lower:
                    found.append(category)
                    break

        return list(set(found))

    async def refresh_context_summary(self, user_id: uuid.UUID) -> str:
        """Refresh and cache the user's context summary.

        Call this after significant events like:
        - Decision resolution
        - New observations added
        - Profile update
        """
        profile = await self.get_or_create_profile(user_id)

        # Build fresh context
        context = await self.build_user_context(
            user_id,
            include_recent_decisions=True,
        )

        # Cache it
        profile.context_summary = context
        profile.context_summary_updated_at = datetime.now(timezone.utc)
        await self.db.commit()

        return context

    async def update_profile_from_conversation(
        self,
        user_id: uuid.UUID,
        learned_data: dict,
    ) -> None:
        """Update user profile with data learned from conversation.

        Args:
            user_id: The user's ID
            learned_data: Dict with fields like:
                - name: str
                - occupation: str
                - values: list[str] (will be merged)
                - patterns: list[str] (will be merged)
        """
        profile = await self.get_or_create_profile(user_id)

        # Update essential fields if provided
        if "name" in learned_data and learned_data["name"]:
            profile.name = learned_data["name"]
        if "occupation" in learned_data and learned_data["occupation"]:
            profile.occupation = learned_data["occupation"]
        if "industry" in learned_data and learned_data["industry"]:
            profile.industry = learned_data["industry"]
        if "age_range" in learned_data and learned_data["age_range"]:
            profile.age_range = learned_data["age_range"]

        # Merge list fields into extended profile
        for field in ["values", "goals", "recurring_themes", "strengths", "growth_areas"]:
            if field in learned_data and learned_data[field]:
                for item in learned_data[field]:
                    profile.add_to_list_field(field, item)

        # Invalidate cached summary
        profile.context_summary_updated_at = None

        await self.db.commit()
