"""Admin tools + link collectors to tools."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "006_admin_tools"
down_revision: Union[str, None] = "005_team_form_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tools",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("auth.organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("vendor", sa.String(64), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("pricing_model", sa.String(32), nullable=False),
        sa.Column("token_price", sa.Numeric(18, 6), nullable=False, server_default="0"),
        sa.Column("package_allowance", sa.BigInteger(), nullable=True),
        sa.Column("overage_price", sa.Numeric(18, 6), nullable=True),
        sa.Column(
            "pricing_config",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("api_token_ciphertext", sa.Text(), nullable=False),
        sa.Column("token_count", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("cost_total", sa.Numeric(18, 6), nullable=False, server_default="0"),
        sa.Column("balance_tokens", sa.BigInteger(), nullable=True),
        sa.Column("sync_status", sa.String(16), nullable=False, server_default="inactive"),
        sa.Column("last_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_sync_error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("organization_id", "name", name="uq_tools_org_name"),
        schema="admin",
    )
    op.create_index(
        "ix_tools_organization_id",
        "tools",
        ["organization_id"],
        schema="admin",
    )

    op.add_column(
        "collector_configs",
        sa.Column(
            "tool_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("admin.tools.id", ondelete="CASCADE"),
            nullable=True,
        ),
        schema="ingestion",
    )
    op.create_index(
        "ix_collector_configs_tool_id",
        "collector_configs",
        ["tool_id"],
        unique=True,
        schema="ingestion",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_collector_configs_tool_id",
        table_name="collector_configs",
        schema="ingestion",
    )
    op.drop_column("collector_configs", "tool_id", schema="ingestion")
    op.drop_index("ix_tools_organization_id", table_name="tools", schema="admin")
    op.drop_table("tools", schema="admin")
