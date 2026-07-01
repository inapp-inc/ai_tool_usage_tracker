"""038 — rename default org to platform for tenant isolation."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "038_platform_tenant"
down_revision: Union[str, None] = "037_org_admin_merge"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            UPDATE auth.organizations
            SET name = 'Platform Administration', slug = 'platform'
            WHERE slug = 'default'
            """
        )
    )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            UPDATE auth.organizations
            SET name = 'Default Organization', slug = 'default'
            WHERE slug = 'platform'
              AND NOT EXISTS (
                  SELECT 1 FROM auth.organizations o WHERE o.slug = 'default'
              )
            """
        )
    )
