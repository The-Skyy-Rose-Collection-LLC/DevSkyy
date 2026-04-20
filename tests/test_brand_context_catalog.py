"""Phase 2 tests for collection-aware brand context injection.

Verifies orchestration.brand_context extensions:

- CatalogContext snapshot is read from canonical CSV with correct aggregates
- compile_catalog_digest returns role-tuned text under the char budget
- Different roles yield different digests (photography vs competitor_scout)
- Output is deterministic given the same CSV state
- get_brand_context composes brand + catalog, honors SKYYROSE_BRAND_INJECT=0
- Cache invalidates when CSV mtime changes

No network, no LLM calls. Uses the real canonical CSV for end-to-end checks
and a temporary CSV fixture for isolated unit checks.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from orchestration.brand_context import (
    _CATALOG_DIGEST_CHAR_BUDGET,
    _cached_digest,
    compile_catalog_digest,
    get_brand_context,
    load_catalog_context,
)

# ---------------------------------------------------------------------------
# CatalogContext — canonical CSV end-to-end
# ---------------------------------------------------------------------------


class TestCatalogContextLive:
    """Sanity checks against the real wordpress-theme canonical CSV."""

    def test_loads_catalog_with_skus(self) -> None:
        ctx = load_catalog_context()
        assert ctx.total_skus > 0, "canonical CSV must have SKUs"
        assert len(ctx.summaries) >= 2, "expected multiple collections"

    def test_known_collections_present(self) -> None:
        ctx = load_catalog_context()
        slugs = {s.collection for s in ctx.summaries}
        # Four canonical collections per brand guidelines — catalog should
        # hold at least black-rose and signature (the other two may be empty).
        assert "black-rose" in slugs
        assert "signature" in slugs

    def test_price_ranges_are_sensible(self) -> None:
        ctx = load_catalog_context()
        for summary in ctx.summaries:
            if summary.price_min is not None:
                assert summary.price_min > 0
                assert summary.price_max is not None
                assert summary.price_max >= summary.price_min


# ---------------------------------------------------------------------------
# compile_catalog_digest — role behavior + budget
# ---------------------------------------------------------------------------


class TestCatalogDigest:
    def test_digest_is_nonempty_for_known_roles(self) -> None:
        for role in (
            "imagery",
            "ecommerce_photography",
            "social_media",
            "competitor_scout",
            "theme_builder",
            "garment_3d",
        ):
            digest = compile_catalog_digest(role)
            assert digest, f"empty digest for role={role}"
            assert "SkyyRose Catalog Digest" in digest
            assert len(digest) <= _CATALOG_DIGEST_CHAR_BUDGET

    def test_digest_differs_by_role_focus(self) -> None:
        """Roles with distinct focus lists must produce distinct digests."""
        photo = compile_catalog_digest("ecommerce_photography")
        scout = compile_catalog_digest("competitor_scout")
        assert (
            photo != scout
        ), "ecommerce_photography and competitor_scout should see different facts"
        # Scout sees prices; photography sees sample names.
        assert "Price range" in scout
        assert "Featured" in photo

    def test_digest_is_deterministic(self) -> None:
        """Two calls with identical CSV state return identical bytes."""
        a = compile_catalog_digest("imagery")
        b = compile_catalog_digest("imagery")
        assert a == b

    def test_unknown_role_uses_default_focus(self) -> None:
        """An unregistered role name must still produce a valid digest."""
        digest = compile_catalog_digest("made_up_role_xyz")
        assert digest
        assert "SkyyRose Catalog Digest" in digest


# ---------------------------------------------------------------------------
# get_brand_context — unified brand + catalog accessor
# ---------------------------------------------------------------------------


class TestGetBrandContext:
    def test_default_includes_catalog(self) -> None:
        block = get_brand_context("imagery")
        assert "Brand Voice" in block
        assert "SkyyRose Catalog Digest" in block

    def test_include_catalog_false_strips_digest(self) -> None:
        block = get_brand_context("imagery", include_catalog=False)
        assert "Brand Voice" in block
        assert "SkyyRose Catalog Digest" not in block

    def test_env_var_opt_out_honored(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """SKYYROSE_BRAND_INJECT=0 strips the digest even when include_catalog is None."""
        monkeypatch.setenv("SKYYROSE_BRAND_INJECT", "0")
        block = get_brand_context("imagery")
        assert "Brand Voice" in block
        assert "SkyyRose Catalog Digest" not in block


# ---------------------------------------------------------------------------
# Cache invalidation — mtime-keyed lru_cache
# ---------------------------------------------------------------------------


class TestCacheInvalidation:
    def test_cache_hit_on_same_mtime(self) -> None:
        """Calling _cached_digest twice with the same key hits the cache."""
        _cached_digest.cache_clear()
        _cached_digest("imagery", 1000)
        _cached_digest("imagery", 1000)
        info = _cached_digest.cache_info()
        assert info.hits == 1
        assert info.misses == 1

    def test_cache_misses_on_different_mtime(self) -> None:
        """Simulating a CSV edit (new mtime) forces recomputation."""
        _cached_digest.cache_clear()
        _cached_digest("imagery", 1000)
        _cached_digest("imagery", 2000)  # CSV "edited"
        info = _cached_digest.cache_info()
        assert info.misses == 2, "mtime change must bypass cache"


# ---------------------------------------------------------------------------
# Isolated CSV fixture — confirms aggregate math
# ---------------------------------------------------------------------------


@pytest.fixture
def tiny_catalog(tmp_path: Path) -> Path:
    """Write a minimal CSV with known aggregates for deterministic assertions."""
    csv_path = tmp_path / "mini-catalog.csv"
    csv_path.write_text(
        "sku,name,collection,price,published,is_preorder,badge\n"
        "a-1,Alpha One,test-alpha,100,1,0,\n"
        "a-2,Alpha Two,test-alpha,200,1,0,\n"
        "a-3,Alpha Three,test-alpha,50,0,1,Pre-Order\n"
        "b-1,Beta One,test-beta,75,0,0,Draft\n",
        encoding="utf-8",
    )
    return csv_path


class TestIsolatedAggregates:
    def test_fixture_aggregates(self, tiny_catalog: Path) -> None:
        ctx = load_catalog_context(tiny_catalog)
        assert ctx.total_skus == 4
        by_name = {s.collection: s for s in ctx.summaries}
        alpha = by_name["test-alpha"]
        assert alpha.sku_count == 3
        assert alpha.live_count == 2
        assert alpha.preorder_count == 1
        assert alpha.draft_count == 0
        assert alpha.price_min == 50.0
        assert alpha.price_max == 200.0

        beta = by_name["test-beta"]
        assert beta.sku_count == 1
        assert beta.live_count == 0
        assert beta.preorder_count == 0
        assert beta.draft_count == 1
