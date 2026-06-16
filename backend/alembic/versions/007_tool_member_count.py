"""Add member_count to admin.tools."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "007_tool_member_count"
down_revision: Union[str, None] = "006_admin_tools"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "tools",
        sa.Column("member_count", sa.BigInteger(), nullable=False, server_default="0"),
        schema="admin",
    )


def downgrade() -> None:
    op.drop_column("tools", "member_count", schema="admin")
