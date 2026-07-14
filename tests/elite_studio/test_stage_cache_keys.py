"""Phase 1 / P-cachekey: stage A/D cache keys must include the SKU.

Two garments that share an identical base studio photo (common within a
collection) must NOT collide on a cached matte/composite — the cache key has
to be SKU-scoped. Model-free: rembg ``remove`` and the cache dir are stubbed.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

pytestmark = pytest.mark.unit


def _png(p: Path) -> Path:
    Image.new("RGBA", (1, 1), (255, 255, 255, 255)).save(p)
    return p


def test_stage_d_cache_key_differs_per_sku(tmp_path):
    from skyyrose.elite_studio.agents.compositor.stage_d_rasterize import _composite_cache_key

    f = _png(tmp_path / "shared.png")
    k1 = _composite_cache_key(f, f, f, "br-001")
    k2 = _composite_cache_key(f, f, f, "br-012")
    assert k1 != k2, "stage D cache key must include the SKU"


def test_stage_a_different_skus_same_source_distinct_cache(tmp_path, monkeypatch):
    from skyyrose.elite_studio.agents.compositor import stage_a_matte

    cache = tmp_path / "matte-cache"
    cache.mkdir()
    monkeypatch.setattr(stage_a_matte, "_cache_dir", lambda name: cache)
    monkeypatch.setattr(
        stage_a_matte, "remove", lambda b: Image.new("RGBA", (1, 1), (0, 0, 0, 255))
    )

    src = tmp_path / "source.png"
    Image.new("RGBA", (1, 1), (255, 255, 255, 255)).save(src)

    for sku in ("br-001", "br-012"):
        out_dir = tmp_path / sku
        out_dir.mkdir()
        stage_a_matte.extract_alpha(str(src), sku, str(out_dir))

    cached = list(cache.glob("*.png"))
    assert len(cached) == 2, f"expected 2 distinct SKU-scoped cache entries, got {len(cached)}"
