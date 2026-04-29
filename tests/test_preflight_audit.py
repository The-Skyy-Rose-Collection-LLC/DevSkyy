"""Tests for scripts/preflight_audit.py — INFRA-05, INFRA-06, INFRA-07."""

from __future__ import annotations

import json

# Intentional invariant: exactly these two SKUs are accessories (not garments).
# Update only when a product's category changes, not when the catalog grows.
ACCESSORY_SKUS = {"sg-007", "lh-005"}


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
    """SKIPPED.json must equal ACCESSORY_SKUS exactly; no garments may appear there."""
    import scripts.preflight_audit as audit_mod
    from skyyrose.core.catalog_loader import read_catalog_rows

    skipped_path = tmp_path / "SKIPPED.json"
    audit_mod.main(skipped_out=skipped_path)

    rows = read_catalog_rows()
    entries = [audit_mod.classify_sku(row) for row in rows]
    non_accessory_skus = {e.sku for e in entries if e.status != audit_mod.Status.SKIPPED}

    data = json.loads(skipped_path.read_text(encoding="utf-8"))
    skus = {entry["sku"] for entry in data["skipped"]}
    assert skus == ACCESSORY_SKUS, f"expected {ACCESSORY_SKUS}, got {skus}"
    for sku in non_accessory_skus:
        assert sku not in skus, f"{sku} is a non-accessory SKU; must not appear in SKIPPED.json"


def test_pending_user_assets_reported_in_stdout(tmp_path, capsys) -> None:
    """Every PENDING_USER_ASSETS SKU derived from the live catalog appears in stdout."""
    import scripts.preflight_audit as audit_mod
    from skyyrose.core.catalog_loader import read_catalog_rows

    skipped_path = tmp_path / "SKIPPED.json"
    audit_mod.main(skipped_out=skipped_path)
    captured = capsys.readouterr().out

    rows = read_catalog_rows()
    entries = [audit_mod.classify_sku(row) for row in rows]
    pending_skus = {e.sku for e in entries if e.status == audit_mod.Status.PENDING_USER_ASSETS}

    assert "PENDING_USER_ASSETS" in captured
    for sku in pending_skus:
        assert sku in captured, f"{sku} should appear in audit stdout"


def test_status_counts_partition_catalog(tmp_path) -> None:
    """READY + SKIPPED + PENDING_USER_ASSETS must equal the full catalog — no unclassified SKUs."""
    import scripts.preflight_audit as audit_mod
    from skyyrose.core.catalog_loader import read_catalog_rows

    skipped_path = tmp_path / "SKIPPED.json"
    audit_mod.main(skipped_out=skipped_path)

    rows = read_catalog_rows()
    total = len(rows)
    entries = [audit_mod.classify_sku(row) for row in rows]

    ready = sum(1 for e in entries if e.status == audit_mod.Status.READY)
    skipped = sum(1 for e in entries if e.status == audit_mod.Status.SKIPPED)
    pending = sum(1 for e in entries if e.status == audit_mod.Status.PENDING_USER_ASSETS)

    assert ready + skipped + pending == total, (
        f"classification is not a complete partition of the catalog: "
        f"{ready} READY + {skipped} SKIPPED + {pending} PENDING = {ready + skipped + pending}, "
        f"expected {total}"
    )
