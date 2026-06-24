"""Tests for the canonical SOT product-imagery resolver.

The resolver is THE single authority for "what image represents this SKU" across
every surface. These tests pin the front-first fallback contract (on-model render
before flat packshot) that mirrors the WP theme's product-card-holo.php rule, and
the manifest shape that non-Python surfaces (the dashboard) consume.
"""

from __future__ import annotations

import json

from skyyrose.core import sot_images


def test_resolve_front_prefers_on_model_render():
    # br-004 has both front_model_image (on-model) and image (flat packshot).
    path = sot_images.resolve_image("br-004", "front")
    assert path is not None
    assert "onmodel" in path or "model" in path
    # Never the flat packshot when an on-model render exists.
    assert path != sot_images.resolve_image("br-004", "packshot")


def test_resolve_back_uses_back_model_image():
    path = sot_images.resolve_image("br-004", "back")
    assert path is not None
    assert "back" in path


def test_packshot_role_returns_flat_image():
    path = sot_images.resolve_image("br-004", "packshot")
    assert path is not None
    # The flat packshot is the catalog `image` column (jpeg/png studio shot).
    assert path.endswith((".jpeg", ".jpg", ".png"))


def test_unknown_sku_returns_none_not_a_guess():
    assert sot_images.resolve_image("zz-999", "front") is None
    assert sot_images.resolve_image("", "front") is None


def test_resolve_returns_theme_relative_assets_path():
    path = sot_images.resolve_image("br-010", "front")
    assert path is not None
    assert path.startswith("assets/images/products/")


def test_all_four_collections_indexed():
    # Every collection's SOT products are reachable through one index.
    skus = sot_images.all_skus()
    assert any(s.startswith("br-") for s in skus)
    assert any(s.startswith("lh-") for s in skus)
    assert any(s.startswith("sg-") for s in skus)
    assert any(s.startswith("kids-") for s in skus)


def test_has_render_true_for_real_sku_false_for_unknown():
    assert sot_images.has_render("br-004") is True
    assert sot_images.has_render("zz-999") is False


def test_build_manifest_shape():
    manifest = sot_images.build_manifest()
    assert "br-004" in manifest
    entry = manifest["br-004"]
    assert set(entry).issubset({"front", "back", "packshot"})
    assert "front" in entry  # every published SKU has at least a front
    # Manifest paths are the same theme-relative contract as resolve_image.
    assert entry["front"] == sot_images.resolve_image("br-004", "front")


def test_manifest_is_json_serializable():
    # The dashboard consumes this as data/sot-images.json — must round-trip.
    manifest = sot_images.build_manifest()
    assert json.loads(json.dumps(manifest)) == manifest
