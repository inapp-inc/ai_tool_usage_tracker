"""Add column mapping fields to uploads."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "012_upload_column_mapping"
down_revision: Union[str, None] = "011_uploads"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "uploads",
        sa.Column(
            "detected_headers",
            postgresql.JSONB(),
            nullable=True,
        ),
        schema="ingestion",
    )
    op.add_column(
        "uploads",
        sa.Column(
            "column_mapping",
            postgresql.JSONB(),
            nullable=True,
        ),
        schema="ingestion",
    )


def downgrade() -> None:
    op.drop_column("uploads", "column_mapping", schema="ingestion")
    op.drop_column("uploads", "detected_headers", schema="ingestion")
