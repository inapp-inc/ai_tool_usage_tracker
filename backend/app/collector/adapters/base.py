"""Shared types and errors for provider adapters."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Literal

SyncStatus = Literal["active", "inactive", "error"]

SUPPORTED_PROVIDERS = frozenset(
    {
        "openai",
        "anthropic",
        "google",
        "azure_openai",
        "cohere",
        "mistral",
        "custom",
        "mabl",
        "windsurf",
        "cursor",
    }
)


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
