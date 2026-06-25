"""Anthropic (Claude) provider adapter."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.collector.adapters.anthropic_query import (
    anthropic_cost_query_params,
    anthropic_usage_query_params,
    usage_param_fallbacks,
)
from app.collector.adapters.anthropic_usage_parsing import (
    apply_anthropic_costs_to_records,
    parse_anthropic_usage_payload,
)
from app.collector.adapters.base import ProviderMember, ProviderSnapshot, ProviderValidationError, UsageRecord
from app.collector.adapters.http_utils import get_with_detail
from app.integration.http_log import log_provider_http
from app.normalization.converters import token_to_usage_record
from app.normalization.token import map_anthropic_usage

logger = logging.getLogger(__name__)

ANTHROPIC_MODELS_URL = "https://api.anthropic.com/v1/models"
ANTHROPIC_ORG_ME_URL = "https://api.anthropic.com/v1/organizations/me"
ANTHROPIC_USAGE_URL = "https://api.anthropic.com/v1/organizations/usage_report/messages"
ANTHROPIC_COST_URL = "https://api.anthropic.com/v1/organizations/cost_report"
ANTHROPIC_USERS_URL = "https://api.anthropic.com/v1/organizations/users"

_MAX_USAGE_PAGES = 50

_ADMIN_KEY_HINT = (
    "Anthropic usage monitoring requires an Admin API key (sk-ant-admin-…), not a standard "
    "Messages API key (sk-ant-api…). Create one in Claude Console → Settings → Admin keys."
)


def normalize_anthropic_token(api_token: str) -> str:
    token = api_token.strip().replace("\n", "").replace("\r", "")
    if len(token) >= 2 and token[0] == token[-1] and token[0] in {'"', "'"}:
        token = token[1:-1].strip()
    return token


def classify_anthropic_key(token: str) -> str:
    if token.startswith("sk-ant-admin"):
        return "admin"
    if token.startswith("sk-ant-api"):
        return "api"
    return "unknown"


def extract_anthropic_error_message(text: str, payload: dict | list | None) -> str:
    if isinstance(payload, dict):
        error = payload.get("error")
        if isinstance(error, dict):
            message = error.get("message")
            if isinstance(message, str) and message.strip():
                return message.strip()
        message = payload.get("message")
        if isinstance(message, str) and message.strip():
            return message.strip()
    cleaned = text.strip()
    return cleaned[:240] if cleaned else ""


def _headers(api_token: str) -> dict[str, str]:
    return {
        "x-api-key": api_token,
        "anthropic-version": "2023-06-01",
    }


class AnthropicUsageAdapter:
    provider = "anthropic"

    async def validate_api_key(self, api_token: str, **_kwargs: object) -> None:
        token = normalize_anthropic_token(api_token)
        if len(token) < 8:
            raise ProviderValidationError("Anthropic API key must be at least 8 characters.")

        key_kind = classify_anthropic_key(token)
        if key_kind == "admin":
            await self._validate_admin_api_key(token)
            return

        result = await get_with_detail(ANTHROPIC_MODELS_URL, headers=_headers(token))
        status = result.status_code
        if status == 401:
            raise ProviderValidationError("Invalid Anthropic API key.")
        if status >= 400:
            raise ProviderValidationError(f"Anthropic API key validation failed (HTTP {status}).")
        if key_kind == "api":
            raise ProviderValidationError(_ADMIN_KEY_HINT)

    async def _validate_admin_api_key(self, api_token: str) -> None:
        headers = _headers(api_token)
        now = datetime.now(UTC)
        since = now - timedelta(days=1)
        params = anthropic_usage_query_params(since, now, group_by=())
        params = [(key, value) for key, value in params if not key.startswith("group_by")]
        params = [(key, value) for key, value in params if key != "limit"]
        params.append(("limit", 1))

        for probe_name, url, probe_params in (
            ("organizations/me", ANTHROPIC_ORG_ME_URL, None),
            ("usage_report/messages", ANTHROPIC_USAGE_URL, params),
        ):
            result = await get_with_detail(url, headers=headers, params=probe_params)
            log_provider_http(
                operation="validate_admin_api_key",
                method="GET",
                url=url,
                status_code=result.status_code,
                response_body=result.text[:500],
                tool_vendor="anthropic",
            )
            if result.status_code == 200:
                logger.info("Anthropic Admin API key authorized via %s", probe_name)
                return

        models_result = await get_with_detail(ANTHROPIC_MODELS_URL, headers=headers)
        usage_result = await get_with_detail(
            ANTHROPIC_USAGE_URL,
            headers=headers,
            params=params,
        )
        if models_result.status_code == 200 and usage_result.status_code in {401, 403}:
            raise ProviderValidationError(_ADMIN_KEY_HINT)

        detail = extract_anthropic_error_message(usage_result.text, usage_result.json)
        if usage_result.status_code in {401, 403}:
            raise ProviderValidationError(
                f"Invalid or unauthorized Anthropic Admin API key (HTTP {usage_result.status_code}). "
                f"{detail or _ADMIN_KEY_HINT}"
            )
        raise ProviderValidationError(
            f"Anthropic Admin API key validation failed (HTTP {usage_result.status_code}). "
            f"{detail or _ADMIN_KEY_HINT}"
        )

    async def fetch_snapshot(
        self,
        api_token: str,
        *,
        package_allowance: int | None = None,
        pricing_config: dict | None = None,
        **_kwargs: object,
    ) -> ProviderSnapshot:
        del pricing_config
        until = datetime.now(UTC)
        since = until - timedelta(days=30)
        records = await self.fetch_usage(api_token, since=since, until=until)
        tokens_used = sum(record.total_tokens for record in records)
        total_cost = sum((record.estimated_cost for record in records), Decimal("0"))
        balance = None
        if package_allowance is not None:
            balance = max(package_allowance - tokens_used, 0)
        return ProviderSnapshot(
            sync_status="active",
            tokens_used=tokens_used,
            balance_tokens=balance,
            total_cost=total_cost,
            input_cost_per_1k=Decimal("0.003"),
            output_cost_per_1k=Decimal("0.015"),
        )

    async def fetch_usage(
        self,
        api_token: str,
        *,
        since: datetime,
        until: datetime,
        **_kwargs: object,
    ) -> list[UsageRecord]:
        token = normalize_anthropic_token(api_token)
        if classify_anthropic_key(token) != "admin":
            logger.warning(
                "Anthropic fetch_usage | requires Admin API key | since=%s until=%s | %s",
                since.isoformat(),
                until.isoformat(),
                _ADMIN_KEY_HINT,
            )
            return []

        headers = _headers(token)
        account_email_map = await self._fetch_account_email_map(headers)
        records: list[UsageRecord] = []
        seen_event_ids: set[str] = set()

        usage_buckets = await self._fetch_usage_buckets(headers, since=since, until=until)
        for record in parse_anthropic_usage_payload(
            {"data": usage_buckets},
            since=since,
            account_email_map=account_email_map,
        ):
            if record.vendor_event_id in seen_event_ids:
                continue
            seen_event_ids.add(record.vendor_event_id)
            records.append(record)

        cost_buckets, _ok = await self._fetch_all_buckets(
            ANTHROPIC_COST_URL,
            headers=headers,
            params=anthropic_cost_query_params(since, until),
            operation="fetch_cost_report",
        )
        apply_anthropic_costs_to_records(records, cost_buckets, since=since)

        logger.info(
            "Anthropic fetch_usage | records=%s since=%s until=%s",
            len(records),
            since.isoformat(),
            until.isoformat(),
        )
        return records

    async def fetch_members(
        self,
        api_token: str,
        **_kwargs: object,
    ) -> list[ProviderMember]:
        token = normalize_anthropic_token(api_token)
        if classify_anthropic_key(token) != "admin":
            return []

        headers = _headers(token)
        members: list[ProviderMember] = []
        after_id: str | None = None
        for _ in range(20):
            params: dict[str, str | int] = {"limit": 100}
            if after_id:
                params["after_id"] = after_id
            result = await get_with_detail(ANTHROPIC_USERS_URL, headers=headers, params=params)
            if result.status_code != 200 or not isinstance(result.json, dict):
                break
            for row in result.json.get("data") or []:
                if not isinstance(row, dict):
                    continue
                email = str(row.get("email") or "").strip()
                if not email:
                    continue
                members.append(
                    ProviderMember(
                        email=email,
                        name=str(row.get("name") or "").strip() or None,
                    )
                )
            if not result.json.get("has_more"):
                break
            after_id = str(result.json.get("last_id") or "")
            if not after_id:
                break
        return members

    async def _fetch_account_email_map(self, headers: dict[str, str]) -> dict[str, str]:
        mapping: dict[str, str] = {}
        after_id: str | None = None
        for _ in range(20):
            params: dict[str, str | int] = {"limit": 100}
            if after_id:
                params["after_id"] = after_id
            result = await get_with_detail(ANTHROPIC_USERS_URL, headers=headers, params=params)
            if result.status_code != 200 or not isinstance(result.json, dict):
                break
            for row in result.json.get("data") or []:
                if not isinstance(row, dict):
                    continue
                user_id = str(row.get("id") or "").strip()
                email = str(row.get("email") or "").strip()
                if user_id and email:
                    mapping[user_id] = email
            if not result.json.get("has_more"):
                break
            after_id = str(result.json.get("last_id") or "")
            if not after_id:
                break
        return mapping

    async def _fetch_usage_buckets(
        self,
        headers: dict[str, str],
        *,
        since: datetime,
        until: datetime,
    ) -> list[dict]:
        for params in usage_param_fallbacks(since, until):
            buckets, ok = await self._fetch_all_buckets(
                ANTHROPIC_USAGE_URL,
                headers=headers,
                params=params,
                operation="fetch_usage_report",
            )
            if ok:
                return buckets
        return []

    async def _fetch_all_buckets(
        self,
        url: str,
        *,
        headers: dict[str, str],
        params: list[tuple[str, str | int]],
        operation: str,
    ) -> tuple[list[dict], bool]:
        buckets: list[dict] = []
        page: str | None = None
        for page_index in range(_MAX_USAGE_PAGES):
            page_params = list(params)
            if page:
                page_params.append(("page", page))
            result = await get_with_detail(url, headers=headers, params=page_params)
            log_provider_http(
                operation=operation,
                method="GET",
                url=url,
                status_code=result.status_code,
                response_body=result.text[:500] if result.status_code >= 400 else "",
                tool_vendor="anthropic",
            )
            if result.status_code >= 400:
                logger.warning(
                    "Anthropic %s failed | status=%s body=%s",
                    operation,
                    result.status_code,
                    (result.text or "")[:300],
                )
                return [], False
            payload = result.json if isinstance(result.json, dict) else {}
            data = payload.get("data")
            if isinstance(data, list):
                buckets.extend(row for row in data if isinstance(row, dict))
            if not payload.get("has_more"):
                break
            next_page = payload.get("next_page")
            if not isinstance(next_page, str) or not next_page.strip():
                break
            page = next_page.strip()
            if page_index + 1 >= _MAX_USAGE_PAGES:
                logger.warning("Anthropic %s pagination stopped at max pages", operation)
        return buckets, True

    @staticmethod
    def parse_usage_rows(rows: list[dict], *, fallback_at: datetime) -> list[UsageRecord]:
        records: list[UsageRecord] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            normalized = map_anthropic_usage(row, fallback_at=fallback_at)
            if normalized is not None:
                records.append(token_to_usage_record(normalized))
        return records
