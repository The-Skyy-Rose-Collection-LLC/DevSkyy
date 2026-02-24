"""WordPress theme generation tool."""

from typing import Literal

from pydantic import Field

from mcp_tools.api_client import _format_response, _make_api_request
from mcp_tools.security import secure_tool
from mcp_tools.server import mcp
from mcp_tools.types import BaseAgentInput


class WordPressThemeInput(BaseAgentInput):
    """Input for WordPress theme generation."""

    brand_name: str = Field(
        ...,
        description="Brand or business name (e.g., 'FashionHub', 'TechStore')",
        min_length=1,
        max_length=100,
    )
    industry: str = Field(
        ...,
        description="Industry or niche (e.g., 'fashion', 'electronics', 'food')",
        min_length=1,
        max_length=100,
    )
    theme_type: Literal["elementor", "divi", "gutenberg"] = Field(
        default="elementor",
        description="WordPress theme builder to use: elementor, divi, or gutenberg",
    )
    color_palette: list[str] | None = Field(
        default=None,
        description="Hex color codes for brand colors (e.g., ['#FF5733', '#3498DB'])",
        max_length=10,
    )
    pages: list[str] | None = Field(
        default=["home", "shop", "about", "contact"],
        description="Pages to include in theme",
        max_length=20,
    )


@mcp.tool(
    name="devskyy_generate_wordpress_theme",
    annotations={
        "title": "DevSkyy WordPress Theme Builder",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
        "defer_loading": True,
        "input_examples": [
            {
                "brand_name": "FashionHub",
                "industry": "fashion",
                "theme_type": "elementor",
                "color_palette": ["#FF5733", "#3498DB", "#2ECC71"],
                "pages": ["home", "shop", "about", "contact"],
            },
            {
                "brand_name": "TechStore",
                "industry": "electronics",
                "theme_type": "divi",
                "pages": ["home", "products", "support"],
            },
            {
                "brand_name": "SkyyRose",
                "industry": "luxury-fashion",
                "theme_type": "elementor",
                "color_palette": ["#B76E79", "#1A1A1A", "#F5F5F5"],
                "pages": ["home", "shop", "lookbook", "about", "contact"],
            },
        ],
    },
)
@secure_tool("generate_wordpress_theme")
async def generate_wordpress_theme(params: WordPressThemeInput) -> str:
    """Generate custom WordPress themes automatically from brand guidelines.

    **INDUSTRY FIRST**: Automated Elementor/Divi/Gutenberg theme generation.
    The Theme Builder Agent creates fully functional, responsive, SEO-optimized
    WordPress themes tailored to your brand:

    - Automatic page layouts (Home, Shop, About, Contact, etc.)
    - Brand-consistent color schemes and typography
    - Mobile-responsive design
    - E-commerce integration (WooCommerce ready)
    - SEO optimization built-in
    - Accessibility (WCAG 2.1 compliant)
    - Export in compatible formats (.zip)

    Supports: Elementor, Divi, Gutenberg (WordPress 5.0+)

    Args:
        params (WordPressThemeInput): Theme configuration containing:
            - brand_name: Business or brand name
            - industry: Business industry/niche
            - theme_type: elementor, divi, or gutenberg
            - color_palette: Brand colors (hex codes)
            - pages: Pages to include
            - response_format: Output format (markdown/json)

    Returns:
        str: Theme generation results with download URL and setup instructions

    Example:
        >>> generate_wordpress_theme({
        ...     "brand_name": "FashionHub",
        ...     "industry": "fashion",
        ...     "theme_type": "elementor",
        ...     "color_palette": ["#FF5733", "#3498DB", "#2ECC71"]
        ... })
    """
    data = await _make_api_request(
        "theme-builder/generate",
        method="POST",
        data={
            "brand_name": params.brand_name,
            "industry": params.industry,
            "theme_type": params.theme_type,
            "color_palette": params.color_palette or ["#2C3E50", "#3498DB", "#E74C3C"],
            "pages": params.pages,
        },
    )

    return _format_response(data, params.response_format, "WordPress Theme Generated")
