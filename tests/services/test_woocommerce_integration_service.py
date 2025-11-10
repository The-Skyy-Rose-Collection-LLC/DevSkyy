"""
Tests for WooCommerce Integration Service (Phase 3)

WHY: Ensure SEO auto-generation and WooCommerce integration works correctly
HOW: Unit and integration tests with mocked AI and API calls
IMPACT: 90%+ test coverage for Phase 3 implementation

Truth Protocol: All edge cases tested, no placeholders
"""

import pytest
import json
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from services.woocommerce_integration_service import (
    WooCommerceIntegrationService,
    ProductData,
    ProductWithSEOResponse,
    SEOCompliance,
    get_integration_service
)
from services.seo_optimizer import SEOMetaTags, SEOOptimizerError


@pytest.fixture
def mock_seo_service():
    """Mock SEO optimizer service"""
    service = Mock()
    service.generate_seo_tags = AsyncMock(
        return_value=SEOMetaTags(
            metatitle="Premium Leather Jacket - Luxury Style",
            metadescription="Discover our premium leather jacket collection. High-quality craftsmanship, timeless design, and exceptional comfort. Shop now for exclusive deals."
        )
    )
    return service


@pytest.fixture
def integration_service(mock_seo_service):
    """Create integration service instance"""
    return WooCommerceIntegrationService(
        store_url="https://shop.example.com",
        consumer_key="ck_test_key",
        consumer_secret="cs_test_secret",
        seo_service=mock_seo_service
    )


@pytest.fixture
def sample_product_data():
    """Sample product data for testing"""
    return ProductData(
        name="Premium Leather Jacket",
        description="High-quality leather jacket with premium craftsmanship",
        short_description="Premium leather jacket",
        category="Outerwear",
        price=299.99,
        regular_price=399.99,
        sku="PLJ-001",
        stock_quantity=10,
        images=["https://example.com/jacket.jpg"],
        keywords="leather jacket, premium outerwear, fashion"
    )


class TestSchemaMarkupGeneration:
    """Test Schema.org markup generation"""

    def test_generate_schema_markup(self, integration_service, sample_product_data):
        """Test basic schema markup generation"""
        seo_tags = SEOMetaTags(
            metatitle="Test Product",
            metadescription="Test description"
        )

        schema = integration_service._generate_schema_markup(sample_product_data, seo_tags)

        assert schema["@context"] == "https://schema.org/"
        assert schema["@type"] == "Product"
        assert schema["name"] == sample_product_data.name
        assert schema["description"] == seo_tags.metadescription
        assert schema["sku"] == sample_product_data.sku
        assert schema["image"] == sample_product_data.images[0]
        assert schema["category"] == sample_product_data.category
        assert float(schema["offers"]["price"]) == sample_product_data.price
        assert schema["offers"]["priceCurrency"] == "USD"

    def test_schema_markup_without_optional_fields(self, integration_service):
        """Test schema markup with minimal product data"""
        product_data = ProductData(
            name="Simple Product",
            description="Simple description",
            category="General",
            price=99.99
        )
        seo_tags = SEOMetaTags(
            metatitle="Simple Product",
            metadescription="Simple description"
        )

        schema = integration_service._generate_schema_markup(product_data, seo_tags)

        assert "sku" not in schema
        assert "image" not in schema
        assert schema["offers"]["price"] == "99.99"

    def test_schema_markup_json_serializable(self, integration_service, sample_product_data):
        """Test that schema markup is valid JSON"""
        seo_tags = SEOMetaTags(
            metatitle="Test",
            metadescription="Test description"
        )

        schema = integration_service._generate_schema_markup(sample_product_data, seo_tags)

        # Should not raise exception
        json_str = json.dumps(schema)
        assert json_str
        assert isinstance(json_str, str)


class TestSEOComplianceValidation:
    """Test SEO compliance validation logic"""

    def test_validate_compliant_seo(self, integration_service):
        """Test validation of fully compliant SEO"""
        seo_tags = SEOMetaTags(
            metatitle="Premium Leather Jacket - Shop Now",  # 37 chars (30-60 OK)
            metadescription="Discover our premium leather jacket collection. High-quality craftsmanship, timeless design, and exceptional comfort. Shop now for deals."  # 147 chars (120-160 OK)
        )
        schema = {"@type": "Product", "name": "Test"}
        keywords = "leather jacket, fashion"

        compliance = integration_service._validate_seo_compliance(seo_tags, schema, keywords)

        assert compliance.title_length_valid
        assert compliance.description_length_valid
        assert compliance.schema_markup_present
        assert compliance.schema_markup_valid
        assert compliance.focus_keywords_present
        assert compliance.seo_score == 100
        assert compliance.is_compliant
        assert len(compliance.issues) == 0

    def test_validate_title_too_short(self, integration_service):
        """Test validation with title too short"""
        seo_tags = SEOMetaTags(
            metatitle="Short Title",  # 11 chars (< 30)
            metadescription="A" * 140  # Valid length
        )
        schema = {"@type": "Product"}
        keywords = "test"

        compliance = integration_service._validate_seo_compliance(seo_tags, schema, keywords)

        assert not compliance.title_length_valid
        assert "Title too short" in compliance.issues[0]
        assert compliance.seo_score < 100
        assert not compliance.is_compliant

    def test_validate_title_too_long(self, integration_service):
        """Test validation with title too long"""
        seo_tags = SEOMetaTags(
            metatitle="A" * 61,  # 61 chars (> 60)
            metadescription="A" * 140
        )
        schema = {"@type": "Product"}
        keywords = "test"

        compliance = integration_service._validate_seo_compliance(seo_tags, schema, keywords)

        assert not compliance.title_length_valid
        assert "Title too long" in compliance.issues[0]
        assert not compliance.is_compliant

    def test_validate_description_too_short(self, integration_service):
        """Test validation with description too short"""
        seo_tags = SEOMetaTags(
            metatitle="A" * 40,  # Valid
            metadescription="Short description"  # < 120 chars
        )
        schema = {"@type": "Product"}
        keywords = "test"

        compliance = integration_service._validate_seo_compliance(seo_tags, schema, keywords)

        assert not compliance.description_length_valid
        assert "Description too short" in compliance.issues[0]
        assert not compliance.is_compliant

    def test_validate_description_too_long(self, integration_service):
        """Test validation with description too long"""
        seo_tags = SEOMetaTags(
            metatitle="A" * 40,
            metadescription="A" * 161  # > 160 chars
        )
        schema = {"@type": "Product"}
        keywords = "test"

        compliance = integration_service._validate_seo_compliance(seo_tags, schema, keywords)

        assert not compliance.description_length_valid
        assert "Description too long" in compliance.issues[0]

    def test_validate_missing_schema_markup(self, integration_service):
        """Test validation with missing schema markup"""
        seo_tags = SEOMetaTags(
            metatitle="A" * 40,
            metadescription="A" * 140
        )
        schema = {}
        keywords = "test"

        compliance = integration_service._validate_seo_compliance(seo_tags, schema, keywords)

        assert not compliance.schema_markup_present
        assert "Schema markup is missing" in compliance.issues
        assert not compliance.is_compliant

    def test_validate_missing_keywords(self, integration_service):
        """Test validation with missing keywords"""
        seo_tags = SEOMetaTags(
            metatitle="A" * 40,
            metadescription="A" * 140
        )
        schema = {"@type": "Product"}
        keywords = None

        compliance = integration_service._validate_seo_compliance(seo_tags, schema, keywords)

        assert not compliance.focus_keywords_present
        assert "Focus keywords are missing" in compliance.issues
        assert not compliance.is_compliant

    def test_validate_empty_keywords(self, integration_service):
        """Test validation with empty keywords string"""
        seo_tags = SEOMetaTags(
            metatitle="A" * 40,
            metadescription="A" * 140
        )
        schema = {"@type": "Product"}
        keywords = "   "  # Whitespace only

        compliance = integration_service._validate_seo_compliance(seo_tags, schema, keywords)

        assert not compliance.focus_keywords_present

    def test_seo_score_calculation(self, integration_service):
        """Test SEO score calculation with various compliance levels"""
        seo_tags = SEOMetaTags(
            metatitle="A" * 40,  # Valid (30 points)
            metadescription="Short"  # Invalid (0 points)
        )
        schema = {"@type": "Product"}  # Valid (20 points)
        keywords = "test"  # Valid (20 points)

        compliance = integration_service._validate_seo_compliance(seo_tags, schema, keywords)

        assert compliance.seo_score == 70  # 30 + 0 + 20 + 20


class TestYoastMetadataFormatting:
    """Test Yoast SEO field formatting"""

    def test_generate_yoast_metadata(self, integration_service):
        """Test Yoast metadata generation"""
        seo_tags = SEOMetaTags(
            metatitle="Test Product Title",
            metadescription="Test product description"
        )
        schema = {"@type": "Product", "name": "Test"}
        keywords = "test, product, keywords"
        seo_score = 85

        yoast_data = integration_service._generate_yoast_metadata(
            seo_tags, schema, keywords, seo_score
        )

        assert len(yoast_data) == 5
        assert yoast_data[0]["key"] == "_yoast_wpseo_title"
        assert yoast_data[0]["value"] == seo_tags.metatitle
        assert yoast_data[1]["key"] == "_yoast_wpseo_metadesc"
        assert yoast_data[1]["value"] == seo_tags.metadescription
        assert yoast_data[2]["key"] == "_yoast_wpseo_focuskw"
        assert yoast_data[2]["value"] == keywords
        assert yoast_data[3]["key"] == "_yoast_wpseo_linkdex"
        assert yoast_data[3]["value"] == "85"
        assert yoast_data[4]["key"] == "_product_schema_markup"

        # Verify schema is valid JSON
        schema_value = json.loads(yoast_data[4]["value"])
        assert schema_value["@type"] == "Product"

    def test_generate_yoast_metadata_without_keywords(self, integration_service):
        """Test Yoast metadata generation without keywords"""
        seo_tags = SEOMetaTags(
            metatitle="Test",
            metadescription="Test description"
        )
        schema = {"@type": "Product"}

        yoast_data = integration_service._generate_yoast_metadata(
            seo_tags, schema, None, 50
        )

        focus_kw_field = next(f for f in yoast_data if f["key"] == "_yoast_wpseo_focuskw")
        assert focus_kw_field["value"] == ""


class TestFallbackMetadata:
    """Test fallback metadata generation"""

    def test_generate_fallback_metadata(self, integration_service, sample_product_data):
        """Test fallback metadata generation"""
        fallback = integration_service._generate_fallback_metadata(sample_product_data)

        assert "metatitle" in fallback
        assert "metadescription" in fallback
        assert "schema" in fallback
        assert "keywords" in fallback

        # Verify length constraints
        assert 30 <= len(fallback["metatitle"]) <= 60
        assert 120 <= len(fallback["metadescription"]) <= 160

        # Verify schema structure
        assert fallback["schema"]["@type"] == "Product"
        assert fallback["schema"]["name"] == sample_product_data.name

    def test_fallback_title_truncation(self, integration_service):
        """Test fallback title truncation for long names"""
        long_name = "A" * 100
        product_data = ProductData(
            name=long_name,
            description="Description",
            category="Category",
            price=99.99
        )

        fallback = integration_service._generate_fallback_metadata(product_data)

        assert len(fallback["metatitle"]) <= 60

    def test_fallback_description_padding(self, integration_service):
        """Test fallback description padding for short descriptions"""
        product_data = ProductData(
            name="Short Product",
            description="Short",
            short_description="Short",
            category="Category",
            price=99.99
        )

        fallback = integration_service._generate_fallback_metadata(product_data)

        # Should be padded to meet minimum length
        assert len(fallback["metadescription"]) >= 120


class TestCreateProductWithSEO:
    """Test product creation with SEO"""

    @pytest.mark.asyncio
    async def test_create_product_success(self, integration_service, sample_product_data):
        """Test successful product creation with SEO"""
        with patch('httpx.AsyncClient') as mock_client:
            # Mock WooCommerce API response
            mock_response = Mock()
            mock_response.status_code = 201
            mock_response.json.return_value = {
                "id": 123,
                "permalink": "https://shop.example.com/product/test"
            }
            mock_response.raise_for_status = Mock()

            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await integration_service.create_product_with_seo(sample_product_data)

            assert result.success
            assert result.product_id == 123
            assert result.product_url == "https://shop.example.com/product/test"
            assert result.seo_metadata is not None
            assert result.compliance is not None
            assert not result.fallback_used

    @pytest.mark.asyncio
    async def test_create_product_with_seo_failure_fallback(
        self, integration_service, sample_product_data, mock_seo_service
    ):
        """Test product creation with SEO service failure (uses fallback)"""
        # Make SEO service fail
        mock_seo_service.generate_seo_tags.side_effect = SEOOptimizerError("AI service failed")

        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 201
            mock_response.json.return_value = {"id": 124, "permalink": "https://example.com"}
            mock_response.raise_for_status = Mock()

            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await integration_service.create_product_with_seo(sample_product_data)

            assert result.success
            assert result.fallback_used
            assert result.seo_metadata is not None

    @pytest.mark.asyncio
    async def test_create_product_woocommerce_api_error(
        self, integration_service, sample_product_data
    ):
        """Test product creation with WooCommerce API error"""
        with patch('httpx.AsyncClient') as mock_client:
            from httpx import HTTPStatusError, Request, Response

            mock_response = Response(
                status_code=400,
                content=b"Bad request",
                request=Request("POST", "https://example.com")
            )

            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=HTTPStatusError(
                    "Bad request",
                    request=mock_response.request,
                    response=mock_response
                )
            )

            result = await integration_service.create_product_with_seo(sample_product_data)

            assert not result.success
            assert result.error is not None
            assert "WooCommerce API error" in result.error


class TestUpdateProductSEO:
    """Test product SEO update"""

    @pytest.mark.asyncio
    async def test_update_product_seo_success(self, integration_service, sample_product_data):
        """Test successful SEO update"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "id": 123,
                "permalink": "https://shop.example.com/product/test"
            }
            mock_response.raise_for_status = Mock()

            mock_client.return_value.__aenter__.return_value.put = AsyncMock(
                return_value=mock_response
            )

            result = await integration_service.update_product_seo(123, sample_product_data)

            assert result.success
            assert result.product_id == 123
            assert result.seo_metadata is not None
            assert result.compliance is not None

    @pytest.mark.asyncio
    async def test_update_product_seo_with_fallback(
        self, integration_service, sample_product_data, mock_seo_service
    ):
        """Test SEO update with fallback"""
        mock_seo_service.generate_seo_tags.side_effect = SEOOptimizerError("Failed")

        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"id": 123, "permalink": "https://example.com"}
            mock_response.raise_for_status = Mock()

            mock_client.return_value.__aenter__.return_value.put = AsyncMock(
                return_value=mock_response
            )

            result = await integration_service.update_product_seo(123, sample_product_data)

            assert result.success
            assert result.fallback_used


class TestFactoryFunction:
    """Test factory function"""

    def test_get_integration_service(self, mock_seo_service):
        """Test factory function creates service correctly"""
        service = get_integration_service(
            store_url="https://shop.example.com",
            consumer_key="ck_test",
            consumer_secret="cs_test",
            seo_service=mock_seo_service
        )

        assert isinstance(service, WooCommerceIntegrationService)
        assert service.store_url == "https://shop.example.com"
        assert service.api_url == "https://shop.example.com/wp-json/wc/v3"


class TestCharacterLimitConstants:
    """Test character limit constants"""

    def test_character_limits(self, integration_service):
        """Verify character limit constants match Yoast/Google standards"""
        assert integration_service.TITLE_MIN_LENGTH == 30
        assert integration_service.TITLE_MAX_LENGTH == 60
        assert integration_service.DESC_MIN_LENGTH == 120
        assert integration_service.DESC_MAX_LENGTH == 160

    def test_yoast_field_names(self, integration_service):
        """Verify Yoast field names are correct"""
        assert integration_service.YOAST_TITLE_FIELD == "_yoast_wpseo_title"
        assert integration_service.YOAST_DESC_FIELD == "_yoast_wpseo_metadesc"
        assert integration_service.YOAST_FOCUS_KW_FIELD == "_yoast_wpseo_focuskw"
        assert integration_service.YOAST_LINKDEX_FIELD == "_yoast_wpseo_linkdex"
        assert integration_service.SCHEMA_MARKUP_FIELD == "_product_schema_markup"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
