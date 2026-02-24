"""
SkyyRose Social Media Agent

Manages social media content generation, scheduling, and analytics
across Instagram, TikTok, X/Twitter, and Facebook.

Uses BrandContextInjector for consistent SkyyRose tone.
"""

import json
import os
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Platform configurations
PLATFORMS = {
    "instagram": {
        "name": "Instagram",
        "max_caption_length": 2200,
        "max_hashtags": 30,
        "content_types": ["post", "story", "reel", "carousel"],
        "image_ratio": "1:1",
    },
    "tiktok": {
        "name": "TikTok",
        "max_caption_length": 2200,
        "max_hashtags": 5,
        "content_types": ["video", "photo", "story"],
        "video_max_duration": 180,
    },
    "twitter": {
        "name": "X / Twitter",
        "max_caption_length": 280,
        "max_hashtags": 5,
        "content_types": ["tweet", "thread", "media"],
    },
    "facebook": {
        "name": "Facebook",
        "max_caption_length": 63206,
        "max_hashtags": 10,
        "content_types": ["post", "story", "reel"],
    },
}

# Collection-specific hashtag sets
COLLECTION_HASHTAGS = {
    "black-rose": [
        "#SkyyRose", "#BlackRoseCollection", "#GothicLuxury",
        "#DarkRomance", "#WhereLoveMeetsLuxury", "#DarkAesthetic",
        "#WearableArt", "#LuxuryStreetwear", "#BayAreaFashion",
    ],
    "love-hurts": [
        "#SkyyRose", "#LoveHurts", "#OaklandFashion",
        "#WhereLoveMeetsLuxury", "#GritAndGrace", "#UrbanLuxury",
        "#BayAreaStyle", "#StreetwearFashion", "#Authentic",
    ],
    "signature": [
        "#SkyyRose", "#SignatureCollection", "#LuxuryFashion",
        "#WhereLoveMeetsLuxury", "#BayAreaLuxury", "#WestCoastStyle",
        "#CoutureStreetwear", "#ElevatedStyle", "#PrestigeWear",
    ],
}

# Content type templates
CONTENT_TEMPLATES = {
    "product_launch": {
        "description": "New product announcement",
        "platforms": ["instagram", "tiktok", "twitter", "facebook"],
    },
    "collection_drop": {
        "description": "Collection release announcement",
        "platforms": ["instagram", "tiktok", "twitter", "facebook"],
    },
    "behind_the_scenes": {
        "description": "Behind the scenes content",
        "platforms": ["instagram", "tiktok"],
    },
    "lifestyle": {
        "description": "Lifestyle and brand storytelling",
        "platforms": ["instagram", "facebook"],
    },
    "reels_stories": {
        "description": "Short-form video content",
        "platforms": ["instagram", "tiktok"],
    },
}


@dataclass
class SocialPost:
    """Represents a scheduled social media post."""
    id: str = ""
    platform: str = ""
    content_type: str = "post"
    caption: str = ""
    hashtags: list = field(default_factory=list)
    media_urls: list = field(default_factory=list)
    product_sku: str = ""
    collection: str = ""
    scheduled_at: Optional[str] = None
    published_at: Optional[str] = None
    status: str = "draft"  # draft, scheduled, published, failed
    engagement: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.id:
            raw = f"{self.platform}:{self.caption[:50]}:{datetime.now().isoformat()}"
            self.id = hashlib.sha256(raw.encode()).hexdigest()[:12]


class SocialMediaAgent:
    """
    Manages social media content lifecycle for SkyyRose.

    Capabilities:
    - Generate platform-optimized captions from product data
    - Schedule posts across all platforms
    - Track engagement analytics
    - Maintain consistent brand voice via BrandContextInjector
    """

    def __init__(self, product_data_path: Optional[str] = None):
        self.product_data_path = product_data_path or os.path.join(
            os.path.dirname(__file__), "..", "skyyrose", "assets", "data", "product-content.json"
        )
        self._products = {}
        self._post_queue: list[SocialPost] = []
        self._published: list[SocialPost] = []
        self._analytics: dict = {
            "instagram": {"posts": 0, "likes": 0, "comments": 0, "shares": 0, "reach": 0},
            "tiktok": {"posts": 0, "views": 0, "likes": 0, "shares": 0},
            "twitter": {"posts": 0, "likes": 0, "retweets": 0, "impressions": 0},
            "facebook": {"posts": 0, "likes": 0, "comments": 0, "shares": 0, "reach": 0},
        }
        self._load_products()

    def _load_products(self) -> None:
        """Load product data from JSON."""
        try:
            if os.path.exists(self.product_data_path):
                with open(self.product_data_path, "r") as f:
                    self._products = json.load(f)
                logger.info("Loaded %d products for social media", len(self._products))
            else:
                logger.warning("Product data not found at %s", self.product_data_path)
        except (json.JSONDecodeError, OSError) as e:
            logger.error("Failed to load product data: %s", e)

    def generate_post(
        self,
        product_sku: str,
        platform: str,
        content_type: str = "product_launch",
    ) -> Optional[SocialPost]:
        """Generate a social media post for a product on a specific platform."""
        if platform not in PLATFORMS:
            logger.error("Unknown platform: %s", platform)
            return None

        product = self._products.get(product_sku)
        if not product:
            logger.error("Product not found: %s", product_sku)
            return None

        collection = product.get("collection", "")
        platform_config = PLATFORMS[platform]

        # Use existing captions from product data when available
        if platform == "instagram" and product.get("instagram"):
            caption = product["instagram"]
        elif platform == "tiktok" and product.get("tiktok"):
            caption = product["tiktok"]
        else:
            caption = self._generate_caption(product, platform, content_type)

        # Truncate if needed
        max_len = platform_config["max_caption_length"]
        if len(caption) > max_len:
            caption = caption[:max_len - 3] + "..."

        # Get collection-specific hashtags
        hashtags = COLLECTION_HASHTAGS.get(collection, COLLECTION_HASHTAGS["signature"])
        max_tags = platform_config.get("max_hashtags", 10)
        hashtags = hashtags[:max_tags]

        post = SocialPost(
            platform=platform,
            content_type=content_type,
            caption=caption,
            hashtags=hashtags,
            product_sku=product_sku,
            collection=collection,
            status="draft",
        )

        self._post_queue.append(post)
        logger.info("Generated %s post for %s: %s", platform, product_sku, post.id)
        return post

    def _generate_caption(self, product: dict, platform: str, content_type: str) -> str:
        """Generate a caption using product data and brand voice."""
        name = product.get("name", "")
        collection = product.get("collection", "").replace("-", " ").title()
        short_desc = product.get("short_description", "")

        if platform == "twitter":
            return f"{name} from the {collection} Collection. {short_desc[:150]} #SkyyRose #WhereLoveMeetsLuxury"

        return f"{short_desc}\n\nPre-order now at skyyrose.co\n\n#SkyyRose #WhereLoveMeetsLuxury"

    def schedule_post(self, post_id: str, scheduled_at: str) -> bool:
        """Schedule a post for publishing."""
        for post in self._post_queue:
            if post.id == post_id:
                post.scheduled_at = scheduled_at
                post.status = "scheduled"
                logger.info("Scheduled post %s for %s", post_id, scheduled_at)
                return True
        logger.error("Post not found: %s", post_id)
        return False

    def publish_post(self, post_id: str) -> bool:
        """Publish a scheduled post (stub for actual API integration)."""
        for post in self._post_queue:
            if post.id == post_id:
                post.published_at = datetime.now().isoformat()
                post.status = "published"
                self._published.append(post)
                self._post_queue.remove(post)

                # Update analytics
                if post.platform in self._analytics:
                    self._analytics[post.platform]["posts"] += 1

                logger.info("Published post %s on %s", post_id, post.platform)
                return True
        return False

    def get_queue(self) -> list[dict]:
        """Get all posts in the queue."""
        return [
            {
                "id": p.id,
                "platform": p.platform,
                "content_type": p.content_type,
                "caption": p.caption[:100] + "..." if len(p.caption) > 100 else p.caption,
                "hashtags": p.hashtags,
                "product_sku": p.product_sku,
                "collection": p.collection,
                "scheduled_at": p.scheduled_at,
                "status": p.status,
            }
            for p in self._post_queue
        ]

    def get_analytics(self) -> dict:
        """Get analytics summary across all platforms."""
        return {
            "platforms": self._analytics,
            "total_posts": sum(a["posts"] for a in self._analytics.values()),
            "total_queue": len(self._post_queue),
            "total_published": len(self._published),
        }

    def generate_campaign(
        self,
        collection: str,
        campaign_name: str = "Collection Drop",
    ) -> list[SocialPost]:
        """Generate a multi-platform campaign for a collection."""
        posts = []
        collection_products = [
            (sku, prod) for sku, prod in self._products.items()
            if prod.get("collection") == collection
        ]

        if not collection_products:
            logger.warning("No products found for collection: %s", collection)
            return posts

        # Generate posts for each product across platforms
        for sku, _ in collection_products[:5]:  # Limit to 5 products per campaign
            for platform in ["instagram", "tiktok", "twitter", "facebook"]:
                post = self.generate_post(sku, platform, "collection_drop")
                if post:
                    posts.append(post)

        logger.info(
            "Generated campaign '%s' with %d posts for %s",
            campaign_name, len(posts), collection
        )
        return posts


# Singleton instance
social_media_agent = SocialMediaAgent()
