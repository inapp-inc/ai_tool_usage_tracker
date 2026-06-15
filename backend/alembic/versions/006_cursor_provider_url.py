"""Fix Cursor provider URL and document Basic auth usage."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "006_cursor_provider_url"
down_revision: Union[str, None] = "005_providers"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            UPDATE admin.providers
            SET usage_api_url = :new_url,
                description = :description
            WHERE slug = 'cursor'
              AND usage_api_url = :old_url
            """
        ),
        {
            "new_url": "https://api.cursor.com/teams/daily-usage-data",
            "old_url": "https://api.cursor.com/usage",
            "description": "Cursor Team Admin API (Basic auth, POST daily usage)",
        },
    )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            UPDATE admin.providers
            SET usage_api_url = :old_url,
                description = :description
            WHERE slug = 'cursor'
              AND usage_api_url = :new_url
            """
        ),
        {
            "new_url": "https://api.cursor.com/teams/daily-usage-data",
            "old_url": "https://api.cursor.com/usage",
            "description": "Cursor IDE usage API",
        },
    )
