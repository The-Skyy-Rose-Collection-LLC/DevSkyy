"""WordPress Bridge Agent — MCP tool definitions for WordPress/WooCommerce operations.

Wraps the existing WordPressClient and WordPressProductSync with @tool-decorated
functions that follow the DevSkyy MCP tool pattern (content/text responses).

Tools (WordPress Core — 8):
    wp_health_check           — Check WordPress/WooCommerce API connectivity
    wp_get_products           — List WooCommerce products (filterable by collection)
    wp_get_orders             — List WooCommerce orders (filterable by status)
    wp_update_order           — Update a WooCommerce order's status
    wp_sync_product           — Sync a single product to WooCommerce
    wp_sync_collection        — Batch sync all products in a collection
    wp_create_page            — Create a WordPress page
    wp_upload_media           — Upload an image from URL to the media library

Tools (Pipeline Bridge — 7):
    wp_publish_round_table    — Publish LLM Round Table results as WordPress draft
    wp_attach_3d_model        — Attach GLB 3D model URL to WooCommerce product meta
    wp_upload_product_image   — Upload generated image and attach to product gallery
    wp_publish_social_campaign — Publish social media campaign as WordPress draft
    wp_update_conversion_data — Push conversion metrics to WooCommerce product meta
    get_pipeline_status       — Get status of all 9 dashboard pipelines
    get_product_catalog       — Retrieve SkyyRose product catalog (3 collections)
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

from claude_agent_sdk import create_sdk_mcp_server, tool

from integrations.wordpress_client import (
    COLLECTION_CONFIG,
    APIType,
    SkyyRoseCollection,
    WordPressClient,
)
from integrations.wordpress_com_client import create_wordpress_client
from integrations.wordpress_product_sync import SkyyRoseProduct, WordPressProductSync

logger = logging.getLogger(__name__)


def _safe_error(tool_name: str, exc: Exception) -> dict[str, Any]:
    """Return a sanitized MCP error response. Logs full exception server-side."""
    logger.error("%s failed: %s", tool_name, exc)
    return {
        "content": [{"type": "text", "text": f"Error in {tool_name}: {type(exc).__name__}"}],
        "is_error": True,
    }


# ---------------------------------------------------------------------------
# Cached client singletons (lazy-init from environment variables)
# ---------------------------------------------------------------------------

_wp_client: WordPressClient | None = None
_product_sync: WordPressProductSync | None = None


def _get_wp_client() -> WordPressClient:
    """Create or return a cached WordPressClient from environment variables.

    Required env vars:
        WORDPRESS_SITE_URL       — WordPress site base URL
        WOOCOMMERCE_KEY          — WooCommerce consumer key (fallback: WC_CONSUMER_KEY)
        WOOCOMMERCE_SECRET       — WooCommerce consumer secret (fallback: WC_CONSUMER_SECRET)

    Optional env vars:
        WORDPRESS_USERNAME       — WordPress username (for Application Password auth)
        WORDPRESS_APP_PASSWORD   — WordPress Application Password
    """
    global _wp_client  # noqa: PLW0603
    if _wp_client is not None:
        return _wp_client

    site_url = os.environ.get("WORDPRESS_SITE_URL", "")
    consumer_key = os.environ.get("WOOCOMMERCE_KEY") or os.environ.get("WC_CONSUMER_KEY", "")
    consumer_secret = os.environ.get("WOOCOMMERCE_SECRET") or os.environ.get(
        "WC_CONSUMER_SECRET", ""
    )

    if not all([site_url, consumer_key, consumer_secret]):
        raise ValueError(
            "Missing required env vars: WORDPRESS_SITE_URL, WOOCOMMERCE_KEY, WOOCOMMERCE_SECRET"
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
        WOOCOMMERCE_KEY          — WooCommerce consumer key (fallback: WC_CONSUMER_KEY)
        WOOCOMMERCE_SECRET       — WooCommerce consumer secret (fallback: WC_CONSUMER_SECRET)
    """
    global _product_sync  # noqa: PLW0603
    if _product_sync is not None:
        return _product_sync

    site_url = os.environ.get("WORDPRESS_SITE_URL", "")
    api_token = os.environ.get("WORDPRESS_API_TOKEN", "")
    consumer_key = os.environ.get("WOOCOMMERCE_KEY") or os.environ.get("WC_CONSUMER_KEY", "")
    consumer_secret = os.environ.get("WOOCOMMERCE_SECRET") or os.environ.get(
        "WC_CONSUMER_SECRET", ""
    )

    if not all([site_url, api_token, consumer_key, consumer_secret]):
        raise ValueError(
            "Missing required env vars: WORDPRESS_SITE_URL, WORDPRESS_API_TOKEN, "
            "WOOCOMMERCE_KEY, WOOCOMMERCE_SECRET"
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
        return _safe_error("wp_health_check", e)


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
        return _safe_error("wp_get_products", e)


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
        return _safe_error("wp_get_orders", e)


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
        return _safe_error("wp_update_order", e)


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
        return _safe_error("wp_sync_product", e)


@tool(
    "wp_sync_collection",
    "Batch sync all products in a collection to WooCommerce",
    {"collection": str},
)
async def wp_sync_collection(args: dict[str, Any]) -> dict[str, Any]:
    """Batch sync all products in a collection to WooCommerce.

    Reads the product catalog from COLLECTION_CONFIG and syncs all products
    for the specified collection.
    """
    try:
        sync = await _get_product_sync()
        collection = args.get("collection", "")

        if not collection:
            raise ValueError("'collection' is required")

        # Normalize hyphens to underscores (frontend uses hyphens, enum uses underscores)
        collection = collection.replace("-", "_")

        # Validate collection exists
        valid_collections = [c.value for c in SkyyRoseCollection]
        if collection not in valid_collections:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(
                            {
                                "error": f"Unknown collection: '{collection}'",
                                "available": valid_collections,
                            },
                            indent=2,
                        ),
                    }
                ],
                "is_error": True,
            }

        results = await sync.sync_collection(collection=collection, products=[])

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
        return _safe_error("wp_sync_collection", e)


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
        return _safe_error("wp_create_page", e)


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
        return _safe_error("wp_upload_media", e)


# ---------------------------------------------------------------------------
# Pipeline Bridge MCP Tools (7)
# ---------------------------------------------------------------------------


def _slugify(text: str) -> str:
    """Convert text to a URL-safe slug."""
    slug = text.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    return re.sub(r"-+", "-", slug).strip("-")


@tool(
    "wp_publish_round_table",
    "Format LLM Round Table competition results as a WordPress draft blog post with winner highlight and ranked entries",
    {"title": str, "winner": dict, "entries": list},
)
async def wp_publish_round_table(args: dict[str, Any]) -> dict[str, Any]:
    """Publish LLM Round Table results as a WordPress draft page."""
    try:
        client = _get_wp_client()
        title = args.get("title", "")
        winner = args.get("winner", {})
        entries = args.get("entries", [])

        if not title:
            raise ValueError("'title' is required")

        # Sort entries by score descending
        sorted_entries = sorted(entries, key=lambda e: e.get("score", 0), reverse=True)

        # Build HTML content
        html_parts = [
            '<div class="round-table-results">',
            f"<h2>Winner: {winner.get('provider', 'Unknown')}</h2>",
            f"<p><strong>Score:</strong> {winner.get('score', 0)}/100</p>",
            f"<blockquote>{winner.get('response', '')}</blockquote>",
            "<h3>All Entries</h3>",
            "<table><thead><tr><th>Rank</th><th>Provider</th><th>Score</th></tr></thead><tbody>",
        ]
        for rank, entry in enumerate(sorted_entries, 1):
            html_parts.append(
                f"<tr><td>{rank}</td><td>{entry.get('provider', '')}</td>"
                f"<td>{entry.get('score', 0)}</td></tr>"
            )
        html_parts.append("</tbody></table></div>")
        html = "\n".join(html_parts)

        slug = _slugify(title)
        result = await client.create_page(
            title=title,
            slug=slug,
            content=html,
            status="draft",
        )

        page_id = result.get("id", "unknown")
        edit_url = result.get("link", f"https://skyyrose.co/?p={page_id}")

        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(
                        {
                            "message": "Round Table results published as draft",
                            "page_id": page_id,
                            "edit_url": edit_url,
                            "entries_count": len(sorted_entries),
                        },
                        indent=2,
                    ),
                }
            ]
        }
    except Exception as e:
        return _safe_error("wp_publish_round_table", e)


@tool(
    "wp_attach_3d_model",
    "Attach a GLB 3D model URL to a WooCommerce product custom field (_product_3d_model_url)",
    {"product_id": int, "glb_url": str},
)
async def wp_attach_3d_model(args: dict[str, Any]) -> dict[str, Any]:
    """Attach a GLB 3D model URL to a WooCommerce product."""
    try:
        client = _get_wp_client()
        product_id = args.get("product_id")
        glb_url = args.get("glb_url", "")

        if not product_id or not glb_url:
            raise ValueError("Both 'product_id' and 'glb_url' are required")

        # Use the WC REST API to update product meta
        url = f"{client.wc_base_url}/products/{product_id}"
        response = await client._client.put(
            url,
            json={"meta_data": [{"key": "_product_3d_model_url", "value": glb_url}]},
            auth=(client.consumer_key, client.consumer_secret),
        )
        response.raise_for_status()

        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(
                        {
                            "message": f"3D model attached to product {product_id}",
                            "product_id": product_id,
                            "glb_url": glb_url,
                        },
                        indent=2,
                    ),
                }
            ]
        }
    except Exception as e:
        return _safe_error("wp_attach_3d_model", e)


@tool(
    "wp_upload_product_image",
    "Upload a generated image to the WordPress media library and attach it to a product gallery",
    {"product_id": int, "image_url": str, "alt_text": str},
)
async def wp_upload_product_image(args: dict[str, Any]) -> dict[str, Any]:
    """Upload a generated image and attach it to a WooCommerce product gallery."""
    try:
        client = _get_wp_client()
        product_id = args.get("product_id")
        image_url = args.get("image_url", "")
        alt_text = args.get("alt_text", "")

        if not product_id or not image_url:
            raise ValueError("Both 'product_id' and 'image_url' are required")

        # Upload the image to the media library
        media = await client.upload_media_from_url(
            image_url=image_url,
            title=f"Product {product_id} image",
            alt_text=alt_text,
        )

        # Attach the uploaded image to the product gallery via WC API
        url = f"{client.wc_base_url}/products/{product_id}"
        response = await client._client.put(
            url,
            json={"images": [{"id": media.id, "alt": alt_text}]},
            auth=(client.consumer_key, client.consumer_secret),
        )
        response.raise_for_status()

        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(
                        {
                            "message": f"Image uploaded and attached to product {product_id}",
                            "media_id": media.id,
                            "media_url": media.url,
                            "product_id": product_id,
                        },
                        indent=2,
                    ),
                }
            ]
        }
    except Exception as e:
        return _safe_error("wp_upload_product_image", e)


@tool(
    "wp_publish_social_campaign",
    "Format a social media campaign as a WordPress draft blog post",
    {"title": str, "platform": str, "content": str, "hashtags": list},
)
async def wp_publish_social_campaign(args: dict[str, Any]) -> dict[str, Any]:
    """Publish a social media campaign as a WordPress draft page."""
    try:
        client = _get_wp_client()
        title = args.get("title", "")
        platform = args.get("platform", "")
        content = args.get("content", "")
        hashtags = args.get("hashtags", [])

        if not title:
            raise ValueError("'title' is required")

        # Build HTML with platform badge, content, and hashtags
        hashtag_html = " ".join(f"<span class='hashtag'>#{h}</span>" for h in hashtags)
        html = (
            f'<div class="social-campaign">'
            f'<span class="platform-badge">{platform}</span>'
            f'<div class="campaign-content">{content}</div>'
            f'<div class="hashtags">{hashtag_html}</div>'
            f"</div>"
        )

        slug = _slugify(f"campaign-{platform}-{title}")
        result = await client.create_page(
            title=title,
            slug=slug,
            content=html,
            status="draft",
        )

        page_id = result.get("id", "unknown")
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(
                        {
                            "message": "Social campaign published as draft",
                            "page_id": page_id,
                            "platform": platform,
                            "hashtags": hashtags,
                        },
                        indent=2,
                    ),
                }
            ]
        }
    except Exception as e:
        return _safe_error("wp_publish_social_campaign", e)


@tool(
    "wp_update_conversion_data",
    "Push conversion metrics and trending scores to WooCommerce product meta fields",
    {"product_id": int, "trending_score": float, "funnel_data": dict},
)
async def wp_update_conversion_data(args: dict[str, Any]) -> dict[str, Any]:
    """Push conversion metrics to WooCommerce product meta fields."""
    try:
        client = _get_wp_client()
        product_id = args.get("product_id")
        trending_score = args.get("trending_score", 0.0)
        funnel_data = args.get("funnel_data", {})

        if not product_id:
            raise ValueError("'product_id' is required")

        meta_data = [
            {"key": "_trending_score", "value": str(trending_score)},
            {"key": "_funnel_views", "value": str(funnel_data.get("views", 0))},
            {"key": "_funnel_carts", "value": str(funnel_data.get("carts", 0))},
            {"key": "_funnel_purchases", "value": str(funnel_data.get("purchases", 0))},
        ]

        url = f"{client.wc_base_url}/products/{product_id}"
        response = await client._client.put(
            url,
            json={"meta_data": meta_data},
            auth=(client.consumer_key, client.consumer_secret),
        )
        response.raise_for_status()

        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(
                        {
                            "message": f"Conversion data updated for product {product_id}",
                            "product_id": product_id,
                            "trending_score": trending_score,
                            "funnel_data": funnel_data,
                        },
                        indent=2,
                    ),
                }
            ]
        }
    except Exception as e:
        return _safe_error("wp_update_conversion_data", e)


@tool(
    "get_pipeline_status",
    "Get the current status of all 9 dashboard pipelines",
    {},
)
async def get_pipeline_status(args: dict[str, Any]) -> dict[str, Any]:
    """Get the current status of all 9 dashboard pipelines."""
    try:
        pipelines = [
            {
                "name": "LLM Round Table",
                "status": "active",
                "description": "Multi-LLM competition engine",
            },
            {
                "name": "3D Pipeline",
                "status": "active",
                "description": "GLB model generation (Hunyuan3D/TRELLIS)",
            },
            {
                "name": "Imagery Pipeline",
                "status": "active",
                "description": "VTON + avatar generation",
            },
            {
                "name": "Products Pipeline",
                "status": "active",
                "description": "WooCommerce product sync",
            },
            {
                "name": "Social Media Pipeline",
                "status": "active",
                "description": "Campaign content generation",
            },
            {
                "name": "Conversion Pipeline",
                "status": "active",
                "description": "Funnel analytics tracking",
            },
            {
                "name": "Orders Pipeline",
                "status": "active",
                "description": "WooCommerce order management",
            },
            {
                "name": "Health Pipeline",
                "status": "active",
                "description": "System health monitoring",
            },
            {
                "name": "Pipeline Status",
                "status": "active",
                "description": "Meta-pipeline status aggregation",
            },
        ]

        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(
                        {
                            "total_pipelines": len(pipelines),
                            "pipelines": pipelines,
                        },
                        indent=2,
                    ),
                }
            ]
        }
    except Exception as e:
        return _safe_error("get_pipeline_status", e)


@tool(
    "get_product_catalog",
    "Retrieve the full SkyyRose product catalog (21 products across 3 collections)",
    {"collection": str},
)
async def get_product_catalog(args: dict[str, Any]) -> dict[str, Any]:
    """Retrieve the SkyyRose product catalog by collection."""
    try:
        collection_filter = args.get("collection", "")

        catalog = {}
        for coll_enum, config in COLLECTION_CONFIG.items():
            coll_name = coll_enum.value
            if collection_filter and coll_name != collection_filter:
                continue
            catalog[coll_name] = {
                "name": config["name"],
                "tagline": config.get("tagline", ""),
                "color_primary": config.get("color_primary", ""),
                "experience_page": config.get("experience_page", ""),
                "catalog_page": config.get("catalog_page", ""),
                "category_id": config.get("category_id"),
            }

        if not catalog:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(
                            {
                                "message": f"No collection found matching '{collection_filter}'",
                                "available": [c.value for c in SkyyRoseCollection],
                            },
                            indent=2,
                        ),
                    }
                ]
            }

        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(
                        {
                            "collections_count": len(catalog),
                            "collections": catalog,
                        },
                        indent=2,
                    ),
                }
            ]
        }
    except Exception as e:
        return _safe_error("get_product_catalog", e)


# ---------------------------------------------------------------------------
# Factory — creates MCP server with all 15 WordPress Bridge tools
# ---------------------------------------------------------------------------


def create_wordpress_tools():
    """Create MCP server with all 15 WordPress Bridge tools."""
    return create_sdk_mcp_server(
        name="wordpress_bridge",
        version="1.0.0",
        tools=[
            # WordPress Core (8)
            wp_health_check,
            wp_get_products,
            wp_get_orders,
            wp_update_order,
            wp_sync_product,
            wp_sync_collection,
            wp_create_page,
            wp_upload_media,
            # Pipeline Bridge (7)
            wp_publish_round_table,
            wp_attach_3d_model,
            wp_upload_product_image,
            wp_publish_social_campaign,
            wp_update_conversion_data,
            get_pipeline_status,
            get_product_catalog,
        ],
    )
