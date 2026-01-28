"""WordPress Integration API Endpoints.

FastAPI endpoints for WordPress/WooCommerce integration.
"""

from __future__ import annotations

import hashlib
import hmac
import os
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel, Field

from integrations.wordpress_com_client import create_wordpress_client
from integrations.wordpress_product_sync import SkyyRoseProduct, WordPressProductSync

router = APIRouter(prefix="/wordpress", tags=["wordpress"])


# =============================================================================
# Configuration
# =============================================================================


class WordPressSettings(BaseModel):
    """WordPress integration settings from environment."""

    site_url: str = Field(default_factory=lambda: os.getenv("WORDPRESS_SITE_URL", ""))
    api_token: str = Field(default_factory=lambda: os.getenv("WORDPRESS_API_TOKEN", ""))
    consumer_key: str = Field(default_factory=lambda: os.getenv("WC_CONSUMER_KEY", ""))
    consumer_secret: str = Field(
        default_factory=lambda: os.getenv("WC_CONSUMER_SECRET", "")
    )
    webhook_secret: str = Field(
        default_factory=lambda: os.getenv("WC_WEBHOOK_SECRET", "")
    )


def get_settings() -> WordPressSettings:
    """Get WordPress settings."""
    settings = WordPressSettings()
    if not settings.site_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="WordPress integration not configured",
        )
    return settings


# =============================================================================
# Webhook Validation
# =============================================================================


def verify_webhook_signature(
    payload: bytes,
    signature: str,
    secret: str,
) -> bool:
    """Verify WooCommerce webhook signature.

    Args:
        payload: Request body bytes
        signature: X-WC-Webhook-Signature header
        secret: Webhook secret

    Returns:
        True if signature valid
    """
    expected = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256,
    ).digest()
    expected_b64 = expected.hex()
    return hmac.compare_digest(expected_b64, signature)


async def verify_webhook(
    request: Request,
    x_wc_webhook_signature: str = Header(..., alias="X-WC-Webhook-Signature"),
    settings: WordPressSettings = Depends(get_settings),
) -> bytes:
    """Verify WooCommerce webhook signature.

    Args:
        request: FastAPI request
        x_wc_webhook_signature: Webhook signature header
        settings: WordPress settings

    Returns:
        Request body bytes

    Raises:
        HTTPException: If signature invalid
    """
    body = await request.body()

    if not verify_webhook_signature(body, x_wc_webhook_signature, settings.webhook_secret):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature",
        )

    return body


# =============================================================================
# Product Sync Endpoints
# =============================================================================


@router.post("/products/sync")
async def sync_product(
    product: SkyyRoseProduct,
    settings: WordPressSettings = Depends(get_settings),
) -> dict[str, Any]:
    """Sync single product to WooCommerce.

    Args:
        product: SkyyRose product data
        settings: WordPress settings

    Returns:
        Sync result
    """
    async with await create_wordpress_client(
        site_url=settings.site_url,
        api_token=settings.api_token,
        consumer_key=settings.consumer_key,
        consumer_secret=settings.consumer_secret,
    ) as client:
        sync = WordPressProductSync(client)
        result = await sync.sync_product(product)
        return result.model_dump()


@router.post("/products/sync-collection")
async def sync_collection(
    collection: str,
    products: list[SkyyRoseProduct],
    settings: WordPressSettings = Depends(get_settings),
) -> dict[str, Any]:
    """Sync all products in a collection.

    Args:
        collection: Collection name (signature, black-rose, love-hurts)
        products: Products to sync
        settings: WordPress settings

    Returns:
        Sync results
    """
    if collection not in ("signature", "black-rose", "love-hurts"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid collection: {collection}",
        )

    async with await create_wordpress_client(
        site_url=settings.site_url,
        api_token=settings.api_token,
        consumer_key=settings.consumer_key,
        consumer_secret=settings.consumer_secret,
    ) as client:
        sync = WordPressProductSync(client)
        results = await sync.sync_collection(collection, products)  # type: ignore
        return {
            "collection": collection,
            "total": len(results),
            "created": sum(1 for r in results if r.action == "created"),
            "updated": sum(1 for r in results if r.action == "updated"),
            "skipped": sum(1 for r in results if r.action == "skipped"),
            "errors": [r.error for r in results if r.error],
            "results": [r.model_dump() for r in results],
        }


# =============================================================================
# WooCommerce Webhook Endpoints
# =============================================================================


@router.post("/webhooks/order-created")
async def order_created_webhook(
    request: Request,
    body: bytes = Depends(verify_webhook),
) -> dict[str, str]:
    """Handle WooCommerce order.created webhook.

    Args:
        request: FastAPI request
        body: Verified webhook body

    Returns:
        Acknowledgment
    """
    import json

    order_data = json.loads(body)

    # TODO: Process order (e.g., notify fulfillment, update inventory)
    order_id = order_data.get("id")
    customer_email = order_data.get("billing", {}).get("email")

    # Log webhook
    print(f"Order created: #{order_id} - {customer_email}")

    return {"status": "received", "order_id": order_id}


@router.post("/webhooks/order-updated")
async def order_updated_webhook(
    request: Request,
    body: bytes = Depends(verify_webhook),
) -> dict[str, str]:
    """Handle WooCommerce order.updated webhook.

    Args:
        request: FastAPI request
        body: Verified webhook body

    Returns:
        Acknowledgment
    """
    import json

    order_data = json.loads(body)

    # TODO: Process order update (e.g., status change, refund)
    order_id = order_data.get("id")
    status_update = order_data.get("status")

    # Log webhook
    print(f"Order updated: #{order_id} - Status: {status_update}")

    return {"status": "received", "order_id": order_id}


@router.post("/webhooks/product-updated")
async def product_updated_webhook(
    request: Request,
    body: bytes = Depends(verify_webhook),
) -> dict[str, str]:
    """Handle WooCommerce product.updated webhook.

    Args:
        request: FastAPI request
        body: Verified webhook body

    Returns:
        Acknowledgment
    """
    import json

    product_data = json.loads(body)

    # TODO: Sync product updates back to internal catalog
    product_id = product_data.get("id")
    product_sku = product_data.get("sku")

    # Log webhook
    print(f"Product updated: #{product_id} - SKU: {product_sku}")

    return {"status": "received", "product_id": product_id}


# =============================================================================
# Health Check
# =============================================================================


@router.get("/health")
async def wordpress_health(
    settings: WordPressSettings = Depends(get_settings),
) -> dict[str, Any]:
    """Check WordPress integration health.

    Args:
        settings: WordPress settings

    Returns:
        Health status
    """
    async with await create_wordpress_client(
        site_url=settings.site_url,
        api_token=settings.api_token,
        consumer_key=settings.consumer_key,
        consumer_secret=settings.consumer_secret,
    ) as client:
        try:
            # Test WooCommerce connection
            products = await client.list_products(per_page=1)
            return {
                "status": "healthy",
                "site_url": settings.site_url,
                "woocommerce": "connected",
                "test_query": f"Found {len(products)} products",
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"WordPress integration unhealthy: {e}",
            )
