"""036 — add org_admin system role to all organizations."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "036_org_admin_role"
down_revision: Union[str, None] = "035_threshold_event_rule_name"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

RESOURCES = (
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


def upgrade() -> None:
    conn = op.get_bind()

    org_rows = conn.execute(sa.text("SELECT id FROM auth.organizations")).fetchall()
    for (org_id,) in org_rows:
        existing = conn.execute(
            sa.text(
                "SELECT id FROM auth.roles WHERE organization_id = :org_id AND name = 'org_admin'"
            ),
            {"org_id": org_id},
        ).fetchone()
        if existing is not None:
            continue

        role_id = conn.execute(
            sa.text(
                """
                INSERT INTO auth.roles (id, organization_id, name, description, is_system, created_at)
                VALUES (gen_random_uuid(), :org_id, 'org_admin', 'Manage organization users, teams, and roles', true, now())
                RETURNING id
                """
            ),
            {"org_id": org_id},
        ).scalar_one()

        for resource in RESOURCES:
            conn.execute(
                sa.text(
                    """
                    INSERT INTO auth.role_permissions
                        (id, role_id, resource, can_read, can_write, team_scoped)
                    VALUES (gen_random_uuid(), :role_id, :resource, true, true, false)
                    """
                ),
                {"role_id": role_id, "resource": resource},
            )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            DELETE FROM auth.role_permissions
            WHERE role_id IN (SELECT id FROM auth.roles WHERE name = 'org_admin')
            """
        )
    )
    conn.execute(sa.text("DELETE FROM auth.roles WHERE name = 'org_admin'"))
