"""Default provider catalog seeded per organization."""

DEFAULT_PROVIDERS: list[dict[str, str | bool]] = [
    {
        "slug": "openai",
        "name": "OpenAI",
        "usage_api_url": "https://api.openai.com/v1/usage",
        "description": "OpenAI platform usage API",
        "is_system": True,
    },
    {
        "slug": "anthropic",
        "name": "Anthropic",
        "usage_api_url": "https://api.anthropic.com/v1/usage",
        "description": "Anthropic Claude usage API",
        "is_system": True,
    },
    {
        "slug": "google",
        "name": "Google",
        "usage_api_url": "https://generativelanguage.googleapis.com/v1/usage",
        "description": "Google Gemini usage API",
        "is_system": True,
    },
    {
        "slug": "azure_openai",
        "name": "Azure OpenAI",
        "usage_api_url": "https://{resource}.openai.azure.com/openai/usage",
        "description": "Azure OpenAI usage endpoint (replace {resource})",
        "is_system": True,
    },
    {
        "slug": "cohere",
        "name": "Cohere",
        "usage_api_url": "https://api.cohere.ai/v1/usage",
        "description": "Cohere usage API",
        "is_system": True,
    },
    {
        "slug": "mistral",
        "name": "Mistral",
        "usage_api_url": "https://api.mistral.ai/v1/usage",
        "description": "Mistral usage API",
        "is_system": True,
    },
    {
        "slug": "cursor",
        "name": "Cursor",
        "usage_api_url": "https://api.cursor.com/teams/daily-usage-data",
        "description": "Cursor Team Admin API (Basic auth, POST daily usage)",
        "is_system": True,
    },
]
