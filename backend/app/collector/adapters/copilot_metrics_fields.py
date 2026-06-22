"""Shared GitHub Copilot usage-metrics field extraction (API → app bind rules)."""

from __future__ import annotations

from typing import Any

from app.integration.numbers import parse_compact_int

COPILOT_USED_FLAGS: tuple[str, ...] = (
    "used_chat",
    "used_cli",
    "used_agent",
    "used_copilot_coding_agent",
    "used_copilot_cloud_agent",
    "used_copilot_code_review_active",
    "used_copilot_code_review_passive",
)

BREAKDOWN_ARRAY_KEYS: tuple[str, ...] = (
    "totals_by_ide",
    "totals_by_feature",
    "totals_by_language_feature",
    "totals_by_language_model",
    "totals_by_model_feature",
)


def int_field(row: dict[str, Any], key: str) -> int:
    return parse_compact_int(row.get(key), default=0)


def user_login_from_row(row: dict[str, Any]) -> str | None:
    for key in ("user_login", "login", "username"):
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def normalize_download_link(link: object) -> str | None:
    if isinstance(link, str) and link.strip():
        return link.strip()
    if isinstance(link, dict):
        for key in ("url", "uri", "href", "download_url"):
            value = link.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return None


def normalize_download_links(raw: object) -> list[str]:
    if not isinstance(raw, list):
        return []
    links: list[str] = []
    for item in raw:
        normalized = normalize_download_link(item)
        if normalized:
            links.append(normalized)
    return links


def _sum_breakdown_array(row: dict[str, Any], array_key: str, *fields: str) -> int:
    payload = row.get(array_key)
    if not isinstance(payload, list):
        return 0
    total = 0
    for item in payload:
        if not isinstance(item, dict):
            continue
        for field in fields:
            total += int_field(item, field)
    return total


def cli_token_sums(row: dict[str, Any]) -> tuple[int, int]:
    cli = row.get("totals_by_cli")
    if not isinstance(cli, dict):
        return 0, 0
    token_usage = cli.get("token_usage")
    if not isinstance(token_usage, dict):
        return 0, 0
    return (
        int_field(token_usage, "prompt_tokens_sum"),
        int_field(token_usage, "output_tokens_sum"),
    )


def activity_fallback(row: dict[str, Any]) -> int:
    total = (
        int_field(row, "loc_added_sum")
        + int_field(row, "loc_deleted_sum")
        + int_field(row, "loc_suggested_to_add_sum")
        + int_field(row, "loc_suggested_to_delete_sum")
        + int_field(row, "code_generation_activity_count")
        + int_field(row, "code_acceptance_activity_count")
        + int_field(row, "user_initiated_interaction_count")
    )
    for array_key in BREAKDOWN_ARRAY_KEYS:
        total += _sum_breakdown_array(
            row,
            array_key,
            "loc_added_sum",
            "loc_deleted_sum",
            "code_generation_activity_count",
            "code_acceptance_activity_count",
            "user_initiated_interaction_count",
        )
    return total


def breakdown_token_sums(row: dict[str, Any]) -> tuple[int, int]:
    input_tokens = 0
    output_tokens = 0
    for array_key in BREAKDOWN_ARRAY_KEYS:
        input_tokens += _sum_breakdown_array(
            row,
            array_key,
            "loc_added_sum",
            "user_initiated_interaction_count",
            "code_generation_activity_count",
        )
        output_tokens += _sum_breakdown_array(
            row,
            array_key,
            "loc_deleted_sum",
            "code_acceptance_activity_count",
        )
    return input_tokens, output_tokens


def tokens_from_user_day(row: dict[str, Any]) -> tuple[int, int, str]:
    """Return (input_tokens, output_tokens, bind_rule)."""
    prompt, output = cli_token_sums(row)
    if prompt + output > 0:
        return prompt, output, "totals_by_cli.token_usage → input/output tokens"

    breakdown_in, breakdown_out = breakdown_token_sums(row)
    if breakdown_in + breakdown_out > 0:
        return (
            breakdown_in,
            breakdown_out,
            "totals_by_ide/feature breakdown → input/output tokens",
        )

    fallback = activity_fallback(row)
    if fallback > 0:
        return fallback, 0, "loc/activity top-level sums → input_tokens (fallback)"

    if any(row.get(flag) for flag in COPILOT_USED_FLAGS):
        return 0, 0, "used_* flags only → record with zero tokens"

    return 0, 0, "no usage signals → parser returns None"


def has_usage_signal(row: dict[str, Any]) -> bool:
    input_tokens, output_tokens, _rule = tokens_from_user_day(row)
    if input_tokens + output_tokens > 0:
        return True
    return any(row.get(flag) for flag in COPILOT_USED_FLAGS)


def feature_flags_from_row(row: dict[str, Any]) -> list[str]:
    labels = {
        "used_chat": "chat",
        "used_cli": "cli",
        "used_agent": "agent",
        "used_copilot_coding_agent": "coding_agent",
        "used_copilot_cloud_agent": "cloud_agent",
        "used_copilot_code_review_active": "code_review_active",
        "used_copilot_code_review_passive": "code_review_passive",
    }
    features: list[str] = []
    for flag, label in labels.items():
        if row.get(flag):
            features.append(label)
    return features
