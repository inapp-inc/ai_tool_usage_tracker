"""033 — Billing period dates on uploads for Copilot CSV imports."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "033_upload_billing_period"
down_revision: Union[str, None] = "032_copilot_billing_import"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "uploads",
        sa.Column("billing_period_start", sa.Date(), nullable=True),
        schema="ingestion",
    )
    op.add_column(
        "uploads",
        sa.Column("billing_period_end", sa.Date(), nullable=True),
        schema="ingestion",
    )


def downgrade() -> None:
    op.drop_column("uploads", "billing_period_end", schema="ingestion")
    op.drop_column("uploads", "billing_period_start", schema="ingestion")
