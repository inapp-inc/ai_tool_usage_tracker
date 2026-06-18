"""Shared types and errors for provider adapters."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Literal

from app.settings.builtin_catalog import ADAPTER_ALIASES, BUILTIN_PRODUCT_SLUGS

SyncStatus = Literal["active", "inactive", "error"]

SUPPORTED_PROVIDERS = frozenset(BUILTIN_PRODUCT_SLUGS) | frozenset(ADAPTER_ALIASES.keys())


def resolve_provider_api_url(
    api_endpoint: str | None,
    *,
    default_url: str,
) -> str:
    """Prefer tool.api_endpoint when set; otherwise use the adapter default."""
    if api_endpoint and api_endpoint.strip():
        return api_endpoint.strip()
    return default_url


class ProviderValidationError(Exception):
    """Raised when an API key fails provider validation."""


@dataclass(frozen=True)
class UsageRecord:
    """Canonical usage row produced by a collector adapter."""

    vendor_event_id: str
    model: str | None
    occurred_at: datetime
    input_tokens: int
    output_tokens: int
    estimated_cost: Decimal
    user_email: str | None = None
    user_name: str | None = None

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


@dataclass(frozen=True)
class ProviderMember:
    """Team member associated with a provider API token."""

    email: str
    name: str | None = None


@dataclass(frozen=True)
class ProviderSnapshot:
    """Account-level usage snapshot from a vendor API."""

    sync_status: SyncStatus
    tokens_used: int
    balance_tokens: int | None
    total_cost: Decimal
    input_cost_per_1k: Decimal | None = None
    output_cost_per_1k: Decimal | None = None
    member_count: int | None = None
