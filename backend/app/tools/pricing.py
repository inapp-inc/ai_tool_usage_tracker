"""Pricing field normalization for tools API."""

from decimal import Decimal
from typing import Any

from fastapi import HTTPException, status

from app.settings.builtin_catalog import ADAPTER_ALIASES, BUILTIN_PRODUCT_SLUGS

SUPPORTED_VENDORS = frozenset(BUILTIN_PRODUCT_SLUGS) | frozenset(ADAPTER_ALIASES.keys())

SPECIALIZED_ADAPTER_VENDORS = frozenset(
    slug
    for slug in BUILTIN_PRODUCT_SLUGS
    if slug not in {"custom"}
)


def normalize_vendor(value: str) -> str:
    slug = value.strip().lower().replace(" ", "_").replace("-", "_")
    aliases = {
        "open_ai": "openai",
        "azureopenai": "azure_openai",
    }
    return aliases.get(slug, slug)


def validate_vendor(value: str) -> str:
    """Normalize vendor slug; existence is validated against admin.providers in service layer."""
    slug = normalize_vendor(value)
    if not slug:
        msg = "Vendor is required."
        raise ValueError(msg)
    return slug


def vendor_requires_organization_id(vendor: str) -> bool:
    return vendor.strip().lower().replace("-", "_") in {"copilot", "github_copilot", "github"}


def organization_id_from_pricing(pricing_config: dict | None) -> str | None:
    raw = (pricing_config or {}).get("organization_id")
    if raw is None:
        return None
    stripped = str(raw).strip()
    return stripped or None


def validate_organization_id(value: str) -> str:
    stripped = value.strip()
    if not stripped:
        msg = "organization_id is required for this provider."
        raise ValueError(msg)
    if len(stripped) > 100:
        msg = "organization_id must be at most 100 characters."
        raise ValueError(msg)
    return stripped


def vendor_requires_api_endpoint(vendor: str, *, built_in: bool, requires_api_endpoint: bool = False) -> bool:
    """Prefer provider.requires_api_endpoint from DB; fallback for legacy callers."""
    if vendor_requires_organization_id(vendor):
        return False
    if requires_api_endpoint:
        return True
    if vendor == "custom":
        return True
    if not built_in:
        return True
    return vendor in {"azure_openai", "bedrock"}


def validate_pricing_model(pricing_model: str) -> None:
    allowed = {"flat_token", "package_with_overage", "custom"}
    if pricing_model not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid pricing_model: {pricing_model}",
        )


def merge_pricing_config(
    existing: dict[str, Any],
    incoming: dict[str, Any] | None,
) -> dict[str, Any]:
    if not incoming:
        return dict(existing)
    merged = dict(existing)
    merged.update(incoming)
    return merged


def normalize_pricing_config(
    pricing_model: str,
    pricing_config: dict[str, Any] | None,
    *,
    package_allowance: int | None = None,
    overage_price: Decimal | None = None,
) -> dict[str, Any]:
    """Ensure pricing_config contains FE fields and sync from top-level columns."""
    config = dict(pricing_config or {})

    if package_allowance is not None:
        config["included_tokens"] = package_allowance
    elif config.get("included_tokens") is not None:
        try:
            int(config["included_tokens"])
        except (TypeError, ValueError):
            pass

    if overage_price is not None:
        config["overage_rate"] = float(overage_price)
    elif config.get("overage_rate") is not None:
        try:
            Decimal(str(config["overage_rate"]))
        except Exception:  # noqa: BLE001
            pass

    if pricing_model == "package_with_overage" and config.get("model") is None:
        config["model"] = "flat_fee"

    return config


def pricing_config_for_response(
    pricing_model: str,
    pricing_config: dict[str, Any] | None,
    *,
    package_allowance: int | None,
    overage_price: Decimal | None,
) -> dict[str, Any]:
    """Expose plan name, included tokens, and overage rate in API pricing_config."""
    config = dict(pricing_config or {})

    if package_allowance is not None:
        config["included_tokens"] = package_allowance
    if overage_price is not None:
        config["overage_rate"] = float(overage_price)

    if pricing_model == "package_with_overage" and config.get("model") is None:
        config["model"] = "flat_fee"

    return config
