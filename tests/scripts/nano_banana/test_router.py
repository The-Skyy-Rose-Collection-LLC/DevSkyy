"""Unit tests for scripts/nano_banana/router.py."""

from __future__ import annotations

from unittest.mock import patch

from nano_banana.router import RouteDecision, estimate_batch_cost, route_product


def _empty_treatments(*_args, **_kwargs) -> dict:
    return {}


class TestRouteProduct:
    """Tests for route_product() — model selection logic."""

    def test_route_product_default(self) -> None:
        """Basic product with no text/complex fabric returns FLUX primary."""
        product = {
            "sku": "sg-001",
            "name": "The Bay Bridge Shorts",
            "collection": "signature",
            "is_accessory": False,
        }
        vision = {
            "garment_type": "shorts",
            "colors": [{"name": "gold", "hex": "#D4AF37"}],
            "graphics": [],
            "fabric_appearance": "standard cotton jersey",
            "construction": "elastic waist",
        }
        with patch("nano_banana.prompts.LOGO_TREATMENTS", {}):
            decisions = route_product(product, vision)

        assert isinstance(decisions, list)
        assert len(decisions) >= 1
        assert all(isinstance(d, RouteDecision) for d in decisions)
        # Default plain garment should route to flux-pro primary
        assert decisions[0].engine == "flux-pro"

    def test_route_product_with_text_graphics(self) -> None:
        """Product with text content routes to gpt-image for accuracy."""
        product = {
            "sku": "br-003",
            "name": "BLACK is Beautiful Jersey",
            "collection": "black-rose",
            "is_accessory": False,
        }
        vision = {
            "garment_type": "baseball jersey",
            "colors": [{"name": "black", "hex": "#0A0A0A"}],
            "graphics": [
                {
                    "type": "screen print",
                    "content": "black is beautiful",
                    "position": "front chest",
                },
            ],
            "fabric_appearance": "mesh polyester",
            "construction": "button front",
        }
        with patch("nano_banana.prompts.LOGO_TREATMENTS", {}):
            decisions = route_product(product, vision)

        assert decisions[0].engine == "gpt-image"
        assert decisions[0].priority == 1


class TestEstimateBatchCost:
    """Tests for estimate_batch_cost() — cost estimation."""

    def test_estimate_batch_cost(self) -> None:
        """2 products x 2 views = 4 images with correct cost structure."""
        products = [
            {
                "sku": "sg-001",
                "name": "The Bay Bridge Shorts",
                "collection": "signature",
                "is_accessory": False,
            },
            {
                "sku": "kids-001",
                "name": "Kids Red Hoodie Set",
                "collection": "kids-capsule",
                "is_accessory": False,
            },
        ]
        views = ["front", "back"]

        with patch("nano_banana.prompts.LOGO_TREATMENTS", {}):
            result = estimate_batch_cost(products, views)

        assert result["image_count"] == 4
        assert "total_usd" in result
        assert result["total_usd"] > 0
        assert "per_engine" in result
        assert isinstance(result["per_engine"], dict)
        # Both plain garments should route to flux-pro for all views
        assert "flux-pro" in result["per_engine"]
