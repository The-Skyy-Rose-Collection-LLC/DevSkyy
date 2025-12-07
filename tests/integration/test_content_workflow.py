"""
Integration Tests for Content Creation & Publishing Workflows
Comprehensive testing of content generation, optimization, and publishing

Test Coverage:
- Fashion product page generation
- Multi-language content creation
- Image processing and optimization
- WordPress integration flow
- WooCommerce product import
- Category assignment automation
- SEO optimization workflow
- Content review and approval
- Publishing and analytics

Per Truth Protocol:
- Rule #8: Test coverage ≥90%
- Rule #12: Performance SLOs (content generation < 2s)
- Rule #10: No-skip rule - all errors logged
"""

import asyncio
from datetime import datetime
import json
import logging
from pathlib import Path
import tempfile
import time
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agent.fashion_orchestrator import (
    FashionAssetType,
    AIModelProvider,
    ProductDescription,
    FashionOrchestrator,
)


logger = logging.getLogger(__name__)


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def fashion_product_context() -> dict[str, Any]:
    """Create fashion product context for testing."""
    return {
        "product_id": "prod_handbag_001",
        "product_type": FashionAssetType.HANDBAG,
        "brand": "The Skyy Rose Collection",
        "material": "Italian leather",
        "color": "Black",
        "dimensions": {"width": "30cm", "height": "20cm", "depth": "10cm"},
        "price": 299.99,
        "images": [
            "https://example.com/handbag_front.jpg",
            "https://example.com/handbag_side.jpg",
        ],
        "target_languages": ["en", "es", "fr"],
    }


@pytest.fixture
def mock_claude_content_generator():
    """Mock Claude API for content generation."""
    async def generate_content(prompt: str, **kwargs: Any) -> dict[str, Any]:
        return {
            "content": f"Elegant handbag from The Skyy Rose Collection. {prompt}",
            "model": "claude-3-5-sonnet-20241022",
            "tokens_used": 150,
        }

    return AsyncMock(side_effect=generate_content)


@pytest.fixture
def mock_wordpress_client():
    """Mock WordPress REST API client."""
    client = MagicMock()
    client.create_post = AsyncMock(return_value={"id": 12345, "link": "https://example.com/post/12345"})
    client.upload_media = AsyncMock(return_value={"id": 67890, "source_url": "https://example.com/media/67890.jpg"})
    client.create_category = AsyncMock(return_value={"id": 5, "name": "Handbags"})
    return client


@pytest.fixture
def mock_woocommerce_client():
    """Mock WooCommerce REST API client."""
    client = MagicMock()
    client.create_product = AsyncMock(
        return_value={
            "id": 9999,
            "name": "Elegant Handbag",
            "permalink": "https://example.com/product/elegant-handbag",
            "price": "299.99",
        }
    )
    return client


# ============================================================================
# CONTENT GENERATION TESTS
# ============================================================================


class TestContentGeneration:
    """Test content generation workflows."""

    @pytest.mark.asyncio
    async def test_generate_product_description(
        self,
        fashion_product_context: dict[str, Any],
        mock_claude_content_generator: AsyncMock,
    ):
        """Test generating product description using Claude."""
        orchestrator = FashionOrchestrator()

        with patch.object(orchestrator, "generate_content", mock_claude_content_generator):
            description = await orchestrator.generate_product_description(
                product_context=fashion_product_context,
                tone="elegant",
                length="medium",
            )

        assert description is not None
        assert "Elegant handbag" in description["content"]
        assert description["tokens_used"] > 0

    @pytest.mark.asyncio
    async def test_generate_seo_optimized_title(self, fashion_product_context: dict[str, Any]):
        """Test generating SEO-optimized product title."""
        orchestrator = FashionOrchestrator()

        title = await orchestrator.generate_seo_title(
            product_context=fashion_product_context,
            max_length=60,
        )

        assert title is not None
        assert len(title) <= 60
        assert "Handbag" in title or "handbag" in title.lower()
        assert fashion_product_context["brand"] in title

    @pytest.mark.asyncio
    async def test_generate_meta_description(self, fashion_product_context: dict[str, Any]):
        """Test generating SEO meta description."""
        orchestrator = FashionOrchestrator()

        meta_description = await orchestrator.generate_meta_description(
            product_context=fashion_product_context,
            max_length=160,
        )

        assert meta_description is not None
        assert len(meta_description) <= 160
        assert len(meta_description) >= 50  # Minimum for SEO

    @pytest.mark.asyncio
    async def test_generate_bullet_points(self, fashion_product_context: dict[str, Any]):
        """Test generating product feature bullet points."""
        orchestrator = FashionOrchestrator()

        bullet_points = await orchestrator.generate_feature_bullets(
            product_context=fashion_product_context,
            num_bullets=5,
        )

        assert len(bullet_points) == 5
        assert all(isinstance(point, str) for point in bullet_points)
        assert all(len(point) > 10 for point in bullet_points)

    @pytest.mark.asyncio
    async def test_generate_care_instructions(self, fashion_product_context: dict[str, Any]):
        """Test generating product care instructions."""
        orchestrator = FashionOrchestrator()

        care_instructions = await orchestrator.generate_care_instructions(
            product_context=fashion_product_context,
        )

        assert care_instructions is not None
        assert "leather" in care_instructions.lower()
        assert len(care_instructions) > 50

    @pytest.mark.asyncio
    async def test_generate_styling_suggestions(self, fashion_product_context: dict[str, Any]):
        """Test generating styling suggestions."""
        orchestrator = FashionOrchestrator()

        styling_suggestions = await orchestrator.generate_styling_suggestions(
            product_context=fashion_product_context,
            num_suggestions=3,
        )

        assert len(styling_suggestions) == 3
        assert all(isinstance(s, str) for s in styling_suggestions)

    @pytest.mark.asyncio
    async def test_content_generation_performance(self, fashion_product_context: dict[str, Any]):
        """Test content generation completes within 2 seconds."""
        orchestrator = FashionOrchestrator()

        start_time = time.time()
        description = await orchestrator.generate_product_description(
            product_context=fashion_product_context,
            tone="elegant",
        )
        execution_time = time.time() - start_time

        assert execution_time < 2.0, f"Content generation took {execution_time}s, exceeds 2s threshold"
        assert description is not None


# ============================================================================
# MULTI-LANGUAGE CONTENT TESTS
# ============================================================================


class TestMultiLanguageContent:
    """Test multi-language content generation."""

    @pytest.mark.asyncio
    async def test_generate_content_in_multiple_languages(
        self,
        fashion_product_context: dict[str, Any],
    ):
        """Test generating content in multiple languages."""
        orchestrator = FashionOrchestrator()

        languages = ["en", "es", "fr", "de"]
        translations = {}

        for lang in languages:
            content = await orchestrator.generate_product_description(
                product_context=fashion_product_context,
                language=lang,
            )
            translations[lang] = content

        assert len(translations) == 4
        assert all(lang in translations for lang in languages)
        assert all(translations[lang]["content"] for lang in languages)

    @pytest.mark.asyncio
    async def test_translation_consistency(self, fashion_product_context: dict[str, Any]):
        """Test translation maintains consistent messaging."""
        orchestrator = FashionOrchestrator()

        english_content = await orchestrator.generate_product_description(
            product_context=fashion_product_context,
            language="en",
        )

        spanish_content = await orchestrator.generate_product_description(
            product_context=fashion_product_context,
            language="es",
        )

        assert english_content is not None
        assert spanish_content is not None
        assert english_content["content"] != spanish_content["content"]

    @pytest.mark.asyncio
    async def test_localized_currency_formatting(self, fashion_product_context: dict[str, Any]):
        """Test currency formatting for different locales."""
        orchestrator = FashionOrchestrator()

        locales = {
            "en_US": "$299.99",
            "en_GB": "£249.99",
            "fr_FR": "279,99 €",
            "de_DE": "279,99 €",
        }

        for locale, expected_format_pattern in locales.items():
            formatted_price = orchestrator.format_price(
                price=fashion_product_context["price"],
                locale=locale,
            )

            assert formatted_price is not None
            assert any(char in formatted_price for char in ["$", "£", "€"])

    @pytest.mark.asyncio
    async def test_localized_size_measurements(self, fashion_product_context: dict[str, Any]):
        """Test size measurement localization (cm vs inches)."""
        orchestrator = FashionOrchestrator()

        metric_dimensions = orchestrator.format_dimensions(
            dimensions=fashion_product_context["dimensions"],
            unit_system="metric",
        )

        imperial_dimensions = orchestrator.format_dimensions(
            dimensions=fashion_product_context["dimensions"],
            unit_system="imperial",
        )

        assert "cm" in metric_dimensions
        assert "in" in imperial_dimensions or "inches" in imperial_dimensions.lower()


# ============================================================================
# SEO OPTIMIZATION TESTS
# ============================================================================


class TestSEOOptimization:
    """Test SEO optimization workflows."""

    @pytest.mark.asyncio
    async def test_extract_keywords(self, fashion_product_context: dict[str, Any]):
        """Test keyword extraction from product context."""
        orchestrator = FashionOrchestrator()

        keywords = await orchestrator.extract_seo_keywords(
            product_context=fashion_product_context,
            num_keywords=10,
        )

        assert len(keywords) <= 10
        assert "handbag" in [k.lower() for k in keywords]
        assert "leather" in [k.lower() for k in keywords]

    @pytest.mark.asyncio
    async def test_optimize_content_for_seo(self, fashion_product_context: dict[str, Any]):
        """Test SEO optimization of product content."""
        orchestrator = FashionOrchestrator()

        base_content = "Beautiful handbag made from high-quality materials."

        optimized_content = await orchestrator.optimize_for_seo(
            content=base_content,
            target_keywords=["Italian leather", "luxury handbag", "designer bag"],
        )

        assert len(optimized_content) > len(base_content)
        assert "Italian leather" in optimized_content or "italian leather" in optimized_content.lower()

    @pytest.mark.asyncio
    async def test_generate_structured_data(self, fashion_product_context: dict[str, Any]):
        """Test generating Schema.org structured data for SEO."""
        orchestrator = FashionOrchestrator()

        structured_data = orchestrator.generate_structured_data(
            product_context=fashion_product_context,
        )

        assert structured_data is not None
        assert structured_data["@type"] == "Product"
        assert "name" in structured_data
        assert "offers" in structured_data
        assert structured_data["offers"]["price"] == str(fashion_product_context["price"])

    @pytest.mark.asyncio
    async def test_generate_open_graph_metadata(self, fashion_product_context: dict[str, Any]):
        """Test generating Open Graph metadata for social sharing."""
        orchestrator = FashionOrchestrator()

        og_metadata = orchestrator.generate_open_graph_metadata(
            product_context=fashion_product_context,
        )

        assert "og:title" in og_metadata
        assert "og:description" in og_metadata
        assert "og:image" in og_metadata
        assert "og:type" in og_metadata
        assert og_metadata["og:type"] == "product"

    @pytest.mark.asyncio
    async def test_calculate_seo_score(self):
        """Test calculating SEO score for content."""
        orchestrator = FashionOrchestrator()

        content_data = {
            "title": "Elegant Italian Leather Handbag | The Skyy Rose Collection",
            "meta_description": "Discover our elegant Italian leather handbag, handcrafted with premium materials. Perfect for any occasion.",
            "content": "Long product description with relevant keywords...",
            "images": ["image1.jpg", "image2.jpg"],
            "alt_texts": ["Elegant handbag front view", "Handbag side view"],
        }

        seo_score = orchestrator.calculate_seo_score(content_data)

        assert 0 <= seo_score <= 100
        assert isinstance(seo_score, (int, float))


# ============================================================================
# IMAGE PROCESSING TESTS
# ============================================================================


class TestImageProcessing:
    """Test image processing and optimization."""

    @pytest.mark.asyncio
    async def test_optimize_product_image(self):
        """Test image optimization for web."""
        orchestrator = FashionOrchestrator()

        with tempfile.NamedTemporaryFile(suffix=".jpg") as temp_image:
            temp_path = Path(temp_image.name)

            optimized_path = await orchestrator.optimize_image(
                image_path=temp_path,
                target_width=1200,
                quality=85,
            )

            assert optimized_path is not None

    @pytest.mark.asyncio
    async def test_generate_image_variants(self):
        """Test generating multiple image size variants."""
        orchestrator = FashionOrchestrator()

        sizes = {
            "thumbnail": (150, 150),
            "medium": (600, 600),
            "large": (1200, 1200),
            "full": (2400, 2400),
        }

        with tempfile.NamedTemporaryFile(suffix=".jpg") as temp_image:
            temp_path = Path(temp_image.name)

            variants = await orchestrator.generate_image_variants(
                image_path=temp_path,
                sizes=sizes,
            )

            assert len(variants) == len(sizes)
            assert all(size_name in variants for size_name in sizes.keys())

    @pytest.mark.asyncio
    async def test_generate_alt_text(self, fashion_product_context: dict[str, Any]):
        """Test generating SEO-friendly alt text for images."""
        orchestrator = FashionOrchestrator()

        alt_text = await orchestrator.generate_image_alt_text(
            product_context=fashion_product_context,
            image_type="front_view",
        )

        assert alt_text is not None
        assert len(alt_text) > 10
        assert "handbag" in alt_text.lower()

    @pytest.mark.asyncio
    async def test_extract_dominant_colors(self):
        """Test extracting dominant colors from product image."""
        orchestrator = FashionOrchestrator()

        with tempfile.NamedTemporaryFile(suffix=".jpg") as temp_image:
            temp_path = Path(temp_image.name)

            colors = await orchestrator.extract_dominant_colors(
                image_path=temp_path,
                num_colors=5,
            )

            assert isinstance(colors, list)
            assert len(colors) <= 5


# ============================================================================
# WORDPRESS INTEGRATION TESTS
# ============================================================================


class TestWordPressIntegration:
    """Test WordPress content publishing workflow."""

    @pytest.mark.asyncio
    async def test_create_wordpress_post(
        self,
        fashion_product_context: dict[str, Any],
        mock_wordpress_client: MagicMock,
    ):
        """Test creating WordPress post."""
        orchestrator = FashionOrchestrator()
        orchestrator.wordpress_client = mock_wordpress_client

        post_data = {
            "title": "Elegant Italian Leather Handbag",
            "content": "Product description content...",
            "status": "draft",
            "categories": [5],
        }

        result = await orchestrator.create_wordpress_post(post_data)

        assert result is not None
        assert result["id"] == 12345
        assert "link" in result
        mock_wordpress_client.create_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_upload_images_to_wordpress(
        self,
        fashion_product_context: dict[str, Any],
        mock_wordpress_client: MagicMock,
    ):
        """Test uploading product images to WordPress media library."""
        orchestrator = FashionOrchestrator()
        orchestrator.wordpress_client = mock_wordpress_client

        image_urls = fashion_product_context["images"]

        uploaded_media = await orchestrator.upload_images_to_wordpress(image_urls)

        assert len(uploaded_media) == len(image_urls)
        assert mock_wordpress_client.upload_media.call_count == len(image_urls)

    @pytest.mark.asyncio
    async def test_create_wordpress_category(self, mock_wordpress_client: MagicMock):
        """Test creating WordPress category."""
        orchestrator = FashionOrchestrator()
        orchestrator.wordpress_client = mock_wordpress_client

        category_result = await orchestrator.create_wordpress_category(
            name="Handbags",
            slug="handbags",
            parent_id=None,
        )

        assert category_result is not None
        assert category_result["id"] == 5
        assert category_result["name"] == "Handbags"

    @pytest.mark.asyncio
    async def test_publish_wordpress_post(self, mock_wordpress_client: MagicMock):
        """Test publishing WordPress post (draft to published)."""
        orchestrator = FashionOrchestrator()
        orchestrator.wordpress_client = mock_wordpress_client

        mock_wordpress_client.update_post = AsyncMock(
            return_value={"id": 12345, "status": "publish"}
        )

        result = await orchestrator.publish_wordpress_post(post_id=12345)

        assert result["status"] == "publish"
        mock_wordpress_client.update_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_wordpress_category_hierarchy(self, mock_wordpress_client: MagicMock):
        """Test creating hierarchical WordPress categories."""
        orchestrator = FashionOrchestrator()
        orchestrator.wordpress_client = mock_wordpress_client

        parent_category = await orchestrator.create_wordpress_category(
            name="Accessories",
            slug="accessories",
        )

        mock_wordpress_client.create_category = AsyncMock(
            return_value={"id": 6, "name": "Handbags", "parent": 5}
        )

        child_category = await orchestrator.create_wordpress_category(
            name="Handbags",
            slug="handbags",
            parent_id=parent_category["id"],
        )

        assert child_category["parent"] == parent_category["id"]


# ============================================================================
# WOOCOMMERCE INTEGRATION TESTS
# ============================================================================


class TestWooCommerceIntegration:
    """Test WooCommerce product import workflow."""

    @pytest.mark.asyncio
    async def test_create_woocommerce_product(
        self,
        fashion_product_context: dict[str, Any],
        mock_woocommerce_client: MagicMock,
    ):
        """Test creating WooCommerce product."""
        orchestrator = FashionOrchestrator()
        orchestrator.woocommerce_client = mock_woocommerce_client

        product_data = {
            "name": "Elegant Italian Leather Handbag",
            "type": "simple",
            "regular_price": str(fashion_product_context["price"]),
            "description": "Product description...",
            "short_description": "Short description...",
            "categories": [{"id": 5}],
            "images": [{"src": url} for url in fashion_product_context["images"]],
        }

        result = await orchestrator.create_woocommerce_product(product_data)

        assert result is not None
        assert result["id"] == 9999
        assert result["name"] == "Elegant Handbag"
        mock_woocommerce_client.create_product.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_variable_product(
        self,
        fashion_product_context: dict[str, Any],
        mock_woocommerce_client: MagicMock,
    ):
        """Test creating WooCommerce variable product with variations."""
        orchestrator = FashionOrchestrator()
        orchestrator.woocommerce_client = mock_woocommerce_client

        mock_woocommerce_client.create_product = AsyncMock(
            return_value={
                "id": 10000,
                "name": "Leather Handbag",
                "type": "variable",
                "attributes": [
                    {"id": 1, "name": "Color", "options": ["Black", "Brown", "Red"]}
                ],
            }
        )

        product_data = {
            "name": "Leather Handbag",
            "type": "variable",
            "attributes": [
                {
                    "name": "Color",
                    "visible": True,
                    "variation": True,
                    "options": ["Black", "Brown", "Red"],
                }
            ],
        }

        result = await orchestrator.create_woocommerce_product(product_data)

        assert result["type"] == "variable"
        assert len(result["attributes"]) == 1

    @pytest.mark.asyncio
    async def test_set_product_stock_status(self, mock_woocommerce_client: MagicMock):
        """Test setting WooCommerce product stock status."""
        orchestrator = FashionOrchestrator()
        orchestrator.woocommerce_client = mock_woocommerce_client

        mock_woocommerce_client.update_product = AsyncMock(
            return_value={
                "id": 9999,
                "stock_status": "instock",
                "stock_quantity": 50,
            }
        )

        result = await orchestrator.update_product_stock(
            product_id=9999,
            stock_quantity=50,
            stock_status="instock",
        )

        assert result["stock_status"] == "instock"
        assert result["stock_quantity"] == 50

    @pytest.mark.asyncio
    async def test_bulk_product_import(
        self,
        fashion_product_context: dict[str, Any],
        mock_woocommerce_client: MagicMock,
    ):
        """Test bulk import of multiple products to WooCommerce."""
        orchestrator = FashionOrchestrator()
        orchestrator.woocommerce_client = mock_woocommerce_client

        products = [
            {**fashion_product_context, "product_id": f"prod_{i}"}
            for i in range(10)
        ]

        mock_woocommerce_client.create_product = AsyncMock(
            side_effect=[
                {"id": 9999 + i, "name": f"Product {i}"}
                for i in range(10)
            ]
        )

        results = await orchestrator.bulk_import_products(products)

        assert len(results) == 10
        assert all("id" in result for result in results)


# ============================================================================
# CONTENT REVIEW & APPROVAL TESTS
# ============================================================================


class TestContentReviewAndApproval:
    """Test content review and approval workflow."""

    @pytest.mark.asyncio
    async def test_submit_content_for_review(self, fashion_product_context: dict[str, Any]):
        """Test submitting generated content for review."""
        orchestrator = FashionOrchestrator()

        content_package = {
            "product_id": fashion_product_context["product_id"],
            "title": "Elegant Handbag",
            "description": "Product description...",
            "images": fashion_product_context["images"],
        }

        review_id = await orchestrator.submit_for_review(content_package)

        assert review_id is not None
        assert isinstance(review_id, str)

    @pytest.mark.asyncio
    async def test_approve_content(self):
        """Test approving reviewed content."""
        orchestrator = FashionOrchestrator()

        review_id = "review_001"

        approval_result = await orchestrator.approve_content(
            review_id=review_id,
            reviewer_id="reviewer_123",
            comments="Looks great!",
        )

        assert approval_result["status"] == "approved"
        assert approval_result["review_id"] == review_id

    @pytest.mark.asyncio
    async def test_request_content_changes(self):
        """Test requesting changes to content."""
        orchestrator = FashionOrchestrator()

        review_id = "review_002"

        change_request = await orchestrator.request_changes(
            review_id=review_id,
            reviewer_id="reviewer_123",
            requested_changes=[
                "Update product title to include brand name",
                "Add more details about material quality",
            ],
        )

        assert change_request["status"] == "changes_requested"
        assert len(change_request["requested_changes"]) == 2

    @pytest.mark.asyncio
    async def test_auto_approve_with_confidence_threshold(
        self,
        fashion_product_context: dict[str, Any],
    ):
        """Test automatic approval based on quality confidence score."""
        orchestrator = FashionOrchestrator()

        content_package = {
            "product_id": fashion_product_context["product_id"],
            "title": "Elegant Italian Leather Handbag",
            "description": "High-quality product description with all required elements...",
            "seo_score": 95,
            "quality_score": 0.96,
        }

        auto_approval = orchestrator.check_auto_approval_eligibility(
            content_package=content_package,
            quality_threshold=0.90,
        )

        assert auto_approval is True


# ============================================================================
# ANALYTICS & TRACKING TESTS
# ============================================================================


class TestAnalyticsAndTracking:
    """Test analytics and performance tracking."""

    @pytest.mark.asyncio
    async def test_track_content_performance(self):
        """Test tracking content performance metrics."""
        orchestrator = FashionOrchestrator()

        metrics = {
            "post_id": 12345,
            "views": 1500,
            "clicks": 120,
            "conversions": 15,
            "revenue": 4499.85,
        }

        await orchestrator.record_content_metrics(metrics)

        stored_metrics = orchestrator.get_content_metrics(post_id=12345)

        assert stored_metrics["views"] == 1500
        assert stored_metrics["conversions"] == 15

    @pytest.mark.asyncio
    async def test_calculate_conversion_rate(self):
        """Test calculating conversion rate for content."""
        orchestrator = FashionOrchestrator()

        metrics = {
            "views": 1000,
            "clicks": 100,
            "conversions": 10,
        }

        conversion_rate = orchestrator.calculate_conversion_rate(metrics)

        assert conversion_rate == 0.10  # 10%

    @pytest.mark.asyncio
    async def test_generate_content_performance_report(self):
        """Test generating performance report for published content."""
        orchestrator = FashionOrchestrator()

        date_range = {
            "start_date": datetime(2025, 1, 1),
            "end_date": datetime(2025, 1, 31),
        }

        report = await orchestrator.generate_performance_report(
            date_range=date_range,
            metrics=["views", "conversions", "revenue"],
        )

        assert report is not None
        assert "total_views" in report
        assert "total_conversions" in report
        assert "total_revenue" in report


# ============================================================================
# END-TO-END WORKFLOW TESTS
# ============================================================================


class TestEndToEndContentWorkflow:
    """Test complete end-to-end content workflow."""

    @pytest.mark.asyncio
    async def test_complete_product_publishing_workflow(
        self,
        fashion_product_context: dict[str, Any],
        mock_wordpress_client: MagicMock,
        mock_woocommerce_client: MagicMock,
    ):
        """Test complete workflow: generation → review → publish."""
        orchestrator = FashionOrchestrator()
        orchestrator.wordpress_client = mock_wordpress_client
        orchestrator.woocommerce_client = mock_woocommerce_client

        # Step 1: Generate content
        content = await orchestrator.generate_product_description(
            product_context=fashion_product_context,
            tone="elegant",
        )
        assert content is not None

        # Step 2: Generate SEO metadata
        seo_metadata = await orchestrator.generate_seo_metadata(
            product_context=fashion_product_context,
        )
        assert "title" in seo_metadata
        assert "meta_description" in seo_metadata

        # Step 3: Create WordPress post
        post_result = await orchestrator.create_wordpress_post({
            "title": seo_metadata["title"],
            "content": content["content"],
            "status": "draft",
        })
        assert post_result["id"] > 0

        # Step 4: Create WooCommerce product
        product_result = await orchestrator.create_woocommerce_product({
            "name": seo_metadata["title"],
            "regular_price": str(fashion_product_context["price"]),
            "description": content["content"],
        })
        assert product_result["id"] > 0

        # Step 5: Publish
        published_post = await orchestrator.publish_wordpress_post(post_result["id"])
        assert published_post["status"] == "publish"

    @pytest.mark.asyncio
    async def test_workflow_error_recovery(
        self,
        fashion_product_context: dict[str, Any],
        mock_wordpress_client: MagicMock,
    ):
        """Test workflow continues with error handling."""
        orchestrator = FashionOrchestrator()
        orchestrator.wordpress_client = mock_wordpress_client

        mock_wordpress_client.create_post = AsyncMock(
            side_effect=Exception("WordPress API error")
        )

        orchestrator.enable_error_ledger()

        try:
            await orchestrator.create_wordpress_post({
                "title": "Test Post",
                "content": "Test content",
            })
        except Exception:
            pass

        error_ledger = orchestrator.get_error_ledger()
        assert len(error_ledger) > 0
        assert any("WordPress API error" in str(err) for err in error_ledger)

    @pytest.mark.asyncio
    async def test_workflow_performance_end_to_end(
        self,
        fashion_product_context: dict[str, Any],
    ):
        """Test complete workflow completes within 5 seconds."""
        orchestrator = FashionOrchestrator()

        start_time = time.time()

        await orchestrator.generate_product_description(
            product_context=fashion_product_context,
            tone="elegant",
        )
        await orchestrator.generate_seo_metadata(
            product_context=fashion_product_context,
        )

        total_time = time.time() - start_time

        assert total_time < 5.0, f"Workflow took {total_time}s, exceeds 5s threshold"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
