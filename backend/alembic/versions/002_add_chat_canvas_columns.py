"""Add chat_messages_json and canvas_state_json columns to decision_nodes.

Revision ID: 002_chat_canvas
Revises: 001_initial_schema
Create Date: 2026-01-06
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "002_chat_canvas"
down_revision = "001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add chat_messages_json column for storing chat history
    op.add_column(
        "decision_nodes",
        sa.Column("chat_messages_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    # Add canvas_state_json column for storing canvas state
    op.add_column(
        "decision_nodes",
        sa.Column("canvas_state_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("decision_nodes", "canvas_state_json")
    op.drop_column("decision_nodes", "chat_messages_json")
