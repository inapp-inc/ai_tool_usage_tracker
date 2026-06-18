"""023 — built_in flag on catalogue tools."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "023_tool_built_in"
down_revision: Union[str, None] = "022_provider_parents_catalog"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "tools",
        sa.Column(
            "built_in",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        schema="admin",
    )


def downgrade() -> None:
    op.drop_column("tools", "built_in", schema="admin")
