"""Add research costs table

Revision ID: 003_costs
Revises: 002_research
Create Date: 2026-05-21
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "003_costs"
down_revision = "002_research"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "research_costs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("research_sessions.id"),
            nullable=False,
        ),
        sa.Column(
            "run_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("research_agent_runs.id"),
            nullable=False,
        ),
        sa.Column("model", sa.String(255), nullable=False, server_default=""),
        sa.Column("agent_name", sa.String(255), nullable=False, server_default=""),
        sa.Column("input_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reasoning_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("estimated_cost_usd", sa.Float(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_research_costs_session",
        "research_costs",
        ["session_id"],
    )
    op.create_index(
        "ix_research_costs_run",
        "research_costs",
        ["run_id"],
    )


def downgrade() -> None:
    op.drop_table("research_costs")
