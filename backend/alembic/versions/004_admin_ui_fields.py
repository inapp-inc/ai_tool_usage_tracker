"""UI metadata fields for teams settings and credential labels."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "004_admin_ui_fields"
down_revision: Union[str, None] = "003_admin_core"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "teams",
        sa.Column(
            "settings",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        schema="admin",
    )
    op.add_column(
        "credentials",
        sa.Column("label", sa.String(200), nullable=False, server_default=""),
        schema="admin",
    )
    op.add_column(
        "credentials",
        sa.Column("description", sa.String(500), nullable=False, server_default=""),
        schema="admin",
    )
    op.add_column(
        "credentials",
        sa.Column(
            "status",
            sa.String(16),
            nullable=False,
            server_default="active",
        ),
        schema="admin",
    )
    op.add_column(
        "credentials",
        sa.Column("rotation_reminder_days", sa.Integer(), nullable=True),
        schema="admin",
    )
    op.create_check_constraint(
        "chk_credential_status",
        "credentials",
        "status IN ('active', 'inactive')",
        schema="admin",
    )


def downgrade() -> None:
    op.drop_constraint("chk_credential_status", "credentials", schema="admin")
    op.drop_column("credentials", "rotation_reminder_days", schema="admin")
    op.drop_column("credentials", "status", schema="admin")
    op.drop_column("credentials", "description", schema="admin")
    op.drop_column("credentials", "label", schema="admin")
    op.drop_column("teams", "settings", schema="admin")
