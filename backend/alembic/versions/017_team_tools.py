"""Create admin.team_tools for per-team tool pricing."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "017_team_tools"
down_revision: Union[str, None] = "016_tool_api_endpoint"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "team_tools",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "team_id",
            UUID(as_uuid=True),
            sa.ForeignKey("admin.teams.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "tool_id",
            UUID(as_uuid=True),
            sa.ForeignKey("admin.tools.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("pricing_model", sa.String(length=32), nullable=True),
        sa.Column("token_price", sa.Numeric(18, 8), nullable=True),
        sa.Column("output_token_price", sa.Numeric(18, 8), nullable=True),
        sa.Column("cost_per_seat", sa.Numeric(18, 4), nullable=True),
        sa.Column("seat_count", sa.Integer(), nullable=True),
        sa.Column("package_allowance", sa.BigInteger(), nullable=True),
        sa.Column("overage_price", sa.Numeric(18, 8), nullable=True),
        sa.Column("plan_name", sa.String(length=200), nullable=True),
        sa.Column("pricing_config", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
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
        sa.UniqueConstraint("team_id", "tool_id", name="uq_team_tools_team_tool"),
        schema="admin",
    )


def downgrade() -> None:
    op.drop_table("team_tools", schema="admin")
