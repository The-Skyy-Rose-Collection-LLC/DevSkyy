"""
Collection Page Manager
=======================

Design templates and metadata for the three SkyyRose collections.
Used by Python agents for consistency checks, recovery prompts, and
LLM context — not for rendering (that happens in PHP/WordPress).

Collections
-----------
- BLACK_ROSE  — Gothic luxury, Oakland/East Bay, dark elegance
- LOVE_HURTS  — Beauty-and-the-Beast aesthetic, passionate/emotional
- SIGNATURE   — SF/Golden Gate, rose gold runway, premium essentials
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class CollectionType(StrEnum):
    """The three SkyyRose product collections."""

    BLACK_ROSE = "black_rose"
    LOVE_HURTS = "love_hurts"
    SIGNATURE = "signature"


@dataclass
class CollectionTemplate:
    """Design specification for one collection."""

    name: str
    theme: str
    description: str
    colors: dict[str, str]
    html_file_path: str
    metadata: dict[str, Any] | None = field(default=None)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "theme": self.theme,
            "description": self.description,
            "colors": self.colors,
            "html_file_path": self.html_file_path,
            "metadata": self.metadata or {},
        }


# ---------------------------------------------------------------------------
# Authoritative template definitions
# ---------------------------------------------------------------------------

_TEMPLATES: dict[CollectionType, CollectionTemplate] = {
    CollectionType.BLACK_ROSE: CollectionTemplate(
        name="BLACK Rose Collection",
        theme="Gothic luxury — Oakland grit meets dark elegance",
        description=(
            "Where darkness blooms into luxury. "
            "Inspired by Oakland's East Bay streets and gothic romance. "
            "Every piece is a statement in dark, powerful self-expression."
        ),
        colors={
            "primary": "#0A0A0A",
            "secondary": "#B76E79",
            "accent": "#DC143C",
            "text": "#F5F5F5",
            "highlight": "#D4AF37",
        },
        html_file_path="wordpress-theme/skyyrose-flagship/template-collection-black-rose.php",
        metadata={
            "target_audience": "Oakland / Bay Area streetwear enthusiasts, gothic luxury",
            "tagline": "Luxury Grows from Concrete.",
            "mood": "dark, powerful, mysterious, luxurious",
            "inspiration": "Gothic romance, Bay Area night life, street art",
            "hero_scene": "Bay Bridge at night, street luxury",
            "products": [
                "br-001",
                "br-002",
                "br-003",
                "br-004",
                "br-005",
                "br-006",
                "br-007",
                "br-008",
                "br-009",
                "br-010",
                "br-011",
            ],
        },
    ),
    CollectionType.LOVE_HURTS: CollectionTemplate(
        name="Love Hurts Collection",
        theme="Oakland grit meets luxury passion — beauty with a broken heart",
        description=(
            "Feel the fire. Love Hurts channels raw emotion and Bay Area passion "
            "into pieces that wear your heart on your sleeve — literally."
        ),
        colors={
            "primary": "#1A0A0A",
            "secondary": "#DC143C",
            "accent": "#B76E79",
            "text": "#F5F5F5",
            "highlight": "#8B0000",
        },
        html_file_path="wordpress-theme/skyyrose-flagship/template-collection-love-hurts.php",
        metadata={
            "target_audience": "Oakland streetwear, passionate fashion lovers",
            "tagline": "Wear your heart outside.",
            "mood": "passionate, emotional, bold, raw",
            "inspiration": "Beauty and the Beast, enchanted rose, Oakland resilience",
            "hero_scene": "Enchanted rose dome, gothic cathedral atmosphere",
            "products": ["lh-002", "lh-003", "lh-004", "lh-006"],
        },
    ),
    CollectionType.SIGNATURE: CollectionTemplate(
        name="Signature Collection",
        theme="Rose gold runway — SF golden hour premium essentials",
        description=(
            "The crown jewel. Timeless essentials in rose gold, inspired by "
            "San Francisco's Golden Gate and the city's fashion-forward spirit."
        ),
        colors={
            "primary": "#1A1205",
            "secondary": "#D4AF37",
            "accent": "#B76E79",
            "text": "#F5F5F5",
            "highlight": "#C0C0C0",
        },
        html_file_path="wordpress-theme/skyyrose-flagship/template-collection-signature.php",
        metadata={
            "target_audience": "SF fashion, premium streetwear, elevated essentials",
            "tagline": "The Crown Jewel.",
            "mood": "elegant, golden, timeless, premium",
            "inspiration": "Golden Gate Bridge, SF fashion week, rose gold luxury",
            "hero_scene": "Golden Gate Bridge at golden hour, fog through cables",
            "products": [
                "sg-001",
                "sg-002",
                "sg-003",
                "sg-004",
                "sg-005",
                "sg-006",
                "sg-007",
                "sg-009",
                "sg-010",
                "sg-011",
                "sg-012",
                "sg-013",
                "sg-014",
            ],
        },
    ),
}


class CollectionDesignTemplates:
    """
    Static registry of SkyyRose collection design templates.

    All methods are class-level — no instantiation required.
    """

    @classmethod
    def get_template(cls, collection: CollectionType) -> CollectionTemplate:
        """Return the design template for a collection."""
        return _TEMPLATES[collection]

    @classmethod
    def get_all_templates(cls) -> dict[CollectionType, CollectionTemplate]:
        """Return all templates keyed by CollectionType."""
        return dict(_TEMPLATES)

    @classmethod
    def to_agent_reference(cls, collection: CollectionType) -> dict[str, Any]:
        """
        Return a serialisable dict suitable for injecting into an LLM prompt
        or returning as a recovery reference.
        """
        t = _TEMPLATES[collection]
        return {
            "collection": collection.value,
            "name": t.name,
            "theme": t.theme,
            "description": t.description,
            "colors": t.colors,
            "html_file_path": t.html_file_path,
            "metadata": t.metadata or {},
            "recovery_steps": [
                f"Restore primary color to {t.colors['primary']}",
                f"Restore secondary color to {t.colors['secondary']}",
                f"Restore accent color to {t.colors['accent']}",
                f"Reset theme to: {t.theme}",
                f"Reference HTML template: {t.html_file_path}",
            ],
        }


__all__ = ["CollectionType", "CollectionDesignTemplates", "CollectionTemplate"]
