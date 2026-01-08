import uuid
from datetime import datetime

from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.types import UUIDType, JSONType
from app.config import get_settings

# Conditionally import pgvector (only for PostgreSQL)
settings = get_settings()
VECTOR_AVAILABLE = False
Vector = None

if settings.database_type == "postgresql":
    try:
        from pgvector.sqlalchemy import Vector
        VECTOR_AVAILABLE = True
    except ImportError:
        pass


class Memory(Base):
    """Memory model - stores semantic memories with optional vector embeddings."""

    __tablename__ = "memories"

    id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("users.id"), nullable=False
    )
    node_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("decision_nodes.id"), nullable=True
    )
    memory_text: Mapped[str] = mapped_column(Text, nullable=False)
    tags: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="memories")
    node: Mapped["DecisionNode | None"] = relationship(
        "DecisionNode", back_populates="memory"
    )


# Add embedding column if pgvector is available
if VECTOR_AVAILABLE:
    Memory.embedding = mapped_column(Vector(1536), nullable=True)
