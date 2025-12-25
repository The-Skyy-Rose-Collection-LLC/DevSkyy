"""
Blog Page Builder for SkyyRose

Generates blog listing pages with:
- Responsive grid layout using Elementor Custom Skin
- Auto-population from posts
- RankMath SEO schema integration
- Reading time estimates
- Category filters

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


class BlogPageBuilder(ElementorBuilder):
    """
    Blog listing page generator for SkyyRose.

    Builds blog archive pages with SEO optimization and custom grids.
    """

    def __init__(self, config: ElementorConfig | None = None) -> None:
        """Initialize blog page builder."""
        super().__init__(config or ElementorConfig(brand_kit=SKYYROSE_BRAND_KIT))

    def build_blog_header(self) -> list[dict[str, Any]]:
        """
        Build blog header section.

        Returns:
            List of widget dicts
        """
        widgets = []

        widgets.append(self.spacer(60))

        widgets.append(
            self.heading(
                "Stories & Insights",
                size="xxl",
                tag="h1",
                align="center",
            )
        )

        widgets.append(
            self.text(
                "<p>Thoughts on fashion, identity, and the SkyyRose journey.</p>",
                align="center",
            )
        )

        widgets.append(self.spacer(40))

        return widgets

    def build_blog_grid(
        self,
        posts_per_page: int = 12,
    ) -> list[dict[str, Any]]:
        """
        Build blog post grid with custom skin.

        Args:
            posts_per_page: Number of posts to display

        Returns:
            List of widget dicts
        """
        widgets = []

        # Posts widget with custom skin (Elementor Pro)
        widgets.append(
            self._widget(
                WidgetType.LOOP_GRID,
                {
                    "post_type": "post",
                    "posts_per_page": str(posts_per_page),
                    "orderby": "date",
                    "order": "desc",
                    "query_exclude_uids": "",
                    "paginate": "yes",
                    "pagination_type": "numbers",
                    # Custom skin for SkyyRose brand
                    "skin": "custom_grid",
                    "columns": "3",
                    "column_gap": "30",
                    "row_gap": "40",
                    # Card settings
                    "post_title": "yes",
                    "post_excerpt": "yes",
                    "post_featured_image": "yes",
                    "post_date": "yes",
                    "post_author": "yes",
                    "post_category": "yes",
                    "reading_time": "yes",
                },
            )
        )

        return widgets

    def build_category_filter(self) -> list[dict[str, Any]]:
        """
        Build category filter widget.

        Returns:
            List of widget dicts
        """
        widgets = []

        widgets.append(self.spacer(40))

        # Posts filter widget (Elementor Pro)
        widgets.append(
            self._widget(
                WidgetType.LOOP_CONTROLS,
                {
                    "filter_by": "taxonomy",
                    "taxonomy": "category",
                    "filter_type": "select",
                    "layout": "horizontal",
                },
            )
        )

        widgets.append(self.spacer(40))

        return widgets

    def configure_rankmath_schema(self) -> dict[str, Any]:
        """
        Configure RankMath SEO schema for blog.

        Returns:
            RankMath schema configuration
        """
        return {
            "schema_type": "CollectionPage",
            "title": "Stories & Insights - SkyyRose Blog",
            "description": "Thoughts on fashion, identity, and the SkyyRose journey.",
            "url": "/blog",
            "image": "/wp-content/uploads/blog/blog-hero.jpg",
            "publisher": {
                "name": "SkyyRose",
                "logo": "/wp-content/uploads/logo.png",
            },
            # Blog post schema for individual posts
            "post_schema": {
                "type": "BlogPosting",
                "author": {"type": "Person"},
                "datePublished": "auto",
                "dateModified": "auto",
                "image": "featured_image",
                "articleBody": "content",
            },
        }

    def generate(
        self,
        posts_per_page: int = 12,
    ) -> ElementorTemplate:
        """
        Generate complete blog page template.

        Args:
            posts_per_page: Number of posts to display per page

        Returns:
            ElementorTemplate ready for export
        """
        template = ElementorTemplate(
            title="Blog",
            page_settings={
                "hide_title": "yes",
                "template": "elementor_canvas",
                "post_title": "Stories & Insights - SkyyRose Blog",
                "meta_description": "Thoughts on fashion, identity, and the SkyyRose journey. Read our latest stories and insights.",
            },
        )

        # Section 1: Header
        header_widgets = self.build_blog_header()
        template.add_section(
            header_widgets,
            layout=SectionLayout.FULL_WIDTH,
            settings={
                "background_color": self.brand.colors.background_alt,
            },
        )

        # Section 2: Category filter
        filter_widgets = self.build_category_filter()
        template.add_section(
            filter_widgets,
            layout=SectionLayout.BOXED,
        )

        # Section 3: Blog grid
        grid_widgets = self.build_blog_grid(posts_per_page=posts_per_page)
        template.add_section(
            grid_widgets,
            layout=SectionLayout.BOXED,
        )

        # Add RankMath schema to metadata
        template.metadata.update(
            {
                "rankmath_schema": self.configure_rankmath_schema(),
            }
        )

        return template


__all__ = ["BlogPageBuilder"]
