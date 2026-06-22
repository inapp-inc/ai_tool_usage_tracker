"""OpenAI provider adapter."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
import logging

from app.collector.adapters.base import ProviderMember, ProviderSnapshot, ProviderValidationError, UsageRecord
from app.collector.adapters.http_utils import get_with_detail
from app.collector.adapters.member_parsing import dedupe_members, parse_openai_org_users
from app.collector.adapters.openai_usage_parsing import (
    apply_openai_costs_to_records,
    merge_openai_costs,
    parse_openai_completions_payload,
    parse_openai_costs_as_usage_records,
    parse_openai_costs_payload,
)
from app.integration.http_log import log_provider_http

logger = logging.getLogger(__name__)

OPENAI_ORG_USERS_URL = "https://api.openai.com/v1/organization/users"
OPENAI_ORG_USAGE_URL = "https://api.openai.com/v1/organization/usage/completions"
OPENAI_ORG_EMBEDDINGS_URL = "https://api.openai.com/v1/organization/usage/embeddings"
OPENAI_ORG_IMAGES_URL = "https://api.openai.com/v1/organization/usage/images"
OPENAI_ORG_MODERATIONS_URL = "https://api.openai.com/v1/organization/usage/moderations"
OPENAI_ORG_COSTS_URL = "https://api.openai.com/v1/organization/costs"

# Aggregate pulls (no group_by) match OpenAI cookbook — one results row per bucket.
# group_by=user_id drops API-key-only usage where user_id is null.
_OPENAI_USAGE_ENDPOINTS: tuple[tuple[str, str], ...] = (
    (OPENAI_ORG_USAGE_URL, "completions"),
    (OPENAI_ORG_EMBEDDINGS_URL, "embeddings"),
    (OPENAI_ORG_IMAGES_URL, "images"),
    (OPENAI_ORG_MODERATIONS_URL, "moderations"),
)

_MAX_USAGE_PAGES = 50

_ORG_ADMIN_HINT = (
    "OpenAI organization endpoints require an Admin API key (not a project API key). "
    "Create one at platform.openai.com → Organization → Admin keys with "
    "organization usage and members read access."
)

OPENAI_MODELS_URL = "https://api.openai.com/v1/models"
OPENAI_ORG_PROJECTS_URL = "https://api.openai.com/v1/organization/projects"


def normalize_openai_admin_token(api_token: str) -> str:
    """Strip whitespace and common copy-paste wrappers from API keys."""
    token = api_token.strip().replace("\n", "").replace("\r", "")
    if len(token) >= 2 and token[0] == token[-1] and token[0] in {'"', "'"}:
        token = token[1:-1].strip()
    return token


def classify_openai_key(token: str) -> str:
    if token.startswith("sk-proj-"):
        return "project"
    if token.startswith("sk-admin-"):
        return "admin"
    if token.startswith("sk-svcacct-"):
        return "service_account"
    if token.startswith("sk-"):
        return "legacy"
    return "unknown"


def extract_openai_error_message(
    text: str,
    payload: dict | list | None,
) -> str:
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
    if cleaned:
        return cleaned[:240]
    return ""


def _openai_validation_probes(now: datetime) -> list[tuple[str, str, dict[str, str | int]]]:
    start_time = int((now - timedelta(days=1)).timestamp())
    return [
        ("organization/usage/completions", OPENAI_ORG_USAGE_URL, {"start_time": start_time, "limit": 1}),
        ("organization/costs", OPENAI_ORG_COSTS_URL, {"start_time": start_time, "limit": 1}),
        ("organization/users", OPENAI_ORG_USERS_URL, {"limit": 1}),
        ("organization/projects", OPENAI_ORG_PROJECTS_URL, {"limit": 1}),
    ]


def _openai_usage_query_params(
    since: datetime,
    until: datetime,
    *,
    group_by: tuple[str, ...] = (),
) -> list[tuple[str, str | int]]:
    """Build query params for OpenAI org usage/costs APIs (supports repeated group_by)."""
    range_seconds = max(int(until.timestamp()) - int(since.timestamp()), 60)
    if range_seconds >= 2 * 86400:
        bucket_width = "1d"
        limit = min(31, max(7, range_seconds // 86400 + 1))
    elif range_seconds >= 2 * 3600:
        bucket_width = "1h"
        limit = min(168, max(24, range_seconds // 3600 + 1))
    else:
        bucket_width = "1m"
        limit = min(1440, max(60, range_seconds // 60 + 1))

    params: list[tuple[str, str | int]] = [
        ("start_time", int(since.timestamp())),
        ("end_time", int(until.timestamp())),
        ("bucket_width", bucket_width),
        ("limit", limit),
    ]
    for field in group_by:
        params.append(("group_by", field))
    return params


def _openai_usage_detail_query_params(
    since: datetime,
    until: datetime,
) -> list[tuple[str, str | int]]:
    """Per-model breakdown; avoids group_by=user_id which omits key-only usage."""
    return _openai_usage_query_params(since, until, group_by=("model",))


def _openai_costs_query_params(
    since: datetime,
    until: datetime,
    *,
    group_by: tuple[str, ...] = (),
) -> list[tuple[str, str | int]]:
    range_seconds = max(int(until.timestamp()) - int(since.timestamp()), 60)
    days = max(range_seconds // 86400 + 1, 1)
    params: list[tuple[str, str | int]] = [
        ("start_time", int(since.timestamp())),
        ("end_time", int(until.timestamp())),
        ("bucket_width", "1d"),
        ("limit", min(180, days)),
    ]
    for field in group_by:
        params.append(("group_by", field))
    return params


class OpenAIUsageAdapter:
    provider = "openai"

    async def validate_api_key(
        self,
        api_token: str,
        *,
        pricing_config: dict | None = None,
        api_endpoint: str | None = None,
        **_kwargs: object,
    ) -> None:
        del pricing_config, api_endpoint
        token = normalize_openai_admin_token(api_token)
        if len(token) < 8:
            raise ProviderValidationError("OpenAI Admin API key must be at least 8 characters.")
        await self._validate_admin_api_key(token)

    async def _validate_admin_api_key(self, api_token: str) -> None:
        """Verify an Organization Admin API key against OpenAI admin endpoints."""
        key_kind = classify_openai_key(api_token)
        if key_kind == "project":
            raise ProviderValidationError(
                "You entered a project API key (sk-proj-…). "
                "OpenAI usage monitoring requires an Organization Admin API key (sk-admin-…). "
                "Create one at platform.openai.com → Organization → Admin keys."
            )
        if key_kind == "service_account":
            raise ProviderValidationError(
                "You entered a service account API key (sk-svcacct-…). "
                "Use an Organization Admin API key (sk-admin-…) instead. "
                "Create one at platform.openai.com → Organization → Admin keys."
            )

        headers = {"Authorization": f"Bearer {api_token}"}
        now = datetime.now(UTC)
        probe_results: list[tuple[str, int, str, dict | list | None]] = []

        for probe_name, url, params in _openai_validation_probes(now):
            result = await get_with_detail(url, headers=headers, params=params)
            log_provider_http(
                operation="validate_admin_api_key",
                method="GET",
                url=url,
                status_code=result.status_code,
                response_body=result.text[:500],
                tool_vendor="openai",
            )
            probe_results.append((probe_name, result.status_code, result.text, result.json))
            if result.status_code == 200:
                logger.info("OpenAI Admin API key authorized via %s", probe_name)
                return

        statuses = {status for _, status, _, _ in probe_results}
        if statuses == {401}:
            raise ProviderValidationError(
                "Invalid or expired OpenAI Admin API key (HTTP 401). "
                "Copy a fresh key from platform.openai.com → Organization → Admin keys."
            )

        models_result = await get_with_detail(OPENAI_MODELS_URL, headers=headers)
        if models_result.status_code == 200 and 403 in statuses:
            raise ProviderValidationError(
                "This key can call the OpenAI models API but is not an Organization Admin API key. "
                "Create an Admin key (sk-admin-…) at platform.openai.com → Organization → Admin keys."
            )

        if statuses == {403} or (403 in statuses and len(statuses) == 1):
            raise ProviderValidationError(
                "OpenAI rejected this key for all organization admin endpoints (HTTP 403). "
                "Use an Organization Admin API key (sk-admin-…) with read access to usage, costs, "
                "or members. Project keys cannot access these endpoints."
            )

        first_error = next(
            (
                extract_openai_error_message(text, payload)
                for _, status, text, payload in probe_results
                if status not in {401, 403} and (text or payload)
            ),
            "",
        )
        status_summary = ", ".join(
            f"{name}={status}" for name, status, _, _ in probe_results
        )
        detail = first_error or status_summary or "unknown error"
        raise ProviderValidationError(
            f"Could not authorize OpenAI Admin API key. {detail}. {_ORG_ADMIN_HINT}"
        )

    async def fetch_snapshot(
        self,
        api_token: str,
        *,
        package_allowance: int | None = None,
        **_kwargs: object,
    ) -> ProviderSnapshot:
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
            input_cost_per_1k=Decimal("0.005"),
            output_cost_per_1k=Decimal("0.015"),
            member_count=len(await self.fetch_members(api_token)),
        )

    async def fetch_members(self, api_token: str, **_kwargs: object) -> list[ProviderMember]:
        members = await self._fetch_org_users(api_token)
        if members:
            return members
        return await self._fetch_members_from_usage(api_token)

    async def _fetch_org_users(self, api_token: str) -> list[ProviderMember]:
        headers = {"Authorization": f"Bearer {api_token}"}
        members: list[ProviderMember] = []
        after: str | None = None

        for _ in range(10):
            params: dict[str, str | int] = {"limit": 100}
            if after:
                params["after"] = after
            result = await get_with_detail(
                OPENAI_ORG_USERS_URL,
                headers=headers,
                params=params,
            )
            log_provider_http(
                operation="fetch_org_users",
                method="GET",
                url=OPENAI_ORG_USERS_URL,
                status_code=result.status_code,
                response_body=result.text[:500],
                tool_vendor="openai",
            )
            if result.status_code == 403:
                logger.warning(
                    "OpenAI organization/users returned HTTP 403. %s",
                    _ORG_ADMIN_HINT,
                )
                return []
            if result.status_code == 401:
                logger.warning("OpenAI organization/users returned HTTP 401 — invalid or expired key.")
                return []
            if result.status_code != 200:
                logger.warning(
                    "OpenAI organization/users returned HTTP %s — skipping member list.",
                    result.status_code,
                )
                return []
            members.extend(parse_openai_org_users(result.json))
            payload = result.json
            if not isinstance(payload, dict) or not payload.get("has_more"):
                break
            next_after = payload.get("last_id")
            if not isinstance(next_after, str) or not next_after:
                break
            after = next_after

        return dedupe_members(members)

    async def _fetch_members_from_usage(self, api_token: str) -> list[ProviderMember]:
        """Derive member emails from org usage when organization/users is forbidden."""
        until = datetime.now(UTC)
        since = until - timedelta(days=90)
        records = await self.fetch_usage(api_token, since=since, until=until)
        if not records:
            return []
        members: list[ProviderMember] = []
        seen: set[str] = set()
        for record in records:
            email = record.user_email
            if not isinstance(email, str) or not email.strip():
                continue
            key = email.strip().lower()
            if key in seen:
                continue
            seen.add(key)
            members.append(ProviderMember(email=email.strip(), name=record.user_name))
        if members:
            logger.info(
                "OpenAI members derived from usage records (%s users) because organization/users was unavailable.",
                len(members),
            )
        return dedupe_members(members)

    async def fetch_usage(
        self,
        api_token: str,
        *,
        since: datetime,
        until: datetime,
        openai_pull_dumper: object | None = None,
    ) -> list[UsageRecord]:
        headers = {"Authorization": f"Bearer {api_token}"}
        user_id_map = await self._fetch_user_id_map(api_token)
        records: list[UsageRecord] = []
        seen_event_ids: set[str] = set()

        for url, usage_kind in _OPENAI_USAGE_ENDPOINTS:
            aggregate_params = _openai_usage_query_params(since, until)
            endpoint_records = await self._fetch_usage_from_endpoint(
                url,
                usage_kind=usage_kind,
                headers=headers,
                params=aggregate_params,
                user_id_map=user_id_map,
                since=since,
                seen_event_ids=seen_event_ids,
                operation=f"fetch_{usage_kind}_usage",
                openai_pull_dumper=openai_pull_dumper,
            )
            if not endpoint_records:
                detail_params = _openai_usage_detail_query_params(since, until)
                endpoint_records = await self._fetch_usage_from_endpoint(
                    url,
                    usage_kind=f"{usage_kind}-model",
                    headers=headers,
                    params=detail_params,
                    user_id_map=user_id_map,
                    since=since,
                    seen_event_ids=seen_event_ids,
                    operation=f"fetch_{usage_kind}_usage_by_model",
                    require_model=True,
                    openai_pull_dumper=openai_pull_dumper,
                )
            records.extend(endpoint_records)

        await self._merge_costs(
            headers,
            since,
            until,
            records,
            openai_pull_dumper=openai_pull_dumper,
        )
        logger.info(
            "OpenAI fetch_usage | records=%s since=%s until=%s",
            len(records),
            since.isoformat(),
            until.isoformat(),
        )
        return records

    async def _fetch_usage_from_endpoint(
        self,
        url: str,
        *,
        usage_kind: str,
        headers: dict[str, str],
        params: list[tuple[str, str | int]],
        user_id_map: dict[str, str],
        since: datetime,
        seen_event_ids: set[str],
        operation: str,
        require_model: bool = False,
        openai_pull_dumper: object | None = None,
    ) -> list[UsageRecord]:
        status, buckets = await self._fetch_all_buckets(
            url,
            headers=headers,
            params=params,
            operation=operation,
            openai_pull_dumper=openai_pull_dumper,
        )
        if status == 403:
            logger.warning(
                "OpenAI %s returned HTTP 403. %s",
                usage_kind,
                _ORG_ADMIN_HINT,
            )
            return []
        if status != 200:
            logger.warning("OpenAI %s returned HTTP %s — skipping", usage_kind, status)
            return []
        if not buckets:
            logger.info(
                "OpenAI %s returned no buckets | since=%s until=%s",
                usage_kind,
                since.isoformat(),
            )
            return []

        empty_buckets = sum(
            1
            for bucket in buckets
            if isinstance(bucket, dict)
            and isinstance(bucket.get("results"), list)
            and len(bucket.get("results", [])) == 0
            and bucket.get("input_tokens") is None
        )
        if empty_buckets == len(buckets):
            logger.info(
                "OpenAI %s returned %s buckets with empty results for this period.",
                usage_kind,
                len(buckets),
            )

        parsed = parse_openai_completions_payload(
            {"data": buckets},
            since=since,
            user_id_map=user_id_map,
            usage_kind=usage_kind,
            require_model=require_model,
        )
        unique: list[UsageRecord] = []
        for record in parsed:
            event_id = record.vendor_event_id or ""
            if event_id and event_id in seen_event_ids:
                continue
            if event_id:
                seen_event_ids.add(event_id)
            unique.append(record)
        return unique

    async def _fetch_all_buckets(
        self,
        url: str,
        *,
        headers: dict[str, str],
        params: list[tuple[str, str | int]],
        operation: str,
        openai_pull_dumper: object | None = None,
    ) -> tuple[int, list[dict]]:
        buckets: list[dict] = []
        page: str | None = None
        page_number = 0

        for _ in range(_MAX_USAGE_PAGES):
            page_params = list(params)
            if page:
                page_params.append(("page", page))
            result = await get_with_detail(url, headers=headers, params=page_params)
            log_provider_http(
                operation=operation,
                method="GET",
                url=url,
                status_code=result.status_code,
                response_body=result.text[:500],
                tool_vendor="openai",
            )
            if openai_pull_dumper is not None:
                write_raw = getattr(openai_pull_dumper, "write_raw_page", None)
                if callable(write_raw):
                    write_raw(
                        source=operation,
                        page=page_number,
                        request_params=dict(page_params),
                        response_payload=result.json,
                        status_code=result.status_code,
                        url=url,
                    )
            page_number += 1
            if result.status_code != 200:
                return result.status_code, buckets
            payload = result.json
            if not isinstance(payload, dict):
                return result.status_code, buckets
            data = payload.get("data")
            if isinstance(data, list):
                buckets.extend(row for row in data if isinstance(row, dict))
            page = payload.get("next_page")
            if not isinstance(page, str) or not page:
                return 200, buckets

        logger.warning("OpenAI %s pagination stopped after %s pages", operation, _MAX_USAGE_PAGES)
        return 200, buckets

    async def _fetch_user_id_map(self, api_token: str) -> dict[str, str]:
        headers = {"Authorization": f"Bearer {api_token}"}
        id_to_email: dict[str, str] = {}
        after: str | None = None

        for _ in range(10):
            params: dict[str, str | int] = {"limit": 100}
            if after:
                params["after"] = after
            result = await get_with_detail(
                OPENAI_ORG_USERS_URL,
                headers=headers,
                params=params,
            )
            if result.status_code != 200 or not isinstance(result.json, dict):
                break
            for row in result.json.get("data", []):
                if not isinstance(row, dict):
                    continue
                user_id = row.get("id")
                email = row.get("email")
                if isinstance(user_id, str) and isinstance(email, str) and email.strip():
                    id_to_email[user_id] = email.strip()
            payload = result.json
            if not payload.get("has_more"):
                break
            next_after = payload.get("last_id")
            if not isinstance(next_after, str) or not next_after:
                break
            after = next_after

        return id_to_email

    async def _merge_costs(
        self,
        headers: dict[str, str],
        since: datetime,
        until: datetime,
        records: list[UsageRecord],
        *,
        openai_pull_dumper: object | None = None,
    ) -> None:
        cost_params = _openai_costs_query_params(since, until)
        status, buckets = await self._fetch_all_buckets(
            OPENAI_ORG_COSTS_URL,
            headers=headers,
            params=cost_params,
            operation="fetch_costs",
            openai_pull_dumper=openai_pull_dumper,
        )
        if status != 200:
            if status == 403:
                logger.info("OpenAI organization/costs unavailable (HTTP 403) — costs not merged.")
            else:
                logger.warning("OpenAI organization/costs returned HTTP %s — costs not merged.", status)
            return

        if records:
            merge_openai_costs(records, parse_openai_costs_payload({"data": buckets}))
            apply_openai_costs_to_records(records, buckets, since=since)

        has_cost_on_usage = any(record.estimated_cost > 0 for record in records if record.total_tokens > 0)
        if has_cost_on_usage:
            return

        cost_records = parse_openai_costs_as_usage_records({"data": buckets}, since=since)
        if not cost_records:
            detail_params = _openai_costs_query_params(since, until, group_by=("line_item",))
            detail_status, detail_buckets = await self._fetch_all_buckets(
                OPENAI_ORG_COSTS_URL,
                headers=headers,
                params=detail_params,
                operation="fetch_costs_by_line_item",
                openai_pull_dumper=openai_pull_dumper,
            )
            if detail_status == 200:
                cost_records = parse_openai_costs_as_usage_records(
                    {"data": detail_buckets},
                    since=since,
                )

        if cost_records:
            logger.info(
                "OpenAI costs ingested as standalone rows | cost_records=%s usage_records=%s",
                len(cost_records),
                len(records),
            )
            records.extend(cost_records)
