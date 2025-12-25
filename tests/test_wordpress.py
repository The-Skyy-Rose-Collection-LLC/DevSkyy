"""
Tests for wordpress module
==========================

WordPress, Elementor, and WooCommerce tests.
"""

import json

from wordpress import BrandKit, ElementorBuilder, PageSpec, ProductCreate, WordPressConfig
from wordpress.elementor import SKYYROSE_BRAND_KIT, PageType, generate_template


class TestWordPressClient:
    """Test WordPress client."""

    def test_config_from_env(self):
        """Should create config from environment."""
        config = WordPressConfig.from_env()

        assert config.api_version == "wp/v2"
        assert config.timeout == 30.0

    def test_base_url(self):
        """Should construct base URL."""
        config = WordPressConfig(site_url="https://example.com")

        assert config.base_url == "https://example.com/wp-json/wp/v2"


class TestBrandKit:
    """Test BrandKit design tokens."""

    def test_default_brand_kit(self):
        """Should have default brand kit."""
        kit = SKYYROSE_BRAND_KIT

        assert kit.name == "SkyyRose"
        assert kit.colors.primary == "#D4AF37"  # Rose gold
        assert kit.voice.tagline == "Where Love Meets Luxury"

    def test_custom_brand_kit(self):
        """Should allow custom brand kit."""
        from wordpress.elementor import BrandColors, BrandVoice

        kit = BrandKit(
            name="CustomBrand",
            colors=BrandColors(primary="#FF0000"),
            voice=BrandVoice(tagline="Custom tagline"),
        )

        assert kit.name == "CustomBrand"
        assert kit.colors.primary == "#FF0000"

    def test_css_vars_export(self):
        """Should export CSS variables."""
        kit = SKYYROSE_BRAND_KIT
        css_vars = kit.to_css_vars()

        assert "--color-primary" in css_vars
        assert css_vars["--color-primary"] == "#D4AF37"

    def test_elementor_globals_export(self):
        """Should export Elementor globals."""
        kit = SKYYROSE_BRAND_KIT
        globals_ = kit.to_elementor_globals()

        assert "colors" in globals_
        assert "typography" in globals_
        assert len(globals_["colors"]) >= 4


class TestPageSpec:
    """Test PageSpec model."""

    def test_create_page_spec(self):
        """Should create page spec."""
        spec = PageSpec(
            page_type=PageType.HOME,
            title="Home",
            slug="home",
            hero_title="Welcome",
            hero_subtitle="To our store",
        )

        assert spec.page_type == PageType.HOME
        assert spec.hero_enabled is True

    def test_page_spec_to_dict(self):
        """Should convert to dict."""
        spec = PageSpec(
            page_type=PageType.COLLECTION,
            title="Black Rose",
            slug="black-rose",
        )

        data = spec.to_dict()

        assert data["page_type"] == "collection"
        assert data["slug"] == "black-rose"


class TestElementorBuilder:
    """Test Elementor template builder."""

    def test_create_builder(self):
        """Should create builder."""
        builder = ElementorBuilder()

        assert builder.brand.name == "SkyyRose"

    def test_heading_widget(self):
        """Should create heading widget."""
        builder = ElementorBuilder()
        widget = builder.heading("Test Heading", size="xl")

        assert widget["widgetType"] == "heading"
        assert widget["settings"]["title"] == "Test Heading"

    def test_button_widget(self):
        """Should create button widget."""
        builder = ElementorBuilder()
        widget = builder.button("Shop Now", "/shop")

        assert widget["widgetType"] == "button"
        assert widget["settings"]["text"] == "Shop Now"
        assert widget["settings"]["link"]["url"] == "/shop"

    def test_products_grid_widget(self):
        """Should create products grid widget."""
        builder = ElementorBuilder()
        widget = builder.products_grid(columns=4, rows=2)

        assert widget["widgetType"] == "woocommerce-products"
        assert widget["settings"]["columns"] == "4"

    def test_generate_home_page(self):
        """Should generate home page template."""
        builder = ElementorBuilder()
        template = builder.generate_home_page(
            hero_title="SkyyRose",
            hero_subtitle="Where Love Meets Luxury",
        )

        assert template.title == "Home"
        assert len(template.content) >= 1  # At least hero section

    def test_generate_collection_page(self):
        """Should generate collection page template."""
        builder = ElementorBuilder()
        template = builder.generate_collection_page(
            title="Black Rose Collection",
            description="Limited edition pieces",
        )

        assert template.title == "Black Rose Collection"

    def test_template_json_export(self):
        """Should export valid JSON."""
        builder = ElementorBuilder()
        template = builder.generate_home_page(hero_title="Test")

        json_str = template.to_json()
        parsed = json.loads(json_str)

        assert "version" in parsed
        assert "content" in parsed
        assert isinstance(parsed["content"], list)


class TestGenerateTemplate:
    """Test template generation helper."""

    def test_generate_home_template(self):
        """Should generate home template from spec."""
        spec = PageSpec(
            page_type=PageType.HOME,
            title="Home",
            slug="home",
            hero_title="Welcome",
        )

        template = generate_template(spec)

        assert template.title == "Home"

    def test_generate_collection_template(self):
        """Should generate collection template from spec."""
        spec = PageSpec(
            page_type=PageType.COLLECTION,
            title="New Arrivals",
            slug="new-arrivals",
        )

        template = generate_template(spec)

        assert template.title == "New Arrivals"


class TestWooCommerceProducts:
    """Test WooCommerce products client."""

    def test_product_create_model(self):
        """Should create product model."""
        product = ProductCreate(
            name="Test Hoodie",
            regular_price="99.99",
            status="draft",
            sku="TEST-001",
        )

        assert product.name == "Test Hoodie"
        assert product.regular_price == "99.99"
        assert product.type == "simple"

    def test_product_with_categories(self):
        """Should support categories."""
        product = ProductCreate(
            name="Test Product",
            regular_price="50.00",
            categories=[{"id": 15}, {"id": 20}],
        )

        assert len(product.categories) == 2

    def test_product_model_dump(self):
        """Should serialize for API."""
        product = ProductCreate(
            name="Test",
            regular_price="10.00",
        )

        data = product.model_dump(exclude_none=True)

        assert "name" in data
        assert "regular_price" in data
        assert "stock_quantity" not in data  # None excluded
