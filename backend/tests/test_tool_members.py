"""Tests for provider member and usage payload parsing."""

from decimal import Decimal

from app.collector.adapters.base import ProviderMember
from app.collector.adapters.member_parsing import (
    dedupe_members,
    parse_cursor_members,
    parse_generic_members,
    parse_openai_org_users,
)
from app.collector.adapters.usage_parsing import parse_cursor_usage_page


def test_parse_cursor_members_skips_removed_and_dedupes() -> None:
    payload = {
        "teamMembers": [
            {"email": "a@example.com", "name": "A", "isRemoved": False},
            {"email": "A@example.com", "name": "A duplicate", "isRemoved": False},
            {"email": "removed@example.com", "isRemoved": True},
        ]
    }
    members = parse_cursor_members(payload)
    assert len(members) == 1
    assert members[0].email == "a@example.com"
    assert members[0].name == "A"


def test_parse_openai_org_users() -> None:
    payload = {
        "data": [
            {"email": "dev@acme.example", "name": "Dev User"},
            {"email": "", "name": "Missing email"},
        ]
    }
    members = parse_openai_org_users(payload)
    assert members == [ProviderMember(email="dev@acme.example", name="Dev User")]


def test_parse_generic_members_supports_multiple_shapes() -> None:
    payload = {
        "members": [
            {"email": "one@example.com"},
            "two@example.com",
        ]
    }
    members = parse_generic_members(payload)
    assert [member.email for member in members] == [
        "one@example.com",
        "two@example.com",
    ]


def test_dedupe_members_sorts_by_email() -> None:
    members = dedupe_members(
        [
            ProviderMember(email="z@example.com"),
            ProviderMember(email="a@example.com"),
        ]
    )
    assert [member.email for member in members] == [
        "a@example.com",
        "z@example.com",
    ]


def test_parse_cursor_usage_page() -> None:
    payload = {
        "usageEvents": [
            {
                "timestamp": "1750979225854",
                "userEmail": "dev@acme.example",
                "model": "claude-4.5-sonnet",
                "isTokenBasedCall": True,
                "tokenUsage": {
                    "inputTokens": 126,
                    "outputTokens": 450,
                    "cacheWriteTokens": 100,
                    "cacheReadTokens": 50,
                },
                "chargedCents": 21.36,
            }
        ],
        "pagination": {"hasNextPage": False},
    }
    records, has_next = parse_cursor_usage_page(payload)
    assert has_next is False
    assert len(records) == 1
    assert records[0].total_tokens == 726
    assert records[0].estimated_cost == Decimal("0.2136")
    assert records[0].model == "claude-4.5-sonnet"
