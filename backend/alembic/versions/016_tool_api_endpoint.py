"""Add api_endpoint to admin.tools."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "016_tool_api_endpoint"
down_revision: Union[str, None] = "015_audit_logs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "tools",
        sa.Column("api_endpoint", sa.String(length=512), nullable=True),
        schema="admin",
    )


def downgrade() -> None:
    op.drop_column("tools", "api_endpoint", schema="admin")
