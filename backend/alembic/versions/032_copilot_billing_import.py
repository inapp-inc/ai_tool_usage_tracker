"""032 — Copilot CSV billing import + team tool USD alert threshold."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "032_copilot_billing_import"
down_revision: Union[str, None] = "031_copilot_productivity_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "team_tools",
        sa.Column("alert_threshold_usd", sa.Numeric(18, 6), nullable=True),
        schema="admin",
    )
    op.execute(
        """
        UPDATE admin.team_tools
        SET alert_threshold_usd = monthly_budget * (alert_threshold / 100.0)
        WHERE monthly_budget IS NOT NULL
          AND alert_threshold IS NOT NULL
          AND alert_threshold_usd IS NULL
        """
    )

    op.create_table(
        "billing_imports",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("auth.organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "team_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("admin.teams.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "tool_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("admin.tools.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "upload_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("ingestion.uploads.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "package_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("admin.tool_packages.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("billing_period_start", sa.Date()),
        sa.Column("billing_period_end", sa.Date()),
        sa.Column("sku", sa.String(64), nullable=False),
        sa.Column("monthly_cost_limit", sa.Numeric(18, 6), nullable=False, server_default="0"),
        sa.Column("additional_cost", sa.Numeric(18, 6), nullable=False, server_default="0"),
        sa.Column("total_cost", sa.Numeric(18, 6), nullable=False, server_default="0"),
        sa.Column("seat_count", sa.Integer()),
        sa.Column("raw_summary", sa.dialects.postgresql.JSONB(), server_default=sa.text("'{}'::jsonb")),
        sa.Column(
            "imported_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "team_id",
            "tool_id",
            "billing_period_start",
            "billing_period_end",
            "sku",
            name="uq_copilot_billing_import_period_sku",
        ),
        schema="copilot",
    )


def downgrade() -> None:
    op.drop_table("billing_imports", schema="copilot")
    op.drop_column("team_tools", "alert_threshold_usd", schema="admin")
