"""
Comprehensive Unit Tests for WordPress Page Builder Modules

Tests for:
1. blog_builder.py - Blog Page Builder
2. collection_experience_builder.py - Collection Experience Page Builder
3. product_builder.py - Product Page Builder
4. luxury_home_builder.py - Luxury Home Page Builder
5. gsap_animations.py - GSAP Animation Builder

Target: 70%+ coverage for each module.

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import json
import pytest
from typing import Any
from unittest.mock import MagicMock, patch


# =============================================================================
# GSAP Animations Tests
# =============================================================================


class TestAnimationType:
    """Tests for AnimationType enum."""

    def test_animation_type_values(self) -> None:
        """Test that AnimationType has expected values."""
        from wordpress.page_builders.gsap_animations import AnimationType

        assert AnimationType.FADE_IN_UP.value == "fadeInUp"
        assert AnimationType.FADE_IN_DOWN.value == "fadeInDown"
        assert AnimationType.FADE_IN_LEFT.value == "fadeInLeft"
        assert AnimationType.FADE_IN_RIGHT.value == "fadeInRight"
        assert AnimationType.SCALE_IN.value == "scaleIn"
        assert AnimationType.ROTATE_IN.value == "rotateIn"
        assert AnimationType.BLUR_IN.value == "blurIn"
        assert AnimationType.STAGGER_FADE.value == "staggerFade"
        assert AnimationType.PARALLAX.value == "parallax"
        assert AnimationType.MAGNETIC.value == "magnetic"
        assert AnimationType.SPLIT_TEXT.value == "splitText"
        assert AnimationType.REVEAL.value == "reveal"
        assert AnimationType.MORPH.value == "morph"


class TestEasingType:
    """Tests for EasingType enum."""

    def test_easing_type_values(self) -> None:
        """Test that EasingType has expected values."""
        from wordpress.page_builders.gsap_animations import EasingType

        assert EasingType.POWER1_OUT.value == "power1.out"
        assert EasingType.POWER2_OUT.value == "power2.out"
        assert EasingType.POWER3_OUT.value == "power3.out"
        assert EasingType.POWER4_OUT.value == "power4.out"
        assert EasingType.EXPO_OUT.value == "expo.out"
        assert EasingType.CIRC_OUT.value == "circ.out"
        assert EasingType.ELASTIC_OUT.value == "elastic.out(1, 0.5)"
        assert EasingType.BACK_OUT.value == "back.out(1.7)"
        assert EasingType.BOUNCE_OUT.value == "bounce.out"
        assert EasingType.CUSTOM_LUXURY.value == "power2.inOut"


class TestGSAPConfig:
    """Tests for GSAPConfig dataclass."""

    def test_default_values(self) -> None:
        """Test GSAPConfig default values."""
        from wordpress.page_builders.gsap_animations import EasingType, GSAPConfig

        config = GSAPConfig()

        assert config.scroll_trigger_start == "top 80%"
        assert config.scroll_trigger_end == "bottom 20%"
        assert config.scrub is False
        assert config.pin is False
        assert config.markers is False
        assert config.duration == 0.8
        assert config.stagger == 0.1
        assert config.delay == 0
        assert config.easing == EasingType.POWER3_OUT
        assert config.parallax_speed == 0.5
        assert config.parallax_direction == "y"
        assert config.view_transition_name is None
        assert config.view_transition_duration == 0.4

    def test_custom_values(self) -> None:
        """Test GSAPConfig with custom values."""
        from wordpress.page_builders.gsap_animations import EasingType, GSAPConfig

        config = GSAPConfig(
            scroll_trigger_start="top 90%",
            scroll_trigger_end="bottom 10%",
            scrub=True,
            pin=True,
            markers=True,
            duration=1.2,
            stagger=0.2,
            delay=0.5,
            easing=EasingType.EXPO_OUT,
            parallax_speed=0.8,
            parallax_direction="x",
            view_transition_name="hero",
            view_transition_duration=0.6,
        )

        assert config.scroll_trigger_start == "top 90%"
        assert config.duration == 1.2
        assert config.easing == EasingType.EXPO_OUT
        assert config.parallax_direction == "x"


class TestGSAPAnimationBuilder:
    """Tests for GSAPAnimationBuilder class."""

    @pytest.fixture
    def gsap_builder(self):
        """Create a GSAPAnimationBuilder instance."""
        from wordpress.page_builders.gsap_animations import GSAPAnimationBuilder

        return GSAPAnimationBuilder()

    @pytest.fixture
    def custom_config_builder(self):
        """Create a GSAPAnimationBuilder with custom config."""
        from wordpress.page_builders.gsap_animations import (
            GSAPAnimationBuilder,
            GSAPConfig,
        )

        config = GSAPConfig(
            duration=1.0,
            stagger=0.2,
            scroll_trigger_start="top 70%",
        )
        return GSAPAnimationBuilder(config)

    def test_init_with_default_config(self, gsap_builder) -> None:
        """Test builder initialization with default config."""
        assert gsap_builder.config is not None
        assert gsap_builder.config.duration == 0.8

    def test_init_with_custom_config(self, custom_config_builder) -> None:
        """Test builder initialization with custom config."""
        assert custom_config_builder.config.duration == 1.0
        assert custom_config_builder.config.stagger == 0.2

    def test_build_scroll_animation_fade_in_up(self, gsap_builder) -> None:
        """Test building fade in up animation."""
        from wordpress.page_builders.gsap_animations import AnimationType

        result = gsap_builder.build_scroll_animation(
            AnimationType.FADE_IN_UP,
            ".test-element",
        )

        assert result["selector"] == ".test-element"
        assert result["type"] == "fadeInUp"
        assert result["from"]["opacity"] == 0
        assert result["from"]["y"] == 60
        assert result["to"]["opacity"] == 1
        assert result["to"]["y"] == 0
        assert "scrollTrigger" in result
        assert result["scrollTrigger"]["trigger"] == ".test-element"

    def test_build_scroll_animation_scale_in(self, gsap_builder) -> None:
        """Test building scale in animation."""
        from wordpress.page_builders.gsap_animations import AnimationType

        result = gsap_builder.build_scroll_animation(
            AnimationType.SCALE_IN,
            ".scale-element",
        )

        assert result["type"] == "scaleIn"
        assert result["from"]["scale"] == 0.8
        assert result["to"]["scale"] == 1

    def test_build_scroll_animation_blur_in(self, gsap_builder) -> None:
        """Test building blur in animation."""
        from wordpress.page_builders.gsap_animations import AnimationType

        result = gsap_builder.build_scroll_animation(
            AnimationType.BLUR_IN,
            ".blur-element",
        )

        assert result["type"] == "blurIn"
        assert result["from"]["filter"] == "blur(20px)"
        assert result["to"]["filter"] == "blur(0px)"

    def test_build_scroll_animation_reveal(self, gsap_builder) -> None:
        """Test building reveal animation."""
        from wordpress.page_builders.gsap_animations import AnimationType

        result = gsap_builder.build_scroll_animation(
            AnimationType.REVEAL,
            ".reveal-element",
        )

        assert result["type"] == "reveal"
        assert "clipPath" in result["from"]
        assert "clipPath" in result["to"]

    def test_build_scroll_animation_custom_from_to(self, gsap_builder) -> None:
        """Test building animation with custom from/to states."""
        from wordpress.page_builders.gsap_animations import AnimationType

        custom_from = {"opacity": 0, "scale": 0.5, "x": -100}
        custom_to = {"opacity": 1, "scale": 1, "x": 0}

        result = gsap_builder.build_scroll_animation(
            AnimationType.FADE_IN_UP,
            ".custom-element",
            custom_from=custom_from,
            custom_to=custom_to,
        )

        assert result["from"] == custom_from
        assert result["to"] == custom_to

    def test_build_scroll_animation_unknown_type(self, gsap_builder) -> None:
        """Test building animation with unknown type falls back to default."""
        from wordpress.page_builders.gsap_animations import AnimationType

        # MORPH doesn't have a defined animation in the animations dict
        result = gsap_builder.build_scroll_animation(
            AnimationType.MORPH,
            ".morph-element",
        )

        # Should fall back to default opacity animation
        assert result["from"]["opacity"] == 0
        assert result["to"]["opacity"] == 1

    def test_build_magnetic_button(self, gsap_builder) -> None:
        """Test building magnetic button effect."""
        result = gsap_builder.build_magnetic_button(".btn-magnetic")

        assert result["selector"] == ".btn-magnetic"
        assert result["type"] == "magnetic"
        assert result["strength"] == 0.3
        assert result["ease"] == "power2.out"
        assert result["duration"] == 0.4
        assert result["lerp"] == 0.1
        assert result["onEnter"]["scale"] == 1.05
        assert result["onLeave"]["scale"] == 1

    def test_build_parallax_default(self, gsap_builder) -> None:
        """Test building parallax effect with default values."""
        result = gsap_builder.build_parallax(".parallax-layer")

        assert result["selector"] == ".parallax-layer"
        assert result["type"] == "parallax"
        assert result["speed"] == 0.5  # Default from config
        assert result["direction"] == "y"  # Default from config
        assert result["scrub"] is True

    def test_build_parallax_custom(self, gsap_builder) -> None:
        """Test building parallax effect with custom values."""
        result = gsap_builder.build_parallax(
            ".parallax-custom",
            speed=0.8,
            direction="x",
        )

        assert result["speed"] == 0.8
        assert result["direction"] == "x"

    def test_build_split_text_animation_default(self, gsap_builder) -> None:
        """Test building split text animation with default split type."""
        result = gsap_builder.build_split_text_animation(".headline")

        assert result["selector"] == ".headline"
        assert result["type"] == "splitText"
        assert result["splitType"] == "chars,words"
        assert result["from"]["opacity"] == 0
        assert result["from"]["y"] == 20
        assert result["from"]["rotateX"] == -90
        assert result["stagger"] == 0.02
        assert result["duration"] == 0.8
        assert result["ease"] == "back.out(1.7)"

    def test_build_split_text_animation_lines(self, gsap_builder) -> None:
        """Test building split text animation with lines split type."""
        result = gsap_builder.build_split_text_animation(
            ".paragraph",
            split_type="lines",
        )

        assert result["splitType"] == "lines"

    def test_build_custom_cursor(self, gsap_builder) -> None:
        """Test building custom cursor configuration."""
        result = gsap_builder.build_custom_cursor()

        assert result["enabled"] is True
        assert result["size"] == 24
        assert result["expandedSize"] == 80
        assert result["color"] == "rgba(183, 110, 121, 0.3)"
        assert result["borderColor"] == "#B76E79"
        assert result["borderWidth"] == 1
        assert result["blendMode"] == "difference"
        assert result["lerp"] == 0.15
        assert result["hoverTargets"] == "[data-cursor-hover]"
        assert result["productPreview"]["enabled"] is True
        assert result["productPreview"]["size"] == 200

    def test_generate_gsap_script(self, gsap_builder) -> None:
        """Test generating GSAP script from animations."""
        from wordpress.page_builders.gsap_animations import AnimationType

        animations = [
            gsap_builder.build_scroll_animation(AnimationType.FADE_IN_UP, ".element1"),
            gsap_builder.build_magnetic_button(".btn"),
            gsap_builder.build_parallax(".parallax"),
        ]

        script = gsap_builder.generate_gsap_script(animations)

        assert "<script>" in script
        assert "</script>" in script
        assert "gsap.registerPlugin(ScrollTrigger)" in script
        assert "initMagneticButtons" in script
        assert "initSplitTextAnimation" in script
        assert "SkyyRose GSAP Animations" in script
        # Check animations are JSON serialized
        assert '"selector"' in script
        assert ".element1" in script

    def test_generate_view_transitions_css(self, gsap_builder) -> None:
        """Test generating View Transitions CSS."""
        css = gsap_builder.generate_view_transitions_css()

        assert "<style>" in css
        assert "</style>" in css
        assert "@view-transition" in css
        assert "::view-transition-old(root)" in css
        assert "::view-transition-new(root)" in css
        assert "@keyframes fade-out" in css
        assert "@keyframes fade-in" in css
        assert "view-transition-name: hero" in css
        assert "view-transition-name: product" in css
        assert "view-transition-name: card" in css

    def test_generate_glassmorphism_css(self, gsap_builder) -> None:
        """Test generating glassmorphism CSS."""
        css = gsap_builder.generate_glassmorphism_css()

        assert "<style>" in css
        assert "</style>" in css
        assert ".glass-card" in css
        assert "backdrop-filter: blur(20px)" in css
        assert "-webkit-backdrop-filter: blur(20px)" in css
        assert ".glass-hero" in css
        assert ".glass-button" in css
        assert "rgba(183, 110, 121" in css  # SkyyRose brand color

    def test_generate_custom_cursor_script(self, gsap_builder) -> None:
        """Test generating custom cursor script."""
        script = gsap_builder.generate_custom_cursor_script()

        assert "<script>" in script
        assert "</script>" in script
        assert "<style>" in script
        assert "skyyrose-cursor" in script
        assert "skyyrose-cursor-follower" in script
        assert "skyyrose-product-preview" in script
        assert "lerp" in script
        assert "@media (hover: hover)" in script
        assert "requestAnimationFrame" in script


class TestGenerateGSAPEnqueueScript:
    """Tests for generate_gsap_enqueue_script function."""

    def test_generates_php_code(self) -> None:
        """Test that function generates valid PHP code."""
        from wordpress.page_builders.gsap_animations import generate_gsap_enqueue_script

        php = generate_gsap_enqueue_script()

        assert "<?php" in php
        assert "function skyyrose_enqueue_gsap()" in php
        assert "wp_enqueue_script" in php
        assert "gsap-core" in php
        assert "gsap-scrolltrigger" in php
        assert "splittype" in php
        assert "skyyrose-animations" in php
        assert "add_action('wp_enqueue_scripts'" in php


# =============================================================================
# Blog Builder Tests
# =============================================================================


class TestBlogPageBuilder:
    """Tests for BlogPageBuilder class."""

    @pytest.fixture
    def blog_builder(self):
        """Create a BlogPageBuilder instance."""
        from wordpress.page_builders.blog_builder import BlogPageBuilder

        return BlogPageBuilder()

    @pytest.fixture
    def blog_builder_custom_config(self):
        """Create a BlogPageBuilder with custom config."""
        from wordpress.elementor import BrandColors, BrandKit, ElementorConfig
        from wordpress.page_builders.blog_builder import BlogPageBuilder

        custom_brand = BrandKit(
            name="Test Brand",
            colors=BrandColors(primary="#FF0000", secondary="#00FF00"),
        )
        config = ElementorConfig(brand_kit=custom_brand)
        return BlogPageBuilder(config)

    def test_init_default(self, blog_builder) -> None:
        """Test BlogPageBuilder initialization with defaults."""
        assert blog_builder.brand is not None
        assert blog_builder.brand.name == "SkyyRose"

    def test_init_custom_config(self, blog_builder_custom_config) -> None:
        """Test BlogPageBuilder initialization with custom config."""
        assert blog_builder_custom_config.brand.name == "Test Brand"
        assert blog_builder_custom_config.brand.colors.primary == "#FF0000"

    def test_build_blog_header(self, blog_builder) -> None:
        """Test building blog header section."""
        widgets = blog_builder.build_blog_header()

        assert len(widgets) == 4  # spacer, heading, text, spacer
        # Check heading widget
        heading = widgets[1]
        assert heading["widgetType"] == "heading"
        assert heading["settings"]["title"] == "Stories & Insights"
        assert heading["settings"]["header_size"] == "h1"
        # Check text widget
        text = widgets[2]
        assert text["widgetType"] == "text-editor"
        assert "SkyyRose journey" in text["settings"]["editor"]

    def test_build_blog_grid_default(self, blog_builder) -> None:
        """Test building blog grid with default posts_per_page."""
        widgets = blog_builder.build_blog_grid()

        assert len(widgets) == 1
        grid = widgets[0]
        assert grid["widgetType"] == "loop-grid"
        assert grid["settings"]["posts_per_page"] == "12"
        assert grid["settings"]["post_type"] == "post"
        assert grid["settings"]["columns"] == "3"
        assert grid["settings"]["paginate"] == "yes"

    def test_build_blog_grid_custom(self, blog_builder) -> None:
        """Test building blog grid with custom posts_per_page."""
        widgets = blog_builder.build_blog_grid(posts_per_page=24)

        assert widgets[0]["settings"]["posts_per_page"] == "24"

    def test_build_category_filter(self, blog_builder) -> None:
        """Test building category filter section."""
        widgets = blog_builder.build_category_filter()

        assert len(widgets) == 3  # spacer, filter, spacer
        filter_widget = widgets[1]
        assert filter_widget["widgetType"] == "loop-controls"
        assert filter_widget["settings"]["filter_by"] == "taxonomy"
        assert filter_widget["settings"]["taxonomy"] == "category"

    def test_configure_rankmath_schema(self, blog_builder) -> None:
        """Test RankMath SEO schema configuration."""
        schema = blog_builder.configure_rankmath_schema()

        assert schema["schema_type"] == "CollectionPage"
        assert schema["title"] == "Stories & Insights - SkyyRose Blog"
        assert schema["url"] == "/blog"
        assert "publisher" in schema
        assert schema["publisher"]["name"] == "SkyyRose"
        assert "post_schema" in schema
        assert schema["post_schema"]["type"] == "BlogPosting"

    def test_generate_blog_template(self, blog_builder) -> None:
        """Test generating complete blog page template."""
        template = blog_builder.generate(posts_per_page=6)

        assert template.title == "Blog"
        assert template.page_settings["hide_title"] == "yes"
        assert template.page_settings["template"] == "elementor_canvas"
        assert "Stories & Insights" in template.page_settings["post_title"]
        assert len(template.content) == 3  # header, filter, grid sections
        assert "rankmath_schema" in template.metadata

    def test_generate_template_json_export(self, blog_builder) -> None:
        """Test that generated template can be exported to JSON."""
        template = blog_builder.generate()
        json_str = template.to_json()

        # Verify it's valid JSON
        parsed = json.loads(json_str)
        assert parsed["title"] == "Blog"
        assert len(parsed["content"]) == 3


# =============================================================================
# Collection Experience Builder Tests
# =============================================================================


class TestCollectionExperienceBuilder:
    """Tests for CollectionExperienceBuilder class."""

    @pytest.fixture
    def collection_builder(self):
        """Create a CollectionExperienceBuilder instance."""
        from wordpress.page_builders.collection_experience_builder import (
            CollectionExperienceBuilder,
        )

        return CollectionExperienceBuilder()

    def test_init_default(self, collection_builder) -> None:
        """Test CollectionExperienceBuilder initialization."""
        assert collection_builder.brand is not None
        assert collection_builder.brand.name == "SkyyRose"

    def test_build_fullscreen_experience_iframe(self, collection_builder) -> None:
        """Test building fullscreen 3D experience embed."""
        from wordpress.collection_page_manager import CollectionType

        widgets = collection_builder.build_fullscreen_experience_iframe(
            collection_type=CollectionType.BLACK_ROSE,
            experience_url="https://skyyrose.com/3d/black-rose.html",
        )

        assert len(widgets) == 1
        video_widget = widgets[0]
        assert video_widget["widgetType"] == "video"
        assert video_widget["settings"]["hosted_url"] == "https://skyyrose.com/3d/black-rose.html"
        assert video_widget["settings"]["loop"] == "yes"

    def test_build_hotspot_product_cards(self, collection_builder) -> None:
        """Test building product hotspot cards."""
        from wordpress.collection_page_manager import CollectionType

        widgets = collection_builder.build_hotspot_product_cards(
            collection_type=CollectionType.LOVE_HURTS,
        )

        # Should have spacer, heading, spacer, hotspot viewer, spacer
        assert len(widgets) >= 4
        # Check heading
        heading = widgets[1]
        assert heading["widgetType"] == "heading"
        assert "Love Hurts" in heading["settings"]["title"]
        # Check hotspot viewer
        hotspot = widgets[3]
        assert hotspot["widgetType"] == "skyyrose-hotspot-viewer"
        assert hotspot["settings"]["collection_slug"] == "love_hurts"

    def test_build_scroll_camera_controller(self, collection_builder) -> None:
        """Test building scroll-based camera controller."""
        from wordpress.collection_page_manager import CollectionType

        widgets = collection_builder.build_scroll_camera_controller(
            collection_type=CollectionType.SIGNATURE,
        )

        assert len(widgets) == 1
        js_widget = widgets[0]
        assert js_widget["widgetType"] == "text-editor"
        assert "<script>" in js_widget["settings"]["editor"]
        assert "initScrollCamera" in js_widget["settings"]["editor"]
        assert "signature" in js_widget["settings"]["editor"]

    def test_generate_collection_experience_black_rose(self, collection_builder) -> None:
        """Test generating Black Rose collection experience page."""
        from wordpress.collection_page_manager import CollectionType

        template = collection_builder.generate(
            collection_type=CollectionType.BLACK_ROSE,
            experience_url="https://skyyrose.com/3d/black-rose.html",
        )

        assert template.title == "BLACK ROSE Garden"
        assert template.page_settings["template"] == "elementor_canvas"
        assert len(template.content) >= 4  # header, experience, hotspots, scroll, cta

    def test_generate_collection_experience_love_hurts(self, collection_builder) -> None:
        """Test generating Love Hurts collection experience page."""
        from wordpress.collection_page_manager import CollectionType

        template = collection_builder.generate(
            collection_type=CollectionType.LOVE_HURTS,
            experience_url="https://skyyrose.com/3d/love-hurts.html",
        )

        assert template.title == "LOVE HURTS Castle"
        assert "emotional" in template.page_settings["meta_description"].lower() or \
               "Emotional" in template.page_settings["meta_description"]

    def test_generate_collection_experience_signature(self, collection_builder) -> None:
        """Test generating Signature collection experience page."""
        from wordpress.collection_page_manager import CollectionType

        template = collection_builder.generate(
            collection_type=CollectionType.SIGNATURE,
            experience_url="https://skyyrose.com/3d/signature.html",
        )

        assert template.title == "SIGNATURE Runway"
        # Check CTA section exists
        cta_found = False
        for section in template.content:
            if section.get("elements"):
                for col in section["elements"]:
                    for el in col.get("elements", []):
                        if el.get("widgetType") == "button":
                            if "Browse Collection" in el.get("settings", {}).get("text", ""):
                                cta_found = True
        assert cta_found


# =============================================================================
# Product Builder Tests
# =============================================================================


class TestProductPageBuilder:
    """Tests for ProductPageBuilder class."""

    @pytest.fixture
    def product_builder(self):
        """Create a ProductPageBuilder instance."""
        from wordpress.page_builders.product_builder import ProductPageBuilder

        return ProductPageBuilder()

    def test_init_default(self, product_builder) -> None:
        """Test ProductPageBuilder initialization."""
        assert product_builder.brand is not None

    def test_build_3d_viewer_section(self, product_builder) -> None:
        """Test building 3D product viewer section."""
        widgets = product_builder.build_3d_viewer_section(
            product_id=123,
            glb_url="https://cdn.skyyrose.com/models/hoodie.glb",
            usdz_url="https://cdn.skyyrose.com/models/hoodie.usdz",
        )

        assert len(widgets) == 3  # spacer, viewer, spacer
        viewer = widgets[1]
        assert viewer["widgetType"] == "skyyrose-3d-viewer"
        assert viewer["settings"]["product_id"] == "123"
        assert viewer["settings"]["glb_url"] == "https://cdn.skyyrose.com/models/hoodie.glb"
        assert viewer["settings"]["usdz_url"] == "https://cdn.skyyrose.com/models/hoodie.usdz"
        assert viewer["settings"]["auto_rotate"] == "yes"
        assert viewer["settings"]["show_ar_button"] == "yes"

    def test_build_3d_viewer_section_no_usdz(self, product_builder) -> None:
        """Test building 3D viewer without USDZ."""
        widgets = product_builder.build_3d_viewer_section(
            product_id=456,
            glb_url="https://cdn.skyyrose.com/models/jacket.glb",
        )

        viewer = widgets[1]
        assert viewer["settings"]["usdz_url"] == ""

    def test_build_luxury_product_hero(self, product_builder) -> None:
        """Test building luxury 2-column product layout."""
        product = {
            "id": 123,
            "name": "Black Rose Hoodie",
            "price": "149.99",
        }

        section = product_builder.build_luxury_product_hero(product)

        assert section["elType"] == "section"
        assert section["settings"]["layout"] == "boxed"
        assert section["settings"]["gap"] == "extended"  # 48px luxury spacing
        # Check column structure
        assert len(section["elements"]) == 2  # 2 columns
        assert section["elements"][0]["settings"]["_column_size"] == 60  # Gallery column
        assert section["elements"][1]["settings"]["_column_size"] == 40  # Details column
        # Check product widgets in details column
        details_elements = section["elements"][1]["elements"]
        assert any(w["widgetType"] == "woocommerce-product-title" for w in details_elements)
        assert any(w["widgetType"] == "woocommerce-product-price" for w in details_elements)
        assert any(w["widgetType"] == "woocommerce-product-add-to-cart" for w in details_elements)
        # Check branded CTA text
        cart_btn = next(w for w in details_elements if w["widgetType"] == "woocommerce-product-add-to-cart")
        assert cart_btn["settings"]["button_text"] == "Claim Your Rose"

    def test_build_product_tabs(self, product_builder) -> None:
        """Test building product information tabs."""
        widgets = product_builder.build_product_tabs(product_id=123)

        assert len(widgets) == 2  # tabs widget, spacer
        tabs = widgets[0]
        assert tabs["widgetType"] == "tabs"
        assert len(tabs["settings"]["tabs"]) == 4
        tab_titles = [t["tab_title"] for t in tabs["settings"]["tabs"]]
        assert "Description" in tab_titles
        assert "Sizing Guide" in tab_titles
        assert "The Story" in tab_titles
        assert "Pre-Order" in tab_titles

    def test_build_preorder_countdown(self, product_builder) -> None:
        """Test building pre-order countdown timer."""
        widgets = product_builder.build_preorder_countdown(
            product_id=123,
            target_date="2025-03-01T00:00:00Z",
        )

        # Should have spacer, heading, spacer, countdown, spacer, form, spacer
        assert len(widgets) >= 6
        # Check heading
        heading = next(w for w in widgets if w.get("widgetType") == "heading")
        assert heading["settings"]["title"] == "Blooming Soon"
        # Check countdown
        countdown = next(w for w in widgets if w.get("widgetType") == "skyyrose-countdown")
        assert countdown["settings"]["target_date"] == "2025-03-01T00:00:00Z"
        assert countdown["settings"]["product_id"] == "123"
        # Check notification form
        form = next(w for w in widgets if w.get("widgetType") == "form")
        assert form["settings"]["form_name"] == "preorder_notify"
        assert form["settings"]["integration"] == "klaviyo"

    def test_build_ar_quick_look(self, product_builder) -> None:
        """Test building AR Quick Look button."""
        widgets = product_builder.build_ar_quick_look(
            product_id=123,
            usdz_url="https://cdn.skyyrose.com/models/hoodie.usdz",
        )

        assert len(widgets) == 2  # button, spacer
        ar_btn = widgets[0]
        assert ar_btn["widgetType"] == "skyyrose-ar-button"
        assert ar_btn["settings"]["usdz_url"] == "https://cdn.skyyrose.com/models/hoodie.usdz"
        assert ar_btn["settings"]["button_text"] == "View in AR"

    def test_build_limited_edition_badge(self, product_builder) -> None:
        """Test building limited edition badge."""
        widgets = product_builder.build_limited_edition_badge(
            edition_number=23,
            total_edition=50,
        )

        assert len(widgets) == 1
        badge = widgets[0]
        assert badge["widgetType"] == "image-box"
        assert "#23/50 LIMITED EDITION" in badge["settings"]["title"]
        assert "Exclusive piece" in badge["settings"]["description"]

    def test_generate_basic_product_page(self, product_builder) -> None:
        """Test generating basic product page template."""
        template = product_builder.generate(
            product_id=123,
            glb_url="https://cdn.skyyrose.com/models/hoodie.glb",
        )

        assert template.title == "Product 123"
        assert template.type == "single"
        assert template.page_settings["template"] == "elementor_header_footer"
        # Should have at least viewer and tabs sections
        assert len(template.content) >= 2

    def test_generate_product_page_with_preorder(self, product_builder) -> None:
        """Test generating product page with pre-order countdown."""
        template = product_builder.generate(
            product_id=456,
            glb_url="https://cdn.skyyrose.com/models/jacket.glb",
            target_date="2025-06-01T00:00:00Z",
        )

        # Should have viewer, tabs, and countdown sections
        assert len(template.content) >= 3

    def test_generate_product_page_with_ar(self, product_builder) -> None:
        """Test generating product page with AR button."""
        template = product_builder.generate(
            product_id=789,
            glb_url="https://cdn.skyyrose.com/models/tee.glb",
            usdz_url="https://cdn.skyyrose.com/models/tee.usdz",
        )

        # Should have viewer, tabs, and AR sections
        assert len(template.content) >= 3

    def test_generate_product_page_with_limited_edition(self, product_builder) -> None:
        """Test generating product page with limited edition badge."""
        template = product_builder.generate(
            product_id=999,
            glb_url="https://cdn.skyyrose.com/models/limited.glb",
            edition_number=5,
            total_edition=25,
        )

        # Should have viewer, badge, and tabs sections
        assert len(template.content) >= 3

    def test_generate_complete_product_page(self, product_builder) -> None:
        """Test generating product page with all features."""
        template = product_builder.generate(
            product_id=100,
            glb_url="https://cdn.skyyrose.com/models/premium.glb",
            usdz_url="https://cdn.skyyrose.com/models/premium.usdz",
            target_date="2025-12-01T00:00:00Z",
            edition_number=1,
            total_edition=10,
        )

        # Should have all sections
        assert len(template.content) >= 5


# =============================================================================
# Luxury Home Builder Tests
# =============================================================================


class TestLuxuryHomePageBuilder:
    """Tests for LuxuryHomePageBuilder class."""

    @pytest.fixture
    def home_builder(self):
        """Create a LuxuryHomePageBuilder instance."""
        # Need to patch ElementorPageBuilder since it doesn't exist
        from dataclasses import dataclass
        from unittest.mock import patch

        # Create a mock base class
        @dataclass
        class MockElementorPageBuilder:
            pass

        with patch.dict(
            "sys.modules",
            {"wordpress.elementor.ElementorPageBuilder": MockElementorPageBuilder},
        ):
            # Need to patch the import
            with patch(
                "wordpress.elementor.ElementorPageBuilder",
                MockElementorPageBuilder,
                create=True,
            ):
                from wordpress.page_builders.luxury_home_builder import (
                    LuxuryHomePageBuilder,
                )

                builder = LuxuryHomePageBuilder()
                builder.__post_init__()
                return builder

    def test_init_creates_gsap_builder(self, home_builder) -> None:
        """Test that initialization creates GSAP builder."""
        assert home_builder.gsap_builder is not None
        assert home_builder._animations == []

    def test_build_hero_section(self, home_builder) -> None:
        """Test building hero section with GSAP animations."""
        from wordpress.elementor import COLLECTION_BRAND_KITS

        brand_kit = COLLECTION_BRAND_KITS["signature"]
        section = home_builder.build_hero_section(brand_kit)

        assert section["elType"] == "section"
        assert section["settings"]["layout"] == "full_width"
        assert section["settings"]["height"] == "100vh"
        assert "background_video_link" in section["settings"]
        # Check CSS classes for GSAP
        assert "skyyrose-hero" in section["settings"]["_css_classes"]
        assert "glass-hero" in section["settings"]["_css_classes"]
        # Check animations were registered
        assert len(home_builder._animations) >= 3

    def test_build_collections_grid(self, home_builder) -> None:
        """Test building collections grid section."""
        section = home_builder.build_collections_grid()

        assert section["elType"] == "section"
        assert section["settings"]["layout"] == "boxed"
        assert section["settings"]["gap"] == "extended"  # 48px luxury spacing
        assert "collections-section" in section["settings"]["_css_classes"]
        # Check section title
        has_title = False
        for el in section["elements"]:
            if el.get("widgetType") == "heading":
                if el["settings"]["title"] == "The Collections":
                    has_title = True
        assert has_title

    def test_build_collection_card(self, home_builder) -> None:
        """Test building individual collection card."""
        card = home_builder._build_collection_card("signature", 0)

        assert card["elType"] == "container"
        assert "collection-card" in card["settings"]["_css_classes"]
        assert "glass-card" in card["settings"]["_css_classes"]
        assert "stagger-1" in card["settings"]["_css_classes"]
        # Check nested elements
        assert len(card["elements"]) >= 2  # image and overlay

    def test_build_collection_card_all_collections(self, home_builder) -> None:
        """Test building cards for all collections."""
        collections = ["signature", "love-hurts", "black-rose"]
        for idx, slug in enumerate(collections):
            card = home_builder._build_collection_card(slug, idx)
            assert f"stagger-{idx + 1}" in card["settings"]["_css_classes"]

    def test_build_parallax_section(self, home_builder) -> None:
        """Test building parallax showcase section."""
        section = home_builder.build_parallax_section()

        assert section["elType"] == "section"
        assert section["settings"]["layout"] == "full_width"
        assert "parallax-section" in section["settings"]["_css_classes"]
        # Check parallax layers
        parallax_layers = [
            el for el in section["elements"]
            if el.get("settings", {}).get("_css_classes", "")
            and "parallax-layer" in el["settings"]["_css_classes"]
        ]
        assert len(parallax_layers) >= 3  # back, mid, front

    def test_build_instagram_section(self, home_builder) -> None:
        """Test building Instagram feed section."""
        section = home_builder.build_instagram_section()

        assert section["elType"] == "section"
        # Check for Instagram shortcode
        has_shortcode = False
        for el in section["elements"]:
            if el.get("widgetType") == "shortcode":
                if "instagram-feed" in el["settings"].get("shortcode", ""):
                    has_shortcode = True
        assert has_shortcode

    def test_generate_complete_homepage(self, home_builder) -> None:
        """Test generating complete luxury homepage."""
        result = home_builder.generate()

        assert "content" in result
        assert "page_settings" in result
        assert len(result["content"]) >= 4  # hero, collections, parallax, instagram, scripts
        assert result["page_settings"]["template"] == "elementor_canvas"
        assert "SkyyRose" in result["page_settings"]["post_title"]
        # Check scripts section is appended
        scripts_section = result["content"][-1]
        assert "skyyrose-scripts" in scripts_section["settings"]["_element_id"]


# =============================================================================
# Integration Tests
# =============================================================================


class TestPageBuildersIntegration:
    """Integration tests for page builders working together."""

    def test_all_builders_use_consistent_brand_kit(self) -> None:
        """Test that all builders use consistent SkyyRose brand kit."""
        from wordpress.elementor import SKYYROSE_BRAND_KIT
        from wordpress.page_builders.blog_builder import BlogPageBuilder
        from wordpress.page_builders.collection_experience_builder import (
            CollectionExperienceBuilder,
        )
        from wordpress.page_builders.product_builder import ProductPageBuilder

        builders = [
            BlogPageBuilder(),
            CollectionExperienceBuilder(),
            ProductPageBuilder(),
        ]

        for builder in builders:
            assert builder.brand.name == SKYYROSE_BRAND_KIT.name
            assert builder.brand.colors.primary == SKYYROSE_BRAND_KIT.colors.primary

    def test_elementor_template_export_format(self) -> None:
        """Test that all templates export in valid Elementor format."""
        from wordpress.page_builders.blog_builder import BlogPageBuilder
        from wordpress.page_builders.product_builder import ProductPageBuilder

        blog_template = BlogPageBuilder().generate()
        product_template = ProductPageBuilder().generate(
            product_id=1,
            glb_url="https://example.com/model.glb",
        )

        for template in [blog_template, product_template]:
            json_str = template.to_json()
            parsed = json.loads(json_str)
            # Elementor template format requirements
            assert "version" in parsed
            assert "title" in parsed
            assert "type" in parsed
            assert "content" in parsed
            assert isinstance(parsed["content"], list)

    def test_widgets_have_unique_ids(self) -> None:
        """Test that generated widgets have unique IDs."""
        from wordpress.page_builders.product_builder import ProductPageBuilder

        builder = ProductPageBuilder()
        template = builder.generate(
            product_id=1,
            glb_url="https://example.com/model.glb",
            usdz_url="https://example.com/model.usdz",
            target_date="2025-01-01T00:00:00Z",
            edition_number=1,
            total_edition=10,
        )

        # Collect all widget IDs
        widget_ids = []

        def collect_ids(elements):
            for el in elements:
                if "id" in el:
                    widget_ids.append(el["id"])
                if "elements" in el:
                    collect_ids(el["elements"])

        collect_ids(template.content)

        # All IDs should be unique
        assert len(widget_ids) == len(set(widget_ids))


# =============================================================================
# Run tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
