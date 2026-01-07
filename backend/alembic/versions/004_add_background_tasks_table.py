"""Add background_tasks table for async task processing.

Revision ID: 004_add_background_tasks_table
Revises: 003_add_advisors_table
Create Date: 2026-01-06
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "004_add_background_tasks_table"
down_revision: Union[str, None] = "003_add_advisors_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create background_tasks table
    op.create_table(
        "background_tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("celery_task_id", sa.String(255), nullable=True),
        sa.Column("task_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column(
            "decision_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("decisions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "node_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("decision_nodes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("input_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("result_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retry_count", sa.Integer, server_default="0"),
    )

    # Create indexes for efficient queries
    op.create_index("ix_background_tasks_status", "background_tasks", ["status"])
    op.create_index("ix_background_tasks_celery_task_id", "background_tasks", ["celery_task_id"])
    op.create_index("ix_background_tasks_node_id", "background_tasks", ["node_id"])
    op.create_index("ix_background_tasks_decision_id", "background_tasks", ["decision_id"])


def downgrade() -> None:
    op.drop_index("ix_background_tasks_decision_id")
    op.drop_index("ix_background_tasks_node_id")
    op.drop_index("ix_background_tasks_celery_task_id")
    op.drop_index("ix_background_tasks_status")
    op.drop_table("background_tasks")
