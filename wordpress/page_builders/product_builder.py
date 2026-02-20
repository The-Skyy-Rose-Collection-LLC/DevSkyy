"""Product page Elementor template builder."""

from __future__ import annotations

from typing import Any

from wordpress.elementor import SKYYROSE_BRAND_KIT


class ProductPageBuilder:
    """
    Builds WooCommerce product page Elementor templates.

    Features 60/40 gallery-details split layout with 3D viewer support.
    """

    def __init__(self) -> None:
        self.brand_kit = SKYYROSE_BRAND_KIT

    def generate(self, product: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Generate product page template.

        Args:
            product: Product data dict with name, price, description, etc.

        Returns:
            Elementor-compatible template dict.
        """
        product = product or {}
        colors = self.brand_kit["colors"]

        return {
            "content": [
                self.build_luxury_product_hero(product),
            ],
            "page_settings": {
                "post_title": product.get("name", "Product"),
                "template": "elementor_header_footer",
            },
        }

    def build_luxury_product_hero(self, product: dict[str, Any]) -> dict[str, Any]:
        """
        Build luxury product hero section with 60/40 split layout.

        Left (60%): Image gallery with zoom/lightbox/slider
        Right (40%): Product details, pricing, CTA

        Args:
            product: Product data dict.

        Returns:
            Elementor section element dict.
        """
        colors = self.brand_kit["colors"]

        return {
            "elType": "section",
            "settings": {
                "layout": "boxed",
                "background_color": colors["obsidian"],
                "padding": {"unit": "px", "top": "60", "bottom": "60"},
                "structure": "20",  # 60/40 split
            },
            "elements": [
                # Left column - Gallery (60%)
                {
                    "elType": "column",
                    "settings": {"_column_size": 60},
                    "elements": [
                        {
                            "elType": "widget",
                            "widgetType": "image",
                            "settings": {
                                "image": {
                                    "url": product.get("image_url", ""),
                                    "alt": product.get("name", "Product"),
                                },
                                "image_size": "custom",
                                "image_custom_dimension": {
                                    "width": 1200,
                                    "height": 1600,
                                },
                                "lightbox": "yes",
                            },
                        }
                    ],
                },
                # Right column - Details (40%)
                {
                    "elType": "column",
                    "settings": {"_column_size": 40},
                    "elements": [
                        {
                            "elType": "widget",
                            "widgetType": "heading",
                            "settings": {
                                "title": product.get("name", "Product"),
                                "header_size": "h1",
                                "title_color": colors["white"],
                                "typography_font_family": "Playfair Display",
                            },
                        },
                        {
                            "elType": "widget",
                            "widgetType": "heading",
                            "settings": {
                                "title": product.get("price", ""),
                                "header_size": "h3",
                                "title_color": colors["roseGold"],
                                "typography_font_family": "Inter",
                            },
                        },
                        {
                            "elType": "widget",
                            "widgetType": "text-editor",
                            "settings": {
                                "editor": f"<p>{product.get('description', '')}</p>",
                                "text_color": colors["cream"],
                                "typography_font_family": "Inter",
                            },
                        },
                        {
                            "elType": "widget",
                            "widgetType": "button",
                            "settings": {
                                "text": "Claim Your Rose",
                                "link": {"url": "#"},
                                "background_color": colors["roseGold"],
                                "text_color": colors["white"],
                                "typography_font_family": "Inter",
                                "typography_font_weight": "600",
                                "typography_text_transform": "uppercase",
                                "typography_letter_spacing": {"unit": "px", "size": 2},
                            },
                        },
                    ],
                },
            ],
        }
