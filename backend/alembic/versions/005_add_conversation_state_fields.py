"""Add conversation state fields to decision_nodes for adaptive questioning.

Revision ID: 005_conversation_state
Revises: 004_add_background_tasks_table
Create Date: 2026-01-09
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "005_conversation_state"
down_revision: Union[str, None] = "004_add_background_tasks_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add fields for conversational adaptive questioning."""
    # Add conversation_state_json for tracking VoI-based question flow
    op.add_column(
        "decision_nodes",
        sa.Column(
            "conversation_state_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )

    # Add question_history_json for storing Q&A history with canvas impacts
    op.add_column(
        "decision_nodes",
        sa.Column(
            "question_history_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )

    # Add canvas_evolution_json for tracking how canvas changes over time
    op.add_column(
        "decision_nodes",
        sa.Column(
            "canvas_evolution_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )


def downgrade() -> None:
    """Remove conversation state fields."""
    op.drop_column("decision_nodes", "canvas_evolution_json")
    op.drop_column("decision_nodes", "question_history_json")
    op.drop_column("decision_nodes", "conversation_state_json")
