"""Blog/Journal page Elementor template builder."""

from __future__ import annotations

from typing import Any

from wordpress.elementor import ElementorBuilder, ElementorConfig, ElementorTemplate


class BlogPageBuilder:
    """Builds the SkyyRose blog/journal page Elementor template."""

    def __init__(self, config: ElementorConfig | None = None) -> None:
        self._builder = ElementorBuilder(config)

    def generate(self, **kwargs: Any) -> ElementorTemplate:
        """Generate blog page template."""
        colors = self._builder.brand_kit.get("colors", {})

        content = [
            self._builder._section(
                widgets=[
                    self._builder._heading("The Journal", tag="h1"),
                    self._builder._text(
                        "<p>Stories, inspirations, and behind-the-scenes "
                        "from the world of SkyyRose.</p>"
                    ),
                ],
                background=colors.get("obsidian", "#0D0D0D"),
                padding="80px",
            ),
        ]

        return ElementorTemplate(
            content=content,
            page_settings={
                "post_title": "Journal",
                "template": "elementor_header_footer",
            },
        )
