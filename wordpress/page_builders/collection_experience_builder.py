"""
Collection Experience Page Builder for SkyyRose

Generates immersive collection pages with:
- Fullscreen 3D experience viewer
- Interactive product hotspots
- Scroll-based camera transitions
- Product cards with real-time WooCommerce data

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

from typing import Any

from wordpress.collection_page_manager import CollectionDesignTemplates, CollectionType
from wordpress.elementor import (
    SKYYROSE_BRAND_KIT,
    ElementorBuilder,
    ElementorConfig,
    ElementorTemplate,
    SectionLayout,
    WidgetType,
)


class CollectionExperienceBuilder(ElementorBuilder):
    """
    Immersive collection experience page generator.

    Builds fullscreen 3D experiences with hotspots and interactive storytelling.
    """

    def __init__(self, config: ElementorConfig | None = None) -> None:
        """Initialize collection experience builder."""
        super().__init__(config or ElementorConfig(brand_kit=SKYYROSE_BRAND_KIT))

    def build_fullscreen_experience_iframe(
        self,
        collection_type: CollectionType,
        experience_url: str,
    ) -> list[dict[str, Any]]:
        """
        Build fullscreen Three.js experience embed.

        Args:
            collection_type: Black Rose, Love Hurts, or Signature
            experience_url: URL to HTML experience file

        Returns:
            List of widget dicts
        """
        template = CollectionDesignTemplates.get_template(collection_type)

        widgets = []

        # Fullscreen iframe
        widgets.append(
            self._widget(
                WidgetType.VIDEO,
                {
                    "video_type": "hosted",
                    "hosted_url": experience_url,
                    "controls": "yes",
                    "autoplay": "no",
                    "loop": "yes",
                    "muted": "no",
                    "preload": "auto",
                    "aspect_ratio": "16:9",
                },
            )
        )

        return widgets

    def build_hotspot_product_cards(
        self,
        collection_type: CollectionType,
    ) -> list[dict[str, Any]]:
        """
        Build interactive product hotspot cards.

        Args:
            collection_type: Collection slug

        Returns:
            List of widget dicts with product cards
        """
        widgets = []

        widgets.append(self.spacer(60))

        widgets.append(
            self.heading(
                f"Featured Pieces from {collection_type.value.replace('_', ' ').title()}",
                size="lg",
                tag="h2",
                align="center",
            )
        )

        widgets.append(self.spacer(40))

        # Product hotspot viewer (custom widget)
        widgets.append(
            self._widget(
                WidgetType.PRODUCT_HOTSPOT_VIEWER,
                {
                    "collection_slug": collection_type.value,
                    "hotspot_config_url": f"/wp-content/uploads/hotspots/{collection_type.value}-hotspots.json",
                    "auto_load_products": "yes",
                    "enable_cart": "yes",
                    "enable_wishlist": "yes",
                },
            )
        )

        widgets.append(self.spacer(60))

        return widgets

    def build_scroll_camera_controller(
        self,
        collection_type: CollectionType,
    ) -> list[dict[str, Any]]:
        """
        Build scroll-based 3D camera controller.

        Args:
            collection_type: Collection for theme

        Returns:
            List of widget dicts
        """
        widgets = []

        template = CollectionDesignTemplates.get_template(collection_type)

        # JavaScript embed for scroll control
        widgets.append(
            self._widget(
                WidgetType.TEXT_EDITOR,
                {
                    "editor": f"""
<script>
// Scroll-based camera transitions for {template.name}
window.initScrollCamera = function() {{
    const experience = document.querySelector('[data-experience="{collection_type.value}"]');
    if (!experience) return;

    const waypoints = [
        {{ scroll: 0, camera: [3, 2, 4] }},
        {{ scroll: 25, camera: [0, 2, 5] }},
        {{ scroll: 50, camera: [-3, 1, 4] }},
        {{ scroll: 75, camera: [4, 3, 3] }},
        {{ scroll: 100, camera: [0, 2, 4] }}
    ];

    window.addEventListener('scroll', () => {{
        const scroll = (window.scrollY / (document.body.scrollHeight - window.innerHeight)) * 100;
        experience.dispatchEvent(new CustomEvent('camera-update', {{ detail: {{ scroll }} }}));
    }});
}};

if (document.readyState === 'loading') {{
    document.addEventListener('DOMContentLoaded', window.initScrollCamera);
}} else {{
    window.initScrollCamera();
}}
</script>
""",
                },
            )
        )

        return widgets

    def generate(
        self,
        collection_type: CollectionType,
        experience_url: str,
    ) -> ElementorTemplate:
        """
        Generate complete collection experience page.

        Args:
            collection_type: Black Rose, Love Hurts, or Signature
            experience_url: URL to 3D HTML experience file

        Returns:
            ElementorTemplate ready for export
        """
        template_spec = CollectionDesignTemplates.get_template(collection_type)

        template = ElementorTemplate(
            title=template_spec.name,
            page_settings={
                "hide_title": "yes",
                "template": "elementor_canvas",
                "post_title": template_spec.name,
                "meta_description": template_spec.description,
            },
        )

        # Section 1: Collection header with theme
        header_widgets = [
            self.spacer(60),
            self.heading(
                template_spec.name,
                size="xxl",
                tag="h1",
                align="center",
            ),
            self.text(
                f"<p>{template_spec.theme}</p>",
                align="center",
            ),
            self.spacer(40),
        ]
        template.add_section(
            header_widgets,
            layout=SectionLayout.FULL_WIDTH,
            settings={
                "background_color": template_spec.colors.get("accent", "#fff"),
            },
        )

        # Section 2: Fullscreen 3D experience
        experience_widgets = self.build_fullscreen_experience_iframe(
            collection_type=collection_type,
            experience_url=experience_url,
        )
        template.add_section(
            experience_widgets,
            layout=SectionLayout.FULL_WIDTH,
        )

        # Section 3: Product hotspot cards
        hotspot_widgets = self.build_hotspot_product_cards(
            collection_type=collection_type,
        )
        template.add_section(
            hotspot_widgets,
            layout=SectionLayout.BOXED,
        )

        # Section 4: Scroll camera controller
        scroll_widgets = self.build_scroll_camera_controller(
            collection_type=collection_type,
        )
        template.add_section(
            scroll_widgets,
            layout=SectionLayout.FULL_WIDTH,
        )

        # Section 5: CTA to shop
        cta_widgets = [
            self.spacer(80),
            self.heading(
                f"Shop the {template_spec.name}",
                size="lg",
                tag="h2",
                align="center",
            ),
            self.button(
                "Browse Collection",
                f"/collection/{template_spec.slug}",
                style="primary",
                size="lg",
            ),
            self.spacer(80),
        ]
        template.add_section(
            cta_widgets,
            layout=SectionLayout.BOXED,
            settings={
                "background_color": template_spec.colors.get("primary", "#000"),
            },
        )

        return template


__all__ = ["CollectionExperienceBuilder"]
