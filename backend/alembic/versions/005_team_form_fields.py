"""Team budgets and tool access (admin form fields)."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "005_team_form_fields"
down_revision: Union[str, None] = "004_admin_teams"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "teams",
        sa.Column("token_budget", sa.BigInteger(), nullable=True),
        schema="admin",
    )
    op.add_column(
        "teams",
        sa.Column("cost_budget", sa.Numeric(18, 2), nullable=True),
        schema="admin",
    )
    op.add_column(
        "teams",
        sa.Column(
            "tool_ids",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        schema="admin",
    )
    op.create_check_constraint(
        "chk_teams_token_budget_positive",
        "teams",
        "token_budget IS NULL OR token_budget > 0",
        schema="admin",
    )
    op.create_check_constraint(
        "chk_teams_cost_budget_non_negative",
        "teams",
        "cost_budget IS NULL OR cost_budget >= 0",
        schema="admin",
    )


def downgrade() -> None:
    op.drop_constraint(
        "chk_teams_cost_budget_non_negative",
        "teams",
        schema="admin",
        type_="check",
    )
    op.drop_constraint(
        "chk_teams_token_budget_positive",
        "teams",
        schema="admin",
        type_="check",
    )
    op.drop_column("teams", "tool_ids", schema="admin")
    op.drop_column("teams", "cost_budget", schema="admin")
    op.drop_column("teams", "token_budget", schema="admin")
