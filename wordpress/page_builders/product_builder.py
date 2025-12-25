"""
Product Page Builder for SkyyRose

Generates single product pages with:
- Interactive 3D model viewer
- Product tabs (Description, Sizing, Story, Pre-Order)
- AR Quick Look button for iOS
- Pre-order countdown timer
- Limited edition badges

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

from typing import Any

from wordpress.elementor import (
    SKYYROSE_BRAND_KIT,
    ElementorBuilder,
    ElementorConfig,
    ElementorTemplate,
    SectionLayout,
    WidgetType,
)


class ProductPageBuilder(ElementorBuilder):
    """
    Interactive product page generator for SkyyRose.

    Builds product pages with 3D viewers, tabs, and pre-order integration.
    """

    def __init__(self, config: ElementorConfig | None = None) -> None:
        """Initialize product page builder."""
        super().__init__(config or ElementorConfig(brand_kit=SKYYROSE_BRAND_KIT))

    def build_3d_viewer_section(
        self,
        product_id: int,
        glb_url: str,
        usdz_url: str = "",
    ) -> list[dict[str, Any]]:
        """
        Build 3D product viewer section.

        Args:
            product_id: WooCommerce product ID
            glb_url: URL to GLB model (WebGL)
            usdz_url: URL to USDZ model (iOS AR)

        Returns:
            List of widget dicts
        """
        widgets = []

        widgets.append(self.spacer(40))

        # 3D viewer
        widgets.append(
            self.threejs_viewer(
                product_id=product_id,
                glb_url=glb_url,
                usdz_url=usdz_url,
                width="100%",
                height="600px",
                auto_rotate=True,
                enable_zoom=True,
                show_ar_button=True,
                background_color="#F5F5F0",
            )
        )

        widgets.append(self.spacer(32))

        return widgets

    def build_product_tabs(
        self,
        product_id: int,
    ) -> list[dict[str, Any]]:
        """
        Build product information tabs.

        Args:
            product_id: WooCommerce product ID

        Returns:
            List of widget dicts with tab widget
        """
        widgets = []

        # Tabs widget (Elementor Pro)
        widgets.append(
            self._widget(
                WidgetType.TABS,
                {
                    "tabs": [
                        {
                            "tab_title": "Description",
                            "tab_content": f"[product_description id='{product_id}']",
                        },
                        {
                            "tab_title": "Sizing Guide",
                            "tab_content": "[sizing_chart]",
                        },
                        {
                            "tab_title": "The Story",
                            "tab_content": "[product_story id='{product_id}']",
                        },
                        {
                            "tab_title": "Pre-Order",
                            "tab_content": "[preorder_info id='{product_id}']",
                        },
                    ],
                    "tabs_justify_horizontal": "justify",
                    "title_html_tag": "div",
                },
            )
        )

        widgets.append(self.spacer(40))

        return widgets

    def build_preorder_countdown(
        self,
        product_id: int,
        target_date: str,
    ) -> list[dict[str, Any]]:
        """
        Build pre-order countdown timer.

        Args:
            product_id: WooCommerce product ID
            target_date: ISO 8601 launch date

        Returns:
            List of widget dicts
        """
        widgets = []

        widgets.append(self.spacer(40))

        # Status badge
        widgets.append(
            self.heading(
                "Blooming Soon",
                size="md",
                tag="h3",
                align="center",
            )
        )

        widgets.append(self.spacer(16))

        # Countdown timer
        widgets.append(
            self._widget(
                WidgetType.COUNTDOWN_TIMER,
                {
                    "product_id": str(product_id),
                    "target_date": target_date,
                    "display_format": "compact",  # DD:HH:MM:SS
                    "on_complete": "hide",
                    "complete_message": "Now Blooming - Available to Purchase",
                    "timezone": "auto",  # Sync with server
                },
            )
        )

        widgets.append(self.spacer(32))

        # Email notification form
        widgets.append(
            self._widget(
                WidgetType.FORM,
                {
                    "form_name": "preorder_notify",
                    "form_fields": [
                        {
                            "field_type": "email",
                            "field_label": "Email",
                            "placeholder": "Get notified at launch",
                            "required": "yes",
                        }
                    ],
                    "submit_button_text": "Notify Me",
                    "integration": "klaviyo",
                    "klaviyo_list": "preorder_early_access",
                },
            )
        )

        widgets.append(self.spacer(40))

        return widgets

    def build_ar_quick_look(
        self,
        product_id: int,
        usdz_url: str,
    ) -> list[dict[str, Any]]:
        """
        Build AR Quick Look button for iOS.

        Args:
            product_id: WooCommerce product ID
            usdz_url: URL to USDZ model

        Returns:
            List of widget dicts
        """
        widgets = []

        widgets.append(
            self.ar_quick_look_button(
                product_id=product_id,
                usdz_url=usdz_url,
                button_text="View in AR",
                button_style="primary",
                show_on_ios_only=True,
            )
        )

        widgets.append(self.spacer(24))

        return widgets

    def build_limited_edition_badge(
        self,
        edition_number: int,
        total_edition: int,
    ) -> list[dict[str, Any]]:
        """
        Build limited edition badge.

        Args:
            edition_number: Current edition (e.g., 23)
            total_edition: Total edition count (e.g., 50)

        Returns:
            List of widget dicts
        """
        widgets = []

        badge_text = f"#{edition_number}/{total_edition} LIMITED EDITION"

        widgets.append(
            self._widget(
                WidgetType.IMAGE_BOX,
                {
                    "title": badge_text,
                    "title_color": self.brand.colors.primary,
                    "description": "Exclusive piece. Collect them all.",
                    "description_color": self.brand.colors.text_light,
                    "icon": "eicon-star",
                    "icon_color": self.brand.colors.primary,
                },
            )
        )

        return widgets

    def generate(
        self,
        product_id: int,
        glb_url: str,
        usdz_url: str = "",
        target_date: str = "",
        edition_number: int | None = None,
        total_edition: int | None = None,
    ) -> ElementorTemplate:
        """
        Generate complete product page template.

        Args:
            product_id: WooCommerce product ID
            glb_url: URL to GLB model
            usdz_url: URL to USDZ model (AR)
            target_date: Pre-order launch date (ISO 8601)
            edition_number: Limited edition number
            total_edition: Total edition count

        Returns:
            ElementorTemplate ready for export
        """
        template = ElementorTemplate(
            title=f"Product {product_id}",
            type="single",
            page_settings={
                "template": "elementor_header_footer",
                "hide_title": "no",
            },
        )

        # Section 1: Hero with 3D viewer
        viewer_widgets = self.build_3d_viewer_section(
            product_id=product_id,
            glb_url=glb_url,
            usdz_url=usdz_url,
        )
        template.add_section(viewer_widgets, layout=SectionLayout.BOXED)

        # Section 2: Limited edition badge (if applicable)
        if edition_number and total_edition:
            badge_widgets = self.build_limited_edition_badge(
                edition_number=edition_number,
                total_edition=total_edition,
            )
            template.add_section(badge_widgets, layout=SectionLayout.BOXED)

        # Section 3: Product tabs
        tabs_widgets = self.build_product_tabs(product_id=product_id)
        template.add_section(tabs_widgets, layout=SectionLayout.BOXED)

        # Section 4: Pre-order countdown (if target date provided)
        if target_date:
            countdown_widgets = self.build_preorder_countdown(
                product_id=product_id,
                target_date=target_date,
            )
            template.add_section(countdown_widgets, layout=SectionLayout.BOXED)

        # Section 5: AR Quick Look (if iOS model provided)
        if usdz_url:
            ar_widgets = self.build_ar_quick_look(
                product_id=product_id,
                usdz_url=usdz_url,
            )
            template.add_section(ar_widgets, layout=SectionLayout.BOXED)

        return template


__all__ = ["ProductPageBuilder"]
