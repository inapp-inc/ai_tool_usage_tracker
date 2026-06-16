"""Credential metadata columns on admin.tools."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "009_tool_credential_fields"
down_revision: Union[str, None] = "008_team_memberships"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "tools",
        sa.Column("credential_label", sa.String(100), nullable=True),
        schema="admin",
    )
    op.add_column(
        "tools",
        sa.Column(
            "credential_environment",
            sa.String(16),
            nullable=False,
            server_default="production",
        ),
        schema="admin",
    )
    op.add_column(
        "tools",
        sa.Column("credential_expires_at", sa.DateTime(timezone=True), nullable=True),
        schema="admin",
    )
    op.add_column(
        "tools",
        sa.Column("rotation_reminder_days", sa.BigInteger(), nullable=True),
        schema="admin",
    )
    op.add_column(
        "tools",
        sa.Column("last_rotated_at", sa.DateTime(timezone=True), nullable=True),
        schema="admin",
    )


def downgrade() -> None:
    op.drop_column("tools", "last_rotated_at", schema="admin")
    op.drop_column("tools", "rotation_reminder_days", schema="admin")
    op.drop_column("tools", "credential_expires_at", schema="admin")
    op.drop_column("tools", "credential_environment", schema="admin")
    op.drop_column("tools", "credential_label", schema="admin")
