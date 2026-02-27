"""WordPress Bridge Agent — MCP tool definitions for WordPress/WooCommerce operations.

Wraps the existing WordPressClient and WordPressProductSync with @tool-decorated
functions that follow the DevSkyy MCP tool pattern (content/text responses).

Tools:
    wp_health_check       — Check WordPress/WooCommerce API connectivity
    wp_get_products       — List WooCommerce products (filterable by collection)
    wp_get_orders         — List WooCommerce orders (filterable by status)
    wp_update_order       — Update a WooCommerce order's status
    wp_sync_product       — Sync a single product to WooCommerce
    wp_sync_collection    — Batch sync all products in a collection
    wp_create_page        — Create a WordPress page
    wp_upload_media       — Upload an image from URL to the media library
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from claude_agent_sdk import tool

from integrations.wordpress_client import APIType, WordPressClient
from integrations.wordpress_com_client import create_wordpress_client
from integrations.wordpress_product_sync import SkyyRoseProduct, WordPressProductSync

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Cached client singletons (lazy-init from environment variables)
# ---------------------------------------------------------------------------

_wp_client: WordPressClient | None = None
_product_sync: WordPressProductSync | None = None


def _get_wp_client() -> WordPressClient:
    """Create or return a cached WordPressClient from environment variables.

    Required env vars:
        WORDPRESS_SITE_URL       — WordPress site base URL
        WC_CONSUMER_KEY          — WooCommerce consumer key
        WC_CONSUMER_SECRET       — WooCommerce consumer secret

    Optional env vars:
        WORDPRESS_USERNAME       — WordPress username (for Application Password auth)
        WORDPRESS_APP_PASSWORD   — WordPress Application Password
    """
    global _wp_client  # noqa: PLW0603
    if _wp_client is not None:
        return _wp_client

    site_url = os.environ.get("WORDPRESS_SITE_URL", "")
    consumer_key = os.environ.get("WC_CONSUMER_KEY", "")
    consumer_secret = os.environ.get("WC_CONSUMER_SECRET", "")

    if not all([site_url, consumer_key, consumer_secret]):
        raise ValueError(
            "Missing required env vars: WORDPRESS_SITE_URL, WC_CONSUMER_KEY, WC_CONSUMER_SECRET"
        )

    _wp_client = WordPressClient(
        site_url=site_url,
        consumer_key=consumer_key,
        consumer_secret=consumer_secret,
        api_type=APIType.WPCOM,
        wp_username=os.environ.get("WORDPRESS_USERNAME"),
        wp_app_password=os.environ.get("WORDPRESS_APP_PASSWORD"),
    )
    return _wp_client


async def _get_product_sync() -> WordPressProductSync:
    """Create or return a cached WordPressProductSync from environment variables.

    Required env vars:
        WORDPRESS_SITE_URL       — WordPress site base URL
        WORDPRESS_API_TOKEN      — WordPress.com OAuth2 access token
        WC_CONSUMER_KEY          — WooCommerce consumer key
        WC_CONSUMER_SECRET       — WooCommerce consumer secret
    """
    global _product_sync  # noqa: PLW0603
    if _product_sync is not None:
        return _product_sync

    site_url = os.environ.get("WORDPRESS_SITE_URL", "")
    api_token = os.environ.get("WORDPRESS_API_TOKEN", "")
    consumer_key = os.environ.get("WC_CONSUMER_KEY", "")
    consumer_secret = os.environ.get("WC_CONSUMER_SECRET", "")

    if not all([site_url, api_token, consumer_key, consumer_secret]):
        raise ValueError(
            "Missing required env vars: WORDPRESS_SITE_URL, WORDPRESS_API_TOKEN, "
            "WC_CONSUMER_KEY, WC_CONSUMER_SECRET"
        )

    wp_com_client = await create_wordpress_client(
        site_url=site_url,
        api_token=api_token,
        consumer_key=consumer_key,
        consumer_secret=consumer_secret,
    )
    _product_sync = WordPressProductSync(client=wp_com_client)
    return _product_sync


# ---------------------------------------------------------------------------
# WordPress Core MCP Tools (8)
# ---------------------------------------------------------------------------


@tool(
    "wp_health_check",
    "Check WordPress/WooCommerce API connectivity and site status",
    {},
)
async def wp_health_check(args: dict[str, Any]) -> dict[str, Any]:
    """Check WordPress and WooCommerce API connectivity."""
    try:
        client = _get_wp_client()
        result = await client.health_check()
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(result, indent=2),
                }
            ]
        }
    except Exception as e:
        logger.error("wp_health_check failed: %s", e)
        return {
            "content": [{"type": "text", "text": f"Error: {e!s}"}],
            "is_error": True,
        }


@tool(
    "wp_get_products",
    "List WooCommerce products, optionally filtered by collection",
    {"collection": str, "page": int, "per_page": int},
)
async def wp_get_products(args: dict[str, Any]) -> dict[str, Any]:
    """List WooCommerce products with optional collection filter."""
    try:
        client = _get_wp_client()
        collection = args.get("collection")
        page = args.get("page", 1)
        per_page = args.get("per_page", 20)

        products = await client.list_products(
            collection=collection,
            page=page,
            per_page=per_page,
        )
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(
                        {"count": len(products), "products": products},
                        indent=2,
                        default=str,
                    ),
                }
            ]
        }
    except Exception as e:
        logger.error("wp_get_products failed: %s", e)
        return {
            "content": [{"type": "text", "text": f"Error: {e!s}"}],
            "is_error": True,
        }


@tool(
    "wp_get_orders",
    "List WooCommerce orders, optionally filtered by status",
    {"status": str, "page": int, "per_page": int},
)
async def wp_get_orders(args: dict[str, Any]) -> dict[str, Any]:
    """List WooCommerce orders with optional status filter."""
    try:
        client = _get_wp_client()
        status = args.get("status")
        page = args.get("page", 1)
        per_page = args.get("per_page", 20)

        orders = await client.list_orders(
            status=status,
            page=page,
            per_page=per_page,
        )
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(
                        {"count": len(orders), "orders": orders},
                        indent=2,
                        default=str,
                    ),
                }
            ]
        }
    except Exception as e:
        logger.error("wp_get_orders failed: %s", e)
        return {
            "content": [{"type": "text", "text": f"Error: {e!s}"}],
            "is_error": True,
        }


@tool(
    "wp_update_order",
    "Update a WooCommerce order's status",
    {"order_id": int, "status": str},
)
async def wp_update_order(args: dict[str, Any]) -> dict[str, Any]:
    """Update a WooCommerce order status."""
    try:
        client = _get_wp_client()
        order_id = args.get("order_id")
        status = args.get("status")

        if not order_id or not status:
            raise ValueError("Both 'order_id' and 'status' are required")

        result = await client.update_order_status(order_id=order_id, status=status)
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(
                        {"message": f"Order {order_id} updated to '{status}'", "order": result},
                        indent=2,
                        default=str,
                    ),
                }
            ]
        }
    except Exception as e:
        logger.error("wp_update_order failed: %s", e)
        return {
            "content": [{"type": "text", "text": f"Error: {e!s}"}],
            "is_error": True,
        }


@tool(
    "wp_sync_product",
    "Sync a single product to WooCommerce",
    {"sku": str, "name": str, "collection": str, "price": str, "description": str},
)
async def wp_sync_product(args: dict[str, Any]) -> dict[str, Any]:
    """Sync a single SkyyRose product to WooCommerce."""
    try:
        sync = await _get_product_sync()

        sku = args.get("sku", "")
        name = args.get("name", "")
        collection = args.get("collection", "")
        price = args.get("price", "0.00")
        description = args.get("description", "")

        if not all([sku, name, collection]):
            raise ValueError("'sku', 'name', and 'collection' are required")

        product = SkyyRoseProduct(
            sku=sku,
            name=name,
            collection=collection,
            price=price,
            description=description,
            short_description=description[:160] if description else "",
        )

        result = await sync.sync_product(product)
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(
                        {
                            "sku": result.sku,
                            "woo_id": result.woo_id,
                            "action": result.action,
                            "error": result.error,
                        },
                        indent=2,
                    ),
                }
            ]
        }
    except Exception as e:
        logger.error("wp_sync_product failed: %s", e)
        return {
            "content": [{"type": "text", "text": f"Error: {e!s}"}],
            "is_error": True,
        }


@tool(
    "wp_sync_collection",
    "Batch sync all products in a collection to WooCommerce",
    {"collection": str},
)
async def wp_sync_collection(args: dict[str, Any]) -> dict[str, Any]:
    """Batch sync all products in a collection to WooCommerce.

    Note: Product catalog loading comes in Task 3. For now, passes
    an empty products list (returns empty results).
    """
    try:
        sync = await _get_product_sync()
        collection = args.get("collection", "")

        if not collection:
            raise ValueError("'collection' is required")

        # Catalog loading comes in Task 3 -- for now pass empty list
        products: list[SkyyRoseProduct] = []
        results = await sync.sync_collection(collection=collection, products=products)

        summary = [
            {
                "sku": r.sku,
                "woo_id": r.woo_id,
                "action": r.action,
                "error": r.error,
            }
            for r in results
        ]
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(
                        {
                            "collection": collection,
                            "synced": len(results),
                            "results": summary,
                        },
                        indent=2,
                    ),
                }
            ]
        }
    except Exception as e:
        logger.error("wp_sync_collection failed: %s", e)
        return {
            "content": [{"type": "text", "text": f"Error: {e!s}"}],
            "is_error": True,
        }


@tool(
    "wp_create_page",
    "Create or update a WordPress page",
    {"title": str, "slug": str, "content": str, "status": str},
)
async def wp_create_page(args: dict[str, Any]) -> dict[str, Any]:
    """Create a WordPress page."""
    try:
        client = _get_wp_client()
        title = args.get("title", "")
        slug = args.get("slug", "")
        content = args.get("content", "")
        status = args.get("status", "draft")

        if not title or not slug:
            raise ValueError("'title' and 'slug' are required")

        result = await client.create_page(
            title=title,
            slug=slug,
            content=content,
            status=status,
        )
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(
                        {
                            "message": f"Page '{title}' created as {status}",
                            "page": result,
                        },
                        indent=2,
                        default=str,
                    ),
                }
            ]
        }
    except Exception as e:
        logger.error("wp_create_page failed: %s", e)
        return {
            "content": [{"type": "text", "text": f"Error: {e!s}"}],
            "is_error": True,
        }


@tool(
    "wp_upload_media",
    "Upload an image to the WordPress media library from a URL",
    {"image_url": str, "title": str, "alt_text": str},
)
async def wp_upload_media(args: dict[str, Any]) -> dict[str, Any]:
    """Upload an image from URL to the WordPress media library."""
    try:
        client = _get_wp_client()
        image_url = args.get("image_url", "")
        title = args.get("title", "")
        alt_text = args.get("alt_text", "")

        if not image_url or not title:
            raise ValueError("'image_url' and 'title' are required")

        result = await client.upload_media_from_url(
            image_url=image_url,
            title=title,
            alt_text=alt_text,
        )
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(
                        {
                            "media_id": result.id,
                            "url": result.url,
                            "title": result.title,
                            "alt_text": result.alt_text,
                            "mime_type": result.mime_type,
                        },
                        indent=2,
                    ),
                }
            ]
        }
    except Exception as e:
        logger.error("wp_upload_media failed: %s", e)
        return {
            "content": [{"type": "text", "text": f"Error: {e!s}"}],
            "is_error": True,
        }
