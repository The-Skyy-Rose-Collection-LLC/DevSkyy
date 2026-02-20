"""
Elementor Template Builder
============================

Generates Elementor-compatible JSON templates for SkyyRose WordPress pages.
Includes the SkyyRose brand kit with design tokens.

Usage:
    from wordpress.elementor import ElementorBuilder, SKYYROSE_BRAND_KIT

    builder = ElementorBuilder()
    template = builder.generate_home_page(hero_title="SkyyRose")
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# =============================================================================
# Brand Kit
# =============================================================================

SKYYROSE_BRAND_KIT: dict[str, Any] = {
    "colors": {
        "obsidian": "#0D0D0D",
        "roseGold": "#B76E79",
        "gold": "#D4AF37",
        "cream": "#F5F0E8",
        "white": "#FAFAFA",
        "black": "#1A1A1A",
        "deepRed": "#E63946",
        "softPink": "#FFB4C2",
    },
    "typography": {
        "display": {
            "family": "Playfair Display",
            "weight": "700",
            "style": "normal",
        },
        "heading": {
            "family": "Playfair Display",
            "weight": "600",
            "style": "normal",
        },
        "body": {
            "family": "Inter",
            "weight": "400",
            "style": "normal",
        },
        "caption": {
            "family": "Inter",
            "weight": "300",
            "style": "italic",
        },
    },
    "spacing": {
        "unit": 4,
        "section_padding": "120px",
        "content_gap": "48px",
        "grid_gap": "24px",
    },
    "imagery": {
        "hero_aspect_ratio": "16:9",
        "product_aspect_ratio": "3:4",
        "thumbnail_size": "600x600",
        "gallery_size": "1200x1600",
        "max_resolution": "2400px",
    },
    "voice": {
        "tagline": "Where Love Meets Luxury",
        "tone": "confident, sensual, aspirational",
        "brand_name": "SkyyRose",
    },
}


# =============================================================================
# Enums
# =============================================================================


class PageType(str, Enum):
    """Elementor page types."""

    HOME = "home"
    COLLECTION = "collection"
    PRODUCT = "product"
    ABOUT = "about"
    BLOG = "blog"
    CONTACT = "contact"


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class PageSpec:
    """Specification for an Elementor page."""

    page_type: PageType
    title: str
    slug: str
    template: str = "elementor_header_footer"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ElementorConfig:
    """Configuration for Elementor template generation."""

    brand_kit: dict[str, Any] = field(default_factory=lambda: dict(SKYYROSE_BRAND_KIT))
    container_width: int = 1200
    responsive_breakpoints: dict[str, int] = field(
        default_factory=lambda: {"mobile": 768, "tablet": 1024, "desktop": 1440}
    )


class ElementorTemplate:
    """
    Represents a generated Elementor template.

    Can be exported to JSON for WordPress import.
    """

    def __init__(
        self,
        content: list[dict[str, Any]] | None = None,
        page_settings: dict[str, Any] | None = None,
    ) -> None:
        self.content = content or []
        self.page_settings = page_settings or {
            "template": "elementor_header_footer",
        }

    def to_json(self) -> str:
        """Export template as JSON string."""
        return json.dumps(
            {
                "content": self.content,
                "page_settings": self.page_settings,
            },
            indent=2,
        )

    def to_dict(self) -> dict[str, Any]:
        """Export template as dictionary."""
        return {
            "content": self.content,
            "page_settings": self.page_settings,
        }

    def to_file(self, path: str) -> None:
        """
        Export template to a JSON file.

        Args:
            path: Output file path.
        """
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(self.to_json())
        logger.info("template_exported", extra={"path": str(output_path)})


# =============================================================================
# Elementor Builder
# =============================================================================


class ElementorBuilder:
    """
    Builds Elementor-compatible page templates using SkyyRose brand kit.

    Generates structured JSON that can be imported into Elementor
    via the WordPress admin panel.
    """

    def __init__(self, config: ElementorConfig | None = None) -> None:
        self.config = config or ElementorConfig()
        self.brand_kit = self.config.brand_kit

    def _section(
        self,
        widgets: list[dict[str, Any]],
        layout: str = "full_width",
        background: str | None = None,
        padding: str = "60px",
    ) -> dict[str, Any]:
        """Create an Elementor section element."""
        section: dict[str, Any] = {
            "elType": "section",
            "settings": {
                "layout": layout,
                "padding": {"unit": "px", "top": padding, "bottom": padding},
            },
            "elements": [
                {
                    "elType": "column",
                    "settings": {"_column_size": 100},
                    "elements": widgets,
                }
            ],
        }

        if background:
            section["settings"]["background_color"] = background

        return section

    def _heading(
        self,
        text: str,
        tag: str = "h2",
        align: str = "center",
        color: str | None = None,
    ) -> dict[str, Any]:
        """Create a heading widget."""
        colors = self.brand_kit.get("colors", {})
        return {
            "elType": "widget",
            "widgetType": "heading",
            "settings": {
                "title": text,
                "header_size": tag,
                "align": align,
                "title_color": color or colors.get("white", "#FAFAFA"),
                "typography_font_family": "Playfair Display",
                "typography_font_weight": "700",
            },
        }

    def _text(self, content: str, align: str = "center") -> dict[str, Any]:
        """Create a text editor widget."""
        return {
            "elType": "widget",
            "widgetType": "text-editor",
            "settings": {
                "editor": content,
                "align": align,
                "text_color": self.brand_kit.get("colors", {}).get("cream", "#F5F0E8"),
                "typography_font_family": "Inter",
            },
        }

    def _button(
        self,
        text: str,
        link: str = "#",
        style: str = "primary",
    ) -> dict[str, Any]:
        """Create a button widget."""
        colors = self.brand_kit.get("colors", {})
        bg_color = colors.get("roseGold", "#B76E79") if style == "primary" else "transparent"

        return {
            "elType": "widget",
            "widgetType": "button",
            "settings": {
                "text": text,
                "link": {"url": link},
                "background_color": bg_color,
                "text_color": colors.get("white", "#FAFAFA"),
                "border_radius": {"unit": "px", "size": 0},
                "typography_font_family": "Inter",
                "typography_font_weight": "600",
                "typography_text_transform": "uppercase",
                "typography_letter_spacing": {"unit": "px", "size": 2},
            },
        }

    def _image(
        self,
        url: str = "",
        alt: str = "",
        size: str = "full",
    ) -> dict[str, Any]:
        """Create an image widget."""
        return {
            "elType": "widget",
            "widgetType": "image",
            "settings": {
                "image": {"url": url, "alt": alt},
                "image_size": size,
            },
        }

    def generate_home_page(
        self,
        hero_title: str = "SkyyRose",
        hero_subtitle: str = "Where Love Meets Luxury",
        **kwargs: Any,
    ) -> ElementorTemplate:
        """
        Generate a homepage template.

        Args:
            hero_title: Main hero heading text.
            hero_subtitle: Hero subtitle text.
            **kwargs: Additional template options.

        Returns:
            ElementorTemplate ready for export.
        """
        colors = self.brand_kit.get("colors", {})

        content = [
            # Hero Section
            self._section(
                widgets=[
                    self._heading(hero_title, tag="h1"),
                    self._text(f"<p>{hero_subtitle}</p>"),
                    self._button("Explore Collections", link="/collections"),
                ],
                background=colors.get("obsidian", "#0D0D0D"),
                padding="120px",
            ),
            # Collections Grid
            self._section(
                widgets=[
                    self._heading("Our Collections", tag="h2"),
                    self._text(
                        "<p>Discover the artistry of SkyyRose — "
                        "three collections that define luxury streetwear.</p>"
                    ),
                ],
                background=colors.get("black", "#1A1A1A"),
                padding="80px",
            ),
        ]

        return ElementorTemplate(
            content=content,
            page_settings={
                "post_title": hero_title,
                "template": "elementor_header_footer",
            },
        )

    def generate_collection_page(
        self,
        collection_name: str,
        collection_description: str = "",
        experience_url: str = "",
        **kwargs: Any,
    ) -> ElementorTemplate:
        """
        Generate a collection page template.

        Args:
            collection_name: Name of the collection.
            collection_description: Collection description text.
            experience_url: URL for the 3D experience iframe.
            **kwargs: Additional options.

        Returns:
            ElementorTemplate for collection page.
        """
        colors = self.brand_kit.get("colors", {})

        content = [
            self._section(
                widgets=[
                    self._heading(collection_name, tag="h1"),
                    self._text(f"<p>{collection_description}</p>"),
                ],
                background=colors.get("obsidian", "#0D0D0D"),
                padding="120px",
            ),
        ]

        if experience_url:
            content.append(
                self._section(
                    widgets=[
                        {
                            "elType": "widget",
                            "widgetType": "html",
                            "settings": {
                                "html": (
                                    f'<iframe src="{experience_url}" '
                                    f'width="100%" height="800" '
                                    f'frameborder="0" allowfullscreen></iframe>'
                                ),
                            },
                        }
                    ],
                    padding="0px",
                )
            )

        return ElementorTemplate(
            content=content,
            page_settings={
                "post_title": collection_name,
                "template": "elementor_header_footer",
            },
        )

    def generate_product_page(
        self,
        product_name: str = "Product",
        glb_url: str = "",
        **kwargs: Any,
    ) -> ElementorTemplate:
        """Generate a product page template with optional 3D viewer."""
        content = [
            self._section(
                widgets=[
                    self._heading(product_name, tag="h1"),
                ],
                padding="60px",
            ),
        ]

        return ElementorTemplate(
            content=content,
            page_settings={
                "post_title": product_name,
                "template": "elementor_header_footer",
            },
        )


__all__ = [
    "SKYYROSE_BRAND_KIT",
    "PageType",
    "PageSpec",
    "ElementorConfig",
    "ElementorTemplate",
    "ElementorBuilder",
]
