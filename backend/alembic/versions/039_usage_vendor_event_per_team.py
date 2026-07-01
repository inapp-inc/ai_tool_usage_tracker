"""039 — scope usage event idempotency per team (not globally per provider)."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "039_vendor_event_team"
down_revision: Union[str, None] = "038_platform_tenant"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index(
        "ix_usage_events_vendor_event",
        table_name="usage_events",
        schema="usage",
    )
    op.create_index(
        "ix_usage_events_vendor_event_team",
        "usage_events",
        ["provider", "vendor_event_id", "team_id"],
        unique=True,
        schema="usage",
        postgresql_where=sa.text("vendor_event_id IS NOT NULL AND team_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "ix_usage_events_vendor_event_team",
        table_name="usage_events",
        schema="usage",
    )
    op.create_index(
        "ix_usage_events_vendor_event",
        "usage_events",
        ["provider", "vendor_event_id"],
        unique=True,
        schema="usage",
        postgresql_where=sa.text("vendor_event_id IS NOT NULL"),
    )
