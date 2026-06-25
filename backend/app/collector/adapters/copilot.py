"""GitHub Copilot adapter — seats, members, and per-user usage metrics."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import httpx

from app.collector.adapters.base import ProviderMember, ProviderSnapshot, ProviderValidationError, UsageRecord
from app.collector.adapters.copilot_merge import merge_copilot_records
from app.collector.adapters.copilot_metrics_fields import normalize_download_links
from app.collector.adapters.copilot_parsing import (
    parse_copilot_seat_members,
    parse_copilot_user_day,
)
from app.collector.adapters.copilot_dump import CopilotPullDumper
from app.collector.adapters.http_utils import get_with_detail
from app.integration.http_log import log_provider_http
from app.tools.pricing import organization_id_from_pricing

logger = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"
SEATS_PATH = "/orgs/{org}/copilot/billing/seats"
METRICS_REPORT_PATH = "/orgs/{org}/copilot/metrics/reports/users-1-day"
ORG_METRICS_REPORT_PATH = "/orgs/{org}/copilot/metrics/reports/organization-1-day"
MAX_METRICS_DAYS = 28
SEATS_PAGE_SIZE = 100


@dataclass
class CopilotProductivityPull:
    github_org_id: str
    user_metric_rows: list[dict]
    org_metric_rows: list[dict]
    seats: list[dict]


def _github_headers(api_token: str, *, api_version: str = "2022-11-28") -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_token.strip()}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": api_version,
    }


def _require_org_id(pricing_config: dict | None) -> str:
    org_id = organization_id_from_pricing(pricing_config)
    if not org_id:
        raise ProviderValidationError(
            "GitHub organization ID is required for Copilot. "
            "Set it on the Copilot catalogue tool or when connecting credentials."
        )
    return org_id


def _metrics_day_window(since: datetime, until: datetime, *, today: date | None = None) -> tuple[date, date]:
    latest_available_day = (today or datetime.now(UTC).date()) - timedelta(days=1)
    start_day = since.astimezone(UTC).date()
    end_day = min(until.astimezone(UTC).date(), latest_available_day)
    if start_day > end_day:
        start_day = end_day
    return start_day, end_day


def _metrics_error_message(status_code: int, body: str) -> str:
    detail = (body or "").strip()[:500]
    suffix = f" Provider response: {detail}" if detail else ""
    if status_code == 401:
        return f"Invalid GitHub token for Copilot metrics (HTTP 401).{suffix}"
    if status_code == 403:
        return (
            "Insufficient GitHub token scope or Copilot metrics policy for usage metrics "
            f"(HTTP 403). Enable Copilot usage metrics and use an org owner/billing manager token with "
            f"manage_billing:copilot and read:org.{suffix}"
        )
    if status_code == 404:
        return f"GitHub Copilot metrics endpoint or organization was not found (HTTP 404).{suffix}"
    if status_code == 422:
        return (
            "GitHub Copilot usage metrics are disabled or unavailable for this organization "
            f"(HTTP 422). Enable Copilot usage metrics in GitHub organization settings.{suffix}"
        )
    return f"GitHub Copilot metrics request failed (HTTP {status_code}).{suffix}"


class CopilotUsageAdapter:
    provider = "copilot"

    async def validate_api_key(
        self,
        api_token: str,
        *,
        pricing_config: dict | None = None,
        api_endpoint: str | None = None,
        **_kwargs: object,
    ) -> None:
        org_id = _require_org_id(pricing_config)
        url = f"{GITHUB_API}{SEATS_PATH.format(org=org_id)}"
        result = await get_with_detail(
            url,
            headers=_github_headers(api_token),
            params={"page": 1, "per_page": 1},
        )
        log_provider_http(
            operation="validate_seats",
            method="GET",
            url=url,
            status_code=result.status_code,
            response_body=result.text,
            tool_vendor="copilot",
        )
        if result.status_code == 401:
            raise ProviderValidationError("Invalid GitHub token for Copilot (HTTP 401).")
        if result.status_code == 403:
            raise ProviderValidationError(
                "Insufficient GitHub token scope for Copilot. "
                "Requires manage_billing:copilot and read:org."
            )
        if result.status_code == 404:
            raise ProviderValidationError(
                f"GitHub organization '{org_id}' not found or Copilot billing unavailable (HTTP 404)."
            )
        if result.status_code >= 400:
            raise ProviderValidationError(
                f"Copilot validation failed (HTTP {result.status_code}). "
                "See Docker api logs for the provider response body."
            )

    async def fetch_members(
        self,
        api_token: str,
        *,
        pricing_config: dict | None = None,
        **_kwargs: object,
    ) -> list[ProviderMember]:
        org_id = _require_org_id(pricing_config)
        seats = await self._fetch_all_seats(api_token, org_id)
        return parse_copilot_seat_members(seats)

    async def fetch_snapshot(
        self,
        api_token: str,
        *,
        package_allowance: int | None = None,
        pricing_config: dict | None = None,
        api_endpoint: str | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
        **_kwargs: object,
    ) -> ProviderSnapshot:
        end = until or datetime.now(UTC)
        start = since or (end - timedelta(days=MAX_METRICS_DAYS))
        records = await self.fetch_usage(
            api_token,
            since=start,
            until=end,
            pricing_config=pricing_config,
            api_endpoint=api_endpoint,
        )
        members = await self.fetch_members(api_token, pricing_config=pricing_config)
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
            member_count=len(members),
        )

    async def fetch_usage(
        self,
        api_token: str,
        *,
        since: datetime,
        until: datetime,
        pricing_config: dict | None = None,
        api_endpoint: str | None = None,
        copilot_pull_dumper: CopilotPullDumper | None = None,
        **_kwargs: object,
    ) -> list[UsageRecord]:
        org_id = _require_org_id(pricing_config)
        if since.tzinfo is None:
            since = since.replace(tzinfo=UTC)
        if until.tzinfo is None:
            until = until.replace(tzinfo=UTC)

        metrics_records = await self._fetch_user_metrics(
            api_token,
            org_id,
            since=since,
            until=until,
            pull_dumper=copilot_pull_dumper,
        )
        seats = await self._fetch_all_seats(
            api_token,
            org_id,
            pull_dumper=copilot_pull_dumper,
        )
        records = merge_copilot_records(metrics_records, seats, fallback_at=until)

        logger.info(
            "Copilot fetch_usage | org=%s seats=%s metrics_rows=%s total_records=%s",
            org_id,
            len(seats),
            len(metrics_records),
            len(records),
        )
        return records

    async def fetch_productivity_pull(
        self,
        api_token: str,
        *,
        since: datetime,
        until: datetime,
        pricing_config: dict | None = None,
        copilot_pull_dumper: CopilotPullDumper | None = None,
    ) -> CopilotProductivityPull:
        """Fetch raw Copilot productivity payloads for dedicated schema ingest."""
        org_id = _require_org_id(pricing_config)
        if since.tzinfo is None:
            since = since.replace(tzinfo=UTC)
        if until.tzinfo is None:
            until = until.replace(tzinfo=UTC)

        user_rows: list[dict] = []
        org_rows: list[dict] = []
        start_day, end_day = _metrics_day_window(since, until)

        day = start_day
        days_fetched = 0
        while day <= end_day and days_fetched < MAX_METRICS_DAYS:
            user_rows.extend(
                await self._fetch_user_metrics_raw_for_day(
                    api_token,
                    org_id,
                    day,
                    pull_dumper=copilot_pull_dumper,
                )
            )
            org_rows.extend(
                await self._fetch_org_metrics_raw_for_day(
                    api_token,
                    org_id,
                    day,
                    pull_dumper=copilot_pull_dumper,
                )
            )
            day += timedelta(days=1)
            days_fetched += 1

        seats = await self._fetch_all_seats(api_token, org_id, pull_dumper=copilot_pull_dumper)
        return CopilotProductivityPull(
            github_org_id=org_id,
            user_metric_rows=user_rows,
            org_metric_rows=org_rows,
            seats=seats,
        )

    async def _fetch_user_metrics_raw_for_day(
        self,
        api_token: str,
        org_id: str,
        day: date,
        *,
        pull_dumper: CopilotPullDumper | None = None,
    ) -> list[dict]:
        url = f"{GITHUB_API}{METRICS_REPORT_PATH.format(org=org_id)}"
        result = await get_with_detail(
            url,
            headers=_github_headers(api_token, api_version="2026-03-10"),
            params={"day": day.isoformat()},
            timeout=30.0,
        )
        log_provider_http(
            operation="fetch_user_metrics_report",
            method="GET",
            url=url,
            status_code=result.status_code,
            response_body=result.text[:2000],
            tool_vendor="copilot",
        )
        if pull_dumper is not None:
            pull_dumper.write_raw_page(
                source="copilot-user-metrics",
                page=int(day.strftime("%Y%m%d")),
                request_body={"org": org_id, "day": day.isoformat()},
                response_payload=result.json if isinstance(result.json, dict) else {"error": result.text[:500]},
                status_code=result.status_code,
            )
        if result.status_code >= 400:
            raise ProviderValidationError(_metrics_error_message(result.status_code, result.text))
        if result.status_code != 200 or not isinstance(result.json, dict):
            return []

        rows: list[dict] = []
        for link in normalize_download_links(result.json.get("download_links")):
            downloaded, _status, _error = await self._download_report_rows(link, api_token=api_token)
            rows.extend(downloaded)
            if pull_dumper is not None:
                pull_dumper.write_metrics_rows(
                    day=day.isoformat(),
                    download_url=link,
                    rows=downloaded,
                )
        return rows

    async def _fetch_org_metrics_raw_for_day(
        self,
        api_token: str,
        org_id: str,
        day: date,
        *,
        pull_dumper: CopilotPullDumper | None = None,
    ) -> list[dict]:
        url = f"{GITHUB_API}{ORG_METRICS_REPORT_PATH.format(org=org_id)}"
        result = await get_with_detail(
            url,
            headers=_github_headers(api_token, api_version="2026-03-10"),
            params={"day": day.isoformat()},
            timeout=30.0,
        )
        log_provider_http(
            operation="fetch_org_metrics_report",
            method="GET",
            url=url,
            status_code=result.status_code,
            response_body=result.text[:2000],
            tool_vendor="copilot",
        )
        if pull_dumper is not None:
            pull_dumper.write_raw_page(
                source="copilot-org-metrics",
                page=int(day.strftime("%Y%m%d")),
                request_body={"org": org_id, "day": day.isoformat()},
                response_payload=result.json if isinstance(result.json, dict) else {"error": result.text[:500]},
                status_code=result.status_code,
            )
        if result.status_code >= 400:
            raise ProviderValidationError(_metrics_error_message(result.status_code, result.text))
        if result.status_code != 200 or not isinstance(result.json, dict):
            return []

        rows: list[dict] = []
        for link in normalize_download_links(result.json.get("download_links")):
            downloaded, _status, _error = await self._download_report_rows(link, api_token=api_token)
            rows.extend(downloaded)
        return rows

    async def _fetch_all_seats(
        self,
        api_token: str,
        org_id: str,
        *,
        pull_dumper: CopilotPullDumper | None = None,
    ) -> list[dict]:
        url = f"{GITHUB_API}{SEATS_PATH.format(org=org_id)}"
        seats: list[dict] = []
        page = 1

        while page <= 50:
            result = await get_with_detail(
                url,
                headers=_github_headers(api_token),
                params={"page": page, "per_page": SEATS_PAGE_SIZE},
            )
            log_provider_http(
                operation="fetch_seats",
                method="GET",
                url=url,
                status_code=result.status_code,
                response_body=result.text[:4000] if page == 1 else f"(page {page}, truncated)",
                tool_vendor="copilot",
            )
            if result.status_code != 200 or not isinstance(result.json, dict):
                if pull_dumper is not None:
                    pull_dumper.write_raw_page(
                        source="copilot-seats",
                        page=page,
                        request_body={"org": org_id, "page": page, "per_page": SEATS_PAGE_SIZE},
                        response_payload=result.json if isinstance(result.json, dict) else {"error": result.text[:500]},
                        status_code=result.status_code,
                    )
                break

            if pull_dumper is not None:
                pull_dumper.write_raw_page(
                    source="copilot-seats",
                    page=page,
                    request_body={"org": org_id, "page": page, "per_page": SEATS_PAGE_SIZE},
                    response_payload=result.json,
                    status_code=result.status_code,
                )

            batch = result.json.get("seats")
            if not isinstance(batch, list) or not batch:
                break

            seats.extend(row for row in batch if isinstance(row, dict))
            if len(batch) < SEATS_PAGE_SIZE:
                break
            page += 1

        return seats

    async def _fetch_user_metrics(
        self,
        api_token: str,
        org_id: str,
        *,
        since: datetime,
        until: datetime,
        pull_dumper: CopilotPullDumper | None = None,
    ) -> list[UsageRecord]:
        records: list[UsageRecord] = []
        start_day, end_day = _metrics_day_window(since, until)

        day = start_day
        days_fetched = 0
        while day <= end_day and days_fetched < MAX_METRICS_DAYS:
            day_records = await self._fetch_user_metrics_for_day(
                api_token,
                org_id,
                day,
                pull_dumper=pull_dumper,
            )
            records.extend(day_records)
            day += timedelta(days=1)
            days_fetched += 1

        return records

    async def _fetch_user_metrics_for_day(
        self,
        api_token: str,
        org_id: str,
        day: date,
        *,
        pull_dumper: CopilotPullDumper | None = None,
    ) -> list[UsageRecord]:
        url = f"{GITHUB_API}{METRICS_REPORT_PATH.format(org=org_id)}"
        result = await get_with_detail(
            url,
            headers=_github_headers(api_token, api_version="2026-03-10"),
            params={"day": day.isoformat()},
            timeout=30.0,
        )
        log_provider_http(
            operation="fetch_user_metrics_report",
            method="GET",
            url=url,
            status_code=result.status_code,
            response_body=result.text[:2000],
            tool_vendor="copilot",
        )

        if pull_dumper is not None:
            pull_dumper.write_raw_page(
                source="copilot-user-metrics",
                page=int(day.strftime("%Y%m%d")),
                request_body={"org": org_id, "day": day.isoformat()},
                response_payload=result.json if isinstance(result.json, dict) else {"error": result.text[:500]},
                status_code=result.status_code,
            )

        if result.status_code in (401, 403, 404, 422):
            logger.info(
                "Copilot user metrics unavailable for org=%s (HTTP %s — enable "
                "'Copilot usage metrics' in GitHub org settings)",
                org_id,
                result.status_code,
            )
            if pull_dumper is not None:
                pull_dumper.write_metrics_rows(
                    day=day.isoformat(),
                    download_url="",
                    rows=[],
                    download_status=result.status_code,
                    download_error="Metrics API unavailable — enable Copilot usage metrics in GitHub org",
                )
            raise ProviderValidationError(_metrics_error_message(result.status_code, result.text))
        if result.status_code >= 400:
            raise ProviderValidationError(_metrics_error_message(result.status_code, result.text))
        if result.status_code != 200 or not isinstance(result.json, dict):
            if pull_dumper is not None:
                pull_dumper.write_metrics_rows(
                    day=day.isoformat(),
                    download_url="",
                    rows=[],
                    download_status=result.status_code,
                    download_error=(result.text or "")[:500],
                )
            return []

        download_links = normalize_download_links(result.json.get("download_links"))
        if not download_links:
            if pull_dumper is not None:
                pull_dumper.write_metrics_rows(
                    day=day.isoformat(),
                    download_url="",
                    rows=[],
                    download_status=result.status_code,
                    download_error="No download_links in metrics API response",
                )
            return []

        records: list[UsageRecord] = []
        for link in download_links:
            downloaded_rows, download_status, download_error = await self._download_report_rows(
                link,
                api_token=api_token,
            )
            for row in downloaded_rows:
                parsed = parse_copilot_user_day(row)
                if parsed is not None:
                    records.append(parsed)
            if pull_dumper is not None:
                pull_dumper.write_metrics_rows(
                    day=day.isoformat(),
                    download_url=link,
                    rows=downloaded_rows,
                    download_status=download_status,
                    download_error=download_error,
                )
        return records

    async def _download_report_rows(
        self,
        url: str,
        *,
        api_token: str | None = None,
    ) -> tuple[list[dict], int, str | None]:
        headers = {"Accept": "application/json", "User-Agent": "ai-tool-monitor"}
        if api_token:
            headers["Authorization"] = f"Bearer {api_token.strip()}"
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            response = await client.get(url, headers=headers)
        if response.status_code >= 400:
            logger.warning(
                "Copilot metrics download failed | url=%s status=%s",
                url[:120],
                response.status_code,
            )
            return [], response.status_code, response.text[:500]

        text = response.text.strip()
        if not text:
            return [], response.status_code, "Download returned empty body"

        if text.startswith("["):
            try:
                payload = json.loads(text)
            except json.JSONDecodeError:
                return [], response.status_code, "Download JSON array parse failed"
            if isinstance(payload, list):
                return [row for row in payload if isinstance(row, dict)], response.status_code, None
            return [], response.status_code, "Download JSON root is not an array"

        rows: list[dict] = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                rows.append(row)
        if not rows:
            return [], response.status_code, "Download NDJSON contained no object rows"
        return rows, response.status_code, None
