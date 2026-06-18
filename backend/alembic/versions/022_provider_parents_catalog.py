"""Provider parent companies and built-in product catalogue."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "022_provider_parents_catalog"
down_revision: Union[str, None] = "021_usage_event_user_name"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

PARENTS = [
    ("openai", "OpenAI", 10),
    ("anthropic", "Anthropic", 20),
    ("google", "Google", 30),
    ("microsoft", "Microsoft", 40),
    ("amazon", "Amazon", 50),
    ("cursor", "Cursor", 60),
    ("figma", "Figma", 70),
]

PRODUCTS = [
    ("openai", "OpenAI", "openai", "openai", 10, False, None),
    ("anthropic", "Anthropic Claude", "anthropic", "anthropic", 20, False, "Claude models via Anthropic API."),
    ("google", "Google Gemini", "google", "google", 30, False, "Gemini models via Google AI / Vertex."),
    (
        "azure_openai",
        "Azure OpenAI Platform",
        "microsoft",
        "azure_openai",
        40,
        True,
        "Azure-hosted OpenAI deployments.",
    ),
    (
        "copilot",
        "Microsoft Copilot",
        "microsoft",
        "copilot",
        50,
        True,
        "GitHub Copilot / Microsoft Copilot usage APIs.",
    ),
    (
        "bedrock",
        "Amazon Bedrock",
        "amazon",
        "bedrock",
        60,
        True,
        "AWS Bedrock model usage.",
    ),
    ("cursor", "Cursor", "cursor", "cursor", 70, False, None),
    ("figma", "Figma", "figma", "figma", 80, False, None),
    (
        "custom",
        "Custom Integration",
        None,
        "custom",
        200,
        True,
        "Config-driven HTTP integration (future / advanced).",
    ),
]

RETIRED = ("cohere", "mistral", "mabl", "windsurf", "github_copilot")


def upgrade() -> None:
    op.create_table(
        "provider_parents",
        sa.Column("slug", sa.String(length=64), primary_key=True),
        sa.Column("label", sa.String(length=200), nullable=False),
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

    op.add_column(
        "providers",
        sa.Column("parent_slug", sa.String(length=64), nullable=True),
        schema="admin",
    )
    op.add_column(
        "providers",
        sa.Column("adapter_key", sa.String(length=64), nullable=True),
        schema="admin",
    )
    op.add_column(
        "providers",
        sa.Column(
            "requires_api_endpoint",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        schema="admin",
    )
    op.create_foreign_key(
        "fk_providers_parent_slug",
        "providers",
        "provider_parents",
        ["parent_slug"],
        ["slug"],
        source_schema="admin",
        referent_schema="admin",
        ondelete="SET NULL",
    )

    parents = sa.table(
        "provider_parents",
        sa.column("slug", sa.String),
        sa.column("label", sa.String),
        sa.column("sort_order", sa.Integer),
        schema="admin",
    )
    op.bulk_insert(
        parents,
        [{"slug": s, "label": label, "sort_order": order} for s, label, order in PARENTS],
    )

    conn = op.get_bind()
    for slug, label, parent, adapter, sort_order, req_ep, desc in PRODUCTS:
        conn.execute(
            sa.text(
                """
                INSERT INTO admin.providers (
                    slug, label, description, parent_slug, adapter_key,
                    requires_api_endpoint, built_in, active, sort_order
                ) VALUES (
                    :slug, :label, :description, :parent_slug, :adapter_key,
                    :requires_api_endpoint, true, true, :sort_order
                )
                ON CONFLICT (slug) DO UPDATE SET
                    label = EXCLUDED.label,
                    description = EXCLUDED.description,
                    parent_slug = EXCLUDED.parent_slug,
                    adapter_key = EXCLUDED.adapter_key,
                    requires_api_endpoint = EXCLUDED.requires_api_endpoint,
                    built_in = true,
                    active = true,
                    sort_order = EXCLUDED.sort_order
                """
            ),
            {
                "slug": slug,
                "label": label,
                "description": desc,
                "parent_slug": parent,
                "adapter_key": adapter,
                "requires_api_endpoint": req_ep,
                "sort_order": sort_order,
            },
        )

    for slug in RETIRED:
        conn.execute(
            sa.text("UPDATE admin.providers SET active = false WHERE slug = :slug"),
            {"slug": slug},
        )


def downgrade() -> None:
    op.drop_constraint("fk_providers_parent_slug", "providers", schema="admin", type_="foreignkey")
    op.drop_column("providers", "requires_api_endpoint", schema="admin")
    op.drop_column("providers", "adapter_key", schema="admin")
    op.drop_column("providers", "parent_slug", schema="admin")
    op.drop_table("provider_parents", schema="admin")
