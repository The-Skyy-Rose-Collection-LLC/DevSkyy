# api/v1/woocommerce_webhooks.py
"""WooCommerce webhook endpoints for automatic product ingestion.

Implements US-003: WooCommerce auto-ingestion webhook.

Features:
- Receives product.created and product.updated webhooks
- HMAC-SHA256 signature verification (WooCommerce format)
- Automatic image extraction and deduplication
- Queues images for ML processing pipeline

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import logging
import os
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Request, status
from pydantic import BaseModel, Field

from services.image_ingestion import (
    ImageIngestionService,
    IngestionRequest,
    IngestionResult,
    IngestionSource,
    IngestionStatus,
    get_ingestion_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/woocommerce", tags=["WooCommerce Webhooks"])


# =============================================================================
# Configuration
# =============================================================================


class WooCommerceWebhookConfig:
    """WooCommerce webhook configuration."""

    def __init__(self) -> None:
        self.secret = os.getenv("WOOCOMMERCE_WEBHOOK_SECRET", "")
        self.signature_header = "X-WC-Webhook-Signature"
        self.topic_header = "X-WC-Webhook-Topic"
        self.source_header = "X-WC-Webhook-Source"
        self.delivery_id_header = "X-WC-Webhook-Delivery-ID"
        self.max_age_seconds = 300  # 5 minutes

    @classmethod
    def from_env(cls) -> "WooCommerceWebhookConfig":
        """Create config from environment."""
        return cls()


# =============================================================================
# Models
# =============================================================================


class WooCommerceWebhookTopic(str, Enum):
    """WooCommerce webhook topics we handle."""

    PRODUCT_CREATED = "product.created"
    PRODUCT_UPDATED = "product.updated"
    PRODUCT_DELETED = "product.deleted"
    ORDER_CREATED = "order.created"
    ORDER_UPDATED = "order.updated"


class WooCommerceImage(BaseModel):
    """WooCommerce product image from webhook payload."""

    id: int
    date_created: str | None = None
    date_modified: str | None = None
    src: str  # Image URL
    name: str | None = None
    alt: str | None = None


class WooCommerceProduct(BaseModel):
    """WooCommerce product from webhook payload (partial)."""

    id: int
    name: str
    slug: str | None = None
    type: str | None = None
    status: str | None = None
    sku: str | None = None
    description: str | None = None
    short_description: str | None = None
    images: list[WooCommerceImage] = Field(default_factory=list)
    categories: list[dict[str, Any]] = Field(default_factory=list)
    tags: list[dict[str, Any]] = Field(default_factory=list)
    attributes: list[dict[str, Any]] = Field(default_factory=list)


class WebhookReceiveResponse(BaseModel):
    """Response for webhook receive."""

    success: bool
    message: str
    delivery_id: str | None = None
    images_queued: int = 0
    images_skipped: int = 0
    job_ids: list[str] = Field(default_factory=list)


class IngestionResultResponse(BaseModel):
    """Response model for individual ingestion result."""

    status: str
    job_id: str | None = None
    asset_id: str | None = None
    is_duplicate: bool = False
    duplicate_asset_id: str | None = None
    error_message: str | None = None


# =============================================================================
# Signature Verification
# =============================================================================


class WooCommerceSignatureVerifier:
    """Verifies WooCommerce webhook signatures.

    WooCommerce uses HMAC-SHA256 with base64 encoding:
    1. Compute HMAC-SHA256 of raw body using webhook secret
    2. Base64 encode the result
    3. Compare with X-WC-Webhook-Signature header

    Reference: https://woocommerce.github.io/woocommerce-rest-api-docs/#webhooks
    """

    def __init__(self, secret: str) -> None:
        self.secret = secret

    def verify(self, payload: bytes, signature: str) -> bool:
        """Verify webhook signature.

        Args:
            payload: Raw request body bytes
            signature: Value of X-WC-Webhook-Signature header

        Returns:
            True if signature is valid
        """
        if not self.secret:
            logger.warning("WooCommerce webhook secret not configured")
            return False

        # Compute expected signature
        expected = base64.b64encode(
            hmac.new(
                self.secret.encode("utf-8"),
                payload,
                hashlib.sha256,
            ).digest()
        ).decode("utf-8")

        # Constant-time comparison
        return hmac.compare_digest(expected, signature)


# =============================================================================
# Background Processing
# =============================================================================


async def process_product_images(
    product: WooCommerceProduct,
    delivery_id: str,
    *,
    correlation_id: str | None = None,
) -> list[IngestionResult]:
    """Process images from a WooCommerce product.

    Downloads each image, checks for duplicates, and queues for processing.

    Args:
        product: WooCommerce product data
        delivery_id: Webhook delivery ID
        correlation_id: Optional correlation ID

    Returns:
        List of ingestion results
    """
    correlation_id = correlation_id or str(uuid4())
    ingestion_service = get_ingestion_service()
    results: list[IngestionResult] = []

    logger.info(
        f"Processing {len(product.images)} images for product {product.id}",
        extra={
            "product_id": product.id,
            "product_name": product.name,
            "image_count": len(product.images),
            "correlation_id": correlation_id,
        },
    )

    for image in product.images:
        if not image.src:
            logger.warning(
                f"Skipping image {image.id} - no src URL",
                extra={"correlation_id": correlation_id},
            )
            continue

        try:
            request = IngestionRequest(
                image_url=image.src,
                source=IngestionSource.WOOCOMMERCE,
                woocommerce_product_id=str(product.id),
                metadata={
                    "woocommerce_image_id": image.id,
                    "image_name": image.name,
                    "image_alt": image.alt,
                    "product_name": product.name,
                    "product_sku": product.sku,
                    "delivery_id": delivery_id,
                },
                correlation_id=correlation_id,
            )

            result = await ingestion_service.ingest(request)
            results.append(result)

        except Exception as e:
            logger.error(
                f"Failed to ingest image {image.id}: {e}",
                extra={
                    "image_id": image.id,
                    "correlation_id": correlation_id,
                },
            )
            results.append(
                IngestionResult(
                    status=IngestionStatus.FAILED,
                    original_url=image.src,
                    error_message=str(e),
                )
            )

    # Log summary
    completed = sum(1 for r in results if r.status == IngestionStatus.COMPLETED)
    skipped = sum(1 for r in results if r.status == IngestionStatus.SKIPPED)
    failed = sum(1 for r in results if r.status == IngestionStatus.FAILED)

    logger.info(
        f"Product {product.id} ingestion complete: "
        f"{completed} queued, {skipped} duplicates, {failed} failed",
        extra={
            "product_id": product.id,
            "completed": completed,
            "skipped": skipped,
            "failed": failed,
            "correlation_id": correlation_id,
        },
    )

    return results


# =============================================================================
# Endpoints
# =============================================================================


@router.post("/webhook", response_model=WebhookReceiveResponse)
async def receive_woocommerce_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_wc_webhook_signature: str | None = Header(None, alias="X-WC-Webhook-Signature"),
    x_wc_webhook_topic: str | None = Header(None, alias="X-WC-Webhook-Topic"),
    x_wc_webhook_source: str | None = Header(None, alias="X-WC-Webhook-Source"),
    x_wc_webhook_delivery_id: str | None = Header(
        None, alias="X-WC-Webhook-Delivery-ID"
    ),
) -> WebhookReceiveResponse:
    """
    Receive WooCommerce webhook for product events.

    Handles:
    - **product.created**: New product with images
    - **product.updated**: Updated product (checks for new images)

    Signature is verified using HMAC-SHA256 (WooCommerce format).
    Images are automatically extracted and queued for ML processing.

    Headers:
    - X-WC-Webhook-Signature: HMAC-SHA256 signature
    - X-WC-Webhook-Topic: Event type (product.created, product.updated)
    - X-WC-Webhook-Source: Source URL
    - X-WC-Webhook-Delivery-ID: Unique delivery identifier
    """
    correlation_id = str(uuid4())
    delivery_id = x_wc_webhook_delivery_id or correlation_id

    logger.info(
        f"Received WooCommerce webhook: {x_wc_webhook_topic}",
        extra={
            "topic": x_wc_webhook_topic,
            "source": x_wc_webhook_source,
            "delivery_id": delivery_id,
            "correlation_id": correlation_id,
        },
    )

    # Get raw body for signature verification
    body = await request.body()

    # Verify signature
    config = WooCommerceWebhookConfig.from_env()
    if config.secret:
        if not x_wc_webhook_signature:
            logger.warning(
                "Missing webhook signature",
                extra={"correlation_id": correlation_id},
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing webhook signature",
            )

        verifier = WooCommerceSignatureVerifier(config.secret)
        if not verifier.verify(body, x_wc_webhook_signature):
            logger.warning(
                "Invalid webhook signature",
                extra={"correlation_id": correlation_id},
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature",
            )
    else:
        logger.warning(
            "WooCommerce webhook secret not configured - signature verification skipped",
            extra={"correlation_id": correlation_id},
        )

    # Check topic
    if x_wc_webhook_topic not in (
        WooCommerceWebhookTopic.PRODUCT_CREATED.value,
        WooCommerceWebhookTopic.PRODUCT_UPDATED.value,
    ):
        logger.info(
            f"Ignoring webhook topic: {x_wc_webhook_topic}",
            extra={"correlation_id": correlation_id},
        )
        return WebhookReceiveResponse(
            success=True,
            message=f"Webhook topic {x_wc_webhook_topic} not handled",
            delivery_id=delivery_id,
        )

    # Parse product data
    try:
        import json

        data = json.loads(body)
        product = WooCommerceProduct(**data)
    except Exception as e:
        logger.error(
            f"Failed to parse webhook payload: {e}",
            extra={"correlation_id": correlation_id},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid webhook payload: {e}",
        )

    # Check for images
    if not product.images:
        logger.info(
            f"Product {product.id} has no images",
            extra={"correlation_id": correlation_id},
        )
        return WebhookReceiveResponse(
            success=True,
            message="Product has no images",
            delivery_id=delivery_id,
        )

    # Process images (sync for now, could be background)
    results = await process_product_images(
        product,
        delivery_id,
        correlation_id=correlation_id,
    )

    # Build response
    images_queued = sum(1 for r in results if r.status == IngestionStatus.COMPLETED)
    images_skipped = sum(1 for r in results if r.status == IngestionStatus.SKIPPED)
    job_ids = [r.job_id for r in results if r.job_id]

    return WebhookReceiveResponse(
        success=True,
        message=f"Processed {len(results)} images for product {product.id}",
        delivery_id=delivery_id,
        images_queued=images_queued,
        images_skipped=images_skipped,
        job_ids=job_ids,
    )


@router.post("/webhook/test")
async def test_woocommerce_webhook(
    request: Request,
    x_wc_webhook_signature: str | None = Header(None, alias="X-WC-Webhook-Signature"),
) -> dict[str, Any]:
    """
    Test endpoint for verifying WooCommerce webhook configuration.

    Returns signature verification status and parsed payload info.
    """
    body = await request.body()
    config = WooCommerceWebhookConfig.from_env()

    signature_valid = False
    if config.secret and x_wc_webhook_signature:
        verifier = WooCommerceSignatureVerifier(config.secret)
        signature_valid = verifier.verify(body, x_wc_webhook_signature)

    try:
        import json

        data = json.loads(body)
    except Exception:
        data = {"error": "Could not parse JSON"}

    return {
        "signature_valid": signature_valid,
        "secret_configured": bool(config.secret),
        "signature_provided": bool(x_wc_webhook_signature),
        "payload_size_bytes": len(body),
        "payload_preview": str(data)[:500] if data else None,
    }


@router.get("/status")
async def get_woocommerce_webhook_status() -> dict[str, Any]:
    """
    Get WooCommerce webhook integration status.

    Returns configuration and health information.
    """
    config = WooCommerceWebhookConfig.from_env()
    ingestion_service = get_ingestion_service()

    return {
        "secret_configured": bool(config.secret),
        "supported_topics": [
            WooCommerceWebhookTopic.PRODUCT_CREATED.value,
            WooCommerceWebhookTopic.PRODUCT_UPDATED.value,
        ],
        "deduplication_enabled": True,
        "deduplication_stats": ingestion_service._deduplicator.get_stats(),
    }
