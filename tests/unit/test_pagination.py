"""Unit tests for cursor pagination."""

from app.core.pagination import CursorError, decode_cursor, encode_cursor


def test_encode_decode_cursor() -> None:
    cursor = encode_cursor(name="Alpha", id="uuid-1")
    decoded = decode_cursor(cursor)
    assert decoded["name"] == "Alpha"
    assert decoded["id"] == "uuid-1"


def test_invalid_cursor_raises() -> None:
    try:
        decode_cursor("not-a-valid-cursor")
        raise AssertionError("expected CursorError")
    except CursorError:
        pass
