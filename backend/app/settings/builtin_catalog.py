"""Built-in provider catalogue — single source of truth for seeds and adapters."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderParentSeed:
    slug: str
    label: str
    sort_order: int


@dataclass(frozen=True)
class ProviderProductSeed:
    slug: str
    label: str
    parent_slug: str | None
    adapter_key: str
    sort_order: int
    requires_api_endpoint: bool = False
    description: str | None = None


BUILTIN_PROVIDER_PARENTS: tuple[ProviderParentSeed, ...] = (
    ProviderParentSeed("openai", "OpenAI", 10),
    ProviderParentSeed("anthropic", "Anthropic", 20),
    ProviderParentSeed("google", "Google", 30),
    ProviderParentSeed("microsoft", "Microsoft", 40),
    ProviderParentSeed("amazon", "Amazon", 50),
    ProviderParentSeed("cursor", "Cursor", 60),
    ProviderParentSeed("figma", "Figma", 70),
)

BUILTIN_PROVIDER_PRODUCTS: tuple[ProviderProductSeed, ...] = (
    ProviderProductSeed("openai", "OpenAI", "openai", "openai", 10),
    ProviderProductSeed(
        "anthropic",
        "Anthropic Claude",
        "anthropic",
        "anthropic",
        20,
        description="Claude models via Anthropic API.",
    ),
    ProviderProductSeed(
        "google",
        "Google Gemini",
        "google",
        "google",
        30,
        description="Gemini models via Google AI / Vertex.",
    ),
    ProviderProductSeed(
        "azure_openai",
        "Azure OpenAI Platform",
        "microsoft",
        "azure_openai",
        40,
        requires_api_endpoint=True,
        description="Azure-hosted OpenAI deployments.",
    ),
    ProviderProductSeed(
        "copilot",
        "Microsoft Copilot",
        "microsoft",
        "copilot",
        50,
        requires_api_endpoint=False,
        description="GitHub Copilot — requires GitHub organization ID for API URLs.",
    ),
    ProviderProductSeed(
        "bedrock",
        "Amazon Bedrock",
        "amazon",
        "bedrock",
        60,
        requires_api_endpoint=True,
        description="AWS Bedrock model usage.",
    ),
    ProviderProductSeed("cursor", "Cursor", "cursor", "cursor", 70),
    ProviderProductSeed("figma", "Figma", "figma", "figma", 80),
    ProviderProductSeed(
        "custom",
        "Custom Integration",
        None,
        "custom",
        200,
        requires_api_endpoint=True,
        description="Future: config-driven HTTP integration (integration_config).",
    ),
)

BUILTIN_PRODUCT_SLUGS = frozenset(p.slug for p in BUILTIN_PROVIDER_PRODUCTS)

# Products auto-provisioned as org catalogue tools (excludes Custom Integration).
BUILTIN_CATALOGUE_SLUGS = frozenset(
    p.slug for p in BUILTIN_PROVIDER_PRODUCTS if p.slug != "custom"
)

# Slugs retired from the default catalogue (remain in DB inactive if present).
RETIRED_PRODUCT_SLUGS = frozenset({"cohere", "mistral", "mabl", "windsurf", "github_copilot"})

ADAPTER_ALIASES: dict[str, str] = {
    "claude": "anthropic",
    "gemini": "google",
    "github_copilot": "copilot",
    "github": "copilot",
}

COPILOT_DEFAULT_API_ENDPOINT = "https://api.github.com"

COPILOT_INTEGRATION_CONFIG: dict = {
    "version": 1,
    "auth": {"type": "bearer", "header": "Authorization", "prefix": "Bearer "},
    "headers": {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    },
    "usage": {
        "method": "GET",
        "url": f"{COPILOT_DEFAULT_API_ENDPOINT}/orgs/{{organization_id}}/copilot/billing/seats",
        "response": {
            "type": "json_object",
            "records_path": "seats",
            "fields": {
                "vendor_event_id": "assignee.login",
                "occurred_at": "{until_date}",
                "input_tokens": "1",
                "output_tokens": "0",
                "estimated_cost": "0",
                "model": "copilot",
                "user_email": "assignee.login",
                "user_name": "assignee.login",
            },
        },
    },
}
