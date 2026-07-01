"""037 — merge legacy 'Organization Admin' custom role into org_admin."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "037_org_admin_merge"
down_revision: Union[str, None] = "036_org_admin_role"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    org_rows = conn.execute(sa.text("SELECT id FROM auth.organizations")).fetchall()
    for (org_id,) in org_rows:
        legacy = conn.execute(
            sa.text(
                """
                SELECT id FROM auth.roles
                WHERE organization_id = :org_id AND name = 'Organization Admin'
                """
            ),
            {"org_id": org_id},
        ).fetchone()
        if legacy is None:
            continue

        system = conn.execute(
            sa.text(
                """
                SELECT id FROM auth.roles
                WHERE organization_id = :org_id AND name = 'org_admin'
                """
            ),
            {"org_id": org_id},
        ).fetchone()
        if system is None:
            conn.execute(
                sa.text(
                    """
                    UPDATE auth.roles
                    SET name = 'org_admin',
                        description = 'Manage organization users, teams, and roles',
                        is_system = true
                    WHERE id = :role_id
                    """
                ),
                {"role_id": legacy[0]},
            )
            continue

        legacy_id, system_id = legacy[0], system[0]
        conn.execute(
            sa.text(
                """
                UPDATE auth.users
                SET role_id = :system_id
                WHERE role_id = :legacy_id
                """
            ),
            {"system_id": system_id, "legacy_id": legacy_id},
        )
        conn.execute(
            sa.text("DELETE FROM auth.role_permissions WHERE role_id = :legacy_id"),
            {"legacy_id": legacy_id},
        )
        conn.execute(
            sa.text("DELETE FROM auth.roles WHERE id = :legacy_id"),
            {"legacy_id": legacy_id},
        )


def downgrade() -> None:
    # Non-reversible — legacy custom role names are not restored.
    pass
