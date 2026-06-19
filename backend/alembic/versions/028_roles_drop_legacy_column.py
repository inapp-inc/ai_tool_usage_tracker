"""028 — Phase 2 cutover: role_id NOT NULL, drop legacy users.role column."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "028_roles_drop_legacy_column"
down_revision: Union[str, None] = "027_roles_add_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    unmatched = conn.execute(
        sa.text("SELECT COUNT(*) FROM auth.users WHERE role_id IS NULL")
    ).scalar_one()
    if unmatched:
        raise RuntimeError(
            f"Cannot cut over: {unmatched} user(s) still have NULL role_id."
        )

    op.alter_column(
        "users",
        "role_id",
        existing_type=sa.dialects.postgresql.UUID(as_uuid=True),
        nullable=False,
        schema="auth",
    )

    op.drop_constraint("chk_user_role", "users", schema="auth", type_="check")
    op.drop_column("users", "role", schema="auth")


def downgrade() -> None:
    op.add_column(
        "users",
        sa.Column("role", sa.String(32), nullable=True),
        schema="auth",
    )

    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            UPDATE auth.users u
            SET role = r.name
            FROM auth.roles r
            WHERE u.role_id = r.id
            """
        )
    )

    op.alter_column(
        "users",
        "role",
        existing_type=sa.String(32),
        nullable=False,
        schema="auth",
    )

    op.create_check_constraint(
        "chk_user_role",
        "users",
        "role IN ('super_admin','team_admin','finance_viewer','team_member','auditor')",
        schema="auth",
    )

    op.alter_column(
        "users",
        "role_id",
        existing_type=sa.dialects.postgresql.UUID(as_uuid=True),
        nullable=True,
        schema="auth",
    )
