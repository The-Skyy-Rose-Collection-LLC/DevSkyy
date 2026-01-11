"""
Luxury Homepage Builder for SkyyRose.

Generates luxury fashion homepage with editorial layouts following NET-A-PORTER/SSENSE standards.
"""

from dataclasses import dataclass
from typing import Any

from wordpress.elementor import COLLECTION_BRAND_KITS, BrandKit, ElementorPageBuilder


@dataclass
class LuxuryHomePageBuilder(ElementorPageBuilder):
    """Generates luxury fashion homepage with hero, collections grid, editorial sections."""

    def build_hero_section(self, brand_kit: BrandKit) -> dict[str, Any]:
        """
        Full-bleed hero with video background and minimal text overlay.

        Args:
            brand_kit: Collection brand kit for colors and content

        Returns:
            Elementor section configuration dict
        """
        return {
            "elType": "section",
            "settings": {
                "layout": "full_width",
                "height": "100vh",
                "background_video_link": "",  # TODO: Add video URL when available
                "background_overlay": "yes",
                "background_overlay_opacity": 0.3,
                "padding": {"top": 0, "bottom": 0},
            },
            "elements": [
                {
                    "elType": "column",
                    "settings": {"_column_size": 100},
                    "elements": [
                        # Hero headline (Playfair Display)
                        {
                            "elType": "widget",
                            "widgetType": "heading",
                            "settings": {
                                "title": brand_kit.voice.tagline,
                                "typography_font_family": "Playfair Display",
                                "typography_font_size": {"size": 72, "unit": "px"},
                                "typography_font_weight": 700,
                                "typography_line_height": {"size": 1.2, "unit": "em"},
                                "color": "#FFFFFF",
                                "text_align": "center",
                            },
                        },
                        # Subtitle (Inter)
                        {
                            "elType": "widget",
                            "widgetType": "text-editor",
                            "settings": {
                                "editor": brand_kit.name,
                                "typography_font_family": "Inter",
                                "typography_font_size": {"size": 18, "unit": "px"},
                                "color": "#F5F5F0",
                                "text_align": "center",
                            },
                        },
                        # CTA button
                        {
                            "elType": "widget",
                            "widgetType": "button",
                            "settings": {
                                "text": "Explore Collections",
                                "link": {"url": "/collections"},
                                "typography_font_family": "Inter",
                                "typography_font_weight": 600,
                                "typography_text_transform": "uppercase",
                                "typography_letter_spacing": {"size": 0.1, "unit": "em"},
                                "button_background_color": brand_kit.colors.primary,
                                "button_hover_background_color": "#FFFFFF",
                                "button_text_color": "#FFFFFF",
                                "button_hover_text_color": brand_kit.colors.primary,
                                "button_border_width": {"size": 2, "unit": "px"},
                                "button_border_color": brand_kit.colors.primary,
                            },
                        },
                    ],
                }
            ],
        }

    def build_collections_grid(self) -> dict[str, Any]:
        """
        3-column collections grid with hover effects.

        Returns:
            Elementor section configuration dict
        """
        collections = ["signature", "love-hurts", "black-rose"]

        return {
            "elType": "section",
            "settings": {
                "layout": "boxed",
                "gap": "extended",  # 48px gap (luxury spacing)
                "padding": {"top": 120, "bottom": 120, "unit": "px"},
            },
            "elements": [
                {
                    "elType": "column",
                    "settings": {"_column_size": 33},
                    "elements": [self._build_collection_card(coll) for coll in collections],
                }
            ],
        }

    def _build_collection_card(self, collection_slug: str) -> dict[str, Any]:
        """
        Individual collection card with image overlay and hover effect.

        Args:
            collection_slug: Collection identifier (signature, love-hurts, black-rose)

        Returns:
            Widget configuration dict
        """
        brand_kit = COLLECTION_BRAND_KITS[collection_slug]

        return {
            "elType": "widget",
            "widgetType": "image-box",
            "settings": {
                "image": {"url": f"/wp-content/uploads/collections/{collection_slug}-hero.webp"},
                "title_text": brand_kit.name,
                "description_text": "",  # TODO: Add collection descriptions
                "link": {"url": f"/collections/{collection_slug}"},
                "image_size": "full",
                "title_typography_font_family": "Playfair Display",
                "title_typography_font_size": {"size": 32, "unit": "px"},
                "title_color": brand_kit.colors.primary,
                "hover_animation": "grow",
                "overlay_background": f"linear-gradient(180deg, transparent 0%, {brand_kit.colors.dark} 100%)",
            },
        }

    def generate(self) -> dict[str, Any]:
        """
        Generate complete luxury homepage.

        Returns:
            Complete Elementor template configuration dict
        """
        brand_kit = COLLECTION_BRAND_KITS["signature"]  # Default brand

        return {
            "content": [
                self.build_hero_section(brand_kit),
                self.build_collections_grid(),
                # Add editorial section, testimonials, Instagram feed here in future
            ],
            "page_settings": {
                "post_title": "Home - SkyyRose",
                "template": "elementor_canvas",  # Full-width, no header/footer chrome
            },
        }
