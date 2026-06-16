"""Team memberships (admin.team_memberships)."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "008_team_memberships"
down_revision: Union[str, None] = "007_tool_member_count"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "team_memberships",
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
        sa.Column(
            "team_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("admin.teams.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("auth.users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "joined_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("removed_at", sa.DateTime(timezone=True), nullable=True),
        schema="admin",
    )
    op.create_index(
        "ix_team_memberships_team_id",
        "team_memberships",
        ["team_id"],
        schema="admin",
    )
    op.create_index(
        "ix_team_memberships_user_id",
        "team_memberships",
        ["user_id"],
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


def downgrade() -> None:
    op.drop_index("uq_membership_active", table_name="team_memberships", schema="admin")
    op.drop_index("ix_team_memberships_user_id", table_name="team_memberships", schema="admin")
    op.drop_index("ix_team_memberships_team_id", table_name="team_memberships", schema="admin")
    op.drop_table("team_memberships", schema="admin")
