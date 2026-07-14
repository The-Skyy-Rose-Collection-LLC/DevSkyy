"""Phase 1 / P-skuvalidate: composite() rejects an unknown SKU at entry.

A typo SKU must fail fast (ValueError) before any filesystem mutation or paid
stage — not run the whole pipeline and score an unapprovable image. Model-free:
the catalog loader is patched to a fixed set.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from skyyrose.elite_studio.agents.compositor.orchestrator import CompositorAgent

pytestmark = pytest.mark.unit

FAKE_CATALOG = [{"sku": "br-001"}, {"sku": "sg-001"}, {"sku": "lh-001"}]


@patch("skyyrose.core.catalog_loader.read_catalog_rows", return_value=FAKE_CATALOG)
def test_unknown_sku_raises_value_error(_rows):
    """An unknown SKU raises ValueError before the pipeline's try-block runs."""
    agent = CompositorAgent.__new__(CompositorAgent)
    with pytest.raises(ValueError, match="unknown SKU"):
        agent.composite(
            sku="br-999",
            scene_image_path="/tmp/scene.jpg",
            model_image_path="/tmp/model.jpg",
            collection="Black Rose",
            scene_name="test-scene",
        )
