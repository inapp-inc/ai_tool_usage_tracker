"""Team and user attribution on usage events from uploads."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "013_usage_team_attr"
down_revision: Union[str, None] = "012_upload_column_mapping"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "usage_events",
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("auth.organizations.id", ondelete="CASCADE"),
            nullable=True,
        ),
        schema="usage",
    )
    op.add_column(
        "usage_events",
        sa.Column(
            "team_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("admin.teams.id", ondelete="SET NULL"),
            nullable=True,
        ),
        schema="usage",
    )
    op.add_column(
        "usage_events",
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("auth.users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        schema="usage",
    )
    op.add_column(
        "usage_events",
        sa.Column("user_email", sa.String(255), nullable=True),
        schema="usage",
    )
    op.add_column(
        "usage_events",
        sa.Column(
            "upload_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("ingestion.uploads.id", ondelete="SET NULL"),
            nullable=True,
        ),
        schema="usage",
    )
    op.add_column(
        "usage_events",
        sa.Column(
            "tool_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("admin.tools.id", ondelete="SET NULL"),
            nullable=True,
        ),
        schema="usage",
    )
    op.create_index(
        "ix_usage_events_team_id",
        "usage_events",
        ["team_id"],
        schema="usage",
    )
    op.create_index(
        "ix_usage_events_upload_id",
        "usage_events",
        ["upload_id"],
        schema="usage",
    )


def downgrade() -> None:
    op.drop_index("ix_usage_events_upload_id", table_name="usage_events", schema="usage")
    op.drop_index("ix_usage_events_team_id", table_name="usage_events", schema="usage")
    op.drop_column("usage_events", "tool_id", schema="usage")
    op.drop_column("usage_events", "upload_id", schema="usage")
    op.drop_column("usage_events", "user_email", schema="usage")
    op.drop_column("usage_events", "user_id", schema="usage")
    op.drop_column("usage_events", "team_id", schema="usage")
    op.drop_column("usage_events", "organization_id", schema="usage")
