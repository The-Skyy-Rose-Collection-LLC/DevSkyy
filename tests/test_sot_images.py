"""Tests for the canonical SOT product-imagery resolver.

The resolver is THE single authority for "what image represents this SKU" across
every surface. These tests pin the front-first fallback contract (on-model render
before flat packshot) that mirrors the WP theme's product-card-holo.php rule, and
the manifest shape that non-Python surfaces (the dashboard) consume.
"""

from __future__ import annotations

import json

import pytest

from skyyrose.core import sot_images


@pytest.fixture(autouse=True)
def _clear_sot_cache():
    """Drop the lru_cached index around every test so monkeypatched/synthetic
    indices never leak into a later test (the cache is process-global)."""
    sot_images.refresh()
    yield
    sot_images.refresh()


def test_resolve_front_prefers_on_model_render():
    # br-004 has both front_model_image (on-model) and image (flat packshot).
    path = sot_images.resolve_image("br-004", "front")
    assert path is not None
    # Returns the SOT's front_model_image value exactly — assert on the contract,
    # not on a filename substring (which would break on a differently-named asset).
    assert path == sot_images._index()["br-004"]["images"]["front_model_image"]["path"]
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


def test_back_falls_back_to_back_image_when_no_back_model(monkeypatch):
    # In live data every SKU with back_image also has back_model_image, so the
    # second fallback key is otherwise unexercised. Synthesize the gap.
    synthetic = {
        "xx-001": {"images": {"back_image": {"path": "assets/images/products/xx-001-back.webp"}}}
    }
    monkeypatch.setattr(sot_images, "_index", lambda: synthetic)
    assert sot_images.resolve_image("xx-001", "back") == "assets/images/products/xx-001-back.webp"


def test_resolve_rejects_path_traversal(monkeypatch):
    # Defense-in-depth: a poisoned SOT path that escapes the assets tree must raise,
    # never silently return a climbing path a consumer might open()/serve.
    synthetic = {"xx-002": {"images": {"front_model_image": {"path": "../../etc/passwd"}}}}
    monkeypatch.setattr(sot_images, "_index", lambda: synthetic)
    with pytest.raises(ValueError, match="escapes the assets tree"):
        sot_images.resolve_image("xx-002", "front")


def test_resolve_model_3d_none_for_unknown_sku():
    assert sot_images.resolve_model_3d("zz-999") is None
    assert sot_images.resolve_model_3d("") is None


def test_resolve_model_3d_none_when_sku_has_no_model_3d_key():
    # Real, known SKU that has no promoted 3D model yet -- degrades to None
    # rather than crashing, mirroring resolve_image's missing-role fallback.
    assert sot_images.resolve_model_3d("br-004") is None


def test_resolve_model_3d_returns_dict_for_promoted_sku(monkeypatch):
    synthetic = {
        "xx-003": {
            "model_3d": {
                "path": "assets/3d-models-generated/xx-003/xx-003.glb",
                "format": "glb",
                "task_id": "task-abc",
                "approved_at": "2026-07-22T00:00:00+00:00",
            }
        }
    }
    monkeypatch.setattr(sot_images, "_index", lambda: synthetic)
    assert sot_images.resolve_model_3d("xx-003") == synthetic["xx-003"]["model_3d"]


def test_resolve_model_3d_rejects_path_traversal(monkeypatch):
    synthetic = {"xx-004": {"model_3d": {"path": "../../etc/passwd", "format": "glb"}}}
    monkeypatch.setattr(sot_images, "_index", lambda: synthetic)
    with pytest.raises(ValueError, match="escapes the assets tree"):
        sot_images.resolve_model_3d("xx-004")


def test_resolve_model_3d_rejects_absolute_path(monkeypatch):
    synthetic = {"xx-005": {"model_3d": {"path": "/etc/passwd", "format": "glb"}}}
    monkeypatch.setattr(sot_images, "_index", lambda: synthetic)
    with pytest.raises(ValueError, match="escapes the assets tree"):
        sot_images.resolve_model_3d("xx-005")
