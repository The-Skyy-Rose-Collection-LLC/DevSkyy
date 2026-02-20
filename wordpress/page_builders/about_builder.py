"""About page Elementor template builder."""

from __future__ import annotations

from typing import Any

from wordpress.elementor import ElementorBuilder, ElementorConfig, ElementorTemplate


class AboutPageBuilder:
    """Builds the SkyyRose about page Elementor template."""

    def __init__(self, config: ElementorConfig | None = None) -> None:
        self._builder = ElementorBuilder(config)

    def generate(self, **kwargs: Any) -> ElementorTemplate:
        """Generate about page template."""
        colors = self._builder.brand_kit.get("colors", {})

        content = [
            self._builder._section(
                widgets=[
                    self._builder._heading("Our Story", tag="h1"),
                    self._builder._text(
                        "<p>SkyyRose was born from a vision of luxury that speaks "
                        "to the heart. Where Love Meets Luxury isn't just a tagline "
                        "— it's a promise woven into every thread.</p>"
                    ),
                ],
                background=colors.get("obsidian", "#0D0D0D"),
                padding="120px",
            ),
            self._builder._section(
                widgets=[
                    self._builder._heading("The Vision", tag="h2"),
                    self._builder._text(
                        "<p>Every SkyyRose piece tells a story of craftsmanship, "
                        "passion, and uncompromising quality.</p>"
                    ),
                ],
                background=colors.get("black", "#1A1A1A"),
                padding="80px",
            ),
        ]

        return ElementorTemplate(
            content=content,
            page_settings={
                "post_title": "About SkyyRose",
                "template": "elementor_header_footer",
            },
        )
