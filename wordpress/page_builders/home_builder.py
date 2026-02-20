"""Homepage Elementor template builder."""

from __future__ import annotations

from typing import Any

from wordpress.elementor import ElementorBuilder, ElementorConfig, ElementorTemplate


class HomePageBuilder:
    """Builds the SkyyRose homepage Elementor template."""

    def __init__(self, config: ElementorConfig | None = None) -> None:
        self._builder = ElementorBuilder(config)

    def generate(self, **kwargs: Any) -> ElementorTemplate:
        """Generate homepage template."""
        return self._builder.generate_home_page(**kwargs)
