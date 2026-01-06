"""Add advisors table

Revision ID: 003_add_advisors_table
Revises: 002_add_chat_canvas_columns
Create Date: 2026-01-06

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "003_add_advisors_table"
down_revision: Union[str, None] = "002_chat_canvas"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create advisors table
    op.create_table(
        "advisors",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("slug", sa.String(50), unique=True, nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("avatar", sa.String(50), nullable=False, server_default="🤖"),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("expertise_keywords", postgresql.ARRAY(sa.String), nullable=False, server_default="{}"),
        sa.Column("personality_traits", postgresql.ARRAY(sa.String), nullable=False, server_default="{}"),
        sa.Column("system_prompt", sa.Text, nullable=False),
        sa.Column("is_system", sa.Boolean, server_default="false"),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Create index on slug for faster lookups
    op.create_index("ix_advisors_slug", "advisors", ["slug"])

    # Create index on user_id for user's custom advisors
    op.create_index("ix_advisors_user_id", "advisors", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_advisors_user_id")
    op.drop_index("ix_advisors_slug")
    op.drop_table("advisors")
