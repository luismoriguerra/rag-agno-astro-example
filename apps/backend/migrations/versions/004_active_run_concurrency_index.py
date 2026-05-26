"""Add index for active-run concurrency queries.

Revision ID: 004
Revises: 003
Create Date: 2026-05-25
"""

from alembic import op

revision = "004_concurrency_idx"
down_revision = "003_costs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_agent_runs_user_active",
        "agent_runs",
        ["session_id", "status"],
        postgresql_where="status IN ('queued', 'running', 'stopping')",
    )
    op.create_index(
        "ix_research_runs_user_active",
        "research_agent_runs",
        ["session_id", "status"],
        postgresql_where="status IN ('queued', 'running', 'stopping')",
    )


def downgrade() -> None:
    op.drop_index("ix_research_runs_user_active", table_name="research_agent_runs")
    op.drop_index("ix_agent_runs_user_active", table_name="agent_runs")
