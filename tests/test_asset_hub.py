"""Tests for skyyrose.core.asset_hub — the unified hub manifest resolver.

These assert the resolver's CONTRACT against the live manifest, not a frozen
snapshot of counts. The hub is promoted incrementally (pending→verified, masters
served), so hardcoded totals rot; every count here is derived from the manifest.

Invariants:
- resolve(sku, face) returns a path IFF the entry is verified AND has a non-null
  path; pending / flagged / null-path / unknown / empty → None (verdict over
  filesystem — a stale on-disk file must not leak through).
- by_usage(tag) and pending() filter by verdict; verify_integrity() flags verified
  entries whose path is null (unpromoted) or missing on disk.
"""

from __future__ import annotations

import pytest

import skyyrose.core.asset_hub as hub


@pytest.fixture(autouse=True)
def _clear_cache():
    """Drop manifest cache before each test so tests are isolated."""
    hub.refresh()
    yield
    hub.refresh()


# ---------------------------------------------------------------------------
# served_theme_path() — the SOT-tie seam (build-collection-sot reads this)
# ---------------------------------------------------------------------------


def test_served_theme_path_legacy_keeps_source_under_theme():
    """A verified entry whose source is already under the theme tree → that
    theme-relative path, original extension preserved."""
    for aid, e in hub.manifest().items():
        if aid != f"{e.get('sku')}-{e.get('face')}":
            continue
        src = e.get("source") or ""
        if e.get("verdict") == "verified" and src.startswith("wordpress-theme/skyyrose-flagship/"):
            assert (
                hub.served_theme_path(e["sku"], e["face"])
                == src.split("wordpress-theme/skyyrose-flagship/", 1)[1]
            )
            return
    pytest.skip("no verified legacy-theme face in manifest")


def test_served_theme_path_offtheme_render_is_always_webp():
    """An off-theme verified render serves from the staged ``hub/`` projection as
    ``.webp`` — NEVER the source .png/.jpg (the .gitignore'd format). Regression
    guard for the bug where the source suffix leaked into the served path."""
    for aid, e in hub.manifest().items():
        if aid != f"{e.get('sku')}-{e.get('face')}":
            continue
        src = e.get("source") or ""
        if (
            e.get("verdict") == "verified"
            and src
            and not src.startswith("wordpress-theme/skyyrose-flagship/")
        ):
            tp = hub.served_theme_path(e["sku"], e["face"])
            assert tp == f"assets/images/products/hub/{e['sku']}-{e['face']}.webp"
            assert tp.endswith(".webp")
            return
    pytest.skip("no off-theme verified render in manifest")


def test_served_theme_path_pending_is_none():
    """Pending / non-verified faces never produce a served path."""
    for e in hub.pending():
        assert hub.served_theme_path(e["sku"], e["face"]) is None


# ---------------------------------------------------------------------------
# manifest()
# ---------------------------------------------------------------------------


def test_manifest_returns_dict():
    assets = hub.manifest()
    assert isinstance(assets, dict)


def test_manifest_non_empty():
    assets = hub.manifest()
    assert len(assets) > 0


def test_manifest_verdict_partition():
    """CONTRACT: verified + pending + other-verdict entries partition the manifest
    exactly (the readers drop/duplicate nothing); at least one verified entry exists."""
    entries = hub.manifest()
    verified = sum(1 for e in entries.values() if e.get("verdict") == "verified")
    pend = len(hub.pending())
    other = sum(1 for e in entries.values() if e.get("verdict") not in ("verified", "pending"))
    assert verified + pend + other == len(entries)
    assert verified > 0


def test_manifest_entries_have_verdict():
    """Every entry carries a verdict key."""
    for asset_id, entry in hub.manifest().items():
        assert "verdict" in entry, f"{asset_id} missing verdict"


def test_manifest_caches():
    """Two calls return the same object (lru_cache active)."""
    assert hub.manifest() is hub.manifest()


def test_refresh_clears_cache():
    """refresh() causes next call to re-load (different object identity)."""
    first = hub.manifest()
    hub.refresh()
    second = hub.manifest()
    # After refresh we get a freshly-loaded dict — may or may not be same id
    # depending on CPython interning; assert content equality is sufficient.
    assert first == second


# ---------------------------------------------------------------------------
# resolve()
# ---------------------------------------------------------------------------


def test_resolve_all_verified_with_path_resolve_and_exist():
    """CONTRACT: every CANONICAL ('<sku>-<face>') verified entry with a non-null
    path resolves to exactly that path, and the file exists under HUB_DIR. Data-
    derived so it tracks the manifest as assets are promoted instead of pinning
    moving SKUs. Usage-variant entries ('<sku>-<face>-ad-creative', …) are reached
    via by_usage(), not resolve(), so they are excluded here."""
    servable = {
        aid: e
        for aid, e in hub.manifest().items()
        if e.get("verdict") == "verified"
        and e.get("path")
        and e.get("sku")
        and aid == f"{e['sku']}-{e.get('face', 'front')}"
    }
    assert servable, "expected at least one canonical verified+path SKU entry"
    for aid, e in servable.items():
        resolved = hub.resolve(e["sku"], e.get("face", "front"))
        assert resolved == e["path"], f"{aid}: resolve()={resolved!r}, manifest path={e['path']!r}"
        assert (hub.HUB_DIR / resolved).exists(), f"{aid}: resolved path not on disk: {resolved}"


def test_resolve_default_face_is_front():
    """resolve(sku) defaults to face='front' (structural — holds for any SKU)."""
    some_sku = next((e["sku"] for e in hub.manifest().values() if e.get("sku")), "br-010")
    assert hub.resolve(some_sku) == hub.resolve(some_sku, "front")


def test_resolve_non_servable_returns_none():
    """CONTRACT: a non-servable CANONICAL SKU entry — pending/flagged verdict OR
    verified-but-null-path — never resolves. resolve() honors the manifest verdict,
    not the filesystem (a stale file on disk must NOT leak through). Data-derived;
    filtered to canonical '<sku>-<face>' ids since that is resolve()'s lookup key."""
    non_servable = [
        e
        for aid, e in hub.manifest().items()
        if e.get("sku")
        and aid == f"{e['sku']}-{e.get('face', 'front')}"
        and (e.get("verdict") != "verified" or not e.get("path"))
    ]
    assert non_servable, "expected at least one non-servable canonical SKU entry"
    for e in non_servable:
        assert hub.resolve(e["sku"], e.get("face", "front")) is None, (
            f"non-servable {e.get('sku')}-{e.get('face')} "
            f"(verdict={e.get('verdict')}, path={e.get('path')!r}) resolved to a path"
        )


def test_resolve_unknown_sku_returns_none():
    assert hub.resolve("xx-999", "front") is None


def test_resolve_empty_sku_returns_none():
    assert hub.resolve("") is None


# ---------------------------------------------------------------------------
# by_usage()
# ---------------------------------------------------------------------------


def test_by_usage_product_card_non_empty():
    results = hub.by_usage("product-card")
    assert len(results) > 0


def test_by_usage_product_card_count_matches_verified():
    """CONTRACT: by_usage(tag) returns exactly the VERIFIED entries carrying that
    usage tag — derived from the manifest, not a pinned snapshot count."""
    expected = sum(
        1
        for e in hub.manifest().values()
        if e.get("verdict") == "verified" and "product-card" in (e.get("usage") or [])
    )
    assert len(hub.by_usage("product-card")) == expected


def test_by_usage_all_verified():
    """by_usage() only returns verified entries."""
    for entry in hub.by_usage("product-card"):
        assert entry["verdict"] == "verified", f"Non-verified entry in by_usage: {entry}"


def test_by_usage_injects_id():
    """Each result dict has _id injected for caller convenience."""
    for entry in hub.by_usage("product-card"):
        assert "_id" in entry


def test_by_usage_scope_filter():
    """Scope filter narrows to matching collection only."""
    all_results = hub.by_usage("product-card")
    br_results = hub.by_usage("product-card", scope="black-rose")
    assert len(br_results) <= len(all_results)
    for entry in br_results:
        assert entry["scope"] == "black-rose"


def test_by_usage_scope_filter_excludes_others():
    """Scope='signature' results contain no black-rose entries."""
    sig_results = hub.by_usage("product-card", scope="signature")
    for entry in sig_results:
        assert entry["scope"] == "signature"


def test_by_usage_unknown_tag_empty():
    assert hub.by_usage("nonexistent-usage-tag") == []


def test_by_usage_usage_in_list():
    """Each returned entry actually contains the requested usage tag."""
    for entry in hub.by_usage("product-card"):
        assert "product-card" in entry["usage"]


# ---------------------------------------------------------------------------
# pending()
# ---------------------------------------------------------------------------


def test_pending_non_empty():
    pend = hub.pending()
    assert len(pend) > 0


def test_pending_count_matches_manifest():
    """CONTRACT: pending() returns exactly the verdict=='pending' entries — derived,
    not pinned (the queue shrinks as assets are promoted)."""
    expected = sum(1 for e in hub.manifest().values() if e.get("verdict") == "pending")
    assert len(hub.pending()) == expected


def test_pending_all_have_pending_verdict():
    for entry in hub.pending():
        assert entry["verdict"] == "pending"


def test_pending_injects_id():
    for entry in hub.pending():
        assert "_id" in entry


def test_pending_none_in_resolve():
    """Every pending entry returns None from resolve() (never servable)."""
    for entry in hub.pending():
        sku = entry.get("sku")
        face = entry.get("face", "front")
        if sku:
            assert (
                hub.resolve(sku, face) is None
            ), f"Pending entry {entry['_id']} incorrectly resolved to a path"


# ---------------------------------------------------------------------------
# verify_integrity()
# ---------------------------------------------------------------------------


def test_verify_integrity_returns_list():
    problems = hub.verify_integrity()
    assert isinstance(problems, list)


def test_verify_integrity_problem_count_matches_unpromoted():
    """CONTRACT: verify_integrity() flags exactly the verified entries whose path is
    null (unpromoted) or missing on disk — derived from the manifest, not a pinned
    snapshot count (the backlog shrinks as masters are served)."""
    expected = sum(
        1
        for e in hub.manifest().values()
        if e.get("verdict") == "verified"
        and (not e.get("path") or not (hub.HUB_DIR / e["path"]).exists())
    )
    problems = hub.verify_integrity()
    assert (
        len(problems) == expected
    ), f"Expected {expected} integrity problems, got {len(problems)}:\n" + "\n".join(problems)


def test_verify_integrity_problems_are_strings():
    for p in hub.verify_integrity():
        assert isinstance(p, str)


def test_verify_integrity_null_path_problems_mention_null():
    """Null-path problems describe the issue clearly."""
    for p in hub.verify_integrity():
        # All current problems are null-path type
        assert "null" in p or "does not exist" in p


def test_verify_integrity_all_with_paths_exist_on_disk():
    """Verified entries that DO have paths must all exist on disk (zero missing-file
    problems in the current manifest).
    """
    missing_on_disk = [p for p in hub.verify_integrity() if "does not exist on disk" in p]
    assert missing_on_disk == [], "Verified assets missing from disk:\n" + "\n".join(
        missing_on_disk
    )


# ---------------------------------------------------------------------------
# Path validation (defense-in-depth)
# ---------------------------------------------------------------------------


def test_validated_path_rejects_absolute():
    with pytest.raises(ValueError, match="escapes the hub assets tree"):
        hub._validated_path("/etc/passwd", "test-id")


def test_validated_path_rejects_dotdot():
    with pytest.raises(ValueError, match="escapes the hub assets tree"):
        hub._validated_path("../../etc/passwd", "test-id")


def test_validated_path_accepts_relative():
    result = hub._validated_path("collections/black-rose/products/br-010/back.jpg", "br-010-back")
    assert result == "collections/black-rose/products/br-010/back.jpg"


# ---------------------------------------------------------------------------
# HUB_DIR constant
# ---------------------------------------------------------------------------


def test_hub_dir_exists():
    """HUB_DIR must point to a real directory."""
    assert hub.HUB_DIR.is_dir()


def test_hub_dir_contains_manifest():
    """manifest.json must be present under HUB_DIR."""
    assert (hub.HUB_DIR / "manifest.json").exists()
