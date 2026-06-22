"""029 — Cursor included/billable breakdown columns on usage_events."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "029_cursor_usage_breakdown"
down_revision: Union[str, None] = "028_roles_drop_legacy_column"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "usage_events",
        sa.Column(
            "included_in_plan",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        schema="usage",
    )
    op.add_column(
        "usage_events",
        sa.Column("cursor_kind", sa.String(128), nullable=True),
        schema="usage",
    )
    op.add_column(
        "usage_events",
        sa.Column("reference_cost", sa.Numeric(18, 6), nullable=True),
        schema="usage",
    )


def downgrade() -> None:
    op.drop_column("usage_events", "reference_cost", schema="usage")
    op.drop_column("usage_events", "cursor_kind", schema="usage")
    op.drop_column("usage_events", "included_in_plan", schema="usage")
