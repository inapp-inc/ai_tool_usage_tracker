"""Built-in package definitions per vendor slug (ToolNewFlow §3.3)."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.tools.billing_types import BillingType, billing_type_for_vendor


@dataclass(frozen=True)
class PackageSeed:
    package_name: str
    monthly_price: Decimal | None = None
    yearly_price: Decimal | None = None
    token_limit: int | None = None
    request_limit: int | None = None
    seat_limit: int | None = None
    credit_limit: Decimal | None = None


VENDOR_PACKAGES: dict[str, tuple[PackageSeed, ...]] = {
    "cursor": (
        PackageSeed("Hobby"),
        PackageSeed("Pro", monthly_price=Decimal("20")),
        PackageSeed("Business", monthly_price=Decimal("40"), request_limit=500),
        PackageSeed("Enterprise"),
    ),
    "openai": (
        PackageSeed("Pay As You Go"),
        PackageSeed("Scale Tier"),
        PackageSeed("Enterprise"),
    ),
    "copilot": (
        PackageSeed("Individual", monthly_price=Decimal("10"), seat_limit=1),
        PackageSeed("Business", monthly_price=Decimal("19"), seat_limit=1),
        PackageSeed("Enterprise"),
    ),
    "figma": (
        PackageSeed("Starter", seat_limit=3),
        PackageSeed("Professional", monthly_price=Decimal("15"), seat_limit=1),
        PackageSeed("Organization"),
        PackageSeed("Enterprise"),
    ),
    "anthropic": (
        PackageSeed("Free"),
        PackageSeed("Pro", monthly_price=Decimal("20")),
        PackageSeed("Team", monthly_price=Decimal("30")),
        PackageSeed("Enterprise"),
    ),
    "google": (
        PackageSeed("Free"),
        PackageSeed("Advanced", monthly_price=Decimal("20")),
        PackageSeed("Workspace Enterprise"),
    ),
    "azure_openai": (
        PackageSeed("Pay As You Go"),
        PackageSeed("Enterprise"),
    ),
    "bedrock": (
        PackageSeed("Pay As You Go"),
        PackageSeed("Enterprise"),
    ),
}


def packages_for_vendor(vendor: str) -> tuple[PackageSeed, ...]:
    return VENDOR_PACKAGES.get(vendor, ())


def billing_type_for_package_vendor(vendor: str) -> BillingType:
    return billing_type_for_vendor(vendor)
