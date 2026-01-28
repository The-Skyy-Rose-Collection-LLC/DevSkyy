"""
Collection Page Manager for SkyyRose WordPress integration.

Provides design templates and collection type definitions for managing
SkyyRose collection pages on the WordPress site.
"""

from __future__ import annotations

from enum import Enum
from typing import Any


class CollectionType(Enum):
    """SkyyRose collection types."""

    SIGNATURE = "signature"
    BLACK_ROSE = "black_rose"
    LOVE_HURTS = "love_hurts"
    MIDNIGHT_BLOOM = "midnight_bloom"


# Default design templates per collection
_COLLECTION_TEMPLATES: dict[CollectionType, dict[str, Any]] = {
    CollectionType.SIGNATURE: {
        "name": "Signature Collection",
        "description": "Timeless elegance with golden accents",
        "primary_color": "#D4AF37",
        "secondary_color": "#1A1A1A",
        "hero_image": "signature-hero.jpg",
        "layout": "editorial",
        "tagline": "Defining luxury since the beginning",
        "experience_url": "/experience/signature/",
        "shop_url": "/experience/signature/shop/",
    },
    CollectionType.BLACK_ROSE: {
        "name": "Black Rose Collection",
        "description": "Gothic romance meets modern fashion",
        "primary_color": "#1A1A1A",
        "secondary_color": "#8B0000",
        "hero_image": "black-rose-hero.jpg",
        "layout": "dramatic",
        "tagline": "Embrace the darkness within",
        "experience_url": "/experience/black-rose/",
        "shop_url": "/experience/black-rose/shop/",
    },
    CollectionType.LOVE_HURTS: {
        "name": "Love Hurts Collection",
        "description": "Bold rose gold passion statements",
        "primary_color": "#B76E79",
        "secondary_color": "#D4AF37",
        "hero_image": "love-hurts-hero.jpg",
        "layout": "bold",
        "tagline": "Love is the most powerful accessory",
        "experience_url": "/experience/love-hurts/",
        "shop_url": "/experience/love-hurts/shop/",
    },
    CollectionType.MIDNIGHT_BLOOM: {
        "name": "Midnight Bloom Collection",
        "description": "Midnight florals with ethereal elegance",
        "primary_color": "#2C1810",
        "secondary_color": "#B76E79",
        "hero_image": "midnight-bloom-hero.jpg",
        "layout": "ethereal",
        "tagline": "Where midnight meets bloom",
        "experience_url": "/experience/midnight-bloom/",
        "shop_url": "/experience/midnight-bloom/shop/",
    },
}


class CollectionDesignTemplates:
    """Design template management for SkyyRose collections."""

    @staticmethod
    def get_template(collection_type: CollectionType) -> dict[str, Any]:
        """Get design template for a specific collection."""
        template = _COLLECTION_TEMPLATES.get(collection_type)
        if template is None:
            raise ValueError(f"Unknown collection type: {collection_type}")
        return template

    @staticmethod
    def get_all_templates() -> dict[str, dict[str, Any]]:
        """Get all available collection templates."""
        return {
            ct.value: template
            for ct, template in _COLLECTION_TEMPLATES.items()
        }

    @staticmethod
    def to_agent_reference(collection_type: CollectionType) -> dict[str, Any]:
        """Convert a template to an agent-friendly reference format."""
        template = CollectionDesignTemplates.get_template(collection_type)
        return {
            "collection": collection_type.value,
            "display_name": template["name"],
            "description": template["description"],
            "colors": {
                "primary": template["primary_color"],
                "secondary": template["secondary_color"],
            },
            "layout": template["layout"],
            "tagline": template["tagline"],
            "urls": {
                "experience": template.get("experience_url", ""),
                "shop": template.get("shop_url", ""),
            },
        }
