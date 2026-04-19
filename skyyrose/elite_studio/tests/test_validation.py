"""Tests for skyyrose.elite_studio.validation shared validators."""

from __future__ import annotations

import pytest

from skyyrose.elite_studio.validation import (
    IntegrityError,
    Violation,
    collect_duplicates,
    validate_enum,
    validate_hex_color,
    validate_iso_date,
    validate_non_negative,
    validate_not_empty,
    validate_sku_format,
)

# ─── validate_hex_color ─────────────────────────────────────────────────


def test_validate_hex_color_accepts_uppercase() -> None:
    assert validate_hex_color("#B76E79", "field") == "#B76E79"


def test_validate_hex_color_accepts_lowercase() -> None:
    assert validate_hex_color("#0a0a0a", "field") == "#0a0a0a"


def test_validate_hex_color_rejects_short_form() -> None:
    with pytest.raises(ValueError, match="invalid hex color"):
        validate_hex_color("#fff", "field")


def test_validate_hex_color_rejects_missing_hash() -> None:
    with pytest.raises(ValueError, match="invalid hex color"):
        validate_hex_color("B76E79", "field")


def test_validate_hex_color_rejects_non_string() -> None:
    with pytest.raises(ValueError, match="expected hex color"):
        validate_hex_color(0xB76E79, "field")


# ─── validate_enum ──────────────────────────────────────────────────────


def test_validate_enum_accepts_allowed() -> None:
    assert validate_enum("draft", {"draft", "live"}, "field") == "draft"


def test_validate_enum_rejects_outsider() -> None:
    with pytest.raises(ValueError, match="not in allowed values"):
        validate_enum("zombie", {"draft", "live"}, "field")


def test_validate_enum_rejects_non_string() -> None:
    with pytest.raises(ValueError, match="expected str"):
        validate_enum(42, {"a"}, "field")


# ─── validate_sku_format ────────────────────────────────────────────────


def test_validate_sku_format_accepts_standard() -> None:
    assert validate_sku_format("br-001", "field") == "br-001"
    assert validate_sku_format("kids-002", "field") == "kids-002"


def test_validate_sku_format_accepts_draft_prefix() -> None:
    assert validate_sku_format("br-d01", "field") == "br-d01"


def test_validate_sku_format_rejects_uppercase() -> None:
    with pytest.raises(ValueError, match="invalid SKU"):
        validate_sku_format("BR-001", "field")


def test_validate_sku_format_rejects_missing_dash() -> None:
    with pytest.raises(ValueError, match="invalid SKU"):
        validate_sku_format("br001", "field")


# ─── validate_not_empty ─────────────────────────────────────────────────


def test_validate_not_empty_accepts_content() -> None:
    assert validate_not_empty("hello", "field") == "hello"


def test_validate_not_empty_rejects_whitespace() -> None:
    with pytest.raises(ValueError, match="non-empty"):
        validate_not_empty("   ", "field")


def test_validate_not_empty_rejects_empty() -> None:
    with pytest.raises(ValueError, match="non-empty"):
        validate_not_empty("", "field")


# ─── validate_non_negative ──────────────────────────────────────────────


def test_validate_non_negative_accepts_zero() -> None:
    assert validate_non_negative(0, "field") == 0.0


def test_validate_non_negative_rejects_negative() -> None:
    with pytest.raises(ValueError, match=">= 0"):
        validate_non_negative(-0.01, "field")


def test_validate_non_negative_rejects_non_numeric() -> None:
    with pytest.raises(ValueError, match="expected number"):
        validate_non_negative("42", "field")


# ─── validate_iso_date ──────────────────────────────────────────────────


def test_validate_iso_date_accepts_date_only() -> None:
    assert validate_iso_date("2026-04-17", "field") == "2026-04-17"


def test_validate_iso_date_accepts_full_timestamp() -> None:
    assert validate_iso_date("2026-04-17T04:51:48Z", "field") == "2026-04-17T04:51:48Z"


def test_validate_iso_date_null_allowed() -> None:
    assert validate_iso_date(None, "field") is None


def test_validate_iso_date_null_rejected_when_disallowed() -> None:
    with pytest.raises(ValueError, match="got None"):
        validate_iso_date(None, "field", allow_null=False)


def test_validate_iso_date_rejects_garbage() -> None:
    with pytest.raises(ValueError, match="invalid ISO date"):
        validate_iso_date("april 17", "field")


# ─── collect_duplicates ─────────────────────────────────────────────────


def test_collect_duplicates_returns_empty_for_unique() -> None:
    assert collect_duplicates(["a", "b", "c"]) == []


def test_collect_duplicates_returns_dupes_sorted() -> None:
    assert collect_duplicates(["b", "a", "b", "c", "a"]) == ["a", "b"]


# ─── IntegrityError + Violation ─────────────────────────────────────────


def test_violation_format() -> None:
    v = Violation("structural", "bad_hex", "products[0].color_spec.primary", "not hex")
    assert "[structural:bad_hex]" in v.format()
    assert "not hex" in v.format()


def test_integrity_error_aggregates_violations() -> None:
    violations = [
        Violation("referential", "x", "a.b", "msg1"),
        Violation("referential", "y", "c.d", "msg2"),
    ]
    err = IntegrityError(violations)
    assert err.violations == violations
    assert "2 integrity violation(s)" in str(err)
    assert "msg1" in str(err)
    assert "msg2" in str(err)
