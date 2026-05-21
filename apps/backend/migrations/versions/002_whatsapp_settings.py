"""WhatsApp settings and allowlist

Revision ID: 002
Revises: 001
Create Date: 2026-05-20
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002"
down_revision: str | None = "001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "whatsapp_settings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_table(
        "allowed_phone_numbers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "settings_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("whatsapp_settings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("phone_number", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index(
        "ix_allowed_phone_numbers_phone",
        "allowed_phone_numbers",
        ["phone_number"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_allowed_phone_numbers_phone", table_name="allowed_phone_numbers")
    op.drop_table("allowed_phone_numbers")
    op.drop_table("whatsapp_settings")
