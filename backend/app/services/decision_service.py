import uuid
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Decision, DecisionNode, DecisionEvent
from app.models.decision import DecisionStatus
from app.models.decision_node import NodePhase


class DecisionService:
    """Service for managing decisions and nodes."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_decision(
        self,
        user_id: uuid.UUID,
        situation_text: str,
        situation_type: str | None = None,
        title: str | None = None,
    ) -> Decision:
        """Create a new decision."""
        decision = Decision(
            user_id=user_id,
            situation_text=situation_text,
            situation_type=situation_type,
            title=title or situation_text[:100],
            status=DecisionStatus.ACTIVE.value,
        )
        self.db.add(decision)
        await self.db.flush()

        # Log event
        event = DecisionEvent(
            decision_id=decision.id,
            event_type="created",
            payload_json={"situation_text": situation_text},
        )
        self.db.add(event)
        await self.db.commit()
        await self.db.refresh(decision)
        return decision

    async def create_node(
        self,
        decision_id: uuid.UUID,
        phase: NodePhase,
        parent_node_id: uuid.UUID | None = None,
        **kwargs,
    ) -> DecisionNode:
        """Create a new decision node."""
        node = DecisionNode(
            decision_id=decision_id,
            parent_node_id=parent_node_id,
            phase=phase.value,
            **kwargs,
        )
        self.db.add(node)
        await self.db.commit()
        await self.db.refresh(node)
        return node

    async def update_node(self, node: DecisionNode, **kwargs) -> DecisionNode:
        """Update a decision node."""
        for key, value in kwargs.items():
            setattr(node, key, value)
        await self.db.commit()
        await self.db.refresh(node)
        return node

    async def get_decision(self, decision_id: uuid.UUID) -> Decision | None:
        """Get a decision by ID with nodes."""
        result = await self.db.execute(
            select(Decision)
            .where(Decision.id == decision_id)
            .options(selectinload(Decision.nodes))
        )
        return result.scalar_one_or_none()

    async def get_node(self, node_id: uuid.UUID) -> DecisionNode | None:
        """Get a node by ID."""
        result = await self.db.execute(
            select(DecisionNode).where(DecisionNode.id == node_id)
        )
        return result.scalar_one_or_none()

    async def get_decisions_for_user(
        self, user_id: uuid.UUID, limit: int = 20
    ) -> list[Decision]:
        """Get recent decisions for a user."""
        result = await self.db.execute(
            select(Decision)
            .where(Decision.user_id == user_id)
            .options(selectinload(Decision.nodes))
            .order_by(Decision.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def log_event(
        self,
        decision_id: uuid.UUID,
        event_type: str,
        node_id: uuid.UUID | None = None,
        payload: dict | None = None,
    ) -> DecisionEvent:
        """Log a decision event."""
        event = DecisionEvent(
            decision_id=decision_id,
            node_id=node_id,
            event_type=event_type,
            payload_json=payload,
        )
        self.db.add(event)
        await self.db.commit()
        return event

    async def update_decision_status(
        self, decision_id: uuid.UUID, status: DecisionStatus
    ) -> Decision | None:
        """Update decision status."""
        decision = await self.get_decision(decision_id)
        if decision:
            decision.status = status.value
            decision.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(decision)
        return decision
