"""Luxury homepage variant builder."""

from __future__ import annotations

from typing import Any

from wordpress.elementor import SKYYROSE_BRAND_KIT


class LuxuryHomePageBuilder:
    """
    Builds the luxury variant of the SkyyRose homepage.

    Features full-bleed video hero and 3-column collections grid
    with hover effects and 48px gaps.
    """

    def __init__(self) -> None:
        self.brand_kit = SKYYROSE_BRAND_KIT

    def generate(self) -> dict[str, Any]:
        """
        Generate luxury homepage as Elementor-compatible dict.

        Returns:
            Dictionary structure ready for JSON export.
        """
        colors = self.brand_kit["colors"]

        return {
            "content": [
                # Hero section with video background
                {
                    "elType": "section",
                    "settings": {
                        "layout": "full_width",
                        "background_video_url": "",
                        "background_color": colors["obsidian"],
                        "padding": {
                            "unit": "px",
                            "top": "120",
                            "bottom": "120",
                        },
                    },
                    "elements": [
                        {
                            "elType": "column",
                            "settings": {"_column_size": 100},
                            "elements": [
                                {
                                    "elType": "widget",
                                    "widgetType": "heading",
                                    "settings": {
                                        "title": "SkyyRose",
                                        "header_size": "h1",
                                        "align": "center",
                                        "title_color": colors["white"],
                                        "typography_font_family": "Playfair Display",
                                        "typography_font_size": {"unit": "px", "size": 72},
                                    },
                                },
                                {
                                    "elType": "widget",
                                    "widgetType": "text-editor",
                                    "settings": {
                                        "editor": "<p>Where Love Meets Luxury</p>",
                                        "align": "center",
                                        "text_color": colors["roseGold"],
                                        "typography_font_family": "Inter",
                                        "typography_letter_spacing": {"unit": "px", "size": 4},
                                    },
                                },
                            ],
                        }
                    ],
                },
                # Collections grid (3-column)
                {
                    "elType": "section",
                    "settings": {
                        "layout": "boxed",
                        "background_color": colors["black"],
                        "padding": {
                            "unit": "px",
                            "top": "80",
                            "bottom": "80",
                        },
                        "gap": "48px",
                    },
                    "elements": [
                        {
                            "elType": "column",
                            "settings": {"_column_size": 33},
                            "elements": [
                                {
                                    "elType": "widget",
                                    "widgetType": "heading",
                                    "settings": {
                                        "title": "BLACK ROSE",
                                        "header_size": "h3",
                                        "title_color": colors["white"],
                                    },
                                }
                            ],
                        },
                        {
                            "elType": "column",
                            "settings": {"_column_size": 33},
                            "elements": [
                                {
                                    "elType": "widget",
                                    "widgetType": "heading",
                                    "settings": {
                                        "title": "LOVE HURTS",
                                        "header_size": "h3",
                                        "title_color": colors["deepRed"],
                                    },
                                }
                            ],
                        },
                        {
                            "elType": "column",
                            "settings": {"_column_size": 33},
                            "elements": [
                                {
                                    "elType": "widget",
                                    "widgetType": "heading",
                                    "settings": {
                                        "title": "SIGNATURE",
                                        "header_size": "h3",
                                        "title_color": colors["roseGold"],
                                    },
                                }
                            ],
                        },
                    ],
                },
            ],
            "page_settings": {
                "post_title": "Home - Luxury",
                "template": "elementor_header_footer",
            },
        }
