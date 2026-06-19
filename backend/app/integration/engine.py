"""Execute usage polling from tool integration_config."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.collector.adapters.base import UsageRecord
from app.collector.adapters.http_utils import HttpResult, get_with_detail, post_with_detail
from app.integration.auth import build_auth_headers
from app.integration.http_log import log_provider_http
from app.integration.mapping import extract_records, map_record
from app.integration.placeholders import apply_placeholders, apply_placeholders_to_mapping, build_context


class IntegrationConfigError(Exception):
    """Raised when integration_config is invalid or the HTTP call fails."""


def validate_integration_config(config: dict) -> None:
    usage = config.get("usage")
    if not usage or not isinstance(usage, dict):
        return

    url = str(usage.get("url") or "").strip()
    if not url:
        msg = "integration_config.usage.url is required when usage polling is configured."
        raise IntegrationConfigError(msg)

    response = usage.get("response") or {}
    fields = response.get("fields") or {}
    for required in ("vendor_event_id", "occurred_at", "input_tokens"):
        if not str(fields.get(required) or "").strip():
            msg = f"integration_config.usage.response.fields.{required} is required."
            raise IntegrationConfigError(msg)


async def execute_usage_http(
    api_token: str,
    *,
    integration_config: dict,
    since: datetime,
    until: datetime,
    api_endpoint: str | None,
    operation: str = "usage",
    tool_vendor: str | None = None,
    pricing_config: dict | None = None,
) -> HttpResult:
    config = integration_config or {}
    usage = config.get("usage")
    if not usage or not isinstance(usage, dict):
        msg = "integration_config.usage is required for config-driven polling."
        raise IntegrationConfigError(msg)

    validate_integration_config(config)

    context = build_context(
        api_endpoint=api_endpoint,
        since=since,
        until=until,
        pricing_config=pricing_config,
    )
    url = apply_placeholders(str(usage.get("url") or ""), context).strip()
    if not url or "{" in url:
        if "{organization_id}" in str(usage.get("url") or ""):
            msg = (
                "GitHub organization ID is missing. Set it on the Copilot tool "
                "(Tools page) or when connecting credentials."
            )
            raise IntegrationConfigError(msg)
        msg = "Usage URL is empty or has unresolved placeholders."
        raise IntegrationConfigError(msg)

    method = str(usage.get("method") or "GET").upper()
    query = apply_placeholders_to_mapping(usage.get("query"), context)
    headers = build_auth_headers(config.get("auth"), api_token, config.get("headers"))

    if method == "POST":
        body_raw = usage.get("body")
        body = apply_placeholders_to_mapping(body_raw, context) if isinstance(body_raw, dict) else None
        result = await post_with_detail(url, headers=headers, json_body=body)
    else:
        params = {key: str(value) for key, value in query.items()}
        result = await get_with_detail(url, headers=headers, params=params or None)

    log_provider_http(
        operation=operation,
        method=method,
        url=url,
        status_code=result.status_code,
        response_body=result.text,
        tool_vendor=tool_vendor,
    )
    return result


async def validate_connection_from_config(
    api_token: str,
    *,
    integration_config: dict,
    api_endpoint: str | None,
    tool_vendor: str | None = None,
    pricing_config: dict | None = None,
) -> None:
    """Probe the configured usage URL to verify credentials (same HTTP shape as polling)."""
    until = datetime.now(UTC)
    since = until - timedelta(days=1)
    result = await execute_usage_http(
        api_token,
        integration_config=integration_config,
        since=since,
        until=until,
        api_endpoint=api_endpoint,
        operation="validate",
        tool_vendor=tool_vendor,
        pricing_config=pricing_config,
    )
    if result.status_code == 401:
        raise IntegrationConfigError("Invalid API key (HTTP 401).")
    if result.status_code == 403:
        raise IntegrationConfigError("Insufficient API scope (HTTP 403).")
    if result.status_code >= 400:
        raise IntegrationConfigError(
            f"API validation failed (HTTP {result.status_code}). "
            "See Docker api logs for the provider response body."
        )


async def fetch_usage_from_config(
    api_token: str,
    *,
    integration_config: dict,
    since: datetime,
    until: datetime,
    api_endpoint: str | None,
    tool_vendor: str | None = None,
    pricing_config: dict | None = None,
) -> list[UsageRecord]:
    result = await execute_usage_http(
        api_token,
        integration_config=integration_config,
        since=since,
        until=until,
        api_endpoint=api_endpoint,
        operation="usage",
        tool_vendor=tool_vendor,
        pricing_config=pricing_config,
    )

    if result.status_code >= 400:
        msg = f"Usage API returned HTTP {result.status_code}. See Docker api logs for response body."
        raise IntegrationConfigError(msg)

    config = integration_config or {}
    usage = config.get("usage") or {}
    response = usage.get("response") or {}
    response_type = str(response.get("type") or "json_array")
    records_path = str(response.get("records_path") or "").strip()
    fields = response.get("fields") or {}

    raw_records = extract_records(result.json, records_path, response_type)
    results: list[UsageRecord] = []
    for record in raw_records:
        mapped = map_record(record, fields)
        results.append(
            UsageRecord(
                vendor_event_id=mapped["vendor_event_id"],
                model=mapped["model"],
                occurred_at=mapped["occurred_at"],
                input_tokens=mapped["input_tokens"],
                output_tokens=mapped["output_tokens"],
                estimated_cost=mapped["estimated_cost"],
                user_email=mapped.get("user_email"),
                user_name=mapped.get("user_name"),
            )
        )
    return results
