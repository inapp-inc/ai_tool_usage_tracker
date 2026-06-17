"""Add catalogue_only flag to separate tool catalogue from live connections."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "019_tool_catalogue_only"
down_revision: Union[str, None] = "018_admin_providers"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "tools",
        sa.Column(
            "catalogue_only",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        schema="admin",
    )
    # Tools never connected via Credentials are catalogue entries.
    op.execute(
        sa.text(
            """
            UPDATE admin.tools
            SET catalogue_only = true
            WHERE last_rotated_at IS NULL
            """
        )
    )


def downgrade() -> None:
    op.drop_column("tools", "catalogue_only", schema="admin")
