"""Observation Service - Generates and manages AI observations about users."""

import uuid
from datetime import datetime, timedelta
from typing import Optional

from pydantic import BaseModel
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.observation import Observation, ObservationType, ObservationFeedback
from app.ai.gateway import AIGateway


class GeneratedObservation(BaseModel):
    """Schema for AI-generated observation."""
    observation_text: str
    observation_type: str  # pattern, value, strength, growth_area, insight
    confidence: float
    related_theme: Optional[str] = None
    tags: list[str] = []


class ObservationBatch(BaseModel):
    """Batch of observations from conversation analysis."""
    observations: list[GeneratedObservation]


class ObservationService:
    """Service for generating and managing AI observations about users.

    Observations are insights the AI makes about user patterns,
    values, strengths, and growth areas based on conversations.
    """

    def __init__(self, db: AsyncSession, api_key: Optional[str] = None):
        self.db = db
        self.ai = AIGateway(api_key) if api_key else None

    async def generate_observations_from_conversation(
        self,
        user_id: uuid.UUID,
        decision_id: Optional[uuid.UUID],
        chat_messages: list[dict],
        existing_observations: Optional[list[str]] = None,
    ) -> list[Observation]:
        """Analyze conversation and generate observations.

        Called after significant conversations (e.g., 5+ exchanges,
        decision resolution).

        Args:
            user_id: The user's ID
            decision_id: Optional related decision ID
            chat_messages: List of chat messages to analyze
            existing_observations: List of existing observation texts to avoid duplication

        Returns:
            List of newly created Observation objects
        """
        if not self.ai:
            return []

        # Need at least 3 exchanges to have enough signal
        user_messages = [m for m in chat_messages if m.get("role") == "user"]
        if len(user_messages) < 3:
            return []

        # Format conversation for analysis
        conversation_text = "\n".join([
            f"{msg.get('role', 'unknown').upper()}: {msg.get('content', '')}"
            for msg in chat_messages[-20:]  # Last 20 messages
        ])

        # Get existing observations to avoid duplicates
        existing = existing_observations or []
        if not existing:
            result = await self.db.execute(
                select(Observation.observation_text)
                .where(Observation.user_id == user_id)
                .limit(50)
            )
            existing = [row[0] for row in result.fetchall()]

        existing_text = "\n".join([f"- {obs}" for obs in existing]) if existing else "None"

        prompt = f"""Analyze this conversation and identify psychological observations about the user.

## Conversation:
{conversation_text}

## Existing Observations (avoid duplicating):
{existing_text}

## Look For:
1. **Patterns**: Recurring behaviors, thought patterns, decision approaches
2. **Values**: What they prioritize, what matters to them
3. **Strengths**: Capabilities they demonstrate
4. **Growth Areas**: Challenges they face, blind spots
5. **Insights**: Connections between different things they've said

## Requirements:
- Only include observations you're genuinely confident about
- Each observation should be distinct from existing ones
- Be specific, not generic (e.g., "struggles with saying no to opportunities" not "has trouble with decisions")
- Confidence should reflect how certain you are (0.5-0.95 range)
- Maximum 3 new observations

Respond with JSON: {{"observations": [...]}}"""

        try:
            response, _ = await self.ai.generate(
                system_prompt="You are a psychological analyst identifying patterns in human behavior.",
                user_prompt=prompt,
                response_model=ObservationBatch,
                temperature=0.3,
                call_location="observation_service.generate",
            )

            # Create observations
            created = []
            for obs_data in response.observations:
                # Skip if confidence too low
                if obs_data.confidence < 0.5:
                    continue

                observation = Observation(
                    user_id=user_id,
                    decision_id=decision_id,
                    observation_text=obs_data.observation_text,
                    observation_type=obs_data.observation_type,
                    confidence=obs_data.confidence,
                    related_theme=obs_data.related_theme,
                    tags=obs_data.tags,
                    source="conversation",
                )
                self.db.add(observation)
                created.append(observation)

            await self.db.commit()
            return created

        except Exception as e:
            print(f"[WARN] Failed to generate observations: {e}")
            return []

    async def get_inline_observation(
        self,
        user_id: uuid.UUID,
        current_context: Optional[str] = None,
    ) -> Optional[str]:
        """Get an observation to surface inline during chat.

        Returns an observation formatted for natural insertion in conversation.
        Returns None if no suitable observation is available.
        """
        # Get observations that should be surfaced
        result = await self.db.execute(
            select(Observation)
            .where(
                and_(
                    Observation.user_id == user_id,
                    Observation.user_feedback != ObservationFeedback.INCORRECT.value,
                    Observation.confidence >= 0.6,
                )
            )
            .order_by(Observation.surfaced_count.asc(), Observation.confidence.desc())
            .limit(10)
        )
        observations = result.scalars().all()

        for obs in observations:
            if obs.should_surface():
                # Mark as surfaced
                obs.mark_surfaced()
                await self.db.commit()
                return obs.to_inline_text()

        return None

    async def get_observations_for_display(
        self,
        user_id: uuid.UUID,
        limit: int = 20,
        observation_type: Optional[str] = None,
    ) -> list[Observation]:
        """Get observations for the Observations tab.

        Args:
            user_id: The user's ID
            limit: Maximum number to return
            observation_type: Optional filter by type

        Returns:
            List of observations ordered by confidence and recency
        """
        query = select(Observation).where(
            Observation.user_id == user_id,
            Observation.user_feedback != ObservationFeedback.INCORRECT.value,
        )

        if observation_type:
            query = query.where(Observation.observation_type == observation_type)

        query = query.order_by(
            Observation.confidence.desc(),
            Observation.created_at.desc(),
        ).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_observations_grouped(
        self, user_id: uuid.UUID
    ) -> dict[str, list[Observation]]:
        """Get observations grouped by type for display.

        Returns a dict like:
        {
            "patterns": [...],
            "values": [...],
            "strengths": [...],
            "growth_areas": [...],
            "insights": [...]
        }
        """
        observations = await self.get_observations_for_display(user_id, limit=50)

        grouped: dict[str, list[Observation]] = {
            ObservationType.PATTERN.value: [],
            ObservationType.VALUE.value: [],
            ObservationType.STRENGTH.value: [],
            ObservationType.GROWTH_AREA.value: [],
            ObservationType.INSIGHT.value: [],
        }

        for obs in observations:
            if obs.observation_type in grouped:
                grouped[obs.observation_type].append(obs)

        return grouped

    async def set_feedback(
        self,
        observation_id: uuid.UUID,
        user_id: uuid.UUID,
        feedback: ObservationFeedback,
    ) -> Optional[Observation]:
        """Set user feedback on an observation.

        Args:
            observation_id: The observation's ID
            user_id: The user's ID (for verification)
            feedback: The feedback to set

        Returns:
            The updated observation, or None if not found
        """
        result = await self.db.execute(
            select(Observation).where(
                Observation.id == observation_id,
                Observation.user_id == user_id,
            )
        )
        observation = result.scalar_one_or_none()

        if not observation:
            return None

        observation.set_feedback(feedback)
        await self.db.commit()
        return observation

    async def get_recent_insights(
        self,
        user_id: uuid.UUID,
        days: int = 7,
        limit: int = 5,
    ) -> list[Observation]:
        """Get recent high-confidence insights.

        Useful for the "Recent Insights" section of the Observations tab.
        """
        cutoff = datetime.utcnow() - timedelta(days=days)

        result = await self.db.execute(
            select(Observation)
            .where(
                Observation.user_id == user_id,
                Observation.created_at >= cutoff,
                Observation.confidence >= 0.7,
                Observation.user_feedback != ObservationFeedback.INCORRECT.value,
            )
            .order_by(Observation.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
