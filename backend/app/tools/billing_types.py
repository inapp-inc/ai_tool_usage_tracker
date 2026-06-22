"""Billing type constants and vendor mapping (ToolNewFlow)."""

from typing import Literal

BillingType = Literal[
    "TOKEN_BASED",
    "REQUEST_BASED",
    "CREDIT_BASED",
    "SEAT_BASED",
    "LICENSE_BASED",
]

BILLING_TYPES: frozenset[str] = frozenset(
    {
        "TOKEN_BASED",
        "REQUEST_BASED",
        "CREDIT_BASED",
        "SEAT_BASED",
        "LICENSE_BASED",
    }
)

VENDOR_BILLING_TYPE: dict[str, BillingType] = {
    "openai": "TOKEN_BASED",
    "anthropic": "TOKEN_BASED",
    "google": "TOKEN_BASED",
    "azure_openai": "TOKEN_BASED",
    "bedrock": "TOKEN_BASED",
    "cursor": "REQUEST_BASED",
    "copilot": "SEAT_BASED",
    "figma": "SEAT_BASED",
    "custom": "TOKEN_BASED",
}


def billing_type_for_vendor(vendor: str) -> BillingType:
    return VENDOR_BILLING_TYPE.get(vendor, "TOKEN_BASED")
