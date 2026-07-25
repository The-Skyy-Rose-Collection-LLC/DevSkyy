"""
Tests for MCP Virtual Try-On Input Models — SOT Resolution
============================================================

Covers the ``VirtualTryOnInput`` / ``BatchVirtualTryOnInput`` ``product_id`` ->
``garment_image_url`` resolution added on top of the pre-existing (required)
``garment_image_url`` field, so a bare ``product_id`` never silently bypasses the
SOT (skyyrose.core.sot_images.resolve_image).
"""

import pytest
from pydantic import ValidationError

from mcp_tools.tools.virtual_tryon import BatchVirtualTryOnInput, VirtualTryOnInput


class TestVirtualTryOnInputSotResolution:
    """Tests for VirtualTryOnInput.garment_image_url SOT resolution."""

    def test_product_id_only_resolves_garment_image_url(self, mocker):
        """product_id alone should resolve garment_image_url via resolve_image()."""
        mock_resolve = mocker.patch(
            "mcp_tools.tools.virtual_tryon.resolve_image",
            return_value="assets/images/products/br-001.jpg",
        )

        params = VirtualTryOnInput(
            model_image_url="https://example.com/model.jpg",
            product_id="br-001",
        )

        mock_resolve.assert_called_once_with("br-001", "front")
        assert params.garment_image_url == (
            "https://skyyrose.co/wp-content/themes/skyyrose-flagship/"
            "assets/images/products/br-001.jpg"
        )

    def test_explicit_garment_image_url_is_never_overridden(self, mocker):
        """An explicit garment_image_url must win even when product_id is also given."""
        mock_resolve = mocker.patch("mcp_tools.tools.virtual_tryon.resolve_image")

        params = VirtualTryOnInput(
            model_image_url="https://example.com/model.jpg",
            garment_image_url="https://example.com/explicit-garment.jpg",
            product_id="br-001",
        )

        mock_resolve.assert_not_called()
        assert params.garment_image_url == "https://example.com/explicit-garment.jpg"

    def test_neither_field_given_raises(self):
        """Omitting both garment_image_url and product_id must raise ValueError."""
        with pytest.raises(ValidationError, match="garment_image_url is required"):
            VirtualTryOnInput(model_image_url="https://example.com/model.jpg")

    def test_unresolvable_product_id_raises(self, mocker):
        """A product_id the SOT can't resolve must raise, not silently pass through."""
        mocker.patch(
            "mcp_tools.tools.virtual_tryon.resolve_image",
            return_value=None,
        )

        with pytest.raises(ValidationError, match="could not resolve garment_image_url"):
            VirtualTryOnInput(
                model_image_url="https://example.com/model.jpg",
                product_id="zz-999",
            )


class TestBatchVirtualTryOnInputSotResolution:
    """Tests for BatchVirtualTryOnInput.garments SOT resolution."""

    def test_product_id_only_resolves_garment_image_url(self, mocker):
        """A garment dict with only product_id should get garment_image_url filled in."""
        mock_resolve = mocker.patch(
            "mcp_tools.tools.virtual_tryon.resolve_image",
            return_value="assets/images/products/sg-003.jpg",
        )

        params = BatchVirtualTryOnInput(
            model_image_url="https://example.com/model.jpg",
            garments=[{"product_id": "sg-003", "category": "tops"}],
        )

        mock_resolve.assert_called_once_with("sg-003", "front")
        assert params.garments[0]["garment_image_url"] == (
            "https://skyyrose.co/wp-content/themes/skyyrose-flagship/"
            "assets/images/products/sg-003.jpg"
        )

    def test_explicit_garment_image_url_is_never_overridden(self, mocker):
        """A garment dict with an explicit URL must keep it even if product_id is present."""
        mock_resolve = mocker.patch("mcp_tools.tools.virtual_tryon.resolve_image")

        params = BatchVirtualTryOnInput(
            model_image_url="https://example.com/model.jpg",
            garments=[
                {
                    "garment_image_url": "https://example.com/explicit.jpg",
                    "product_id": "sg-003",
                    "category": "tops",
                }
            ],
        )

        mock_resolve.assert_not_called()
        assert params.garments[0]["garment_image_url"] == "https://example.com/explicit.jpg"

    def test_neither_field_given_raises(self):
        """A garment dict missing both garment_image_url and product_id must raise."""
        with pytest.raises(ValidationError, match="each garment needs garment_image_url"):
            BatchVirtualTryOnInput(
                model_image_url="https://example.com/model.jpg",
                garments=[{"category": "tops"}],
            )

    def test_unresolvable_product_id_raises_naming_sku(self, mocker):
        """An unresolvable product_id must raise, naming the offending SKU."""
        mocker.patch(
            "mcp_tools.tools.virtual_tryon.resolve_image",
            return_value=None,
        )

        with pytest.raises(ValidationError, match="zz-999"):
            BatchVirtualTryOnInput(
                model_image_url="https://example.com/model.jpg",
                garments=[{"product_id": "zz-999", "category": "tops"}],
            )

    def test_mixed_batch_resolves_only_missing_urls(self, mocker):
        """A batch mixing explicit URLs and product_id-only items resolves only the latter."""
        mock_resolve = mocker.patch(
            "mcp_tools.tools.virtual_tryon.resolve_image",
            return_value="assets/images/products/br-001.jpg",
        )

        params = BatchVirtualTryOnInput(
            model_image_url="https://example.com/model.jpg",
            garments=[
                {"garment_image_url": "https://example.com/explicit.jpg", "category": "tops"},
                {"product_id": "br-001", "category": "outerwear"},
            ],
        )

        mock_resolve.assert_called_once_with("br-001", "front")
        assert params.garments[0]["garment_image_url"] == "https://example.com/explicit.jpg"
        assert params.garments[1]["garment_image_url"] == (
            "https://skyyrose.co/wp-content/themes/skyyrose-flagship/"
            "assets/images/products/br-001.jpg"
        )
