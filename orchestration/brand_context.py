"""
SkyyRose Brand Context Layer
============================

Injects brand DNA into all LLM interactions for consistent voice.

Features:
- Brand knowledge base (colors, tone, values)
- System prompt injection
- Product catalog context
- Collection-specific styling

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

from llm import Message

logger = logging.getLogger(__name__)


# =============================================================================
# Brand Knowledge Base
# =============================================================================


class Collection(str, Enum):
    """SkyyRose collections."""

    BLACK_ROSE = "BLACK_ROSE"
    SIGNATURE = "SIGNATURE"
    MIDNIGHT_BLOOM = "MIDNIGHT_BLOOM"
    LOVE_HURTS = "LOVE_HURTS"


SKYYROSE_BRAND: dict[str, Any] = {
    "name": "The Skyy Rose Collection",
    "tagline": "Luxury Streetwear with Soul",
    "philosophy": "Where Love Meets Luxury",
    "location": "Oakland, California",

    "tone": {
        "primary": "Elegant, empowering, romantic, bold",
        "descriptors": [
            "sophisticated yet accessible",
            "poetic but not pretentious",
            "confident without arrogance",
            "romantic with edge",
        ],
        "avoid": [
            "generic fashion buzzwords",
            "overly casual language",
            "aggressive or harsh tones",
            "clichéd luxury language",
        ],
    },

    "colors": {
        "primary": {"name": "Black Rose", "hex": "#1A1A1A", "rgb": "26, 26, 26"},
        "accent": {"name": "Rose Gold", "hex": "#D4AF37", "rgb": "212, 175, 55"},
        "highlight": {"name": "Deep Rose", "hex": "#8B0000", "rgb": "139, 0, 0"},
        "ivory": {"name": "Ivory", "hex": "#F5F5F0", "rgb": "245, 245, 240"},
        "obsidian": {"name": "Obsidian", "hex": "#0D0D0D", "rgb": "13, 13, 13"},
    },

    "typography": {
        "heading": "Playfair Display",
        "body": "Inter",
        "accent": "Cormorant Garamond",
    },

    "target_audience": {
        "age_range": "18-35",
        "description": "Fashion-forward individuals who value self-expression",
        "interests": ["streetwear", "luxury fashion", "self-expression", "art", "music"],
        "values": ["authenticity", "quality", "individuality", "emotional connection"],
    },

    "product_types": ["hoodies", "tees", "bombers", "track pants", "accessories", "caps", "beanies"],

    "quality_descriptors": [
        "premium heavyweight cotton",
        "meticulous construction",
        "attention to detail",
        "limited edition exclusivity",
        "elevated street poetry",
    ],
}


COLLECTION_CONTEXT: dict[Collection, dict[str, Any]] = {
    Collection.BLACK_ROSE: {
        "name": "Black Rose",
        "tagline": "Limited Edition Exclusivity",
        "mood": "mysterious, sophisticated, rare, coveted",
        "colors": "deep black, subtle rose gold accents, matte finish",
        "style": "dark elegance, limited edition, exclusive drops",
        "description": "The pinnacle of SkyyRose luxury. Each Black Rose piece is a limited release, crafted for those who understand that true style is rare.",
    },
    Collection.SIGNATURE: {
        "name": "Signature",
        "tagline": "Timeless Essentials",
        "mood": "classic, versatile, foundational, elevated basics",
        "colors": "clean neutrals, rose gold details, ivory accents",
        "style": "essential wardrobe, everyday luxury, refined simplicity",
        "description": "The foundation of SkyyRose style. Signature pieces are the building blocks of a discerning wardrobe—timeless, versatile, unmistakably premium.",
    },
    Collection.MIDNIGHT_BLOOM: {
        "name": "Midnight Bloom",
        "tagline": "Beauty in Darkness",
        "mood": "romantic, mysterious, nocturnal, blooming",
        "colors": "deep purples, midnight blue, silver accents",
        "style": "romantic darkness, floral motifs, night-inspired",
        "description": "For those who find beauty in the shadows. Midnight Bloom celebrates the romance of darkness, where flowers bloom under moonlight.",
    },
    Collection.LOVE_HURTS: {
        "name": "Love Hurts",
        "tagline": "Feel Everything",
        "mood": "passionate, vulnerable, powerful, emotional",
        "colors": "deep reds, black, heart motifs, distressed textures",
        "style": "emotional expression, storytelling through design",
        "description": "Raw emotion worn proudly. Love Hurts transforms the beautiful pain of human experience into wearable art.",
    },
}


# System prompt template
BRAND_SYSTEM_PROMPT = """You are an AI assistant for The Skyy Rose Collection, a luxury streetwear brand based in Oakland, California.

## Brand Voice
{tone_primary}

When writing for SkyyRose:
{tone_descriptors}

Avoid:
{tone_avoid}

## Brand Colors
- Primary: {color_primary} ({color_primary_hex})
- Accent: {color_accent} ({color_accent_hex})
- Highlight: {color_highlight} ({color_highlight_hex})

## Target Audience
{target_audience}

## Quality Language
Use these descriptors: {quality_descriptors}

{collection_context}

Maintain consistent brand voice across all content. Be {tone_primary}."""


# =============================================================================
# Brand Context Injector
# =============================================================================


@dataclass
class BrandContextInjector:
    """
    Injects SkyyRose brand context into LLM prompts.

    Usage:
        injector = BrandContextInjector()

        # Inject brand context into messages
        messages = injector.inject([
            Message.user("Write a product description for the Black Rose Hoodie")
        ])

        # With specific collection
        messages = injector.inject(
            [Message.user("Write marketing copy")],
            collection=Collection.LOVE_HURTS
        )
    """

    include_colors: bool = True
    include_audience: bool = True
    include_quality: bool = True
    compact_mode: bool = False

    def get_system_prompt(self, collection: Collection | None = None) -> str:
        """
        Generate brand-aware system prompt.

        Args:
            collection: Optional specific collection context

        Returns:
            Formatted system prompt with brand DNA
        """
        brand = SKYYROSE_BRAND

        # Format tone descriptors
        tone_descriptors = "\n".join(f"- {d}" for d in brand["tone"]["descriptors"])
        tone_avoid = "\n".join(f"- {a}" for a in brand["tone"]["avoid"])

        # Collection context
        collection_context = ""
        if collection:
            coll = COLLECTION_CONTEXT[collection]
            collection_context = f"""
## Current Collection: {coll['name']}
Tagline: {coll['tagline']}
Mood: {coll['mood']}
Colors: {coll['colors']}
Style: {coll['style']}
Description: {coll['description']}"""

        # Format quality descriptors
        quality = ", ".join(brand["quality_descriptors"][:4])

        # Target audience
        audience = brand["target_audience"]
        audience_str = f"{audience['description']} (ages {audience['age_range']})"

        prompt = BRAND_SYSTEM_PROMPT.format(
            tone_primary=brand["tone"]["primary"],
            tone_descriptors=tone_descriptors,
            tone_avoid=tone_avoid,
            color_primary=brand["colors"]["primary"]["name"],
            color_primary_hex=brand["colors"]["primary"]["hex"],
            color_accent=brand["colors"]["accent"]["name"],
            color_accent_hex=brand["colors"]["accent"]["hex"],
            color_highlight=brand["colors"]["highlight"]["name"],
            color_highlight_hex=brand["colors"]["highlight"]["hex"],
            target_audience=audience_str,
            quality_descriptors=quality,
            collection_context=collection_context,
        )

        return prompt.strip()

    def get_compact_prompt(self, collection: Collection | None = None) -> str:
        """Get a compact version of the brand prompt."""
        brand = SKYYROSE_BRAND

        prompt = f"""SkyyRose Brand Voice: {brand['tone']['primary']}
Colors: Black Rose (#1A1A1A), Rose Gold (#D4AF37), Deep Rose (#8B0000)
Style: Luxury streetwear, Oakland CA. {brand['tagline']}."""

        if collection:
            coll = COLLECTION_CONTEXT[collection]
            prompt += f"\nCollection: {coll['name']} - {coll['tagline']}. {coll['mood']}."

        return prompt

    def inject(
        self,
        messages: list[Message],
        collection: Collection | None = None,
        prepend_system: bool = True,
    ) -> list[Message]:
        """
        Inject brand context into message list.

        Args:
            messages: Original messages
            collection: Optional collection context
            prepend_system: Whether to add system message at start

        Returns:
            Messages with brand context injected
        """
        if not prepend_system:
            return messages

        # Get appropriate prompt
        if self.compact_mode:
            system_content = self.get_compact_prompt(collection)
        else:
            system_content = self.get_system_prompt(collection)

        # Check if first message is already a system message
        if messages and messages[0].role == "system":
            # Prepend brand context to existing system message
            enhanced = Message.system(
                f"{system_content}\n\n{messages[0].content}"
            )
            return [enhanced] + list(messages[1:])

        # Add new system message
        return [Message.system(system_content)] + list(messages)

    def get_product_context(
        self,
        product_name: str,
        product_type: str,
        collection: Collection | None = None,
        price: float | None = None,
    ) -> str:
        """
        Generate product-specific context for LLM.

        Args:
            product_name: Name of the product
            product_type: Type (hoodie, tee, bomber, etc.)
            collection: Which collection it belongs to
            price: Optional price point

        Returns:
            Product context string
        """
        context = f"Product: {product_name}\nType: {product_type}"

        if collection:
            coll = COLLECTION_CONTEXT[collection]
            context += f"\nCollection: {coll['name']} ({coll['tagline']})"
            context += f"\nMood: {coll['mood']}"

        if price:
            context += f"\nPrice Point: ${price:.2f}"

        # Add relevant quality descriptors
        if product_type.lower() in ["hoodie", "sweatshirt"]:
            context += "\nQuality: Premium heavyweight cotton, meticulous construction"
        elif product_type.lower() in ["bomber", "jacket"]:
            context += "\nQuality: Premium materials, satin lining, quality hardware"
        elif product_type.lower() in ["tee", "t-shirt"]:
            context += "\nQuality: Heavyweight cotton, relaxed fit, quality construction"

        return context


# =============================================================================
# Convenience Functions
# =============================================================================


def get_brand_system_prompt(collection: Collection | None = None) -> str:
    """Get SkyyRose brand system prompt."""
    return BrandContextInjector().get_system_prompt(collection)


def inject_brand_context(
    messages: list[Message],
    collection: Collection | None = None,
) -> list[Message]:
    """Inject brand context into messages."""
    return BrandContextInjector().inject(messages, collection)


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "BrandContextInjector",
    "Collection",
    "SKYYROSE_BRAND",
    "COLLECTION_CONTEXT",
    "get_brand_system_prompt",
    "inject_brand_context",
]

