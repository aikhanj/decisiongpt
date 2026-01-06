"""Initial schema

Revision ID: 001_initial_schema
Revises:
Create Date: 2024-01-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Create users table
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=True),
        sa.Column("display_name", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Create decisions table
    op.create_table(
        "decisions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("situation_text", sa.Text, nullable=False),
        sa.Column("situation_type", sa.String(50), nullable=True),
        sa.Column("status", sa.String(20), server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Create decision_nodes table
    op.create_table(
        "decision_nodes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("decision_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("decisions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("parent_node_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("decision_nodes.id"), nullable=True),
        sa.Column("phase", sa.String(20), nullable=False),
        sa.Column("state_json", postgresql.JSONB, nullable=True),
        sa.Column("questions_json", postgresql.JSONB, nullable=True),
        sa.Column("answers_json", postgresql.JSONB, nullable=True),
        sa.Column("moves_json", postgresql.JSONB, nullable=True),
        sa.Column("chosen_move_id", sa.String(10), nullable=True),
        sa.Column("execution_plan_json", postgresql.JSONB, nullable=True),
        sa.Column("mood_state", sa.String(20), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB, nullable=True),
        sa.Column("policy_version", sa.String(20), nullable=True),
        sa.Column("prompt_hash", sa.String(64), nullable=True),
        sa.Column("model_version", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Create decision_events table
    op.create_table(
        "decision_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("decision_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("decisions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("node_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("decision_nodes.id"), nullable=True),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("payload_json", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Create decision_outcomes table
    op.create_table(
        "decision_outcomes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("node_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("decision_nodes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("progress_yesno", sa.Boolean, nullable=True),
        sa.Column("sentiment_2h", sa.Integer, nullable=True),
        sa.Column("sentiment_24h", sa.Integer, nullable=True),
        sa.Column("brier_score", sa.Numeric(5, 4), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("sentiment_2h BETWEEN -2 AND 2", name="check_sentiment_2h_range"),
        sa.CheckConstraint("sentiment_24h BETWEEN -2 AND 2", name="check_sentiment_24h_range"),
    )

    # Create calibration_models table
    op.create_table(
        "calibration_models",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("situation_type", sa.String(50), nullable=True),
        sa.Column("version", sa.Integer, server_default="1"),
        sa.Column("parameters_json", postgresql.JSONB, nullable=True),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Create memories table
    op.create_table(
        "memories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("node_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("decision_nodes.id"), nullable=True),
        sa.Column("memory_text", sa.Text, nullable=False),
        sa.Column("tags", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Add vector column for embeddings (using raw SQL for pgvector)
    op.execute("ALTER TABLE memories ADD COLUMN embedding vector(1536)")

    # Create index for vector similarity search
    op.execute("CREATE INDEX ON memories USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)")

    # Insert default demo user
    op.execute("""
        INSERT INTO users (id, email, display_name, created_at, updated_at)
        VALUES (
            '00000000-0000-0000-0000-000000000001',
            'demo@gentleman-coach.local',
            'Demo User',
            NOW(),
            NOW()
        )
    """)


def downgrade() -> None:
    op.drop_table("memories")
    op.drop_table("calibration_models")
    op.drop_table("decision_outcomes")
    op.drop_table("decision_events")
    op.drop_table("decision_nodes")
    op.drop_table("decisions")
    op.drop_table("users")
    op.execute("DROP EXTENSION IF EXISTS vector")
