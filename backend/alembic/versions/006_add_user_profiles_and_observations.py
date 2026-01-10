"""Add user_profiles and user_observations tables for personalization.

Revision ID: 006_add_user_profiles_and_observations
Revises: 005_add_conversation_state_fields
Create Date: 2026-01-10
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "006_user_profiles_observations"
down_revision: Union[str, None] = "005_conversation_state"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create user_profiles table
    op.create_table(
        "user_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        # Essential fields
        sa.Column("name", sa.String(100), nullable=True),
        sa.Column("age_range", sa.String(20), nullable=True),
        sa.Column("occupation", sa.String(100), nullable=True),
        sa.Column("industry", sa.String(100), nullable=True),
        sa.Column("specialty", sa.String(200), nullable=True),
        # Extended profile as JSONB
        sa.Column(
            "extended_profile",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default="{}",
        ),
        # AI-generated context summary
        sa.Column("context_summary", sa.Text, nullable=True),
        sa.Column("context_summary_updated_at", sa.DateTime(timezone=True), nullable=True),
        # Onboarding state
        sa.Column("onboarding_completed", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("onboarding_step", sa.String(50), nullable=True, server_default="not_started"),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Create index on user_id for fast lookups
    op.create_index("ix_user_profiles_user_id", "user_profiles", ["user_id"], unique=True)

    # Create user_observations table
    op.create_table(
        "user_observations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "decision_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("decisions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        # Observation content
        sa.Column("observation_text", sa.Text, nullable=False),
        sa.Column("observation_type", sa.String(50), nullable=False, server_default="insight"),
        sa.Column("confidence", sa.Numeric(3, 2), nullable=False, server_default="0.70"),
        # Categorization
        sa.Column(
            "tags",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default="[]",
        ),
        sa.Column("related_theme", sa.String(100), nullable=True),
        # Tracking
        sa.Column("surfaced_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("last_surfaced_at", sa.DateTime(timezone=True), nullable=True),
        # User feedback
        sa.Column("user_feedback", sa.String(20), nullable=True),
        # Source
        sa.Column("source", sa.String(50), nullable=False, server_default="conversation"),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Create indexes for efficient queries
    op.create_index("ix_user_observations_user_id", "user_observations", ["user_id"])
    op.create_index("ix_user_observations_decision_id", "user_observations", ["decision_id"])
    op.create_index("ix_user_observations_type", "user_observations", ["observation_type"])
    op.create_index("ix_user_observations_confidence", "user_observations", ["confidence"])


def downgrade() -> None:
    # Drop user_observations indexes and table
    op.drop_index("ix_user_observations_confidence")
    op.drop_index("ix_user_observations_type")
    op.drop_index("ix_user_observations_decision_id")
    op.drop_index("ix_user_observations_user_id")
    op.drop_table("user_observations")

    # Drop user_profiles index and table
    op.drop_index("ix_user_profiles_user_id")
    op.drop_table("user_profiles")
