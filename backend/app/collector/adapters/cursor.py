"""Cursor provider adapter."""

import base64
import logging
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.collector.adapters.base import ProviderMember, ProviderSnapshot, ProviderValidationError, UsageRecord
from app.collector.adapters.http_utils import get_json, get_with_detail, post_with_detail
from app.collector.adapters.cursor_dump import CursorPullDumper
from app.collector.adapters.member_parsing import parse_cursor_members
from app.collector.adapters.usage_parsing import parse_cursor_daily_usage_page, parse_cursor_usage_page
from app.integration.http_log import log_provider_http

logger = logging.getLogger(__name__)

MAX_USAGE_PAGES = 50
DEFAULT_USAGE_PAGE_SIZE = 100
MAX_FILTERED_USAGE_DAYS = 30
MAX_DAILY_USAGE_DAYS = 90

FILTERED_USAGE_URL = "https://api.cursor.com/teams/filtered-usage-events"
DAILY_USAGE_URL = "https://api.cursor.com/teams/daily-usage-data"
MEMBERS_URL = "https://api.cursor.com/teams/members"
ME_URL = "https://api.cursor.com/v1/me"


def _basic_auth_headers(api_token: str) -> dict[str, str]:
    encoded = base64.b64encode(f"{api_token}:".encode()).decode("ascii")
    return {"Authorization": f"Basic {encoded}"}


def _cursor_usage_error(status: int, payload: object, text: str) -> str:
    if status == 401:
        return (
            "Cursor Team Admin API key required to pull usage. "
            "Create one in Cursor → Settings → Admin API (Enterprise plan)."
        )
    if status == 403:
        return "Cursor team usage API requires an Enterprise plan and Team Admin API key."
    if status == 429:
        return "Cursor API rate limit exceeded. Try again in a few minutes."
    if status == 400:
        message = ""
        if isinstance(payload, dict):
            raw = payload.get("message") or payload.get("error")
            if isinstance(raw, str):
                message = raw.strip()
        detail = f" {message}" if message else ""
        return f"Cursor usage request rejected (HTTP 400).{detail}"
    if status >= 500:
        return f"Cursor usage API temporarily unavailable (HTTP {status})."
    snippet = text.strip().replace("\n", " ")[:200]
    if snippet:
        return f"Cursor usage API failed (HTTP {status}): {snippet}"
    return f"Cursor usage API failed (HTTP {status})."


def _log_cursor_http(
    *,
    operation: str,
    method: str,
    url: str,
    status_code: int,
    response_body: str = "",
) -> None:
    log_provider_http(
        operation=operation,
        method=method,
        url=url,
        status_code=status_code,
        response_body=response_body,
        tool_vendor="cursor",
    )


def _clamp_range(
    since: datetime,
    until: datetime,
    *,
    max_days: int,
) -> tuple[datetime, datetime]:
    if since.tzinfo is None:
        since = since.replace(tzinfo=UTC)
    if until.tzinfo is None:
        until = until.replace(tzinfo=UTC)
    if since > until:
        since, until = until, since
    earliest = until - timedelta(days=max_days)
    if since < earliest:
        since = earliest
    return since, until


class CursorUsageAdapter:
    provider = "cursor"

    async def validate_api_key(self, api_token: str, **_kwargs: object) -> None:
        admin = await get_with_detail(MEMBERS_URL, headers=_basic_auth_headers(api_token))
        _log_cursor_http(
            operation="validate_members",
            method="GET",
            url=MEMBERS_URL,
            status_code=admin.status_code,
            response_body=admin.text,
        )
        if admin.status_code == 200:
            await self._probe_usage_access(api_token)
            return
        if admin.status_code == 403:
            raise ProviderValidationError(
                "Cursor Team Admin API key required (Enterprise plan)."
            )
        if admin.status_code == 401:
            bearer = await get_with_detail(
                ME_URL,
                headers={"Authorization": f"Bearer {api_token}"},
            )
            _log_cursor_http(
                operation="validate_me",
                method="GET",
                url=ME_URL,
                status_code=bearer.status_code,
                response_body=bearer.text,
            )
            if bearer.status_code == 200:
                raise ProviderValidationError(
                    "Personal Cursor API keys cannot pull team usage. "
                    "Use a Team Admin API key from Cursor → Settings → Admin API."
                )
            raise ProviderValidationError("Invalid Cursor API key.")

        bearer = await get_with_detail(
            ME_URL,
            headers={"Authorization": f"Bearer {api_token}"},
        )
        _log_cursor_http(
            operation="validate_me",
            method="GET",
            url=ME_URL,
            status_code=bearer.status_code,
            response_body=bearer.text,
        )
        if bearer.status_code == 200:
            raise ProviderValidationError(
                "Personal Cursor API keys cannot pull team usage. "
                "Use a Team Admin API key from Cursor → Settings → Admin API."
            )
        if bearer.status_code == 401 and admin.status_code not in {200, 403}:
            raise ProviderValidationError("Invalid Cursor API key.")
        raise ProviderValidationError(
            f"Cursor API key validation failed (HTTP {admin.status_code})."
        )

    async def _probe_usage_access(self, api_token: str) -> None:
        until = datetime.now(UTC)
        since = until - timedelta(days=1)
        start_ms = int(since.timestamp() * 1000)
        end_ms = int(until.timestamp() * 1000)
        headers = {
            **_basic_auth_headers(api_token),
            "Content-Type": "application/json",
        }
        body = {
            "startDate": start_ms,
            "endDate": end_ms,
            "page": 1,
            "pageSize": 1,
        }

        filtered = await post_with_detail(
            FILTERED_USAGE_URL,
            headers=headers,
            json_body=body,
        )
        _log_cursor_http(
            operation="probe_filtered_usage",
            method="POST",
            url=FILTERED_USAGE_URL,
            status_code=filtered.status_code,
            response_body=filtered.text,
        )
        if filtered.status_code == 200:
            return
        if filtered.status_code == 401:
            raise ProviderValidationError(_cursor_usage_error(401, filtered.json, filtered.text))
        if filtered.status_code == 403:
            raise ProviderValidationError(_cursor_usage_error(403, filtered.json, filtered.text))

        logger.warning(
            "Cursor filtered-usage-events probe HTTP %s; trying daily-usage-data",
            filtered.status_code,
        )
        daily = await post_with_detail(
            DAILY_USAGE_URL,
            headers=headers,
            json_body=body,
        )
        _log_cursor_http(
            operation="probe_daily_usage",
            method="POST",
            url=DAILY_USAGE_URL,
            status_code=daily.status_code,
            response_body=daily.text,
        )
        if daily.status_code == 200:
            return
        raise ProviderValidationError(
            _cursor_usage_error(filtered.status_code, filtered.json, filtered.text)
        )

    async def fetch_snapshot(
        self,
        api_token: str,
        *,
        package_allowance: int | None = None,
        **_kwargs: object,
    ) -> ProviderSnapshot:
        until = datetime.now(UTC)
        since = until - timedelta(days=MAX_FILTERED_USAGE_DAYS)
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
            input_cost_per_1k=Decimal("0.004"),
            output_cost_per_1k=Decimal("0.012"),
            member_count=len(await self.fetch_members(api_token)),
        )

    async def fetch_members(self, api_token: str, **_kwargs: object) -> list[ProviderMember]:
        status, payload = await get_json(
            MEMBERS_URL,
            headers=_basic_auth_headers(api_token),
        )
        if status == 200:
            return parse_cursor_members(payload)

        bearer_status, bearer_payload = await get_json(
            ME_URL,
            headers={"Authorization": f"Bearer {api_token}"},
        )
        if bearer_status == 200 and isinstance(bearer_payload, dict):
            email = bearer_payload.get("email")
            if isinstance(email, str) and email.strip():
                return [ProviderMember(email=email.strip())]
        return []

    async def fetch_usage(
        self,
        api_token: str,
        *,
        since: datetime,
        until: datetime,
        cursor_pull_dumper: CursorPullDumper | None = None,
        **_kwargs: object,
    ) -> list[UsageRecord]:
        logger.info(
            "Cursor fetch_usage | since=%s until=%s",
            since.isoformat(),
            until.isoformat(),
        )
        since_filtered, until_filtered = _clamp_range(
            since,
            until,
            max_days=MAX_FILTERED_USAGE_DAYS,
        )
        records, filtered_status, filtered_error = await self._fetch_filtered_usage(
            api_token,
            since=since_filtered,
            until=until_filtered,
            pull_dumper=cursor_pull_dumper,
        )
        if filtered_status == 401:
            raise ProviderValidationError(filtered_error or _cursor_usage_error(401, None, ""))
        if filtered_status == 200:
            if records:
                return records
            daily_records, daily_status, daily_error = await self._fetch_daily_usage(
                api_token,
                since=since,
                until=until,
                pull_dumper=cursor_pull_dumper,
            )
            if daily_status == 401:
                raise ProviderValidationError(daily_error or _cursor_usage_error(401, None, ""))
            if daily_records:
                logger.info(
                    "Cursor filtered-usage-events returned no rows; ingested %d daily usage rows",
                    len(daily_records),
                )
                return daily_records
            return []

        logger.warning(
            "Cursor filtered-usage-events HTTP %s; falling back to daily-usage-data",
            filtered_status,
        )
        daily_records, daily_status, daily_error = await self._fetch_daily_usage(
            api_token,
            since=since,
            until=until,
            pull_dumper=cursor_pull_dumper,
        )
        if daily_status == 401:
            raise ProviderValidationError(daily_error or _cursor_usage_error(401, None, ""))
        if daily_status == 200:
            if daily_records:
                logger.info(
                    "Cursor daily-usage-data fallback ingested %d rows after filtered HTTP %s",
                    len(daily_records),
                    filtered_status,
                )
                return daily_records
            if filtered_error:
                raise ProviderValidationError(filtered_error)
            return []

        message = daily_error or filtered_error or _cursor_usage_error(
            daily_status or filtered_status,
            None,
            "",
        )
        raise ProviderValidationError(message)

    async def _fetch_filtered_usage(
        self,
        api_token: str,
        *,
        since: datetime,
        until: datetime,
        pull_dumper: CursorPullDumper | None = None,
    ) -> tuple[list[UsageRecord], int | None, str | None]:
        start_ms = int(since.timestamp() * 1000)
        end_ms = int(until.timestamp() * 1000)
        headers = {
            **_basic_auth_headers(api_token),
            "Content-Type": "application/json",
        }
        records: list[UsageRecord] = []
        page = 1
        last_status: int | None = None
        last_error: str | None = None

        while page <= MAX_USAGE_PAGES:
            request_body = {
                "startDate": start_ms,
                "endDate": end_ms,
                "page": page,
                "pageSize": DEFAULT_USAGE_PAGE_SIZE,
            }
            result = await post_with_detail(
                FILTERED_USAGE_URL,
                headers=headers,
                json_body=request_body,
            )
            last_status = result.status_code
            _log_cursor_http(
                operation="fetch_filtered_usage",
                method="POST",
                url=FILTERED_USAGE_URL,
                status_code=result.status_code,
                response_body=result.text,
            )
            if pull_dumper is not None and result.json is not None:
                pull_dumper.write_raw_page(
                    source="filtered-usage-events",
                    page=page,
                    request_body=request_body,
                    response_payload=result.json,
                    status_code=result.status_code,
                )
            if result.status_code != 200:
                last_error = _cursor_usage_error(
                    result.status_code,
                    result.json,
                    result.text,
                )
                logger.warning(
                    "Cursor filtered-usage-events page=%s HTTP %s body=%s",
                    page,
                    result.status_code,
                    result.text[:300],
                )
                break

            batch, has_next = parse_cursor_usage_page(result.json)
            records.extend(batch)
            logger.info(
                "Cursor filtered-usage-events page=%s rows=%s has_next=%s total=%s",
                page,
                len(batch),
                has_next,
                len(records),
            )
            if not has_next or not batch:
                break
            page += 1

        return records, last_status, last_error

    async def _fetch_daily_usage(
        self,
        api_token: str,
        *,
        since: datetime,
        until: datetime,
        pull_dumper: CursorPullDumper | None = None,
    ) -> tuple[list[UsageRecord], int | None, str | None]:
        since_daily, until_daily = _clamp_range(since, until, max_days=MAX_DAILY_USAGE_DAYS)
        start_ms = int(since_daily.timestamp() * 1000)
        end_ms = int(until_daily.timestamp() * 1000)
        headers = {
            **_basic_auth_headers(api_token),
            "Content-Type": "application/json",
        }
        records: list[UsageRecord] = []
        page = 1
        last_status: int | None = None
        last_error: str | None = None

        while page <= MAX_USAGE_PAGES:
            request_body = {
                "startDate": start_ms,
                "endDate": end_ms,
                "page": page,
                "pageSize": DEFAULT_USAGE_PAGE_SIZE,
            }
            result = await post_with_detail(
                DAILY_USAGE_URL,
                headers=headers,
                json_body=request_body,
            )
            last_status = result.status_code
            _log_cursor_http(
                operation="fetch_daily_usage",
                method="POST",
                url=DAILY_USAGE_URL,
                status_code=result.status_code,
                response_body=result.text,
            )
            if pull_dumper is not None and result.json is not None:
                pull_dumper.write_raw_page(
                    source="daily-usage-data",
                    page=page,
                    request_body=request_body,
                    response_payload=result.json,
                    status_code=result.status_code,
                )
            if result.status_code != 200:
                last_error = _cursor_usage_error(
                    result.status_code,
                    result.json,
                    result.text,
                )
                logger.warning(
                    "Cursor daily-usage-data page=%s HTTP %s body=%s",
                    page,
                    result.status_code,
                    result.text[:300],
                )
                break

            batch, has_next = parse_cursor_daily_usage_page(result.json)
            records.extend(batch)
            logger.info(
                "Cursor daily-usage-data page=%s rows=%s has_next=%s total=%s",
                page,
                len(batch),
                has_next,
                len(records),
            )
            if not has_next or not batch:
                break
            page += 1

        return records, last_status, last_error
