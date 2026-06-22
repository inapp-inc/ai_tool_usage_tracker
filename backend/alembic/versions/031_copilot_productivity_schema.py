"""031 — GitHub Copilot seat-based productivity analytics tables."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "031_copilot_productivity_schema"
down_revision: Union[str, None] = "030_tool_packages_billing"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS copilot")

    op.create_table(
        "copilot_organizations",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "team_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("admin.teams.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "tool_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("admin.tools.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("organization_name", sa.String(255)),
        sa.Column("organization_id", sa.String(128), nullable=False),
        sa.Column("subscription_type", sa.String(64)),
        sa.Column("monthly_cost", sa.Numeric(18, 6), nullable=False, server_default="0"),
        sa.Column("total_seats", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("assigned_seats", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("active_users", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("report_date", sa.Date()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        schema="copilot",
    )
    op.create_index(
        "ix_copilot_org_team_org_date",
        "copilot_organizations",
        ["team_id", "organization_id", "report_date"],
        unique=True,
        schema="copilot",
    )

    op.create_table(
        "copilot_user_usage",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "team_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("admin.teams.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "organization_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("copilot.copilot_organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("report_date", sa.Date(), nullable=False),
        sa.Column("user_login", sa.String(255), nullable=False),
        sa.Column("user_email", sa.String(255)),
        sa.Column("user_name", sa.String(255)),
        sa.Column("feature", sa.String(64), nullable=False, server_default="all"),
        sa.Column("editor", sa.String(64), nullable=False, server_default="all"),
        sa.Column("language", sa.String(64), nullable=False, server_default="all"),
        sa.Column("active_days", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("chat_turns", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("suggestions_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("acceptances_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("acceptance_rate", sa.Numeric(8, 4)),
        sa.Column("lines_suggested", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("lines_accepted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("estimated_cost", sa.Numeric(18, 6), nullable=False, server_default="0"),
        sa.Column("raw_payload", sa.dialects.postgresql.JSONB),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        schema="copilot",
    )
    op.create_index(
        "ix_copilot_user_usage_unique",
        "copilot_user_usage",
        [
            "team_id",
            "organization_id",
            "user_login",
            "report_date",
            "feature",
            "editor",
            "language",
        ],
        unique=True,
        schema="copilot",
    )
    op.create_index(
        "ix_copilot_user_usage_team_date",
        "copilot_user_usage",
        ["team_id", "report_date"],
        schema="copilot",
    )

    op.create_table(
        "copilot_seats",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("copilot.copilot_organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("user_login", sa.String(255), nullable=False),
        sa.Column("user_email", sa.String(255)),
        sa.Column("seat_status", sa.String(32), nullable=False, server_default="assigned"),
        sa.Column("assigned_at", sa.DateTime(timezone=True)),
        sa.Column("last_activity_at", sa.DateTime(timezone=True)),
        sa.Column("monthly_cost", sa.Numeric(18, 6), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        schema="copilot",
    )
    op.create_index(
        "ix_copilot_seats_org_login",
        "copilot_seats",
        ["organization_id", "user_login"],
        unique=True,
        schema="copilot",
    )


def downgrade() -> None:
    op.drop_index("ix_copilot_seats_org_login", table_name="copilot_seats", schema="copilot")
    op.drop_table("copilot_seats", schema="copilot")
    op.drop_index("ix_copilot_user_usage_team_date", table_name="copilot_user_usage", schema="copilot")
    op.drop_index("ix_copilot_user_usage_unique", table_name="copilot_user_usage", schema="copilot")
    op.drop_table("copilot_user_usage", schema="copilot")
    op.drop_index("ix_copilot_org_team_org_date", table_name="copilot_organizations", schema="copilot")
    op.drop_table("copilot_organizations", schema="copilot")
    op.execute("DROP SCHEMA IF EXISTS copilot CASCADE")
