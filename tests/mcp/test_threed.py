"""Tests for mcp_tools/tools/threed.py.

Covers:
    - sku-only resolves image_url via the SOT (resolve_image), mocked
    - explicit image_url is never overridden by sku resolution
    - neither field given raises ValidationError (from the after-validator)
    - sku given but unresolvable raises ValidationError
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from pydantic import ValidationError

from mcp_tools.tools import threed
from mcp_tools.tools.threed import ThreeDImageInput

_THEME_BASE_URL = "https://skyyrose.co/wp-content/themes/skyyrose-flagship/"


class TestSkuResolution:
    def test_sku_only_resolves_image_url(self) -> None:
        with patch.object(
            threed, "resolve_image", return_value="assets/images/products/br-004-front.webp"
        ) as mock_resolve:
            params = ThreeDImageInput(product_name="Black Rose Bomber", sku="br-004")

        mock_resolve.assert_called_once_with("br-004", "front")
        assert params.image_url == _THEME_BASE_URL + "assets/images/products/br-004-front.webp"

    def test_explicit_image_url_never_overridden(self) -> None:
        explicit_url = "https://cdn.skyyrose.co/designs/hoodie-front.jpg"
        with patch.object(
            threed, "resolve_image", return_value="assets/images/products/SENTINEL.webp"
        ) as mock_resolve:
            params = ThreeDImageInput(
                product_name="Custom Hoodie", image_url=explicit_url, sku="br-004"
            )

        mock_resolve.assert_not_called()
        assert params.image_url == explicit_url

    def test_neither_field_given_raises(self) -> None:
        with pytest.raises(ValidationError, match="Either image_url or sku must be provided"):
            ThreeDImageInput(product_name="Nameless Thing")

    def test_sku_unresolvable_raises(self) -> None:
        with patch.object(threed, "resolve_image", return_value=None):
            with pytest.raises(ValidationError, match="Could not resolve a front product image"):
                ThreeDImageInput(product_name="Ghost Product", sku="totally-bogus-sku-xyz")
