"""Admin thresholds + notification threshold events."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "010_thresholds"
down_revision: Union[str, None] = "009_tool_credential_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "thresholds",
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
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("threshold_type", sa.String(32), nullable=False),
        sa.Column("scope", sa.String(16), nullable=False),
        sa.Column(
            "tool_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("admin.tools.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "team_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("admin.teams.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("auth.users.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("limit_value", sa.Numeric(18, 6), nullable=False),
        sa.Column("severity", sa.String(16), nullable=False),
        sa.Column("notify_email", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("notify_in_app", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("webhook_url", sa.String(512), nullable=True),
        sa.Column(
            "email_recipients",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        schema="admin",
    )
    op.create_index(
        "ix_thresholds_organization_id",
        "thresholds",
        ["organization_id"],
        schema="admin",
    )

    op.create_table(
        "threshold_events",
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
            "threshold_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("admin.thresholds.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("severity", sa.String(16), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column(
            "team_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("admin.teams.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "triggered_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "acknowledged_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("auth.users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        schema="notifications",
    )
    op.create_index(
        "ix_threshold_events_threshold_id",
        "threshold_events",
        ["threshold_id"],
        schema="notifications",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_threshold_events_threshold_id",
        table_name="threshold_events",
        schema="notifications",
    )
    op.drop_table("threshold_events", schema="notifications")
    op.drop_index("ix_thresholds_organization_id", table_name="thresholds", schema="admin")
    op.drop_table("thresholds", schema="admin")
