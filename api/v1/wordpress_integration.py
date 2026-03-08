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

    site_url: str = Field(
        default_factory=lambda: os.getenv("WORDPRESS_SITE_URL", os.getenv("WORDPRESS_URL", ""))
    )
    api_token: str = Field(default_factory=lambda: os.getenv("WORDPRESS_API_TOKEN", ""))
    wp_auth_user: str = Field(default_factory=lambda: os.getenv("WP_AUTH_USER", ""))
    wp_auth_pass: str = Field(default_factory=lambda: os.getenv("WP_AUTH_PASS", ""))
    consumer_key: str = Field(
        default_factory=lambda: os.getenv("WOOCOMMERCE_KEY") or os.getenv("WC_CONSUMER_KEY", "")
    )
    consumer_secret: str = Field(
        default_factory=lambda: (
            os.getenv("WOOCOMMERCE_SECRET") or os.getenv("WC_CONSUMER_SECRET", "")
        )
    )
    webhook_secret: str = Field(default_factory=lambda: os.getenv("WC_WEBHOOK_SECRET", ""))

    @property
    def has_wp_auth(self) -> bool:
        return bool(self.api_token or (self.wp_auth_user and self.wp_auth_pass))


def get_settings() -> WordPressSettings:
    """Get WordPress settings."""
    settings = WordPressSettings()
    if not settings.site_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="WordPress integration not configured — set WORDPRESS_SITE_URL",
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
        api_token=settings.api_token or None,
        consumer_key=settings.consumer_key or None,
        consumer_secret=settings.consumer_secret or None,
        username=settings.wp_auth_user or None,
        app_password=settings.wp_auth_pass or None,
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
        api_token=settings.api_token or None,
        consumer_key=settings.consumer_key or None,
        consumer_secret=settings.consumer_secret or None,
        username=settings.wp_auth_user or None,
        app_password=settings.wp_auth_pass or None,
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
) -> dict[str, Any]:
    """Handle WooCommerce order.created webhook."""
    import json
    import logging
    import uuid

    logger = logging.getLogger(__name__)
    order_data = json.loads(body)
    order_id = order_data.get("id")

    from database.db import EventRecord, db_manager

    async with db_manager.session() as session:
        event = EventRecord(
            event_id=str(uuid.uuid4()),
            event_type="woocommerce.order.created",
            aggregate_id=str(order_id),
            aggregate_type="order",
            data_json=json.dumps(order_data),
        )
        session.add(event)
        await session.commit()

    logger.info("WooCommerce order.created: #%s", order_id)
    return {"status": "received", "order_id": str(order_id)}


@router.post("/webhooks/order-updated")
async def order_updated_webhook(
    request: Request,
    body: bytes = Depends(verify_webhook),
) -> dict[str, Any]:
    """Handle WooCommerce order.updated webhook."""
    import json
    import logging
    import uuid

    logger = logging.getLogger(__name__)
    order_data = json.loads(body)
    order_id = order_data.get("id")
    order_status = order_data.get("status")

    from database.db import EventRecord, db_manager

    async with db_manager.session() as session:
        event = EventRecord(
            event_id=str(uuid.uuid4()),
            event_type="woocommerce.order.updated",
            aggregate_id=str(order_id),
            aggregate_type="order",
            data_json=json.dumps(order_data),
        )
        session.add(event)
        await session.commit()

    logger.info("WooCommerce order.updated: #%s -> %s", order_id, order_status)
    return {"status": "received", "order_id": str(order_id), "new_status": order_status}


@router.post("/webhooks/product-updated")
async def product_updated_webhook(
    request: Request,
    body: bytes = Depends(verify_webhook),
) -> dict[str, Any]:
    """Handle WooCommerce product.updated webhook."""
    import json
    import logging
    import uuid

    logger = logging.getLogger(__name__)
    product_data = json.loads(body)
    product_id = product_data.get("id")
    product_sku = product_data.get("sku")

    from database.db import EventRecord, ProductRepository, db_manager

    async with db_manager.session() as session:
        event = EventRecord(
            event_id=str(uuid.uuid4()),
            event_type="woocommerce.product.updated",
            aggregate_id=str(product_id),
            aggregate_type="product",
            data_json=json.dumps(product_data),
        )
        session.add(event)

        # Sync product updates back to internal catalog
        if product_sku:
            try:
                repo = ProductRepository(session)
                existing = await repo.get_by_sku(product_sku)
                if existing:
                    existing.name = product_data.get("name", existing.name)
                    existing.price = float(product_data.get("price", existing.price))
                    await repo.update(existing)
                    logger.info("Synced WooCommerce product %s back to catalog", product_sku)
            except Exception as e:
                logger.warning("Failed to sync product %s: %s", product_sku, e)

        await session.commit()

    logger.info("WooCommerce product.updated: #%s SKU=%s", product_id, product_sku)
    return {"status": "received", "product_id": str(product_id), "sku": product_sku}


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
        api_token=settings.api_token or None,
        consumer_key=settings.consumer_key or None,
        consumer_secret=settings.consumer_secret or None,
        username=settings.wp_auth_user or None,
        app_password=settings.wp_auth_pass or None,
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
