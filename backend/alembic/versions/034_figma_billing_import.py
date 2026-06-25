"""034 — Figma CSV billing import tables."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "034_figma_billing_import"
down_revision: Union[str, None] = "033_upload_billing_period"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS figma")

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
        sa.Column("usage_period_start", sa.Date()),
        sa.Column("usage_period_end", sa.Date()),
        sa.Column("total_seat_cost", sa.Numeric(18, 6), nullable=False, server_default="0"),
        sa.Column("total_paid_cost", sa.Numeric(18, 6), nullable=False, server_default="0"),
        sa.Column("total_cost", sa.Numeric(18, 6), nullable=False, server_default="0"),
        sa.Column("full_seat_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("view_seat_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("user_count", sa.Integer(), nullable=False, server_default="0"),
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
            "usage_period_start",
            "usage_period_end",
            name="uq_figma_billing_import_period",
        ),
        schema="figma",
    )

    op.create_table(
        "billing_import_users",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "import_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("figma.billing_imports.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("figma_user_id", sa.String(128)),
        sa.Column("user_email", sa.String(255)),
        sa.Column("user_name", sa.String(255)),
        sa.Column("seat_type", sa.String(32), nullable=False, server_default="full"),
        sa.Column("seat_credits_used", sa.Numeric(18, 6), nullable=False, server_default="0"),
        sa.Column("paid_credits_used", sa.Numeric(18, 6), nullable=False, server_default="0"),
        sa.Column("seat_cost_usd", sa.Numeric(18, 6), nullable=False, server_default="0"),
        sa.Column("paid_cost_usd", sa.Numeric(18, 6), nullable=False, server_default="0"),
        sa.Column("total_cost_usd", sa.Numeric(18, 6), nullable=False, server_default="0"),
        sa.Column("last_activity_at", sa.DateTime(timezone=True)),
        sa.Column(
            "matched_user_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("auth.users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("raw_payload", sa.dialects.postgresql.JSONB(), server_default=sa.text("'{}'::jsonb")),
        schema="figma",
    )
    op.create_index(
        "ix_figma_billing_import_users_import_id",
        "billing_import_users",
        ["import_id"],
        schema="figma",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_figma_billing_import_users_import_id",
        table_name="billing_import_users",
        schema="figma",
    )
    op.drop_table("billing_import_users", schema="figma")
    op.drop_table("billing_imports", schema="figma")
