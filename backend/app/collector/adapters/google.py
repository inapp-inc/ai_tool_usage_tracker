"""Google Gemini provider adapter."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.collector.adapters.base import ProviderSnapshot, ProviderValidationError, UsageRecord
from app.collector.adapters.google_gcp_auth import fetch_gcp_access_token
from app.collector.adapters.google_monitoring import (
    fetch_gemini_monitoring_usage,
    resolve_gcp_project_id,
    resolve_service_account_from_config,
)
from app.collector.adapters.http_utils import get_json
from app.normalization.converters import token_to_usage_record
from app.normalization.token import map_gemini_usage

logger = logging.getLogger(__name__)

_GCP_USAGE_HINT = (
    "Gemini historical usage requires GCP Cloud Monitoring. Add pricing_config.gcp_project_id "
    "and pricing_config.gcp_service_account_json (service account with roles/monitoring.viewer) "
    "on the connected tool, then re-sync."
)


class GoogleUsageAdapter:
    provider = "google"

    async def validate_api_key(self, api_token: str, **_kwargs: object) -> None:
        token = api_token.strip()
        if token.startswith("{"):
            return
        status, _ = await get_json(
            "https://generativelanguage.googleapis.com/v1beta/models",
            params={"key": token},
        )
        if status in {401, 403}:
            raise ProviderValidationError("Invalid Google API key.")
        if status >= 400:
            raise ProviderValidationError(f"Google API key validation failed (HTTP {status}).")

    async def fetch_snapshot(
        self,
        api_token: str,
        *,
        package_allowance: int | None = None,
        pricing_config: dict | None = None,
        **_kwargs: object,
    ) -> ProviderSnapshot:
        until = datetime.now(UTC)
        since = until - timedelta(days=30)
        records = await self.fetch_usage(
            api_token,
            since=since,
            until=until,
            pricing_config=pricing_config,
        )
        tokens_used = sum(record.total_tokens for record in records)
        total_cost = sum((record.estimated_cost for record in records), Decimal("0"))
        balance = None
        if package_allowance is not None:
            balance = max(package_allowance - tokens_used, 0)

        config = pricing_config or {}
        input_cost = _decimal_from_config(config.get("input_cost_per_1k"), Decimal("0.00125"))
        output_cost = _decimal_from_config(config.get("output_cost_per_1k"), Decimal("0.005"))
        return ProviderSnapshot(
            sync_status="active",
            tokens_used=tokens_used,
            balance_tokens=balance,
            total_cost=total_cost,
            input_cost_per_1k=input_cost,
            output_cost_per_1k=output_cost,
        )

    async def fetch_usage(
        self,
        api_token: str,
        *,
        since: datetime,
        until: datetime,
        pricing_config: dict | None = None,
        **_kwargs: object,
    ) -> list[UsageRecord]:
        service_account = resolve_service_account_from_config(pricing_config, api_token=api_token)
        if service_account is None:
            logger.warning(
                "Google fetch_usage | no GCP monitoring credentials | since=%s until=%s | %s",
                since.isoformat(),
                until.isoformat(),
                _GCP_USAGE_HINT,
            )
            return []

        try:
            project_id = resolve_gcp_project_id(pricing_config, service_account)
            access_token = await fetch_gcp_access_token(service_account)
            rows = await fetch_gemini_monitoring_usage(
                project_id=project_id,
                access_token=access_token,
                since=since,
                until=until,
            )
        except Exception as exc:  # noqa: BLE001 — surface as empty pull with log
            logger.warning(
                "Google fetch_usage | monitoring pull failed | project=%s error=%s",
                (pricing_config or {}).get("gcp_project_id") or service_account.get("project_id"),
                exc,
            )
            return []

        records = self.parse_usage_rows(rows, fallback_at=until)
        logger.info(
            "Google fetch_usage | records=%s since=%s until=%s",
            len(records),
            since.isoformat(),
            until.isoformat(),
        )
        return records

    @staticmethod
    def parse_usage_rows(rows: list[dict], *, fallback_at: datetime) -> list[UsageRecord]:
        records: list[UsageRecord] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            normalized = map_gemini_usage(row, fallback_at=fallback_at)
            if normalized is not None:
                records.append(token_to_usage_record(normalized))
        return records


def _decimal_from_config(value: object, default: Decimal) -> Decimal:
    try:
        if value is None:
            return default
        return Decimal(str(value))
    except Exception:  # noqa: BLE001
        return default
