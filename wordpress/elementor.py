"""
Elementor Template Builder
==========================

Generate Elementor-compatible templates programmatically.

Features:
- BrandKit: Design tokens (colors, typography, spacing)
- PageSpec: Page type definitions
- Template generation for various page types
- JSON export in Elementor Kit format

Compatible with:
- Elementor Pro 3.32+
- Shoptimizer 2.9.0 theme

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# =============================================================================
# Enums
# =============================================================================


class WidgetType(str, Enum):
    """Elementor widget types."""

    HEADING = "heading"
    TEXT_EDITOR = "text-editor"
    IMAGE = "image"
    IMAGE_BOX = "image-box"
    BUTTON = "button"
    ICON = "icon"
    ICON_BOX = "icon-box"
    SPACER = "spacer"
    DIVIDER = "divider"
    VIDEO = "video"

    # WooCommerce
    PRODUCTS = "woocommerce-products"
    PRODUCT_IMAGES = "woocommerce-product-images"
    PRODUCT_TITLE = "woocommerce-product-title"
    PRODUCT_PRICE = "woocommerce-product-price"
    ADD_TO_CART = "woocommerce-product-add-to-cart"

    # Pro
    LOOP_GRID = "loop-grid"
    POSTS = "posts"
    GALLERY = "gallery"
    FORM = "form"
    SLIDES = "slides"
    NAV_MENU = "nav-menu"


class SectionLayout(str, Enum):
    """Section layout types."""

    BOXED = "boxed"
    FULL_WIDTH = "full_width"
    FULL_SCREEN = "full_screen"


class PageType(str, Enum):
    """Page types for template generation."""

    HOME = "home"
    COLLECTION = "collection"
    PRODUCT = "product"
    ABOUT = "about"
    CONTACT = "contact"
    LOOKBOOK = "lookbook"


# =============================================================================
# BrandKit
# =============================================================================


@dataclass
class BrandColors:
    """Brand color palette."""

    primary: str = "#D4AF37"  # Rose gold
    secondary: str = "#0D0D0D"  # Obsidian black
    accent: str = "#F5F5F0"  # Ivory
    text: str = "#1A1A1A"
    text_light: str = "#666666"
    background: str = "#FFFFFF"
    background_alt: str = "#F9F9F9"


@dataclass
class BrandTypography:
    """Brand typography settings."""

    heading_font: str = "Playfair Display"
    body_font: str = "Inter"
    heading_weight: int = 700
    body_weight: int = 400
    base_size: int = 16
    line_height: float = 1.6
    letter_spacing: str = "0.02em"


@dataclass
class BrandSpacing:
    """Brand spacing system."""

    unit: int = 8  # Base unit in pixels
    xs: int = 8
    sm: int = 16
    md: int = 24
    lg: int = 48
    xl: int = 80
    xxl: int = 120


@dataclass
class BrandImagery:
    """Brand imagery guidelines."""

    aspect_ratio_product: str = "3:4"
    aspect_ratio_hero: str = "16:9"
    aspect_ratio_square: str = "1:1"
    default_placeholder: str = ""
    logo_url: str = ""
    favicon_url: str = ""


@dataclass
class BrandVoice:
    """Brand voice and copy guidelines."""

    tagline: str = "Where Love Meets Luxury"
    tone: str = "sophisticated, elevated, authentic"
    cta_primary: str = "Shop Now"
    cta_secondary: str = "Discover More"


@dataclass
class BrandKit:
    """
    Complete brand design system.

    Contains all design tokens needed for consistent template generation.
    """

    name: str = "SkyyRose"
    colors: BrandColors = field(default_factory=BrandColors)
    typography: BrandTypography = field(default_factory=BrandTypography)
    spacing: BrandSpacing = field(default_factory=BrandSpacing)
    imagery: BrandImagery = field(default_factory=BrandImagery)
    voice: BrandVoice = field(default_factory=BrandVoice)

    def to_css_vars(self) -> dict[str, str]:
        """Export as CSS custom properties."""
        return {
            "--color-primary": self.colors.primary,
            "--color-secondary": self.colors.secondary,
            "--color-accent": self.colors.accent,
            "--color-text": self.colors.text,
            "--color-text-light": self.colors.text_light,
            "--color-bg": self.colors.background,
            "--color-bg-alt": self.colors.background_alt,
            "--font-heading": self.typography.heading_font,
            "--font-body": self.typography.body_font,
            "--spacing-unit": f"{self.spacing.unit}px",
        }

    def to_elementor_globals(self) -> dict[str, Any]:
        """Export as Elementor global settings."""
        return {
            "colors": [
                {"_id": "primary", "title": "Primary", "color": self.colors.primary},
                {"_id": "secondary", "title": "Secondary", "color": self.colors.secondary},
                {"_id": "accent", "title": "Accent", "color": self.colors.accent},
                {"_id": "text", "title": "Text", "color": self.colors.text},
            ],
            "typography": [
                {
                    "_id": "heading",
                    "title": "Heading",
                    "typography_font_family": self.typography.heading_font,
                    "typography_font_weight": str(self.typography.heading_weight),
                },
                {
                    "_id": "body",
                    "title": "Body",
                    "typography_font_family": self.typography.body_font,
                    "typography_font_weight": str(self.typography.body_weight),
                },
            ],
        }


# Default SkyyRose brand kit
SKYYROSE_BRAND_KIT = BrandKit()


# =============================================================================
# PageSpec
# =============================================================================


@dataclass
class PageSpec:
    """
    Page specification for template generation.

    Defines the structure and content requirements for a page type.
    """

    page_type: PageType
    title: str
    slug: str
    description: str = ""

    # Layout
    sections: list[str] = field(default_factory=list)
    layout: SectionLayout = SectionLayout.FULL_WIDTH

    # Content
    hero_enabled: bool = True
    hero_title: str = ""
    hero_subtitle: str = ""
    hero_cta: str = ""
    hero_image: str = ""

    # SEO
    meta_title: str = ""
    meta_description: str = ""

    # Template settings
    template: str = "elementor_canvas"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "page_type": self.page_type.value,
            "title": self.title,
            "slug": self.slug,
            "description": self.description,
            "sections": self.sections,
            "layout": self.layout.value,
            "hero": {
                "enabled": self.hero_enabled,
                "title": self.hero_title,
                "subtitle": self.hero_subtitle,
                "cta": self.hero_cta,
                "image": self.hero_image,
            },
            "seo": {
                "meta_title": self.meta_title,
                "meta_description": self.meta_description,
            },
        }


# =============================================================================
# Elementor Template
# =============================================================================


class ElementorTemplate(BaseModel):
    """Elementor template data structure."""

    version: str = "0.4"
    title: str = ""
    type: str = "page"
    content: list[dict[str, Any]] = Field(default_factory=list)
    page_settings: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def add_section(
        self,
        widgets: list[dict[str, Any]],
        layout: SectionLayout = SectionLayout.BOXED,
        settings: dict[str, Any] | None = None,
    ) -> str:
        """Add a section with widgets."""
        section_id = f"s{uuid.uuid4().hex[:7]}"

        section = {
            "id": section_id,
            "elType": "section",
            "settings": {
                "layout": layout.value,
                "content_width": (
                    {"size": 1200, "unit": "px"} if layout == SectionLayout.BOXED else {}
                ),
                **(settings or {}),
            },
            "elements": [
                {
                    "id": f"c{uuid.uuid4().hex[:7]}",
                    "elType": "column",
                    "settings": {"_column_size": 100},
                    "elements": widgets,
                }
            ],
        }

        self.content.append(section)
        return section_id

    def to_json(self) -> str:
        """Export as JSON string."""
        return json.dumps(self.model_dump(), indent=2)

    def to_file(self, filepath: str) -> None:
        """Export to file."""
        with open(filepath, "w") as f:
            f.write(self.to_json())


# =============================================================================
# ElementorConfig
# =============================================================================


@dataclass
class ElementorConfig:
    """Elementor generation configuration."""

    brand_kit: BrandKit = field(default_factory=lambda: SKYYROSE_BRAND_KIT)
    elementor_version: str = "3.32.0"
    shoptimizer_version: str = "2.9.0"
    output_dir: str = "./templates/elementor"


# =============================================================================
# Elementor Builder
# =============================================================================


class ElementorBuilder:
    """
    Elementor template generator.

    Usage:
        builder = ElementorBuilder()

        # Generate home page
        template = builder.generate_home_page(
            hero_title="SkyyRose",
            hero_subtitle="Where Love Meets Luxury",
            collections=["BLACK_ROSE", "LOVE_HURTS", "SIGNATURE"],
        )

        # Generate PDP template
        template = builder.generate_product_page()

        # Export
        template.to_file("home.json")
    """

    def __init__(self, config: ElementorConfig | None = None) -> None:
        self.config = config or ElementorConfig()
        self.brand = self.config.brand_kit

    # -------------------------------------------------------------------------
    # Widget Builders
    # -------------------------------------------------------------------------

    def _widget(
        self,
        widget_type: WidgetType,
        settings: dict[str, Any],
    ) -> dict[str, Any]:
        """Create a widget element."""
        return {
            "id": f"w{uuid.uuid4().hex[:7]}",
            "elType": "widget",
            "widgetType": widget_type.value,
            "settings": settings,
        }

    def heading(
        self,
        text: str,
        size: str = "xl",
        tag: str = "h2",
        align: str = "center",
    ) -> dict[str, Any]:
        """Create heading widget."""
        size_map = {"sm": "small", "md": "medium", "lg": "large", "xl": "xl", "xxl": "xxl"}
        return self._widget(
            WidgetType.HEADING,
            {
                "title": text,
                "size": size_map.get(size, "large"),
                "header_size": tag,
                "align": align,
                "title_color": self.brand.colors.text,
                "typography_font_family": self.brand.typography.heading_font,
                "typography_font_weight": str(self.brand.typography.heading_weight),
            },
        )

    def text(self, content: str, align: str = "center") -> dict[str, Any]:
        """Create text editor widget."""
        return self._widget(
            WidgetType.TEXT_EDITOR,
            {
                "editor": content,
                "align": align,
                "text_color": self.brand.colors.text_light,
                "typography_font_family": self.brand.typography.body_font,
            },
        )

    def button(
        self,
        text: str,
        link: str = "#",
        style: str = "primary",
        size: str = "md",
    ) -> dict[str, Any]:
        """Create button widget."""
        bg_color = self.brand.colors.primary if style == "primary" else "transparent"
        text_color = "#FFFFFF" if style == "primary" else self.brand.colors.primary

        return self._widget(
            WidgetType.BUTTON,
            {
                "text": text,
                "link": {"url": link, "is_external": False},
                "size": size,
                "button_background_color": bg_color,
                "button_text_color": text_color,
                "button_border_border": "solid" if style != "primary" else "",
                "button_border_width": (
                    {"top": "1", "right": "1", "bottom": "1", "left": "1"}
                    if style != "primary"
                    else {}
                ),
                "button_border_color": self.brand.colors.primary if style != "primary" else "",
                "typography_font_family": self.brand.typography.body_font,
                "typography_font_weight": "600",
                "typography_letter_spacing": {"size": 1, "unit": "px"},
            },
        )

    def image(
        self,
        url: str,
        alt: str = "",
        size: str = "full",
        align: str = "center",
    ) -> dict[str, Any]:
        """Create image widget."""
        return self._widget(
            WidgetType.IMAGE,
            {
                "image": {"url": url, "alt": alt},
                "image_size": size,
                "align": align,
            },
        )

    def spacer(self, size: int = 48) -> dict[str, Any]:
        """Create spacer widget."""
        return self._widget(
            WidgetType.SPACER,
            {"space": {"size": size, "unit": "px"}},
        )

    def products_grid(
        self,
        columns: int = 4,
        rows: int = 2,
        category: str = "",
    ) -> dict[str, Any]:
        """Create WooCommerce products grid."""
        return self._widget(
            WidgetType.PRODUCTS,
            {
                "columns": str(columns),
                "rows": str(rows),
                "query_post_type": "product",
                "query_product_cat_ids": [category] if category else [],
                "paginate": "yes",
            },
        )

    # -------------------------------------------------------------------------
    # Section Builders
    # -------------------------------------------------------------------------

    def hero_section(
        self,
        title: str,
        subtitle: str = "",
        cta_text: str = "",
        cta_link: str = "",
        background_image: str = "",
    ) -> list[dict[str, Any]]:
        """Build hero section widgets."""
        widgets = []

        widgets.append(self.spacer(80))
        widgets.append(self.heading(title, size="xxl", tag="h1"))

        if subtitle:
            widgets.append(self.text(f"<p>{subtitle}</p>"))

        if cta_text:
            widgets.append(self.spacer(24))
            widgets.append(self.button(cta_text, cta_link))

        widgets.append(self.spacer(80))

        return widgets

    def collection_section(
        self,
        title: str,
        subtitle: str = "",
        category_slug: str = "",
        columns: int = 4,
    ) -> list[dict[str, Any]]:
        """Build collection section widgets."""
        widgets = []

        widgets.append(self.spacer(60))
        widgets.append(self.heading(title, size="xl"))

        if subtitle:
            widgets.append(self.text(f"<p>{subtitle}</p>"))

        widgets.append(self.spacer(32))
        widgets.append(self.products_grid(columns=columns, category=category_slug))
        widgets.append(self.spacer(60))

        return widgets

    # -------------------------------------------------------------------------
    # Template Generators
    # -------------------------------------------------------------------------

    def generate_home_page(
        self,
        hero_title: str = "",
        hero_subtitle: str = "",
        hero_cta: str = "",
        hero_link: str = "/shop",
        hero_image: str = "",
        collections: list[dict[str, str]] | None = None,
    ) -> ElementorTemplate:
        """Generate home page template."""
        template = ElementorTemplate(
            title="Home",
            page_settings={
                "hide_title": "yes",
                "template": "elementor_canvas",
            },
        )

        # Hero section
        hero_widgets = self.hero_section(
            title=hero_title or self.brand.name,
            subtitle=hero_subtitle or self.brand.voice.tagline,
            cta_text=hero_cta or self.brand.voice.cta_primary,
            cta_link=hero_link,
            background_image=hero_image,
        )
        template.add_section(hero_widgets, layout=SectionLayout.FULL_WIDTH)

        # Collection sections
        if collections:
            for col in collections:
                col_widgets = self.collection_section(
                    title=col.get("title", "Collection"),
                    subtitle=col.get("subtitle", ""),
                    category_slug=col.get("slug", ""),
                )
                template.add_section(col_widgets)

        return template

    def generate_collection_page(
        self,
        title: str,
        description: str = "",
        category_slug: str = "",
    ) -> ElementorTemplate:
        """Generate collection/archive page template."""
        template = ElementorTemplate(
            title=title,
            page_settings={"template": "elementor_header_footer"},
        )

        # Header
        header_widgets = [
            self.spacer(48),
            self.heading(title, size="xl", tag="h1"),
        ]
        if description:
            header_widgets.append(self.text(f"<p>{description}</p>"))
        header_widgets.append(self.spacer(32))

        template.add_section(header_widgets)

        # Products
        products_widgets = [
            self.products_grid(columns=4, rows=4, category=category_slug),
            self.spacer(48),
        ]
        template.add_section(products_widgets)

        return template

    def generate_product_page(self) -> ElementorTemplate:
        """Generate single product page template."""
        template = ElementorTemplate(
            title="Single Product",
            type="single",
            page_settings={"template": "elementor_header_footer"},
        )

        # Product images (left column would be handled differently)
        product_widgets = [
            self._widget(WidgetType.PRODUCT_IMAGES, {}),
            self._widget(WidgetType.PRODUCT_TITLE, {}),
            self._widget(WidgetType.PRODUCT_PRICE, {}),
            self._widget(WidgetType.ADD_TO_CART, {}),
        ]

        template.add_section(product_widgets)

        return template


# =============================================================================
# Convenience Function
# =============================================================================


def generate_template(
    page_spec: PageSpec,
    brand_kit: BrandKit | None = None,
) -> ElementorTemplate:
    """
    Generate template from page specification.

    Args:
        page_spec: Page specification
        brand_kit: Brand design tokens

    Returns:
        ElementorTemplate ready for export
    """
    config = ElementorConfig(brand_kit=brand_kit or SKYYROSE_BRAND_KIT)
    builder = ElementorBuilder(config)

    if page_spec.page_type == PageType.HOME:
        return builder.generate_home_page(
            hero_title=page_spec.hero_title,
            hero_subtitle=page_spec.hero_subtitle,
            hero_cta=page_spec.hero_cta,
            hero_image=page_spec.hero_image,
        )
    elif page_spec.page_type == PageType.COLLECTION:
        return builder.generate_collection_page(
            title=page_spec.title,
            description=page_spec.description,
        )
    elif page_spec.page_type == PageType.PRODUCT:
        return builder.generate_product_page()
    else:
        # Default to basic page
        template = ElementorTemplate(title=page_spec.title)
        return template


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "ElementorBuilder",
    "ElementorConfig",
    "ElementorTemplate",
    "BrandKit",
    "BrandColors",
    "BrandTypography",
    "BrandSpacing",
    "BrandImagery",
    "BrandVoice",
    "PageSpec",
    "PageType",
    "WidgetType",
    "SectionLayout",
    "SKYYROSE_BRAND_KIT",
    "generate_template",
]
