"""Tests for tool usage CSV import parsing."""

from app.admin.tools.csv_importer import (
    CsvColumnMapping,
    CsvImportParseError,
    inspect_tool_usage_csv,
    parse_tool_usage_csv,
)


def test_parse_daily_rows_csv() -> None:
    content = b"""date,tokens,cost
2026-06-01,1000,1.50
2026-06-02,2000,2.00
"""
    result = parse_tool_usage_csv(content)
    assert result.token_count == 3000
    assert result.cost_total == 3.5
    assert result.date_from == "2026-06-01"
    assert result.date_to == "2026-06-02"
    assert len(result.daily_usage) == 2


def test_parse_summary_row_csv() -> None:
    content = b"""total_tokens,total_cost,date_from,date_to
50000,125.40,2026-05-01,2026-05-31
"""
    result = parse_tool_usage_csv(content)
    assert result.token_count == 50000
    assert result.cost_total == 125.4
    assert result.date_from == "2026-05-01"
    assert result.date_to == "2026-05-31"


def test_parse_with_custom_headers() -> None:
    content = b"""Usage Date,Token Used,Total Cost
2026-06-01,900,1.10
2026-06-02,1100,1.40
"""
    inspected = inspect_tool_usage_csv(content)
    assert "Usage Date" in inspected.headers
    result = parse_tool_usage_csv(
        content,
        mapping=CsvColumnMapping(
            token_column="Token Used",
            cost_column="Total Cost",
            date_column="Usage Date",
        ),
    )
    assert result.token_count == 2000
    assert result.cost_total == 2.5


def test_missing_token_column_raises() -> None:
    content = b"date,cost\n2026-06-01,1.00\n"
    try:
        parse_tool_usage_csv(content)
    except CsvImportParseError as exc:
        assert "token" in str(exc).lower()
    else:
        raise AssertionError("Expected CsvImportParseError")


def test_parse_cursor_export_with_included_price() -> None:
    content = b"""Day,Subscription Included Reqs,Usage Based Reqs,API Key Reqs,Composer Requests,Chat Requests,Agent Requests,Price
2026-06-01,10,0,0,5,3,2,Included
2026-06-02,8,1,0,4,2,1,$1.50
"""
    result = parse_tool_usage_csv(content)
    assert result.token_count == 36
    assert result.cost_total == 1.5
    assert result.date_from == "2026-06-01"
    assert result.date_to == "2026-06-02"
    assert len(result.daily_usage) == 2
    assert result.daily_usage[0]["cost"] == 0.0
    assert result.daily_usage[1]["cost"] == 1.5


def test_parse_cost_text_values() -> None:
    content = b"""date,composer_requests,price
2026-06-01,5,Included
2026-06-02,3,Free
2026-06-03,2,$0 included
2026-06-04,1,2.75
"""
    result = parse_tool_usage_csv(content)
    assert result.token_count == 11
    assert result.cost_total == 2.75
