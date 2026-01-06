import uuid
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.gateway import AIGateway
from app.config import get_settings
from app.models import Memory, DecisionNode


class MemoryService:
    """Service for semantic memory operations (optional feature)."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.settings = get_settings()

    @property
    def is_enabled(self) -> bool:
        """Check if vector memory is enabled."""
        return self.settings.use_vector_memory

    async def create_memory(
        self,
        user_id: uuid.UUID,
        memory_text: str,
        api_key: str,
        node_id: uuid.UUID | None = None,
        tags: dict | None = None,
    ) -> Memory | None:
        """
        Create a memory with embedding.

        Args:
            user_id: ID of the user
            memory_text: Text to store and embed
            api_key: User's OpenAI API key for embedding
            node_id: Optional associated node ID
            tags: Optional tags (situation_type, mood_state, outcome)

        Returns:
            Created memory or None if vector memory is disabled
        """
        if not self.is_enabled:
            return None

        # Create AI gateway with user's API key and generate embedding
        ai = AIGateway(api_key)
        embedding = await ai.get_embedding(memory_text)

        memory = Memory(
            user_id=user_id,
            node_id=node_id,
            memory_text=memory_text,
            tags=tags,
        )
        # Set embedding if column exists
        if hasattr(Memory, "embedding"):
            memory.embedding = embedding

        self.db.add(memory)
        await self.db.commit()
        await self.db.refresh(memory)
        return memory

    async def find_similar_memories(
        self,
        user_id: uuid.UUID,
        query_text: str,
        api_key: str,
        limit: int = 3,
    ) -> list[Memory]:
        """
        Find similar memories using vector similarity.

        Args:
            user_id: ID of the user
            query_text: Text to find similar memories for
            api_key: User's OpenAI API key for embedding
            limit: Maximum number of results

        Returns:
            List of similar memories
        """
        if not self.is_enabled:
            return []

        # Create AI gateway with user's API key and generate embedding for query
        ai = AIGateway(api_key)
        query_embedding = await ai.get_embedding(query_text)

        # Use raw SQL for vector similarity search
        # pgvector uses <=> for cosine distance
        result = await self.db.execute(
            text("""
                SELECT id, user_id, node_id, memory_text, tags, created_at
                FROM memories
                WHERE user_id = :user_id
                ORDER BY embedding <=> :query_embedding
                LIMIT :limit
            """),
            {
                "user_id": str(user_id),
                "query_embedding": str(query_embedding),
                "limit": limit,
            },
        )
        rows = result.fetchall()

        # Convert to Memory objects
        memories = []
        for row in rows:
            memory = Memory(
                id=row.id,
                user_id=row.user_id,
                node_id=row.node_id,
                memory_text=row.memory_text,
                tags=row.tags,
                created_at=row.created_at,
            )
            memories.append(memory)

        return memories

    async def create_memory_from_node(
        self, node: DecisionNode, api_key: str
    ) -> Memory | None:
        """
        Create a memory from a completed decision node.

        Args:
            node: The decision node to create memory from
            api_key: User's OpenAI API key for embedding

        Returns:
            Created memory or None
        """
        if not self.is_enabled or not node.execution_plan_json:
            return None

        # Build memory text from node data
        summary = node.state_json.get("summary", "") if node.state_json else ""
        chosen_move = None
        if node.moves_json and node.chosen_move_id:
            moves = node.moves_json.get("moves", [])
            chosen_move = next(
                (m for m in moves if m["move_id"] == node.chosen_move_id), None
            )

        memory_text = f"Situation: {summary}"
        if chosen_move:
            memory_text += f"\nChose: {chosen_move.get('title', 'Unknown')}"

        # Get decision for user_id and situation_type
        from app.services.decision_service import DecisionService
        decision_service = DecisionService(self.db)
        decision = await decision_service.get_decision(node.decision_id)
        if not decision:
            return None

        tags = {
            "situation_type": decision.situation_type,
            "mood_state": node.mood_state,
            "chosen_move_id": node.chosen_move_id,
        }

        return await self.create_memory(
            user_id=decision.user_id,
            memory_text=memory_text,
            api_key=api_key,
            node_id=node.id,
            tags=tags,
        )
