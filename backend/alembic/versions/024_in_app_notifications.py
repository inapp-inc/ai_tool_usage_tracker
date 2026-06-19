"""024 — in-app notification center table."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "024_in_app_notifications"
down_revision: Union[str, None] = "023_tool_built_in"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "notifications",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("auth.organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("auth.users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "threshold_event_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("notifications.threshold_events.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("notification_type", sa.String(32), nullable=False),
        sa.Column("severity", sa.String(16), nullable=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column(
            "payload",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("read", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        schema="notifications",
    )
    op.create_index(
        "ix_notif_user_unread",
        "notifications",
        ["user_id", "read", sa.text("created_at DESC")],
        schema="notifications",
    )


def downgrade() -> None:
    op.drop_index("ix_notif_user_unread", table_name="notifications", schema="notifications")
    op.drop_table("notifications", schema="notifications")
