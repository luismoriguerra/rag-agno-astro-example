"""Initial chat schema

Revision ID: 001
Revises:
Create Date: 2026-05-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "user_identities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("auth_subject", sa.String(255), nullable=False, unique=True),
        sa.Column("display_name", sa.String(255)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_table(
        "chat_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_identity_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("user_identities.id"), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
    )
    op.create_index(
        "ix_chat_sessions_user_status_updated",
        "chat_sessions",
        ["user_identity_id", "status", "updated_at"],
    )
    op.create_table(
        "chat_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("chat_sessions.id"), nullable=False),
        sa.Column("role", sa.String(30), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("sequence_index", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
    )
    op.create_index(
        "ix_chat_messages_session_seq",
        "chat_messages",
        ["session_id", "sequence_index"],
    )
    op.create_table(
        "agent_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("chat_sessions.id"), nullable=False),
        sa.Column("user_message_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("chat_messages.id"), nullable=False),
        sa.Column("assistant_message_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("chat_messages.id")),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("error_code", sa.String(100)),
        sa.Column("error_message", sa.Text()),
    )
    op.create_index(
        "ix_agent_runs_session_status",
        "agent_runs",
        ["session_id", "status", "started_at"],
    )
    op.create_table(
        "search_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("agent_run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agent_runs.id"), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("snippet", sa.Text()),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index(
        "ix_search_results_run_rank",
        "search_results",
        ["agent_run_id", "rank"],
    )


def downgrade() -> None:
    op.drop_index("ix_search_results_run_rank", table_name="search_results")
    op.drop_table("search_results")
    op.drop_index("ix_agent_runs_session_status", table_name="agent_runs")
    op.drop_table("agent_runs")
    op.drop_index("ix_chat_messages_session_seq", table_name="chat_messages")
    op.drop_table("chat_messages")
    op.drop_index("ix_chat_sessions_user_status_updated", table_name="chat_sessions")
    op.drop_table("chat_sessions")
    op.drop_table("user_identities")
