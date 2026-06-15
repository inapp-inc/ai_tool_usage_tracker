"""Provider registry for configurable vendor integrations."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "005_providers"
down_revision: Union[str, None] = "004_admin_ui_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DEFAULT_PROVIDERS = [
    (
        "openai",
        "OpenAI",
        "https://api.openai.com/v1/usage",
        "OpenAI platform usage API",
    ),
    (
        "anthropic",
        "Anthropic",
        "https://api.anthropic.com/v1/usage",
        "Anthropic Claude usage API",
    ),
    (
        "google",
        "Google",
        "https://generativelanguage.googleapis.com/v1/usage",
        "Google Gemini usage API",
    ),
    (
        "azure_openai",
        "Azure OpenAI",
        "https://{resource}.openai.azure.com/openai/usage",
        "Azure OpenAI usage endpoint (replace {resource})",
    ),
    (
        "cohere",
        "Cohere",
        "https://api.cohere.ai/v1/usage",
        "Cohere usage API",
    ),
    (
        "mistral",
        "Mistral",
        "https://api.mistral.ai/v1/usage",
        "Mistral usage API",
    ),
    (
        "cursor",
        "Cursor",
        "https://api.cursor.com/teams/daily-usage-data",
        "Cursor Team Admin API (Basic auth, POST daily usage)",
    ),
]


def upgrade() -> None:
    op.create_table(
        "providers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("auth.organizations.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("slug", sa.String(64), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("usage_api_url", sa.String(2048), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column(
            "is_system",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("organization_id", "slug", name="uq_provider_org_slug"),
        schema="admin",
    )
    op.create_index(
        "ix_providers_org_active",
        "providers",
        ["organization_id", "active"],
        schema="admin",
    )

    conn = op.get_bind()
    org_rows = conn.execute(sa.text("SELECT id FROM auth.organizations")).fetchall()
    for (org_id,) in org_rows:
        for slug, name, url, description in DEFAULT_PROVIDERS:
            conn.execute(
                sa.text(
                    """
                    INSERT INTO admin.providers (
                        id, organization_id, slug, name, usage_api_url,
                        description, is_system, active
                    ) VALUES (
                        gen_random_uuid(), :org_id, :slug, :name, :url,
                        :description, true, true
                    )
                    """
                ),
                {
                    "org_id": org_id,
                    "slug": slug,
                    "name": name,
                    "url": url,
                    "description": description,
                },
            )


def downgrade() -> None:
    op.drop_index("ix_providers_org_active", table_name="providers", schema="admin")
    op.drop_table("providers", schema="admin")
