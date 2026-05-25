"""Tests for the LogoRegistry path resolver."""

from __future__ import annotations

import pytest

from skyyrose.elite_studio.logo_registry import (
    LogoNotFoundError,
    LogoRegistry,
    SkuFolderUnknownError,
)


@pytest.fixture(scope="module")
def registry() -> LogoRegistry:
    return LogoRegistry.load()


# ─── Schema basics ────────────────────────────────────────────────────


def test_version_is_current(registry: LogoRegistry) -> None:
    assert registry.version >= 4


def test_brand_primary_is_sr_monogram(registry: LogoRegistry) -> None:
    assert registry.brand_primary == "sr-monogram-rose-gold"


# ─── Centralized logo path resolution ─────────────────────────────────


def test_brand_primary_resolves_to_logos_dir(registry: LogoRegistry) -> None:
    path = registry.image_path(sku="br-005", logo_id="sr-monogram-rose-gold")
    assert path.parent.name == "logos"
    assert path.name == "sr-monogram-rose-gold.jpeg"
    assert path.exists(), f"missing brand-primary asset: {path}"


def test_black_roses_stays_centralized(registry: LogoRegistry) -> None:
    """High-fanout collection logo stays in logos/, not co-located."""
    entry = registry.get_logo("black-roses-cloud-cluster")
    assert entry.co_located_per_sku is False
    assert entry.collection == "black_rose"


def test_signature_red_rose_is_signature_collection(registry: LogoRegistry) -> None:
    """red-roses-cloud-cluster was misclassified pre-v4; must be Signature."""
    entry = registry.get_logo("red-roses-cloud-cluster")
    assert entry.collection == "signature"


def test_heart_rose_is_love_hurts(registry: LogoRegistry) -> None:
    entry = registry.get_logo("heart-rose-composite")
    assert entry.collection == "love_hurts"


# ─── Per-SKU sport patch resolution ───────────────────────────────────


@pytest.mark.parametrize(
    "sku,logo_id,expected_folder",
    [
        ("br-008", "nfl-authentic-collection-card", "black-is-beautiful-football-jersey-red"),
        ("br-009", "nfl-authentic-collection-card", "black-is-beautiful-football-jersey-white"),
        ("br-010", "nba-authentic-collection-card", "black-is-beautiful-basketball-jersey"),
        ("br-011", "hockey-championship-card", "black-is-beautiful-hockey-jersey"),
        ("br-003", "mlb-authentic-collection-card", "black-is-beautiful-jersey"),
        ("br-012", "mlb-authentic-collection-card", "jersey-last-oakland-baseball"),
        ("br-014", "mlb-authentic-collection-card", "black-is-beautiful-jersey-giants"),
        ("br-015", "mlb-authentic-collection-card", "black-is-beautiful-jersey-white"),
    ],
)
def test_sport_patch_resolves_to_per_sku_folder(
    registry: LogoRegistry, sku: str, logo_id: str, expected_folder: str
) -> None:
    path = registry.image_path(sku=sku, logo_id=logo_id)
    assert path.parent.name == expected_folder
    assert path.name.endswith(".jpeg")
    assert path.exists(), f"missing per-SKU patch asset: {path}"


def test_sport_patch_without_sku_folder_raises(registry: LogoRegistry) -> None:
    with pytest.raises(SkuFolderUnknownError):
        registry.image_path(sku="zz-999", logo_id="nfl-authentic-collection-card")


def test_unknown_logo_raises(registry: LogoRegistry) -> None:
    with pytest.raises(LogoNotFoundError):
        registry.image_path(sku="br-005", logo_id="nonexistent-logo")


# ─── Placement lookups ────────────────────────────────────────────────


def test_new_baseball_skus_have_mlb_patch(registry: LogoRegistry) -> None:
    """br-014/015 added in registry v4 — must carry mlb patch (br-013 retired)."""
    for sku in ("br-014", "br-015"):
        assert registry.has_sku(sku), f"{sku} missing from sku_logos"
        placements = registry.placements_for(sku)
        logo_ids = {p["logo_id"] for p in placements}
        assert "mlb-authentic-collection-card" in logo_ids
        assert "black-roses-cloud-cluster" in logo_ids


def test_br013_retired(registry: LogoRegistry) -> None:
    """br-013 was confirmed duplicate of br-003 and retired 2026-05-25."""
    assert not registry.has_sku("br-013")
    assert registry.sku_folder("br-013") is None


def test_four_mlb_jerseys_exactly(registry: LogoRegistry) -> None:
    """The MLB authentic collection patch is now placed on exactly 4 SKUs."""
    mlb_users = [
        sku
        for sku in registry._sku_logos  # noqa: SLF001 — test-only introspection
        if any(
            p["logo_id"] == "mlb-authentic-collection-card" for p in registry.placements_for(sku)
        )
    ]
    assert sorted(mlb_users) == ["br-003", "br-012", "br-014", "br-015"]


def test_lh003_uses_heart_rose_not_red_rose(registry: LogoRegistry) -> None:
    """v4 correction: lh-003 must not reference red-roses (Signature LOGO)."""
    placements = registry.placements_for("lh-003")
    logo_ids = [p["logo_id"] for p in placements]
    assert "red-roses-cloud-cluster" not in logo_ids
    assert logo_ids.count("heart-rose-composite") >= 2  # all_over + mesh_panels


def test_lh004_uses_heart_rose_not_red_rose(registry: LogoRegistry) -> None:
    placements = registry.placements_for("lh-004")
    logo_ids = [p["logo_id"] for p in placements]
    assert "red-roses-cloud-cluster" not in logo_ids
    assert "heart-rose-composite" in logo_ids


def test_sg009_uses_red_rose(registry: LogoRegistry) -> None:
    """Signature Sherpa is the canonical home of red-roses-cloud-cluster."""
    placements = registry.placements_for("sg-009")
    logo_ids = [p["logo_id"] for p in placements]
    assert "red-roses-cloud-cluster" in logo_ids


# ─── Sport patch enumeration ──────────────────────────────────────────


def test_four_sport_patches_registered(registry: LogoRegistry) -> None:
    patches = registry.sport_patches()
    assert set(patches.keys()) == {
        "nfl-authentic-collection-card",
        "nba-authentic-collection-card",
        "mlb-authentic-collection-card",
        "hockey-championship-card",
    }
    for entry in patches.values():
        assert entry.co_located_per_sku is True
        assert entry.category == "sport_patch"
