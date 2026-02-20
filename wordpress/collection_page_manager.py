"""
WordPress Collection Page Manager
===================================

Manages SkyyRose collection pages via WordPress REST API.
Provides design templates for brand consistency and recovery.

Usage:
    from wordpress.collection_page_manager import (
        CollectionType,
        CollectionDesignTemplates,
        WordPressCollectionPageManager,
        WordPressConfig,
    )

    config = WordPressConfig(
        wp_url="https://skyyrose.co",
        username="admin",
        app_password="xxxx xxxx xxxx xxxx",
    )
    manager = WordPressCollectionPageManager(config=config)
    await manager.create_collection_page(
        collection_type=CollectionType.BLACK_ROSE,
        html_file_path="path/to/template.html",
    )
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# =============================================================================
# Enums
# =============================================================================


class CollectionType(str, Enum):
    """SkyyRose collection types."""

    BLACK_ROSE = "black_rose"
    LOVE_HURTS = "love_hurts"
    SIGNATURE = "signature"


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class WordPressConfig:
    """WordPress connection configuration."""

    wp_url: str = ""
    username: str = ""
    app_password: str = ""
    timeout: int = 30
    verify_ssl: bool = True


@dataclass
class CollectionTemplate:
    """Design template for a SkyyRose collection."""

    name: str
    collection_type: CollectionType
    theme: str
    description: str
    colors: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] | None = None
    html_file_path: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert template to dictionary representation."""
        return {
            "name": self.name,
            "collection_type": self.collection_type.value,
            "theme": self.theme,
            "description": self.description,
            "colors": self.colors,
            "metadata": self.metadata or {},
            "html_file_path": self.html_file_path,
        }


# =============================================================================
# Collection Design Templates
# =============================================================================


class CollectionDesignTemplates:
    """
    Design template registry for SkyyRose collections.

    Provides reference templates for brand consistency and recovery.
    Each collection has a defined color palette, theme, and design specs.
    """

    _TEMPLATES: dict[CollectionType, CollectionTemplate] = {
        CollectionType.BLACK_ROSE: CollectionTemplate(
            name="BLACK ROSE Collection",
            collection_type=CollectionType.BLACK_ROSE,
            theme="Dark Elegance — Gothic Luxury",
            description=(
                "Dark, dramatic aesthetic inspired by gothic architecture. "
                "The BLACK ROSE collection embodies mysterious luxury with "
                "deep obsidian tones and rose gold accents."
            ),
            colors={
                "primary": "#0D0D0D",
                "secondary": "#1A1A1A",
                "accent": "#B76E79",
                "text": "#F5F5F5",
                "highlight": "#D4AF37",
            },
            metadata={
                "environment": "cathedral",
                "lighting": "dramatic_chiaroscuro",
                "typography": {
                    "display": "Playfair Display",
                    "body": "Inter",
                },
                "target_audience": "luxury seekers, gothic fashion enthusiasts",
                "3d_scene": "enchanted_cathedral",
            },
            html_file_path="wordpress/collection_templates/skyyrose-black_rose-garden-production.html",
        ),
        CollectionType.LOVE_HURTS: CollectionTemplate(
            name="LOVE HURTS Collection",
            collection_type=CollectionType.LOVE_HURTS,
            theme="Emotional Expression — Castle Romance",
            description=(
                "An emotional journey through love and pain. "
                "The LOVE HURTS collection features castle environments, "
                "enchanted ballrooms, and dramatic red-and-rose palettes."
            ),
            colors={
                "primary": "#1A0A0E",
                "secondary": "#2D1117",
                "accent": "#E63946",
                "text": "#F1FAEE",
                "highlight": "#B76E79",
            },
            metadata={
                "environment": "castle_ballroom",
                "lighting": "warm_romantic",
                "typography": {
                    "display": "Playfair Display",
                    "body": "Inter",
                },
                "target_audience": "expressive souls, romantic rebels",
                "3d_scene": "enchanted_ballroom",
            },
            html_file_path="wordpress/collection_templates/skyyrose-love_hurts-garden-production.html",
        ),
        CollectionType.SIGNATURE: CollectionTemplate(
            name="SIGNATURE Collection",
            collection_type=CollectionType.SIGNATURE,
            theme="Premium Essentials — Runway Showcase",
            description=(
                "Clean, minimal design with premium materials. "
                "The SIGNATURE collection represents SkyyRose's foundation, "
                "featuring elegant simplicity and timeless luxury."
            ),
            colors={
                "primary": "#FAFAFA",
                "secondary": "#F0F0F0",
                "accent": "#B76E79",
                "text": "#1A1A1A",
                "highlight": "#D4AF37",
            },
            metadata={
                "environment": "city_runway",
                "lighting": "clean_studio",
                "typography": {
                    "display": "Playfair Display",
                    "body": "Inter",
                },
                "target_audience": "fashion-forward professionals",
                "3d_scene": "city_tour",
            },
            html_file_path="wordpress/collection_templates/skyyrose-signature-garden-production.html",
        ),
    }

    @classmethod
    def get_template(cls, collection_type: CollectionType) -> CollectionTemplate:
        """
        Get design template for a collection type.

        Args:
            collection_type: The collection to get template for.

        Returns:
            CollectionTemplate with design specifications.

        Raises:
            KeyError: If collection type not found.
        """
        if collection_type not in cls._TEMPLATES:
            raise KeyError(f"No template found for collection: {collection_type}")
        return cls._TEMPLATES[collection_type]

    @classmethod
    def get_all_templates(cls) -> dict[CollectionType, CollectionTemplate]:
        """Get all design templates."""
        return dict(cls._TEMPLATES)

    @classmethod
    def to_agent_reference(cls, collection_type: CollectionType) -> dict[str, Any]:
        """
        Convert template to agent-friendly reference format.

        Used by agents to verify design consistency.

        Args:
            collection_type: The collection to reference.

        Returns:
            Dictionary with template data for agent consumption.
        """
        template = cls.get_template(collection_type)
        return {
            "collection": collection_type.value,
            "name": template.name,
            "theme": template.theme,
            "description": template.description,
            "colors": template.colors,
            "metadata": template.metadata or {},
            "html_file_path": template.html_file_path,
            "recovery_instructions": (
                f"Restore {template.name} using colors: {template.colors} "
                f"and theme: {template.theme}. "
                f"Reference HTML: {template.html_file_path}"
            ),
        }


# =============================================================================
# WordPress Collection Page Manager
# =============================================================================


class WordPressCollectionPageManager:
    """
    Manages SkyyRose collection pages via WordPress REST API.

    Handles page CRUD, media uploads, custom meta fields,
    and collection-specific configurations.

    Usage:
        config = WordPressConfig(wp_url="https://skyyrose.co", ...)
        manager = WordPressCollectionPageManager(config=config)
        await manager.create_collection_page(CollectionType.BLACK_ROSE, html_path)
    """

    def __init__(self, config: WordPressConfig) -> None:
        """
        Initialize with WordPress configuration.

        Args:
            config: WordPress connection settings.
        """
        self.config = config
        self._base_url = config.wp_url.rstrip("/")
        self._auth = (config.username, config.app_password) if config.username else None

        logger.info(
            "wordpress_collection_manager_initialized",
            extra={"wp_url": self._base_url},
        )

    async def create_page(
        self,
        title: str,
        slug: str,
        template_json: str = "",
        status: str = "draft",
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Create a WordPress page.

        Args:
            title: Page title.
            slug: URL slug.
            template_json: Elementor template JSON content.
            status: Post status (draft, publish, etc.).
            **kwargs: Additional page data.

        Returns:
            Created page data from WordPress API.
        """
        from wordpress.client import WordPressClient

        async with WordPressClient(
            wp_url=self._base_url,
            username=self.config.username,
            app_password=self.config.app_password,
        ) as client:
            page_data: dict[str, Any] = {
                "title": title,
                "slug": slug,
                "status": status,
                "content": template_json,
                **kwargs,
            }
            result = await client.create_page(**page_data)

            logger.info(
                "page_created",
                extra={"title": title, "slug": slug, "id": result.get("id")},
            )
            return result

    async def create_collection_page(
        self,
        collection_type: CollectionType,
        html_file_path: str,
        status: str = "draft",
    ) -> dict[str, Any]:
        """
        Create a collection page with 3D experience HTML.

        Args:
            collection_type: Which collection to create page for.
            html_file_path: Path to the HTML experience file.
            status: Post status.

        Returns:
            Created page data.
        """
        template = CollectionDesignTemplates.get_template(collection_type)

        # Read HTML content if file exists
        content = ""
        html_path = Path(html_file_path)
        if html_path.exists():
            content = html_path.read_text()
        else:
            logger.warning(
                "html_file_not_found",
                extra={"path": html_file_path},
            )

        slug = f"collection-{collection_type.value.replace('_', '-')}"
        result = await self.create_page(
            title=template.name,
            slug=slug,
            template_json=content,
            status=status,
        )

        # Set collection-specific meta
        if result.get("id"):
            from wordpress.client import WordPressClient

            async with WordPressClient(
                wp_url=self._base_url,
                username=self.config.username,
                app_password=self.config.app_password,
            ) as client:
                await client.update_post_meta(
                    result["id"],
                    {
                        "_skyyrose_collection_type": collection_type.value,
                        "_skyyrose_theme": template.theme,
                        "_skyyrose_colors": str(template.colors),
                    },
                )

        return result

    async def update_collection_page(
        self,
        page_id: int,
        collection_type: CollectionType,
        content: str = "",
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Update an existing collection page.

        Args:
            page_id: WordPress page ID.
            collection_type: Collection type.
            content: Updated HTML content.
            **kwargs: Additional update data.

        Returns:
            Updated page data.
        """
        from wordpress.client import WordPressClient

        async with WordPressClient(
            wp_url=self._base_url,
            username=self.config.username,
            app_password=self.config.app_password,
        ) as client:
            update_data: dict[str, Any] = {"content": content, **kwargs}
            result = await client.update_post(page_id, update_data)

            logger.info(
                "collection_page_updated",
                extra={"page_id": page_id, "collection": collection_type.value},
            )
            return result

    async def delete_collection_page(self, page_id: int) -> dict[str, Any]:
        """
        Delete a collection page.

        Args:
            page_id: WordPress page ID to delete.

        Returns:
            Deletion result.
        """
        from wordpress.client import WordPressClient

        async with WordPressClient(
            wp_url=self._base_url,
            username=self.config.username,
            app_password=self.config.app_password,
        ) as client:
            result = await client.delete_post(page_id)
            logger.info("collection_page_deleted", extra={"page_id": page_id})
            return result


__all__ = [
    "CollectionType",
    "CollectionTemplate",
    "CollectionDesignTemplates",
    "WordPressConfig",
    "WordPressCollectionPageManager",
]
