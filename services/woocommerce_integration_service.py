"""
WooCommerce + SEO Integration Service (Phase 3)

WHY: Automatically generate and sync SEO metadata to WooCommerce products on creation/update
HOW: Integrate SEO optimizer with WooCommerce API, format for Yoast SEO fields
IMPACT: 100% of products have optimized SEO metadata from creation, improving organic visibility

Truth Protocol: Character limits enforced, Yoast field validation, fallback on SEO failure
Version: 1.0.0
"""

from datetime import datetime
import json
import logging
from typing import Optional

import httpx
from pydantic import BaseModel, Field

from services.seo_optimizer import ProductInfo, SEOMetaTags, SEOOptimizerError, SEOOptimizerService


logger = logging.getLogger(__name__)


class ProductData(BaseModel):
    """Product data for WooCommerce creation"""

    name: str = Field(..., min_length=1, max_length=200, description="Product name")
    description: str = Field(default="", description="Full product description")
    short_description: str = Field(default="", description="Short product description")
    category: str = Field(default="", description="Product category")
    price: float = Field(..., gt=0, description="Product price")
    regular_price: Optional[float] = Field(None, description="Regular price (before sale)")
    sku: Optional[str] = Field(None, description="Stock Keeping Unit")
    stock_quantity: Optional[int] = Field(None, ge=0, description="Stock quantity")
    images: list[str] = Field(default_factory=list, description="Image URLs")
    keywords: Optional[str] = Field(None, description="Target keywords for SEO")


class SEOCompliance(BaseModel):
    """SEO compliance report"""

    title_length_valid: bool = Field(..., description="Title is 30-60 characters")
    title_length: int = Field(..., description="Actual title length")
    description_length_valid: bool = Field(..., description="Description is 120-160 characters")
    description_length: int = Field(..., description="Actual description length")
    schema_markup_present: bool = Field(..., description="Schema markup exists")
    schema_markup_valid: bool = Field(..., description="Schema markup is valid JSON")
    focus_keywords_present: bool = Field(..., description="Focus keywords are not empty")
    seo_score: int = Field(..., ge=0, le=100, description="Overall SEO score")
    issues: list[str] = Field(default_factory=list, description="List of compliance issues")

    @property
    def is_compliant(self) -> bool:
        """Returns True if all validations pass"""
        return (
            self.title_length_valid
            and self.description_length_valid
            and self.schema_markup_present
            and self.schema_markup_valid
            and self.focus_keywords_present
        )


class ProductWithSEOResponse(BaseModel):
    """Response from product creation with SEO"""

    success: bool
    product_id: Optional[int] = None
    product_url: Optional[str] = None
    seo_metadata: Optional[dict] = None
    compliance: Optional[SEOCompliance] = None
    fallback_used: bool = False
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class WooCommerceIntegrationService:
    """
    Unified WooCommerce + SEO Integration Service

    Features:
    - Automatic SEO metadata generation on product creation
    - Yoast SEO field mapping (_yoast_wpseo_*)
    - Character limit validation (60/160)
    - Schema markup (JSON-LD)
    - SEO compliance checking
    - Graceful fallback on SEO service failure
    """

    # Yoast SEO field names (WordPress meta keys)
    YOAST_TITLE_FIELD = "_yoast_wpseo_title"
    YOAST_DESC_FIELD = "_yoast_wpseo_metadesc"
    YOAST_FOCUS_KW_FIELD = "_yoast_wpseo_focuskw"
    YOAST_LINKDEX_FIELD = "_yoast_wpseo_linkdex"
    SCHEMA_MARKUP_FIELD = "_product_schema_markup"

    # Character limits (Yoast/Google standards)
    TITLE_MIN_LENGTH = 30
    TITLE_MAX_LENGTH = 60
    DESC_MIN_LENGTH = 120
    DESC_MAX_LENGTH = 160

    def __init__(self, store_url: str, consumer_key: str, consumer_secret: str, seo_service: SEOOptimizerService):
        """
        Initialize WooCommerce integration service

        Args:
            store_url: WooCommerce store URL (e.g., https://shop.example.com)
            consumer_key: WooCommerce REST API consumer key
            consumer_secret: WooCommerce REST API consumer secret
            seo_service: Initialized SEO optimizer service
        """
        self.store_url = store_url.rstrip("/")
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.api_url = f"{self.store_url}/wp-json/wc/v3"
        self.seo_service = seo_service

        logger.info("WooCommerceIntegrationService initialized", extra={"store_url": self.store_url})

    def _generate_schema_markup(self, product_data: ProductData, seo_tags: SEOMetaTags) -> dict:
        """
        Generate Product Schema markup (JSON-LD)

        Args:
            product_data: Product information
            seo_tags: Generated SEO tags

        Returns:
            Schema.org Product markup dictionary
        """
        schema = {
            "@context": "https://schema.org/",
            "@type": "Product",
            "name": product_data.name,
            "description": seo_tags.metadescription,
            "offers": {
                "@type": "Offer",
                "price": str(product_data.price),
                "priceCurrency": "USD",
                "availability": "https://schema.org/InStock",
            },
        }

        if product_data.sku:
            schema["sku"] = product_data.sku

        if product_data.images:
            schema["image"] = product_data.images[0]

        if product_data.category:
            schema["category"] = product_data.category

        return schema

    def _validate_seo_compliance(
        self, seo_tags: SEOMetaTags, schema_markup: dict, keywords: Optional[str] = None
    ) -> SEOCompliance:
        """
        Validate SEO compliance against Yoast/Google standards

        Args:
            seo_tags: Generated SEO tags
            schema_markup: Product schema markup
            keywords: Focus keywords

        Returns:
            SEOCompliance report with validation results
        """
        issues = []

        # Validate title length
        title_length = len(seo_tags.metatitle)
        title_length_valid = self.TITLE_MIN_LENGTH <= title_length <= self.TITLE_MAX_LENGTH
        if not title_length_valid:
            if title_length < self.TITLE_MIN_LENGTH:
                issues.append(f"Title too short ({title_length} chars, minimum {self.TITLE_MIN_LENGTH})")
            else:
                issues.append(f"Title too long ({title_length} chars, maximum {self.TITLE_MAX_LENGTH})")

        # Validate description length
        desc_length = len(seo_tags.metadescription)
        desc_length_valid = self.DESC_MIN_LENGTH <= desc_length <= self.DESC_MAX_LENGTH
        if not desc_length_valid:
            if desc_length < self.DESC_MIN_LENGTH:
                issues.append(f"Description too short ({desc_length} chars, minimum {self.DESC_MIN_LENGTH})")
            else:
                issues.append(f"Description too long ({desc_length} chars, maximum {self.DESC_MAX_LENGTH})")

        # Validate schema markup
        schema_markup_present = bool(schema_markup)
        schema_markup_valid = False
        if schema_markup_present:
            try:
                json.dumps(schema_markup)
                schema_markup_valid = True
            except Exception:
                issues.append("Schema markup is not valid JSON")
        else:
            issues.append("Schema markup is missing")

        # Validate focus keywords
        focus_keywords_present = bool(keywords and keywords.strip())
        if not focus_keywords_present:
            issues.append("Focus keywords are missing")

        # Calculate SEO score (0-100)
        score = 0
        if title_length_valid:
            score += 30
        if desc_length_valid:
            score += 30
        if schema_markup_valid:
            score += 20
        if focus_keywords_present:
            score += 20

        return SEOCompliance(
            title_length_valid=title_length_valid,
            title_length=title_length,
            description_length_valid=desc_length_valid,
            description_length=desc_length,
            schema_markup_present=schema_markup_present,
            schema_markup_valid=schema_markup_valid,
            focus_keywords_present=focus_keywords_present,
            seo_score=score,
            issues=issues,
        )

    def _generate_yoast_metadata(
        self, seo_tags: SEOMetaTags, schema_markup: dict, keywords: Optional[str] = None, seo_score: int = 0
    ) -> list[dict[str, str]]:
        """
        Format SEO metadata for Yoast SEO fields

        Args:
            seo_tags: Generated SEO tags
            schema_markup: Product schema markup
            keywords: Focus keywords (comma-separated)
            seo_score: Calculated SEO score (0-100)

        Returns:
            List of WooCommerce meta_data entries for Yoast fields
        """
        meta_data = [
            {"key": self.YOAST_TITLE_FIELD, "value": seo_tags.metatitle},
            {"key": self.YOAST_DESC_FIELD, "value": seo_tags.metadescription},
            {"key": self.YOAST_FOCUS_KW_FIELD, "value": keywords or ""},
            {"key": self.YOAST_LINKDEX_FIELD, "value": str(seo_score)},
            {"key": self.SCHEMA_MARKUP_FIELD, "value": json.dumps(schema_markup)},
        ]

        return meta_data

    def _generate_fallback_metadata(self, product_data: ProductData) -> dict:
        """
        Generate fallback SEO metadata when AI service fails

        Args:
            product_data: Product information

        Returns:
            Dictionary with fallback SEO tags
        """
        # Generate simple rule-based metadata
        title = product_data.name[: self.TITLE_MAX_LENGTH]
        if len(product_data.name) > self.TITLE_MAX_LENGTH:
            title = title.rsplit(" ", 1)[0]  # Truncate at word boundary

        description = product_data.short_description or product_data.description
        if len(description) > self.DESC_MAX_LENGTH:
            description = description[: self.DESC_MAX_LENGTH].rsplit(" ", 1)[0]
        elif len(description) < self.DESC_MIN_LENGTH:
            # Pad with product name and category
            description = f"{product_data.name}. {product_data.category}. {description}"
            description = description[: self.DESC_MAX_LENGTH]

        # Ensure minimum lengths
        if len(title) < self.TITLE_MIN_LENGTH:
            title = f"{product_data.name} - {product_data.category}"[: self.TITLE_MAX_LENGTH]

        if len(description) < self.DESC_MIN_LENGTH:
            description = (
                f"{product_data.name}. Premium {product_data.category}. Shop now for the best quality and prices."[
                    : self.DESC_MAX_LENGTH
                ]
            )

        schema = {
            "@context": "https://schema.org/",
            "@type": "Product",
            "name": product_data.name,
            "description": description,
            "offers": {"@type": "Offer", "price": str(product_data.price), "priceCurrency": "USD"},
        }

        keywords = product_data.keywords or f"{product_data.name}, {product_data.category}"

        return {"metatitle": title, "metadescription": description, "schema": schema, "keywords": keywords}

    async def create_product_with_seo(self, product_data: ProductData) -> ProductWithSEOResponse:
        """
        Create product in WooCommerce with auto-generated SEO metadata

        Workflow:
        1. Generate SEO metadata using AI (with fallback)
        2. Validate SEO compliance
        3. Format for Yoast SEO fields
        4. Create product in WooCommerce with meta_data
        5. Return complete response with compliance report

        Args:
            product_data: Product information

        Returns:
            ProductWithSEOResponse with product ID, SEO metadata, and compliance
        """
        fallback_used = False

        try:
            logger.info("Creating product with SEO", extra={"product_name": product_data.name})

            # Step 1: Generate SEO metadata
            try:
                product_info = ProductInfo(
                    title=product_data.name,
                    category=product_data.category,
                    short_description=product_data.short_description,
                    description=product_data.description,
                    keywords=product_data.keywords,
                )

                seo_tags = await self.seo_service.generate_seo_tags(product=product_info, fallback=True)

                seo_metadata = {
                    "metatitle": seo_tags.metatitle,
                    "metadescription": seo_tags.metadescription,
                    "keywords": product_data.keywords or "",
                }

                schema_markup = self._generate_schema_markup(product_data, seo_tags)

                logger.info(
                    "SEO metadata generated",
                    extra={
                        "product": product_data.name,
                        "title_length": len(seo_tags.metatitle),
                        "desc_length": len(seo_tags.metadescription),
                    },
                )

            except SEOOptimizerError as e:
                logger.warning("SEO service failed, using fallback metadata", extra={"error": str(e)})
                fallback_used = True
                fallback_data = self._generate_fallback_metadata(product_data)

                # Create SEOMetaTags from fallback
                seo_tags = SEOMetaTags(
                    metatitle=fallback_data["metatitle"], metadescription=fallback_data["metadescription"]
                )

                seo_metadata = {
                    "metatitle": fallback_data["metatitle"],
                    "metadescription": fallback_data["metadescription"],
                    "keywords": fallback_data["keywords"],
                }

                schema_markup = fallback_data["schema"]

            # Step 2: Validate SEO compliance
            compliance = self._validate_seo_compliance(
                seo_tags=seo_tags, schema_markup=schema_markup, keywords=seo_metadata.get("keywords")
            )

            # Step 3: Format Yoast metadata
            yoast_metadata = self._generate_yoast_metadata(
                seo_tags=seo_tags,
                schema_markup=schema_markup,
                keywords=seo_metadata.get("keywords"),
                seo_score=compliance.seo_score,
            )

            # Step 4: Prepare WooCommerce product data
            wc_product_data = {
                "name": product_data.name,
                "type": "simple",
                "regular_price": str(product_data.regular_price or product_data.price),
                "price": str(product_data.price),
                "description": product_data.description,
                "short_description": product_data.short_description,
                "meta_data": yoast_metadata,
            }

            if product_data.sku:
                wc_product_data["sku"] = product_data.sku

            if product_data.stock_quantity is not None:
                wc_product_data["manage_stock"] = True
                wc_product_data["stock_quantity"] = product_data.stock_quantity

            if product_data.images:
                wc_product_data["images"] = [{"src": img} for img in product_data.images]

            # Step 5: Create product in WooCommerce
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/products",
                    auth=(self.consumer_key, self.consumer_secret),
                    json=wc_product_data,
                    timeout=30.0,
                )
                response.raise_for_status()
                wc_product = response.json()

            product_id = wc_product.get("id")
            product_url = wc_product.get("permalink")

            logger.info(
                "Product created with SEO",
                extra={
                    "product_id": product_id,
                    "seo_score": compliance.seo_score,
                    "compliant": compliance.is_compliant,
                    "fallback_used": fallback_used,
                },
            )

            return ProductWithSEOResponse(
                success=True,
                product_id=product_id,
                product_url=product_url,
                seo_metadata=seo_metadata,
                compliance=compliance,
                fallback_used=fallback_used,
            )

        except httpx.HTTPStatusError as e:
            logger.error(
                "WooCommerce API error", extra={"status_code": e.response.status_code, "response": e.response.text}
            )
            return ProductWithSEOResponse(
                success=False, error=f"WooCommerce API error: {e.response.status_code} - {e.response.text}"
            )

        except Exception as e:
            logger.exception("Product creation failed")
            return ProductWithSEOResponse(success=False, error=f"Product creation failed: {e!s}")

    async def update_product_seo(self, product_id: int, product_data: ProductData) -> ProductWithSEOResponse:
        """
        Update existing product with regenerated SEO metadata

        Args:
            product_id: WooCommerce product ID
            product_data: Updated product information

        Returns:
            ProductWithSEOResponse with updated SEO metadata and compliance
        """
        fallback_used = False

        try:
            logger.info("Updating product SEO", extra={"product_id": product_id})

            # Step 1: Generate SEO metadata
            try:
                product_info = ProductInfo(
                    title=product_data.name,
                    category=product_data.category,
                    short_description=product_data.short_description,
                    description=product_data.description,
                    keywords=product_data.keywords,
                )

                seo_tags = await self.seo_service.generate_seo_tags(product=product_info, fallback=True)

                seo_metadata = {
                    "metatitle": seo_tags.metatitle,
                    "metadescription": seo_tags.metadescription,
                    "keywords": product_data.keywords or "",
                }

                schema_markup = self._generate_schema_markup(product_data, seo_tags)

            except SEOOptimizerError as e:
                logger.warning("SEO service failed, using fallback metadata", extra={"error": str(e)})
                fallback_used = True
                fallback_data = self._generate_fallback_metadata(product_data)

                seo_tags = SEOMetaTags(
                    metatitle=fallback_data["metatitle"], metadescription=fallback_data["metadescription"]
                )

                seo_metadata = {
                    "metatitle": fallback_data["metatitle"],
                    "metadescription": fallback_data["metadescription"],
                    "keywords": fallback_data["keywords"],
                }

                schema_markup = fallback_data["schema"]

            # Step 2: Validate compliance
            compliance = self._validate_seo_compliance(
                seo_tags=seo_tags, schema_markup=schema_markup, keywords=seo_metadata.get("keywords")
            )

            # Step 3: Format Yoast metadata
            yoast_metadata = self._generate_yoast_metadata(
                seo_tags=seo_tags,
                schema_markup=schema_markup,
                keywords=seo_metadata.get("keywords"),
                seo_score=compliance.seo_score,
            )

            # Step 4: Update product in WooCommerce
            async with httpx.AsyncClient() as client:
                response = await client.put(
                    f"{self.api_url}/products/{product_id}",
                    auth=(self.consumer_key, self.consumer_secret),
                    json={"meta_data": yoast_metadata},
                    timeout=30.0,
                )
                response.raise_for_status()
                wc_product = response.json()

            product_url = wc_product.get("permalink")

            logger.info(
                "Product SEO updated",
                extra={
                    "product_id": product_id,
                    "seo_score": compliance.seo_score,
                    "compliant": compliance.is_compliant,
                    "fallback_used": fallback_used,
                },
            )

            return ProductWithSEOResponse(
                success=True,
                product_id=product_id,
                product_url=product_url,
                seo_metadata=seo_metadata,
                compliance=compliance,
                fallback_used=fallback_used,
            )

        except httpx.HTTPStatusError as e:
            logger.error(
                "WooCommerce API error", extra={"status_code": e.response.status_code, "response": e.response.text}
            )
            return ProductWithSEOResponse(
                success=False, error=f"WooCommerce API error: {e.response.status_code} - {e.response.text}"
            )

        except Exception as e:
            logger.exception("Product SEO update failed")
            return ProductWithSEOResponse(success=False, error=f"SEO update failed: {e!s}")


def get_integration_service(
    store_url: str, consumer_key: str, consumer_secret: str, seo_service: SEOOptimizerService
) -> WooCommerceIntegrationService:
    """
    Factory function to create WooCommerce integration service

    Args:
        store_url: WooCommerce store URL
        consumer_key: WooCommerce REST API consumer key
        consumer_secret: WooCommerce REST API consumer secret
        seo_service: Initialized SEO optimizer service

    Returns:
        WooCommerceIntegrationService instance
    """
    return WooCommerceIntegrationService(
        store_url=store_url, consumer_key=consumer_key, consumer_secret=consumer_secret, seo_service=seo_service
    )
