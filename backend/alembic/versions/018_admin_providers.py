"""Create admin.providers lookup table with built-in seeds."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "018_admin_providers"
down_revision: Union[str, None] = "017_team_tools"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

BUILT_IN_PROVIDERS = [
    ("openai", "OpenAI", 10),
    ("anthropic", "Anthropic", 20),
    ("google", "Google", 30),
    ("azure_openai", "Azure OpenAI", 40),
    ("cohere", "Cohere", 50),
    ("mistral", "Mistral", 60),
    ("cursor", "Cursor", 70),
    ("mabl", "Mabl", 80),
    ("windsurf", "Windsurf", 90),
    ("figma", "Figma", 100),
    ("custom", "Custom", 110),
]


def upgrade() -> None:
    op.create_table(
        "providers",
        sa.Column("slug", sa.String(length=64), primary_key=True),
        sa.Column("label", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("logo_url", sa.String(length=512), nullable=True),
        sa.Column("built_in", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
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
        schema="admin",
    )

    providers = sa.table(
        "providers",
        sa.column("slug", sa.String),
        sa.column("label", sa.String),
        sa.column("description", sa.Text),
        sa.column("built_in", sa.Boolean),
        sa.column("active", sa.Boolean),
        sa.column("sort_order", sa.Integer),
        schema="admin",
    )
    op.bulk_insert(
        providers,
        [
            {
                "slug": slug,
                "label": label,
                "description": None,
                "built_in": True,
                "active": True,
                "sort_order": sort_order,
            }
            for slug, label, sort_order in BUILT_IN_PROVIDERS
        ],
    )


def downgrade() -> None:
    op.drop_table("providers", schema="admin")
