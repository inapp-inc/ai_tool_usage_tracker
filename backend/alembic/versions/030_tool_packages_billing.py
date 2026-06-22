"""030 — Tool packages, billing_type on tools, team package binding."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "030_tool_packages_billing"
down_revision: Union[str, None] = "029_cursor_usage_breakdown"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "tools",
        sa.Column(
            "billing_type",
            sa.String(32),
            nullable=False,
            server_default="TOKEN_BASED",
        ),
        schema="admin",
    )
    op.create_check_constraint(
        "chk_tools_billing_type",
        "tools",
        "billing_type IN ('TOKEN_BASED','REQUEST_BASED','CREDIT_BASED','SEAT_BASED','LICENSE_BASED')",
        schema="admin",
    )

    op.create_table(
        "tool_packages",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tool_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("admin.tools.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("package_name", sa.String(128), nullable=False),
        sa.Column("billing_type", sa.String(32), nullable=False),
        sa.Column("monthly_price", sa.Numeric(18, 6)),
        sa.Column("yearly_price", sa.Numeric(18, 6)),
        sa.Column("seat_limit", sa.Integer()),
        sa.Column("token_limit", sa.BigInteger()),
        sa.Column("request_limit", sa.BigInteger()),
        sa.Column("credit_limit", sa.Numeric(18, 6)),
        sa.Column("currency", sa.CHAR(3), nullable=False, server_default="USD"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
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
        sa.UniqueConstraint("tool_id", "package_name", name="uq_tool_packages_tool_name"),
        schema="admin",
    )

    op.add_column(
        "team_tools",
        sa.Column(
            "package_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("admin.tool_packages.id", ondelete="SET NULL"),
            nullable=True,
        ),
        schema="admin",
    )
    op.add_column(
        "team_tools",
        sa.Column("subscription_start", sa.Date()),
        schema="admin",
    )
    op.add_column(
        "team_tools",
        sa.Column("subscription_end", sa.Date()),
        schema="admin",
    )
    op.add_column(
        "team_tools",
        sa.Column("monthly_budget", sa.Numeric(18, 6)),
        schema="admin",
    )
    op.add_column(
        "team_tools",
        sa.Column("alert_threshold", sa.Numeric(5, 2)),
        schema="admin",
    )

    op.add_column(
        "usage_events",
        sa.Column("requests", sa.Integer(), nullable=False, server_default="0"),
        schema="usage",
    )


def downgrade() -> None:
    op.drop_column("usage_events", "requests", schema="usage")
    op.drop_column("team_tools", "alert_threshold", schema="admin")
    op.drop_column("team_tools", "monthly_budget", schema="admin")
    op.drop_column("team_tools", "subscription_end", schema="admin")
    op.drop_column("team_tools", "subscription_start", schema="admin")
    op.drop_column("team_tools", "package_id", schema="admin")
    op.drop_table("tool_packages", schema="admin")
    op.drop_constraint("chk_tools_billing_type", "tools", schema="admin", type_="check")
    op.drop_column("tools", "billing_type", schema="admin")
