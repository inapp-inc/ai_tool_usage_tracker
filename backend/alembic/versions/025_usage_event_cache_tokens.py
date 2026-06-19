"""025 — cache token columns on usage events (Cursor API)."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "025_usage_event_cache_tokens"
down_revision: Union[str, None] = "024_in_app_notifications"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "usage_events",
        sa.Column("cache_write_tokens", sa.BigInteger(), nullable=False, server_default="0"),
        schema="usage",
    )
    op.add_column(
        "usage_events",
        sa.Column("cache_read_tokens", sa.BigInteger(), nullable=False, server_default="0"),
        schema="usage",
    )


def downgrade() -> None:
    op.drop_column("usage_events", "cache_read_tokens", schema="usage")
    op.drop_column("usage_events", "cache_write_tokens", schema="usage")
