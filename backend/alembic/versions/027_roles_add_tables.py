"""027 — add auth.roles, auth.role_permissions, nullable users.role_id (Phase 1)."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "027_roles_add_tables"
down_revision: Union[str, None] = "026_team_delete_cascade"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SYSTEM_ROLES = (
    "super_admin",
    "team_admin",
    "finance_viewer",
    "auditor",
    "team_member",
)

ROLE_DESCRIPTIONS = {
    "super_admin": "Full platform access",
    "team_admin": "Manage teams, members, alerts, and uploads within assigned teams",
    "finance_viewer": "Read-only access to reports and personal usage",
    "auditor": "Read-only access to audit logs",
    "team_member": "View personal usage data",
}

# (can_read, can_write, team_scoped) per resource — mirrors app.core.role_seed_data
_ROLE_MATRIX: dict[str, dict[str, tuple[bool, bool, bool]]] = {
    "super_admin": {
        r: (True, True, False)
        for r in (
            "insights",
            "alerts",
            "uploads",
            "members",
            "reports",
            "audit_logs",
            "tools",
            "teams",
            "credentials",
            "collectors",
            "settings",
            "my_usage",
        )
    },
    "team_admin": {
        "insights": (True, False, True),
        "alerts": (True, True, True),
        "uploads": (True, True, True),
        "members": (True, True, True),
        "reports": (False, False, False),
        "audit_logs": (False, False, False),
        "tools": (True, False, False),
        "teams": (True, False, False),
        "credentials": (False, False, False),
        "collectors": (True, False, True),
        "settings": (False, False, False),
        "my_usage": (True, False, False),
    },
    "finance_viewer": {
        "insights": (False, False, False),
        "alerts": (False, False, False),
        "uploads": (False, False, False),
        "members": (False, False, False),
        "reports": (True, False, False),
        "audit_logs": (False, False, False),
        "tools": (False, False, False),
        "teams": (False, False, False),
        "credentials": (False, False, False),
        "collectors": (False, False, False),
        "settings": (False, False, False),
        "my_usage": (True, False, False),
    },
    "auditor": {
        "insights": (False, False, False),
        "alerts": (False, False, False),
        "uploads": (False, False, False),
        "members": (False, False, False),
        "reports": (False, False, False),
        "audit_logs": (True, False, False),
        "tools": (False, False, False),
        "teams": (False, False, False),
        "credentials": (False, False, False),
        "collectors": (False, False, False),
        "settings": (False, False, False),
        "my_usage": (True, False, False),
    },
    "team_member": {
        "insights": (False, False, False),
        "alerts": (False, False, False),
        "uploads": (False, False, False),
        "members": (False, False, False),
        "reports": (False, False, False),
        "audit_logs": (False, False, False),
        "tools": (False, False, False),
        "teams": (False, False, False),
        "credentials": (False, False, False),
        "collectors": (False, False, False),
        "settings": (False, False, False),
        "my_usage": (True, False, False),
    },
}


def upgrade() -> None:
    op.create_table(
        "roles",
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
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("organization_id", "name", name="uq_roles_org_name"),
        schema="auth",
    )

    op.create_table(
        "role_permissions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "role_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("auth.roles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("resource", sa.String(64), nullable=False),
        sa.Column("can_read", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("can_write", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("team_scoped", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.UniqueConstraint("role_id", "resource", name="uq_role_permissions_role_resource"),
        schema="auth",
    )

    conn = op.get_bind()

    org_rows = conn.execute(sa.text("SELECT id FROM auth.organizations")).fetchall()
    for (org_id,) in org_rows:
        for role_name in SYSTEM_ROLES:
            role_id = conn.execute(
                sa.text(
                    """
                    INSERT INTO auth.roles (organization_id, name, description, is_system)
                    VALUES (:org_id, :name, :description, true)
                    RETURNING id
                    """
                ),
                {
                    "org_id": org_id,
                    "name": role_name,
                    "description": ROLE_DESCRIPTIONS[role_name],
                },
            ).scalar_one()

            matrix = _ROLE_MATRIX[role_name]
            for resource, (can_read, can_write, team_scoped) in matrix.items():
                conn.execute(
                    sa.text(
                        """
                        INSERT INTO auth.role_permissions
                            (role_id, resource, can_read, can_write, team_scoped)
                        VALUES (:role_id, :resource, :can_read, :can_write, :team_scoped)
                        """
                    ),
                    {
                        "role_id": role_id,
                        "resource": resource,
                        "can_read": can_read,
                        "can_write": can_write,
                        "team_scoped": team_scoped,
                    },
                )

    op.add_column(
        "users",
        sa.Column(
            "role_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("auth.roles.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        schema="auth",
    )

    conn.execute(
        sa.text(
            """
            UPDATE auth.users u
            SET role_id = r.id
            FROM auth.roles r
            WHERE r.organization_id = u.organization_id
              AND r.name = u.role
            """
        )
    )

    unmatched = conn.execute(
        sa.text("SELECT COUNT(*) FROM auth.users WHERE role_id IS NULL")
    ).scalar_one()
    if unmatched:
        raise RuntimeError(
            f"Role backfill failed: {unmatched} user(s) have no matching system role. "
            "Fix auth.users.role values before re-running migration."
        )


def downgrade() -> None:
    op.drop_column("users", "role_id", schema="auth")
    op.drop_table("role_permissions", schema="auth")
    op.drop_table("roles", schema="auth")
