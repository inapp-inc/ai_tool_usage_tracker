"""Add user_name to usage.usage_events."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "021_usage_event_user_name"
down_revision: Union[str, None] = "020_tool_integration_config"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "usage_events",
        sa.Column("user_name", sa.String(length=255), nullable=True),
        schema="usage",
    )


def downgrade() -> None:
    op.drop_column("usage_events", "user_name", schema="usage")
