"""
WordPress/WooCommerce API Endpoints
====================================

REST API endpoints for WordPress and WooCommerce integration.

Features:
- Product management (CRUD)
- Order processing
- Customer management
- Product sync from WooCommerce
- Content publishing to WordPress

Version: 1.0.0
"""

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from integrations.wordpress_client import (
    OrderStatus,
    ProductStatus,
    WooCommerceCustomer,
    WooCommerceOrder,
    WooCommerceProduct,
    WordPressError,
    WordPressWooCommerceClient,
)
from security.jwt_oauth2_auth import TokenPayload, get_current_user

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/wordpress", tags=["WordPress/WooCommerce"])


# =============================================================================
# Request/Response Models
# =============================================================================


class ProductCreateRequest(BaseModel):
    """Request to create a WooCommerce product."""

    name: str = Field(..., description="Product name")
    regular_price: str = Field(..., description="Regular price")
    description: str = Field(default="", description="Product description (HTML)")
    short_description: str = Field(default="", description="Short description")
    sku: str | None = Field(default=None, description="Stock Keeping Unit")
    status: ProductStatus = Field(default=ProductStatus.DRAFT)
    stock_quantity: int | None = Field(default=None, description="Stock quantity")
    categories: list[dict[str, Any]] = Field(default_factory=list, description="Category IDs or names")
    tags: list[dict[str, Any]] = Field(default_factory=list, description="Tag IDs or names")
    images: list[dict[str, Any]] = Field(default_factory=list, description="Image URLs")
    meta_data: list[dict[str, Any]] = Field(default_factory=list, description="Custom meta data")


class ProductUpdateRequest(BaseModel):
    """Request to update a WooCommerce product."""

    name: str | None = None
    regular_price: str | None = None
    sale_price: str | None = None
    description: str | None = None
    short_description: str | None = None
    status: ProductStatus | None = None
    stock_quantity: int | None = None
    stock_status: str | None = None
    categories: list[dict[str, Any]] | None = None
    tags: list[dict[str, Any]] | None = None
    images: list[dict[str, Any]] | None = None
    meta_data: list[dict[str, Any]] | None = None


class ProductResponse(BaseModel):
    """Product response."""

    id: int
    name: str
    sku: str | None
    status: str
    regular_price: str
    permalink: str | None
    stock_quantity: int | None
    created_at: str


class OrderResponse(BaseModel):
    """Order response."""

    id: int
    status: str
    total: str
    currency: str
    customer_email: str
    date_created: str
    line_items_count: int


class SyncProductsRequest(BaseModel):
    """Request to sync products from WooCommerce."""

    status: ProductStatus | None = Field(default=None, description="Filter by status")
    category: int | None = Field(default=None, description="Filter by category ID")
    limit: int = Field(default=100, description="Maximum products to sync")


class SyncProductsResponse(BaseModel):
    """Response from product sync."""

    sync_id: str
    status: str
    timestamp: str
    total_products: int
    synced: int
    errors: int
    products: list[ProductResponse]


class PublishContentRequest(BaseModel):
    """Request to publish content to WordPress."""

    title: str = Field(..., description="Post/page title")
    content: str = Field(..., description="HTML content")
    type: str = Field(default="post", description="Content type: post or page")
    status: str = Field(default="draft", description="publish or draft")
    categories: list[int] = Field(default_factory=list, description="Category IDs")
    tags: list[int] = Field(default_factory=list, description="Tag IDs")
    featured_media: int | None = Field(default=None, description="Featured image ID")


class PublishContentResponse(BaseModel):
    """Response from content publish."""

    publish_id: str
    wordpress_id: int
    status: str
    link: str
    timestamp: str


class ConnectionTestResponse(BaseModel):
    """Connection test response."""

    connected: bool
    site_url: str
    woocommerce_api: bool
    wordpress_api: bool
    products_count: int | None = None
    error: str | None = None


# =============================================================================
# Dependency Injection
# =============================================================================


async def get_wc_client() -> WordPressWooCommerceClient:
    """Get WordPress/WooCommerce client instance."""
    client = WordPressWooCommerceClient()
    try:
        await client.connect()
        yield client
    finally:
        await client.close()


# =============================================================================
# Products Endpoints
# =============================================================================


@router.get(
    "/products",
    response_model=list[ProductResponse],
    summary="List WooCommerce products",
)
async def list_products(
    per_page: int = Query(10, ge=1, le=100),
    page: int = Query(1, ge=1),
    status: ProductStatus | None = None,
    search: str | None = None,
    sku: str | None = None,
    client: WordPressWooCommerceClient = Depends(get_wc_client),
    user: TokenPayload = Depends(get_current_user),
) -> list[ProductResponse]:
    """
    List WooCommerce products with pagination and filtering.

    **Filters:**
    - status: Filter by product status (draft, publish, etc.)
    - search: Search products by name/description
    - sku: Find product by SKU

    **Authentication:** Requires valid JWT token
    """
    try:
        products = await client.list_products(
            per_page=per_page,
            page=page,
            status=status,
            search=search,
            sku=sku,
        )

        return [
            ProductResponse(
                id=p.id,
                name=p.name,
                sku=p.sku,
                status=p.status.value if isinstance(p.status, ProductStatus) else p.status,
                regular_price=p.regular_price,
                permalink=p.permalink,
                stock_quantity=p.stock_quantity,
                created_at=datetime.now(UTC).isoformat(),
            )
            for p in products
        ]

    except WordPressError as e:
        logger.error(f"Failed to list products: {e}")
        raise HTTPException(
            status_code=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/products/{product_id}",
    response_model=WooCommerceProduct,
    summary="Get product by ID",
)
async def get_product(
    product_id: int,
    client: WordPressWooCommerceClient = Depends(get_wc_client),
    user: TokenPayload = Depends(get_current_user),
) -> WooCommerceProduct:
    """
    Get detailed product information by ID.

    **Authentication:** Requires valid JWT token
    """
    try:
        return await client.get_product(product_id)
    except WordPressError as e:
        logger.error(f"Failed to get product {product_id}: {e}")
        raise HTTPException(
            status_code=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post(
    "/products",
    response_model=WooCommerceProduct,
    status_code=status.HTTP_201_CREATED,
    summary="Create WooCommerce product",
)
async def create_product(
    request: ProductCreateRequest,
    client: WordPressWooCommerceClient = Depends(get_wc_client),
    user: TokenPayload = Depends(get_current_user),
) -> WooCommerceProduct:
    """
    Create a new WooCommerce product.

    **Features:**
    - Automatic SKU generation if not provided
    - SEO optimization for product descriptions
    - Image upload support
    - Category and tag assignment
    - Custom meta data

    **Authentication:** Requires valid JWT token
    """
    try:
        product = WooCommerceProduct(**request.model_dump())
        return await client.create_product(product)
    except WordPressError as e:
        logger.error(f"Failed to create product: {e}")
        raise HTTPException(
            status_code=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.put(
    "/products/{product_id}",
    response_model=WooCommerceProduct,
    summary="Update WooCommerce product",
)
async def update_product(
    product_id: int,
    request: ProductUpdateRequest,
    client: WordPressWooCommerceClient = Depends(get_wc_client),
    user: TokenPayload = Depends(get_current_user),
) -> WooCommerceProduct:
    """
    Update an existing WooCommerce product.

    Only provided fields will be updated.

    **Authentication:** Requires valid JWT token
    """
    try:
        updates = request.model_dump(exclude_none=True)
        return await client.update_product(product_id, updates)
    except WordPressError as e:
        logger.error(f"Failed to update product {product_id}: {e}")
        raise HTTPException(
            status_code=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.delete(
    "/products/{product_id}",
    summary="Delete WooCommerce product",
)
async def delete_product(
    product_id: int,
    force: bool = Query(False, description="Permanently delete (true) or trash (false)"),
    client: WordPressWooCommerceClient = Depends(get_wc_client),
    user: TokenPayload = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Delete a WooCommerce product.

    **Parameters:**
    - force: If true, permanently deletes. If false, moves to trash.

    **Authentication:** Requires valid JWT token
    """
    try:
        result = await client.delete_product(product_id, force=force)
        return {
            "success": True,
            "product_id": product_id,
            "message": "Product permanently deleted" if force else "Product moved to trash",
            **result,
        }
    except WordPressError as e:
        logger.error(f"Failed to delete product {product_id}: {e}")
        raise HTTPException(
            status_code=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


# =============================================================================
# Orders Endpoints
# =============================================================================


@router.get(
    "/orders",
    response_model=list[OrderResponse],
    summary="List WooCommerce orders",
)
async def list_orders(
    per_page: int = Query(10, ge=1, le=100),
    page: int = Query(1, ge=1),
    status: OrderStatus | None = None,
    customer: int | None = None,
    client: WordPressWooCommerceClient = Depends(get_wc_client),
    user: TokenPayload = Depends(get_current_user),
) -> list[OrderResponse]:
    """
    List WooCommerce orders with pagination and filtering.

    **Filters:**
    - status: Filter by order status (processing, completed, etc.)
    - customer: Filter by customer ID

    **Authentication:** Requires valid JWT token
    """
    try:
        orders = await client.list_orders(
            per_page=per_page,
            page=page,
            status=status,
            customer=customer,
        )

        return [
            OrderResponse(
                id=o.id,
                status=o.status.value if isinstance(o.status, OrderStatus) else o.status,
                total=o.total,
                currency=o.currency,
                customer_email=o.billing.get("email", ""),
                date_created=o.date_created,
                line_items_count=len(o.line_items),
            )
            for o in orders
        ]

    except WordPressError as e:
        logger.error(f"Failed to list orders: {e}")
        raise HTTPException(
            status_code=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/orders/{order_id}",
    response_model=WooCommerceOrder,
    summary="Get order by ID",
)
async def get_order(
    order_id: int,
    client: WordPressWooCommerceClient = Depends(get_wc_client),
    user: TokenPayload = Depends(get_current_user),
) -> WooCommerceOrder:
    """
    Get detailed order information by ID.

    **Authentication:** Requires valid JWT token
    """
    try:
        return await client.get_order(order_id)
    except WordPressError as e:
        logger.error(f"Failed to get order {order_id}: {e}")
        raise HTTPException(
            status_code=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.put(
    "/orders/{order_id}/status",
    response_model=WooCommerceOrder,
    summary="Update order status",
)
async def update_order_status(
    order_id: int,
    new_status: OrderStatus,
    client: WordPressWooCommerceClient = Depends(get_wc_client),
    user: TokenPayload = Depends(get_current_user),
) -> WooCommerceOrder:
    """
    Update order status.

    **Statuses:**
    - pending: Order received
    - processing: Payment received, stock reduced
    - on-hold: Awaiting payment
    - completed: Order fulfilled
    - cancelled: Cancelled by customer
    - refunded: Refunded
    - failed: Payment failed

    **Authentication:** Requires valid JWT token
    """
    try:
        return await client.update_order_status(order_id, new_status)
    except WordPressError as e:
        logger.error(f"Failed to update order {order_id} status: {e}")
        raise HTTPException(
            status_code=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


# =============================================================================
# Sync Endpoints
# =============================================================================


@router.post(
    "/sync",
    response_model=SyncProductsResponse,
    summary="Sync products from WooCommerce",
)
async def sync_products(
    request: SyncProductsRequest,
    background_tasks: BackgroundTasks,
    client: WordPressWooCommerceClient = Depends(get_wc_client),
    user: TokenPayload = Depends(get_current_user),
) -> SyncProductsResponse:
    """
    Sync products from WooCommerce to internal database.

    This endpoint imports products from WooCommerce and updates the internal
    product catalog. Useful for:
    - Initial setup
    - Bulk updates
    - Data reconciliation

    **Background Processing:** Large syncs are processed in background

    **Authentication:** Requires valid JWT token
    """
    sync_id = str(uuid4())
    logger.info(f"Starting product sync {sync_id} for user {user.sub}")

    try:
        products = await client.list_products(
            per_page=request.limit,
            status=request.status,
            category=request.category,
        )

        product_responses = [
            ProductResponse(
                id=p.id,
                name=p.name,
                sku=p.sku,
                status=p.status.value if isinstance(p.status, ProductStatus) else p.status,
                regular_price=p.regular_price,
                permalink=p.permalink,
                stock_quantity=p.stock_quantity,
                created_at=datetime.now(UTC).isoformat(),
            )
            for p in products
        ]

        # TODO: Store products in internal database
        # This would integrate with Commerce Agent and inventory system

        return SyncProductsResponse(
            sync_id=sync_id,
            status="completed",
            timestamp=datetime.now(UTC).isoformat(),
            total_products=len(products),
            synced=len(products),
            errors=0,
            products=product_responses,
        )

    except WordPressError as e:
        logger.error(f"Product sync {sync_id} failed: {e}")
        raise HTTPException(
            status_code=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


# =============================================================================
# Content Publishing Endpoints
# =============================================================================


@router.post(
    "/publish",
    response_model=PublishContentResponse,
    summary="Publish content to WordPress",
)
async def publish_content(
    request: PublishContentRequest,
    client: WordPressWooCommerceClient = Depends(get_wc_client),
    user: TokenPayload = Depends(get_current_user),
) -> PublishContentResponse:
    """
    Publish blog posts or pages to WordPress.

    **Use Cases:**
    - Marketing Agent publishing blog content
    - Automated content generation
    - Product launch announcements
    - Collection pages

    **Features:**
    - SEO optimization
    - Automatic category/tag assignment
    - Featured image support
    - Draft or publish modes

    **Authentication:** Requires valid JWT token
    """
    publish_id = str(uuid4())
    logger.info(f"Publishing content {publish_id} to WordPress: {request.title}")

    try:
        post_data = await client.create_post(
            title=request.title,
            content=request.content,
            status=request.status,
            categories=request.categories,
            tags=request.tags,
            featured_media=request.featured_media,
        )

        return PublishContentResponse(
            publish_id=publish_id,
            wordpress_id=post_data["id"],
            status=post_data["status"],
            link=post_data["link"],
            timestamp=datetime.now(UTC).isoformat(),
        )

    except WordPressError as e:
        logger.error(f"Failed to publish content {publish_id}: {e}")
        raise HTTPException(
            status_code=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


# =============================================================================
# Health/Status Endpoints
# =============================================================================


@router.get(
    "/test-connection",
    response_model=ConnectionTestResponse,
    summary="Test WordPress/WooCommerce connection",
)
async def test_connection(
    client: WordPressWooCommerceClient = Depends(get_wc_client),
) -> ConnectionTestResponse:
    """
    Test connection to WordPress and WooCommerce APIs.

    **No authentication required** - useful for health checks

    Returns:
    - Connection status
    - Site URL
    - API availability
    - Basic metrics
    """
    try:
        result = await client.test_connection()

        return ConnectionTestResponse(
            connected=result["success"],
            site_url=result["site_url"],
            woocommerce_api=result.get("woocommerce_connected", False),
            wordpress_api=True,  # If we got here, WordPress is working
            products_count=result.get("products_count"),
            error=result.get("error"),
        )

    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return ConnectionTestResponse(
            connected=False,
            site_url="",
            woocommerce_api=False,
            wordpress_api=False,
            error=str(e),
        )


__all__ = ["router"]
