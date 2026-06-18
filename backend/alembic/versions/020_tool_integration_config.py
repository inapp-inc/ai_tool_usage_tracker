"""Add integration_config to admin.tools."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "020_tool_integration_config"
down_revision: Union[str, None] = "019_tool_catalogue_only"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "tools",
        sa.Column(
            "integration_config",
            JSONB,
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        schema="admin",
    )


def downgrade() -> None:
    op.drop_column("tools", "integration_config", schema="admin")
