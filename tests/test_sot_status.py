"""Pure-function tests for scripts/sot_status.py and scripts/wc_reconcile.py.

No subprocess, no network, no filesystem beyond the real (deterministic) catalog CSV.
Covers: domain-table assembly, status rollup, freshness-guard section parsing, and the
WC-vs-CSV diff logic via fixture dicts.
"""

from __future__ import annotations

import pytest

from scripts.sot_status import (
    BROKEN,
    DRIFT,
    LIVE_SKIPPED,
    OK,
    UNCHECKED,
    DomainStatus,
    _parse_freshness_guard_section,
    broken,
    build_row,
    overall_exit_code,
    status_from_checks,
    unchecked,
)
from scripts.wc_reconcile import CredentialsMissing, diff_products, load_csv_rows, reconcile

# ---------------------------------------------------------------------------
# status_from_checks — rollup
# ---------------------------------------------------------------------------


def test_status_from_checks_empty_is_broken():
    status, detail = status_from_checks({})
    assert status == BROKEN
    assert "no check results" in detail


def test_status_from_checks_all_pass_is_ok():
    status, detail = status_from_checks({"a": (True, "fine"), "b": (True, "fine")})
    assert status == OK
    assert detail == "2/2 checks passed"


def test_status_from_checks_any_fail_is_drift_and_names_failures():
    status, detail = status_from_checks(
        {"a": (True, "fine"), "b": (False, "broke"), "c": (False, "also broke")}
    )
    assert status == DRIFT
    assert "b: broke" in detail
    assert "c: also broke" in detail
    assert "a: fine" not in detail  # passing checks aren't named in the failure detail


# ---------------------------------------------------------------------------
# unchecked / broken / build_row
# ---------------------------------------------------------------------------


def test_unchecked_helper():
    assert unchecked("no validator wired") == (UNCHECKED, "no validator wired")


def test_broken_helper():
    assert broken("crashed") == (BROKEN, "crashed")


def test_build_row_assembles_fields():
    row = build_row("catalog", "skyyrose-catalog.csv", "some-check", (OK, "all good"))
    assert row == DomainStatus(
        domain="catalog",
        artifact="skyyrose-catalog.csv",
        check="some-check",
        status=OK,
        detail="all good",
    )


# ---------------------------------------------------------------------------
# overall_exit_code — rollup across the whole table
# ---------------------------------------------------------------------------


def _row(status: str) -> DomainStatus:
    return DomainStatus(domain="d", artifact="a", check="c", status=status)


def test_exit_code_zero_when_all_ok():
    assert overall_exit_code([_row(OK), _row(OK)]) == 0


def test_exit_code_zero_for_unchecked_and_live_skipped_only():
    assert overall_exit_code([_row(OK), _row(UNCHECKED), _row(LIVE_SKIPPED)]) == 0


def test_exit_code_nonzero_on_drift():
    assert overall_exit_code([_row(OK), _row(DRIFT)]) == 1


def test_exit_code_nonzero_on_broken():
    assert overall_exit_code([_row(OK), _row(BROKEN)]) == 1


def test_exit_code_zero_on_empty_table():
    assert overall_exit_code([]) == 0


# ---------------------------------------------------------------------------
# _parse_freshness_guard_section — coarse section-header parse, ANSI-safe
# ---------------------------------------------------------------------------

_FRESHNESS_OUTPUT_ALL_OK = """
freshness-guard (--all)

1. Collection SOT ↔ masters
  \x1b[32m  ✓\x1b[0m SOT in sync (4 collections verified)

2. Minified assets ↔ source
  \x1b[32m  ✓\x1b[0m .min build up to date

3. Theme version sync
  \x1b[32m  ✓\x1b[0m version synced (1.9.3)

4. Retired-master references
  \x1b[32m  ✓\x1b[0m no retired-master references

freshness-guard: all derived files fresh
"""

_FRESHNESS_OUTPUT_VERSION_DRIFT = """
1. Collection SOT ↔ masters
  \x1b[32m  ✓\x1b[0m SOT in sync

3. Theme version sync
  \x1b[31m  ✗\x1b[0m VERSION DRIFT — style.css=1.9.3  functions.php=1.9.2  readme.txt=1.9.3

4. Retired-master references
  \x1b[32m  ✓\x1b[0m no retired-master references
"""


def test_parse_freshness_section_ok():
    assert _parse_freshness_guard_section(_FRESHNESS_OUTPUT_ALL_OK, "3. Theme version sync") is True


def test_parse_freshness_section_drift():
    result = _parse_freshness_guard_section(
        _FRESHNESS_OUTPUT_VERSION_DRIFT, "3. Theme version sync"
    )
    assert result is False


def test_parse_freshness_section_not_found():
    assert (
        _parse_freshness_guard_section(_FRESHNESS_OUTPUT_ALL_OK, "9. Nonexistent section") is None
    )


def test_parse_freshness_section_isolates_correct_section():
    # section 1 is OK, section 3 has DRIFT in the version-drift fixture — make sure
    # the parser doesn't bleed section 1's ✓ into section 3's result.
    assert (
        _parse_freshness_guard_section(_FRESHNESS_OUTPUT_VERSION_DRIFT, "1. Collection SOT") is True
    )
    assert (
        _parse_freshness_guard_section(_FRESHNESS_OUTPUT_VERSION_DRIFT, "3. Theme version sync")
        is False
    )


# ---------------------------------------------------------------------------
# wc_reconcile.diff_products — pure diff, fixture dicts, no network
# ---------------------------------------------------------------------------


def _csv_row(
    sku: str, *, name="Product", price="45", published="1", is_preorder="0"
) -> dict[str, str]:
    return {
        "sku": sku,
        "name": name,
        "price": price,
        "published": published,
        "is_preorder": is_preorder,
    }


def _live_product(
    sku: str, *, name="Product", price="45", status="publish", is_preorder_meta: str | None = None
) -> dict:
    meta = []
    if is_preorder_meta is not None:
        meta.append({"key": "_is_preorder", "value": is_preorder_meta})
    return {"sku": sku, "name": name, "price": price, "status": status, "meta_data": meta}


def test_diff_products_clean_when_identical():
    csv_rows = {"br-001": _csv_row("br-001")}
    live = {"br-001": _live_product("br-001")}
    result = diff_products(csv_rows, live)
    assert result.clean
    assert result.csv_count == 1
    assert result.live_count == 1


def test_diff_products_detects_csv_only_sku():
    csv_rows = {"br-001": _csv_row("br-001"), "br-002": _csv_row("br-002")}
    live = {"br-001": _live_product("br-001")}
    result = diff_products(csv_rows, live)
    assert not result.clean
    assert result.csv_only == ("br-002",)
    assert result.live_only == ()


def test_diff_products_detects_live_only_sku():
    csv_rows = {"br-001": _csv_row("br-001")}
    live = {"br-001": _live_product("br-001"), "lh-999": _live_product("lh-999")}
    result = diff_products(csv_rows, live)
    assert result.live_only == ("lh-999",)


def test_diff_products_detects_price_drift():
    csv_rows = {"br-001": _csv_row("br-001", price="45")}
    live = {"br-001": _live_product("br-001", price="50")}
    result = diff_products(csv_rows, live)
    assert len(result.field_drift) == 1
    d = result.field_drift[0]
    assert d.field == "price"
    assert d.csv_value == "45.00"
    assert d.live_value == "50.00"


def test_diff_products_price_tolerates_decimal_formatting():
    # '45' vs '45.00' must NOT be flagged as drift
    csv_rows = {"br-001": _csv_row("br-001", price="45")}
    live = {"br-001": _live_product("br-001", price="45.00")}
    result = diff_products(csv_rows, live)
    assert result.clean


def test_diff_products_detects_name_drift():
    csv_rows = {"br-001": _csv_row("br-001", name="BLACK Rose Crewneck")}
    live = {"br-001": _live_product("br-001", name="Black Rose Crew")}
    result = diff_products(csv_rows, live)
    assert any(d.field == "name" for d in result.field_drift)


def test_diff_products_name_tolerates_html_entity_encoding():
    # Live-verified false positive (2026-07-02): WooCommerce returns product titles
    # with "&" HTML-entity-encoded as "&amp;" — must NOT be flagged as drift.
    csv_rows = {"sg-006": _csv_row("sg-006", name="Mint & Lavender Hoodie")}
    live = {"sg-006": _live_product("sg-006", name="Mint &amp; Lavender Hoodie")}
    result = diff_products(csv_rows, live)
    assert result.clean


def test_diff_products_detects_published_drift():
    csv_rows = {"br-001": _csv_row("br-001", published="1")}
    live = {"br-001": _live_product("br-001", status="draft")}
    result = diff_products(csv_rows, live)
    assert any(d.field == "published" for d in result.field_drift)


def test_diff_products_detects_preorder_drift():
    csv_rows = {"lh-005": _csv_row("lh-005", is_preorder="1")}
    live = {"lh-005": _live_product("lh-005", is_preorder_meta="0")}
    result = diff_products(csv_rows, live)
    assert any(d.field == "is_preorder" for d in result.field_drift)


def test_diff_products_preorder_matches_when_meta_agrees():
    csv_rows = {"lh-005": _csv_row("lh-005", is_preorder="1")}
    live = {"lh-005": _live_product("lh-005", is_preorder_meta="1")}
    result = diff_products(csv_rows, live)
    assert result.clean


def test_diff_products_missing_preorder_meta_treated_as_false():
    csv_rows = {"br-001": _csv_row("br-001", is_preorder="0")}
    live = {"br-001": _live_product("br-001")}  # no _is_preorder meta at all
    result = diff_products(csv_rows, live)
    assert result.clean


# ---------------------------------------------------------------------------
# wc_reconcile.load_csv_rows — reads the real canonical CSV (deterministic fixture)
# ---------------------------------------------------------------------------


def test_load_csv_rows_reads_real_catalog():
    rows = load_csv_rows()
    assert len(rows) > 0
    assert "br-001" in rows
    assert rows["br-001"]["sku"] == "br-001"


# ---------------------------------------------------------------------------
# wc_reconcile.reconcile — credentials gate (no network reached when absent)
# ---------------------------------------------------------------------------


def test_reconcile_raises_credentials_missing_without_env(monkeypatch, tmp_path):
    monkeypatch.delenv("WOOCOMMERCE_KEY", raising=False)
    monkeypatch.delenv("WOOCOMMERCE_SECRET", raising=False)
    # Point ENV_FILE at an empty tmp file so load_dotenv can't pick up the real
    # repo .env.wordpress and mask the missing-env-var behavior under test.
    empty_env = tmp_path / "empty.env"
    empty_env.write_text("")
    monkeypatch.setattr("scripts.wc_reconcile.ENV_FILE", empty_env)
    with pytest.raises(CredentialsMissing):
        reconcile()
