"""
SkyyRose WordPress Knowledge Base

This module provides WordPress/Elementor development resources for the SkyyRose brand.
Assets are loaded and served by the RAG MCP for semantic search and ML continuous learning.

Contents:
- WORDPRESS_GUIDE.md: Complete theme development guide
- manifest.json: Product catalog, brand colors, typography, collections
- css/skyyrose-custom.css: Brand-consistent CSS styles

Usage:
    from mcp_servers.wordpress import (
        load_manifest,
        get_brand_colors,
        get_collections,
        get_products_by_collection,
        get_css_variables,
    )
"""

import json
from pathlib import Path
import re
from typing import Any


# Module directory
WORDPRESS_DIR = Path(__file__).parent


def load_manifest() -> dict[str, Any]:
    """
    Load the SkyyRose theme manifest with product catalog and brand assets.

    Returns:
        Complete manifest dictionary with brand, collections, products, colors, etc.
    """
    manifest_path = WORDPRESS_DIR / "manifest.json"
    if manifest_path.exists():
        with open(manifest_path, encoding="utf-8") as f:
            return json.load(f)
    return {}


def load_guide() -> str:
    """
    Load the WordPress development guide markdown.

    Returns:
        Full content of WORDPRESS_GUIDE.md
    """
    guide_path = WORDPRESS_DIR / "WORDPRESS_GUIDE.md"
    if guide_path.exists():
        return guide_path.read_text(encoding="utf-8")
    return ""


def load_css() -> str:
    """
    Load the SkyyRose custom CSS.

    Returns:
        Full content of skyyrose-custom.css
    """
    css_path = WORDPRESS_DIR / "css" / "skyyrose-custom.css"
    if css_path.exists():
        return css_path.read_text(encoding="utf-8")
    return ""


def get_brand_colors() -> dict[str, str]:
    """
    Get SkyyRose brand color palette.

    Returns:
        Dictionary of color names to hex values.
        Example: {"obsidian": "#0D0D0D", "ivory": "#F5F5F0", ...}
    """
    manifest = load_manifest()
    return manifest.get("colors", {})


def get_typography() -> dict[str, dict[str, Any]]:
    """
    Get SkyyRose typography settings.

    Returns:
        Dictionary with headline and body font configurations.
    """
    manifest = load_manifest()
    return manifest.get("typography", {})


def get_collections() -> dict[str, dict[str, Any]]:
    """
    Get all SkyyRose collections.

    Returns:
        Dictionary of collection slugs to collection data.
        Example: {"love-hurts": {"name": "Love Hurts", "anchor_products": [...]}}
    """
    manifest = load_manifest()
    return manifest.get("collections", {})


def get_products_by_collection(collection_slug: str) -> list[dict[str, Any]]:
    """
    Get all products in a specific collection.

    Args:
        collection_slug: Collection key (e.g., "love-hurts", "black-rose", "signature")

    Returns:
        List of product dictionaries with name, slug, sku_prefix, variants, price.
    """
    manifest = load_manifest()
    products = manifest.get("products", {})
    return products.get(collection_slug, [])


def get_all_products() -> list[dict[str, Any]]:
    """
    Get all products across all collections.

    Returns:
        List of all product dictionaries with collection attached.
    """
    manifest = load_manifest()
    products = manifest.get("products", {})
    all_products = []
    for collection_slug, collection_products in products.items():
        for product in collection_products:
            product_copy = product.copy()
            product_copy["collection"] = collection_slug
            all_products.append(product_copy)
    return all_products


def get_variants() -> dict[str, list[str]]:
    """
    Get available product variants.

    Returns:
        Dictionary with color and size variants.
        Example: {"color": ["Onyx", "Ivory", ...], "size": ["Small", "Medium", ...]}
    """
    manifest = load_manifest()
    return manifest.get("variants", {})


def get_elementor_config() -> dict[str, Any]:
    """
    Get Elementor Pro configuration settings.

    Returns:
        Dictionary with global colors, fonts, and container width.
    """
    manifest = load_manifest()
    return manifest.get("elementor", {})


def get_woocommerce_config() -> dict[str, Any]:
    """
    Get WooCommerce configuration settings.

    Returns:
        Dictionary with image sizes, categories, and attributes.
    """
    manifest = load_manifest()
    return manifest.get("woocommerce", {})


def get_image_specs() -> dict[str, dict[str, Any]]:
    """
    Get image specification requirements.

    Returns:
        Dictionary with product, hero, and collection banner image specs.
    """
    manifest = load_manifest()
    return manifest.get("images", {})


def get_css_variables() -> dict[str, str]:
    """
    Extract CSS custom properties (variables) from the stylesheet.

    Returns:
        Dictionary of CSS variable names to values.
        Example: {"--sr-obsidian": "#0D0D0D", "--sr-ivory": "#F5F5F0", ...}
    """
    css_content = load_css()
    variables = {}

    # Parse :root block for CSS variables
    root_match = re.search(r":root\s*\{([^}]+)\}", css_content, re.DOTALL)
    if root_match:
        root_content = root_match.group(1)
        var_pattern = re.compile(r"(--sr-[\w-]+)\s*:\s*([^;]+);")
        for match in var_pattern.finditer(root_content):
            variables[match.group(1)] = match.group(2).strip()

    return variables


def get_css_classes() -> list[str]:
    """
    Extract all SkyyRose CSS class names.

    Returns:
        List of CSS class names (prefixed with .sr-).
    """
    css_content = load_css()
    classes = set()

    # Find all .sr- prefixed classes
    class_pattern = re.compile(r"\.(sr-[\w-]+)")
    for match in class_pattern.finditer(css_content):
        classes.add(match.group(1))

    return sorted(classes)


def generate_sku(product_slug: str, color: str, size: str | None = None) -> str:
    """
    Generate a SKU based on SkyyRose naming convention.

    Args:
        product_slug: Product SKU prefix (e.g., "HARP", "HRTY")
        color: Color variant abbreviation (e.g., "ONX", "IVY", "EMB")
        size: Optional size (e.g., "S", "M", "L", "XL", "XXL", "XXXL")

    Returns:
        Formatted SKU string (e.g., "HARP-ONX-M")
    """
    color_map = {
        "Onyx": "ONX",
        "Ivory": "IVY",
        "Ember": "EMB",
        "Oak": "OAK",
        "Rosewood": "RSW",
        "Heather": "HTH",
        "Slate": "SLT",
        "Black": "BLK",
        "White": "WHT",
        "Peach": "PCH",
        "Pink": "PNK",
        "Lavender/Mint": "LVM",
    }
    size_map = {
        "Small": "S",
        "Medium": "M",
        "Large": "L",
        "X-Large": "XL",
        "XX-Large": "XXL",
        "XXX-Large": "XXXL",
    }

    color_code = color_map.get(color, color[:3].upper())
    parts = [product_slug, color_code]

    if size:
        size_code = size_map.get(size, size[0].upper())
        parts.append(size_code)

    return "-".join(parts)


# Brand constants for quick access
BRAND_NAME = "SkyyRose"
BRAND_DOMAIN = "skyyrose.co"
BRAND_TAGLINE = "Where Love Meets Luxury"
BRAND_LOCATION = "Oakland, California"

__all__ = [
    "BRAND_DOMAIN",
    "BRAND_LOCATION",
    "BRAND_NAME",
    "BRAND_TAGLINE",
    "WORDPRESS_DIR",
    "generate_sku",
    "get_all_products",
    "get_brand_colors",
    "get_collections",
    "get_css_classes",
    "get_css_variables",
    "get_elementor_config",
    "get_image_specs",
    "get_products_by_collection",
    "get_typography",
    "get_variants",
    "get_woocommerce_config",
    "load_css",
    "load_guide",
    "load_manifest",
]
