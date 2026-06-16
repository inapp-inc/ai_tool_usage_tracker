"""Tests for upload CSV parser."""

from uuid import uuid4

from app.uploads.parser import (
    ToolLookup,
    extract_csv_headers,
    parse_csv_content,
    suggest_column_mapping,
)


def test_parse_csv_extracts_raw_and_maps_tokens() -> None:
    tool_id = uuid4()
    user_id = uuid4()
    csv_text = """email,model,input_tokens,output_tokens,cost,timestamp,tool
dev@acme.example,gpt-4o,100,50,0.25,2025-06-01T10:00:00Z,Cursor
"""

    result = parse_csv_content(
        csv_text,
        tools=[ToolLookup(id=tool_id, name="Cursor", vendor="cursor")],
        users_by_email={"dev@acme.example": user_id},
    )

    assert result.error_message is None
    assert len(result.rows) == 1
    row = result.rows[0]
    assert row.raw_payload["email"] == "dev@acme.example"
    assert row.mapped_payload["tool_name"] == "Cursor"
    assert row.input_tokens == 100
    assert row.output_tokens == 50
    assert row.match_status == "matched"


def test_extract_csv_headers_and_suggest_mapping() -> None:
    csv_text = """User Email,Amount,Prompt Tokens,Completion Tokens,Model Name
dev@acme.example,1.50,100,50,gpt-4o
"""
    headers, error = extract_csv_headers(csv_text)
    assert error is None
    assert headers == [
        "User Email",
        "Amount",
        "Prompt Tokens",
        "Completion Tokens",
        "Model Name",
    ]

    suggested = suggest_column_mapping(headers)
    assert suggested["email"] == "User Email"
    assert suggested["cost"] == "Amount"
    assert suggested["input_tokens"] == "Prompt Tokens"
    assert suggested["output_tokens"] == "Completion Tokens"
    assert suggested["model"] == "Model Name"


def test_parse_csv_with_explicit_column_mapping() -> None:
    tool_id = uuid4()
    user_id = uuid4()
    csv_text = """User Email,Amount,Prompt Tokens,Completion Tokens,Model Name
dev@acme.example,1.50,100,50,gpt-4o
"""
    mapping = {
        "email": "User Email",
        "cost": "Amount",
        "input_tokens": "Prompt Tokens",
        "output_tokens": "Completion Tokens",
        "model": "Model Name",
    }

    result = parse_csv_content(
        csv_text,
        tools=[ToolLookup(id=tool_id, name="Cursor", vendor="cursor")],
        users_by_email={"dev@acme.example": user_id},
        column_mapping=mapping,
    )

    assert result.error_message is None
    row = result.rows[0]
    assert row.user_email == "dev@acme.example"
    assert row.input_tokens == 100
    assert row.output_tokens == 50
    assert row.mapped_payload["estimated_cost"] == 1.5
    assert row.mapped_payload["model"] == "gpt-4o"
