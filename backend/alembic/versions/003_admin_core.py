"""Admin schema: teams, tools, credentials (TASK-DB-002)."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003_admin_core"
down_revision: Union[str, None] = "002_auth"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "teams",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
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
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["auth.organizations.id"],
            name="fk_teams_organization_id",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint("organization_id", "name", name="uq_teams_org_name"),
        schema="admin",
    )

    op.create_table(
        "team_memberships",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "joined_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("removed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["auth.organizations.id"],
            name="fk_team_memberships_organization_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["team_id"],
            ["admin.teams.id"],
            name="fk_team_memberships_team_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["auth.users.id"],
            name="fk_team_memberships_user_id",
            ondelete="CASCADE",
        ),
        schema="admin",
    )
    op.create_index(
        "uq_membership_active",
        "team_memberships",
        ["team_id", "user_id"],
        unique=True,
        schema="admin",
        postgresql_where=sa.text("removed_at IS NULL"),
    )

    op.create_table(
        "tools",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("vendor", sa.String(100), nullable=False),
        sa.Column("pricing_model", sa.String(32), nullable=False),
        sa.Column("token_price", sa.Numeric(18, 6), nullable=False),
        sa.Column("package_allowance", sa.BigInteger(), nullable=True),
        sa.Column("overage_price", sa.Numeric(18, 6), nullable=True),
        sa.Column(
            "pricing_config",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
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
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["auth.organizations.id"],
            name="fk_tools_organization_id",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint("token_price >= 0", name="chk_token_price_nonneg"),
        sa.CheckConstraint(
            "(pricing_model != 'package_with_overage') OR "
            "(package_allowance IS NOT NULL AND overage_price IS NOT NULL)",
            name="chk_package_pricing",
        ),
        sa.UniqueConstraint("organization_id", "name", name="uq_tools_org_name"),
        schema="admin",
    )

    op.create_table(
        "credentials",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tool_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("environment", sa.String(16), nullable=False),
        sa.Column("secret_ciphertext", sa.LargeBinary(), nullable=False),
        sa.Column("secret_last_four", sa.String(4), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_rotated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
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
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["auth.organizations.id"],
            name="fk_credentials_organization_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tool_id"],
            ["admin.tools.id"],
            name="fk_credentials_tool_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["team_id"],
            ["admin.teams.id"],
            name="fk_credentials_team_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["auth.users.id"],
            name="fk_credentials_created_by",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            "environment IN ('sandbox', 'production')",
            name="chk_credential_environment",
        ),
        schema="admin",
    )
    op.create_index(
        "ix_credentials_expiry",
        "credentials",
        ["organization_id", "expires_at"],
        schema="admin",
    )


def downgrade() -> None:
    op.drop_index("ix_credentials_expiry", table_name="credentials", schema="admin")
    op.drop_table("credentials", schema="admin")
    op.drop_table("tools", schema="admin")
    op.drop_index("uq_membership_active", table_name="team_memberships", schema="admin")
    op.drop_table("team_memberships", schema="admin")
    op.drop_table("teams", schema="admin")
