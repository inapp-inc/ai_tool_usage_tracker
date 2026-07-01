"""Tests for Copilot billing Excel conversion."""

from io import BytesIO

from openpyxl import Workbook

from app.copilot.billing_spreadsheet import xlsx_to_csv_text


def test_xlsx_to_csv_text_reads_first_sheet() -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["date", "sku", "applied_cost_per_quantity"])
    sheet.append(["2026-06-01", "copilot_for_business", 950])
    buffer = BytesIO()
    workbook.save(buffer)

    text, headers, error = xlsx_to_csv_text(buffer.getvalue())
    assert error is None
    assert headers == ["date", "sku", "applied_cost_per_quantity"]
    assert "applied_cost_per_quantity" in text
    assert "950" in text
