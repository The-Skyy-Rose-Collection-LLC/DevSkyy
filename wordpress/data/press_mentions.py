"""
SkyyRose Press Mentions and Media Coverage

Centralized data source for press timeline, media coverage, and recognition.
Used by:
- AboutPageBuilder (wordpress/page_builders/about_builder.py)
- PressTimeline component (frontend/components/PressTimeline.tsx)
- WordPress REST API endpoints

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class PressMention(BaseModel):
    """Structured press mention with validation.

    Attributes:
        date: Publication date (ISO 8601 format)
        publication: Publication name (e.g., "Maxim Magazine")
        title: Article title
        excerpt: Short description of article (optional)
        link: URL to full article
        logo_url: Path to publication logo (relative or absolute)
        featured: Whether to highlight in featured press section
        impact_score: Relative importance (1-10 scale)
    """

    date: str = Field(
        ...,
        description="Publication date in ISO 8601 format (YYYY-MM-DD)",
        pattern=r"^\d{4}-\d{2}-\d{2}$",
    )
    publication: str = Field(..., min_length=1, max_length=100)
    title: str = Field(..., min_length=1, max_length=300)
    excerpt: str = Field(default="", max_length=500)
    link: str = Field(..., pattern=r"^https?://")
    logo_url: str = Field(...)
    featured: bool = Field(default=False)
    impact_score: int = Field(default=5, ge=1, le=10)

    def to_dict(self) -> dict[str, Any]:
        """Export to dictionary for WordPress/frontend use."""
        return self.model_dump(mode="json")

    @property
    def month_year(self) -> str:
        """Format date as Month Year (e.g., 'June 2024')."""
        dt = datetime.strptime(self.date, "%Y-%m-%d")
        return dt.strftime("%B %Y")


# ============================================================================
# FEATURED PRESS (Top tier publications)
# ============================================================================

FEATURED_PRESS: list[PressMention] = [
    PressMention(
        date="2024-06-15",
        publication="Maxim Magazine",
        title="Oakland's SkyyRose Redefines Luxury Streetwear",
        excerpt="A deep dive into how SkyyRose is merging street culture with premium craftsmanship.",
        link="https://maxim.com/style/fashion/skyyrose-luxury-streetwear",
        logo_url="/wp-content/uploads/press/logos/maxim-logo.png",
        featured=True,
        impact_score=10,
    ),
    PressMention(
        date="2024-04-12",
        publication="CEO Weekly",
        title="Women in Fashion: The SkyyRose Success Story",
        excerpt="How SkyyRose founder built a global luxury brand from Oakland roots.",
        link="https://ceoweekly.com/fashion/skyyrose-founder",
        logo_url="/wp-content/uploads/press/logos/ceo-weekly-logo.png",
        featured=True,
        impact_score=9,
    ),
    PressMention(
        date="2024-02-08",
        publication="San Francisco Post",
        title="Emerging Luxury Brands You Need to Know About in 2024",
        excerpt="SkyyRose joins an elite list of innovative Bay Area brands reshaping fashion.",
        link="https://sfpost.com/business/emerging-luxury-brands-2024",
        logo_url="/wp-content/uploads/press/logos/sf-post-logo.png",
        featured=True,
        impact_score=8,
    ),
]

# ============================================================================
# GENERAL PRESS (Ongoing coverage)
# ============================================================================

GENERAL_PRESS: list[PressMention] = [
    PressMention(
        date="2024-12-10",
        publication="Vogue Business",
        title="SkyyRose: The New Face of Sustainable Luxury",
        excerpt="How ethical sourcing became a competitive advantage.",
        link="https://voguebusiness.com/articles/skyyrose-sustainable-luxury",
        logo_url="/wp-content/uploads/press/logos/vogue-logo.png",
        featured=False,
        impact_score=9,
    ),
    PressMention(
        date="2024-11-05",
        publication="Hypebeast",
        title="This Oakland Streetwear Brand Is Winning Fashion Critics",
        excerpt="Limited drops and 3D virtual try-ons set SkyyRose apart.",
        link="https://hypebeast.com/2024/11/skyyrose-streetwear",
        logo_url="/wp-content/uploads/press/logos/hypebeast-logo.png",
        featured=False,
        impact_score=8,
    ),
    PressMention(
        date="2024-10-22",
        publication="TechCrunch",
        title="How SkyyRose Is Using AR and 3D to Revolutionize E-Commerce",
        excerpt="Virtual try-ons and immersive experiences drive conversion rates.",
        link="https://techcrunch.com/2024/10/skyyrose-ar-ecommerce",
        logo_url="/wp-content/uploads/press/logos/techcrunch-logo.png",
        featured=False,
        impact_score=8,
    ),
    PressMention(
        date="2024-09-18",
        publication="The Guardian - Fashion",
        title="From Oakland Streets to Global Runways: SkyyRose's Rise",
        excerpt="An in-depth look at heritage, identity, and craftsmanship.",
        link="https://theguardian.com/fashion/2024/sep/skyyrose",
        logo_url="/wp-content/uploads/press/logos/guardian-logo.png",
        featured=False,
        impact_score=10,
    ),
    PressMention(
        date="2024-08-30",
        publication="FastCompany",
        title="SkyyRose Proves That Fashion Brands Need Purpose",
        excerpt="How intentionality in design attracts conscious consumers.",
        link="https://fastcompany.com/90954321/skyyrose",
        logo_url="/wp-content/uploads/press/logos/fastcompany-logo.png",
        featured=False,
        impact_score=7,
    ),
    PressMention(
        date="2024-07-14",
        publication="Forbes - 30 Under 30",
        title="Meet the Founder Reimagining Luxury Fashion",
        excerpt="SkyyRose founder named to Forbes 30 Under 30 in Fashion.",
        link="https://forbes.com/30under30/2024/fashion/skyyrose",
        logo_url="/wp-content/uploads/press/logos/forbes-logo.png",
        featured=True,
        impact_score=10,
    ),
    PressMention(
        date="2024-05-28",
        publication="Refinery29",
        title="The Collections That Have Everyone Talking",
        excerpt="Why SkyyRose's LOVE HURTS collection went viral.",
        link="https://refinery29.com/en-us/skyyrose-collection",
        logo_url="/wp-content/uploads/press/logos/refinery29-logo.png",
        featured=False,
        impact_score=7,
    ),
    PressMention(
        date="2024-03-12",
        publication="WWD (Women's Wear Daily)",
        title="The New Luxury Lexicon: How SkyyRose Is Speaking to Gen Z",
        excerpt="Bold designs and authentic storytelling resonate with younger audiences.",
        link="https://wwd.com/fashion-news/fashion-scoops/skyyrose-gen-z",
        logo_url="/wp-content/uploads/press/logos/wwd-logo.png",
        featured=False,
        impact_score=8,
    ),
]

# ============================================================================
# ONLINE MENTIONS (Blog features, reviews)
# ============================================================================

ONLINE_MENTIONS: list[PressMention] = [
    PressMention(
        date="2024-12-05",
        publication="StyleBakery (Fashion Blog)",
        title="Best New Luxury Streetwear Brands of 2024",
        excerpt="SkyyRose tops our list for innovation and storytelling.",
        link="https://stylebakery.com/best-luxury-streetwear-2024",
        logo_url="/wp-content/uploads/press/logos/stylebakery-logo.png",
        featured=False,
        impact_score=6,
    ),
    PressMention(
        date="2024-11-20",
        publication="The Fashion Law",
        title="Protecting Brand Identity: SkyyRose Case Study",
        excerpt="How ethical practices and IP protection go hand in hand.",
        link="https://thefashionlaw.com/skyyrose-brand-protection",
        logo_url="/wp-content/uploads/press/logos/tflaw-logo.png",
        featured=False,
        impact_score=6,
    ),
    PressMention(
        date="2024-10-09",
        publication="Medium - Fashion & Technology",
        title="The Future of Luxury: AR, 3D, and Human Connection",
        excerpt="How SkyyRose uses immersive tech responsibly.",
        link="https://medium.com/@fashiontech/skyyrose-ar-3d",
        logo_url="/wp-content/uploads/press/logos/medium-logo.png",
        featured=False,
        impact_score=5,
    ),
    PressMention(
        date="2024-09-01",
        publication="Entrepreneur Magazine",
        title="From Idea to Impact: The SkyyRose Journey",
        excerpt="Lessons in building a brand with purpose.",
        link="https://entrepreneur.com/article/skyyrose-journey",
        logo_url="/wp-content/uploads/press/logos/entrepreneur-logo.png",
        featured=False,
        impact_score=7,
    ),
]

# ============================================================================
# EXPORTS FOR USE IN TEMPLATES AND APIS
# ============================================================================


def get_all_press() -> list[PressMention]:
    """Get all press mentions sorted by date (newest first).

    Returns:
        Sorted list of all press mentions
    """
    all_press = FEATURED_PRESS + GENERAL_PRESS + ONLINE_MENTIONS
    return sorted(all_press, key=lambda x: x.date, reverse=True)


def get_featured_press(limit: int = 3) -> list[PressMention]:
    """Get featured press mentions (highlighted in about page).

    Args:
        limit: Maximum number of press mentions to return

    Returns:
        List of featured press mentions, sorted by impact score
    """
    featured = [m for m in get_all_press() if m.featured]
    return sorted(featured, key=lambda x: (-x.impact_score, x.date), reverse=True)[:limit]


def get_press_by_publication(publication: str) -> list[PressMention]:
    """Get all mentions from a specific publication.

    Args:
        publication: Publication name to filter by

    Returns:
        List of mentions from specified publication
    """
    return [m for m in get_all_press() if publication.lower() in m.publication.lower()]


def get_press_by_date_range(start_date: str, end_date: str) -> list[PressMention]:
    """Get press mentions within a date range.

    Args:
        start_date: Start date in ISO 8601 format (YYYY-MM-DD)
        end_date: End date in ISO 8601 format (YYYY-MM-DD)

    Returns:
        List of mentions within date range
    """
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    return [m for m in get_all_press() if start <= datetime.strptime(m.date, "%Y-%m-%d") <= end]


def get_top_press(limit: int = 5) -> list[PressMention]:
    """Get top press mentions by impact score.

    Args:
        limit: Maximum number to return

    Returns:
        List of highest-impact press mentions
    """
    return sorted(get_all_press(), key=lambda x: -x.impact_score)[:limit]


# ============================================================================
# PRESS STATISTICS
# ============================================================================


def get_press_stats() -> dict[str, Any]:
    """Get aggregate press statistics.

    Returns:
        Dictionary with press coverage statistics
    """
    all_press = get_all_press()
    featured = [m for m in all_press if m.featured]

    return {
        "total_mentions": len(all_press),
        "featured_count": len(featured),
        "average_impact_score": (
            sum(m.impact_score for m in all_press) / len(all_press) if all_press else 0
        ),
        "highest_impact_publication": (
            max(all_press, key=lambda x: x.impact_score).publication if all_press else None
        ),
        "date_range": {
            "earliest": min(all_press, key=lambda x: x.date).date if all_press else None,
            "latest": max(all_press, key=lambda x: x.date).date if all_press else None,
        },
    }


__all__ = [
    "PressMention",
    "FEATURED_PRESS",
    "GENERAL_PRESS",
    "ONLINE_MENTIONS",
    "get_all_press",
    "get_featured_press",
    "get_press_by_publication",
    "get_press_by_date_range",
    "get_top_press",
    "get_press_stats",
]
