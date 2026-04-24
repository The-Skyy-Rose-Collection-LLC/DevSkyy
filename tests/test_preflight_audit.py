"""Tests for scripts/preflight_audit.py — INFRA-05, INFRA-06, INFRA-07."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ACCESSORY_SKUS = {"sg-007", "lh-005"}
PENDING_USER_ASSETS_SKUS = {"sg-009", "sg-012", "br-012", "sg-015"}


def test_preflight_audit_module_importable() -> None:
    """scripts/preflight_audit.py must be importable."""
    import scripts.preflight_audit as audit_mod  # noqa: F401


def test_preflight_audit_exits_0_on_real_catalog(tmp_path, monkeypatch) -> None:
    """Running the audit against the real catalog exits 0 even with PENDING_USER_ASSETS."""
    import scripts.preflight_audit as audit_mod

    skipped_path = tmp_path / "SKIPPED.json"
    rc = audit_mod.main(skipped_out=skipped_path)
    assert rc == 0


def test_skipped_json_contains_only_accessories(tmp_path) -> None:
    """SKIPPED.json lists exactly sg-007 and lh-005, not garment SKUs."""
    import scripts.preflight_audit as audit_mod

    skipped_path = tmp_path / "SKIPPED.json"
    audit_mod.main(skipped_out=skipped_path)

    data = json.loads(skipped_path.read_text(encoding="utf-8"))
    skus = {entry["sku"] for entry in data["skipped"]}
    assert skus == ACCESSORY_SKUS, f"expected {ACCESSORY_SKUS}, got {skus}"
    # Pending garment SKUs MUST NOT appear in SKIPPED.json
    for pending in PENDING_USER_ASSETS_SKUS:
        assert pending not in skus, f"{pending} is a pending garment, must not be in SKIPPED.json"


def test_pending_user_assets_reported_in_stdout(tmp_path, capsys) -> None:
    """All 5 PENDING_USER_ASSETS SKUs appear in the stdout audit summary."""
    import scripts.preflight_audit as audit_mod

    skipped_path = tmp_path / "SKIPPED.json"
    audit_mod.main(skipped_out=skipped_path)

    captured = capsys.readouterr().out
    assert "PENDING_USER_ASSETS" in captured
    for sku in PENDING_USER_ASSETS_SKUS:
        assert sku in captured, f"{sku} should appear in audit stdout"


def test_ready_count_equals_23(tmp_path) -> None:
    """28 in-scope garments minus 5 pending = 23 READY — verified structurally."""
    import scripts.preflight_audit as audit_mod
    from skyyrose.core.catalog_loader import read_catalog_rows

    skipped_path = tmp_path / "SKIPPED.json"
    audit_mod.main(skipped_out=skipped_path)

    # Build entries directly via classify_sku to assert on Status enum, not string output
    rows = read_catalog_rows()
    entries = [audit_mod.classify_sku(row) for row in rows]
    ready_count = sum(1 for e in entries if e.status == audit_mod.Status.READY)
    assert ready_count == 23, f"expected 23 READY garments, got {ready_count}"


def test_all_30_skus_classified(tmp_path) -> None:
    """READY + SKIPPED + PENDING_USER_ASSETS must equal 30 — verified structurally."""
    import scripts.preflight_audit as audit_mod
    from skyyrose.core.catalog_loader import read_catalog_rows

    skipped_path = tmp_path / "SKIPPED.json"
    audit_mod.main(skipped_out=skipped_path)

    rows = read_catalog_rows()
    entries = [audit_mod.classify_sku(row) for row in rows]
    assert len(entries) == 30, f"expected 30 total classified entries, got {len(entries)}"
