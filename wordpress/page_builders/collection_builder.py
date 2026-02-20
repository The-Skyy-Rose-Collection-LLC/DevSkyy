"""Collection experience page Elementor template builder."""

from __future__ import annotations

from typing import Any

from wordpress.collection_page_manager import CollectionDesignTemplates, CollectionType
from wordpress.elementor import ElementorBuilder, ElementorConfig, ElementorTemplate


class CollectionExperienceBuilder:
    """Builds collection experience pages with 3D integration."""

    def __init__(self, config: ElementorConfig | None = None) -> None:
        self._builder = ElementorBuilder(config)

    def generate(
        self,
        collection_type: CollectionType | None = None,
        experience_url: str = "",
        **kwargs: Any,
    ) -> ElementorTemplate:
        """
        Generate collection experience template.

        Args:
            collection_type: Which collection to build for.
            experience_url: URL for the 3D experience iframe.
            **kwargs: Additional options.

        Returns:
            ElementorTemplate for the collection page.
        """
        if collection_type is None:
            collection_type = CollectionType.BLACK_ROSE

        template = CollectionDesignTemplates.get_template(collection_type)

        return self._builder.generate_collection_page(
            collection_name=template.name,
            collection_description=template.description,
            experience_url=experience_url,
        )
