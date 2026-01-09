"""
WordPress/WooCommerce REST API Client
======================================

Production-grade client for WordPress REST API and WooCommerce REST API.

Features:
- OAuth 1.0a authentication for WooCommerce
- Application Password authentication for WordPress
- Async/await with proper connection pooling
- Automatic retries with exponential backoff
- Comprehensive error handling
- Type-safe with Pydantic models

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import logging
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal
from urllib.parse import quote

import aiohttp
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# =============================================================================
# Exceptions
# =============================================================================


class WordPressError(Exception):
    """Base WordPress/WooCommerce error."""

    def __init__(
        self, message: str, status_code: int | None = None, response_data: dict | None = None
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class AuthenticationError(WordPressError):
    """Authentication failed."""


class NotFoundError(WordPressError):
    """Resource not found."""


class RateLimitError(WordPressError):
    """Rate limit exceeded."""


class ValidationError(WordPressError):
    """Validation failed."""


# =============================================================================
# Models
# =============================================================================


class ProductStatus(str, Enum):
    """WooCommerce product status."""

    DRAFT = "draft"
    PENDING = "pending"
    PRIVATE = "private"
    PUBLISH = "publish"


class OrderStatus(str, Enum):
    """WooCommerce order status."""

    PENDING = "pending"
    PROCESSING = "processing"
    ON_HOLD = "on-hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    FAILED = "failed"


class WooCommerceProduct(BaseModel):
    """WooCommerce product model."""

    id: int | None = None
    name: str
    type: str = "simple"
    status: ProductStatus = ProductStatus.DRAFT
    regular_price: str
    sale_price: str | None = None
    description: str = ""
    short_description: str = ""
    sku: str | None = None
    manage_stock: bool = True
    stock_quantity: int | None = None
    stock_status: Literal["instock", "outofstock", "onbackorder"] = "instock"
    categories: list[dict[str, Any]] = Field(default_factory=list)
    tags: list[dict[str, Any]] = Field(default_factory=list)
    images: list[dict[str, Any]] = Field(default_factory=list)
    attributes: list[dict[str, Any]] = Field(default_factory=list)
    meta_data: list[dict[str, Any]] = Field(default_factory=list)
    permalink: str | None = None

    class Config:
        use_enum_values = True


class WooCommerceOrder(BaseModel):
    """WooCommerce order model."""

    id: int
    status: OrderStatus
    currency: str
    total: str
    customer_id: int
    billing: dict[str, Any]
    shipping: dict[str, Any]
    line_items: list[dict[str, Any]]
    shipping_lines: list[dict[str, Any]] = Field(default_factory=list)
    meta_data: list[dict[str, Any]] = Field(default_factory=list)
    date_created: str
    date_modified: str

    class Config:
        use_enum_values = True


class WooCommerceCustomer(BaseModel):
    """WooCommerce customer model."""

    id: int | None = None
    email: str
    first_name: str = ""
    last_name: str = ""
    username: str | None = None
    billing: dict[str, Any] = Field(default_factory=dict)
    shipping: dict[str, Any] = Field(default_factory=dict)
    meta_data: list[dict[str, Any]] = Field(default_factory=list)


# =============================================================================
# Configuration
# =============================================================================


@dataclass
class WordPressConfig:
    """WordPress/WooCommerce API configuration."""

    site_url: str = field(default_factory=lambda: os.getenv("WORDPRESS_URL", ""))

    # WooCommerce OAuth 1.0a credentials
    wc_consumer_key: str = field(default_factory=lambda: os.getenv("WOOCOMMERCE_KEY", ""))
    wc_consumer_secret: str = field(default_factory=lambda: os.getenv("WOOCOMMERCE_SECRET", ""))

    # WordPress Application Password (for posts/pages)
    wp_username: str = field(default_factory=lambda: os.getenv("WORDPRESS_USERNAME", ""))
    wp_app_password: str = field(default_factory=lambda: os.getenv("WORDPRESS_APP_PASSWORD", ""))

    # Configuration
    api_version: str = "wc/v3"
    wp_api_version: str = "wp/v2"
    timeout: float = 30.0
    max_retries: int = 3
    verify_ssl: bool = True

    @classmethod
    def from_env(cls) -> WordPressConfig:
        """Create config from environment variables."""
        return cls()

    @property
    def wc_base_url(self) -> str:
        """WooCommerce API base URL."""
        return f"{self.site_url.rstrip('/')}/wp-json/{self.api_version}"

    @property
    def wp_base_url(self) -> str:
        """WordPress API base URL."""
        return f"{self.site_url.rstrip('/')}/wp-json/{self.wp_api_version}"


# =============================================================================
# OAuth 1.0a Signature Generator
# =============================================================================


class OAuth1Signature:
    """OAuth 1.0a signature generator for WooCommerce."""

    @staticmethod
    def generate_signature(
        method: str,
        url: str,
        params: dict[str, Any],
        consumer_secret: str,
    ) -> dict[str, str]:
        """
        Generate OAuth 1.0a signature for WooCommerce API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            url: Request URL
            params: Query parameters
            consumer_secret: WooCommerce consumer secret

        Returns:
            OAuth parameters dict with signature
        """
        # OAuth parameters
        oauth_params = {
            "oauth_consumer_key": params.get("oauth_consumer_key", ""),
            "oauth_timestamp": str(int(time.time())),
            "oauth_nonce": hashlib.sha1(str(time.time()).encode()).hexdigest(),
            "oauth_signature_method": "HMAC-SHA256",
        }

        # Combine with query params
        all_params = {**params, **oauth_params}

        # Sort parameters
        sorted_params = sorted(all_params.items())

        # Create parameter string
        param_string = "&".join(
            [f"{quote(str(k), safe='')}={quote(str(v), safe='')}" for k, v in sorted_params]
        )

        # Create signature base string
        base_string = f"{method.upper()}&{quote(url, safe='')}&{quote(param_string, safe='')}"

        # Create signing key
        signing_key = f"{quote(consumer_secret, safe='')}&"

        # Generate signature
        signature = hmac.new(signing_key.encode(), base_string.encode(), hashlib.sha256).digest()

        # Base64 encode
        import base64

        oauth_params["oauth_signature"] = base64.b64encode(signature).decode()

        return oauth_params


# =============================================================================
# WordPress/WooCommerce Client
# =============================================================================


class WordPressWooCommerceClient:
    """
    Unified WordPress and WooCommerce REST API client.

    Features:
    - WooCommerce API with OAuth 1.0a
    - WordPress API with Application Password
    - Async/await with connection pooling
    - Automatic retries with exponential backoff
    - Production-grade error handling

    Example:
        async with WordPressWooCommerceClient() as client:
            products = await client.list_products(per_page=10)
            orders = await client.list_orders(status="processing")
    """

    def __init__(self, config: WordPressConfig | None = None) -> None:
        """
        Initialize client.

        Args:
            config: Optional configuration (defaults to environment variables)
        """
        self.config = config or WordPressConfig.from_env()
        self._session: aiohttp.ClientSession | None = None
        self._validate_config()

    def _validate_config(self) -> None:
        """Validate configuration."""
        if not self.config.site_url:
            raise ValueError("WORDPRESS_URL is required")
        if not self.config.wc_consumer_key or not self.config.wc_consumer_secret:
            raise ValueError("WOOCOMMERCE_KEY and WOOCOMMERCE_SECRET are required")

    async def __aenter__(self) -> WordPressWooCommerceClient:
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        await self.close()

    async def connect(self) -> None:
        """Create HTTP session with connection pooling."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            connector = aiohttp.TCPConnector(
                limit=100,
                limit_per_host=10,
                ttl_dns_cache=300,
            )
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector,
            )
            logger.info(f"Connected to WordPress site: {self.config.site_url}")

    async def close(self) -> None:
        """Close HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
            logger.info("WordPress client closed")

    async def _request_wc(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> Any:
        """
        Make WooCommerce API request with OAuth 1.0a.

        Args:
            method: HTTP method
            endpoint: API endpoint (e.g., 'products')
            params: Query parameters
            json: JSON body

        Returns:
            Response data

        Raises:
            WordPressError: If request fails
        """
        await self.connect()

        url = f"{self.config.wc_base_url}/{endpoint.lstrip('/')}"
        params = params or {}

        # Add OAuth consumer key to params
        params["oauth_consumer_key"] = self.config.wc_consumer_key

        # Generate OAuth signature
        oauth_params = OAuth1Signature.generate_signature(
            method=method,
            url=url,
            params=params,
            consumer_secret=self.config.wc_consumer_secret,
        )

        # Merge OAuth params
        params.update(oauth_params)

        # Retry with exponential backoff
        for attempt in range(self.config.max_retries):
            try:
                async with self._session.request(
                    method,
                    url,
                    params=params,
                    json=json,
                    ssl=self.config.verify_ssl,
                ) as response:
                    # Handle rate limiting
                    if response.status == 429:
                        retry_after = int(response.headers.get("Retry-After", 60))
                        logger.warning(f"Rate limited, retrying after {retry_after}s")
                        await asyncio.sleep(retry_after)
                        continue

                    # Handle errors
                    if response.status == 401:
                        raise AuthenticationError("WooCommerce authentication failed", 401)
                    if response.status == 404:
                        raise NotFoundError("Resource not found", 404)
                    if response.status >= 400:
                        error_data = await response.json()
                        raise WordPressError(
                            error_data.get("message", "Request failed"),
                            response.status,
                            error_data,
                        )

                    # Success
                    if response.status == 204:
                        return {}
                    return await response.json()

            except aiohttp.ClientError as e:
                if attempt == self.config.max_retries - 1:
                    raise WordPressError(
                        f"Request failed after {self.config.max_retries} retries: {e}"
                    )
                # Exponential backoff
                await asyncio.sleep(2**attempt)

        raise WordPressError("Request failed after max retries")

    async def _request_wp(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> Any:
        """
        Make WordPress API request with Application Password.

        Args:
            method: HTTP method
            endpoint: API endpoint (e.g., 'posts')
            params: Query parameters
            json: JSON body

        Returns:
            Response data
        """
        await self.connect()

        url = f"{self.config.wp_base_url}/{endpoint.lstrip('/')}"

        # Application Password authentication
        auth = aiohttp.BasicAuth(self.config.wp_username, self.config.wp_app_password)

        for attempt in range(self.config.max_retries):
            try:
                async with self._session.request(
                    method,
                    url,
                    params=params,
                    json=json,
                    auth=auth,
                    ssl=self.config.verify_ssl,
                ) as response:
                    if response.status >= 400:
                        error_text = await response.text()
                        raise WordPressError(error_text, response.status)

                    if response.status == 204:
                        return {}
                    return await response.json()

            except aiohttp.ClientError as e:
                if attempt == self.config.max_retries - 1:
                    raise WordPressError(str(e))
                await asyncio.sleep(2**attempt)

    # =========================================================================
    # WooCommerce Products
    # =========================================================================

    async def list_products(
        self,
        per_page: int = 10,
        page: int = 1,
        status: ProductStatus | None = None,
        category: int | None = None,
        search: str | None = None,
        sku: str | None = None,
    ) -> list[WooCommerceProduct]:
        """
        List WooCommerce products.

        Args:
            per_page: Results per page (max 100)
            page: Page number
            status: Filter by status
            category: Filter by category ID
            search: Search term
            sku: Filter by SKU

        Returns:
            List of products
        """
        params = {"per_page": min(per_page, 100), "page": page}
        if status:
            params["status"] = status.value
        if category:
            params["category"] = category
        if search:
            params["search"] = search
        if sku:
            params["sku"] = sku

        data = await self._request_wc("GET", "products", params=params)
        return [WooCommerceProduct(**item) for item in data]

    async def get_product(self, product_id: int) -> WooCommerceProduct:
        """
        Get product by ID.

        Args:
            product_id: WooCommerce product ID

        Returns:
            Product data
        """
        data = await self._request_wc("GET", f"products/{product_id}")
        return WooCommerceProduct(**data)

    async def create_product(self, product: WooCommerceProduct) -> WooCommerceProduct:
        """
        Create a new product.

        Args:
            product: Product data

        Returns:
            Created product with ID
        """
        data = await self._request_wc(
            "POST",
            "products",
            json=product.model_dump(exclude_none=True, exclude={"id", "permalink"}),
        )
        return WooCommerceProduct(**data)

    async def update_product(
        self,
        product_id: int,
        updates: dict[str, Any],
    ) -> WooCommerceProduct:
        """
        Update existing product.

        Args:
            product_id: Product ID
            updates: Fields to update

        Returns:
            Updated product
        """
        data = await self._request_wc("PUT", f"products/{product_id}", json=updates)
        return WooCommerceProduct(**data)

    async def delete_product(self, product_id: int, force: bool = False) -> dict[str, Any]:
        """
        Delete product.

        Args:
            product_id: Product ID
            force: Permanently delete (true) or move to trash (false)

        Returns:
            Deletion result
        """
        params = {"force": "true" if force else "false"}
        return await self._request_wc("DELETE", f"products/{product_id}", params=params)

    # =========================================================================
    # WooCommerce Orders
    # =========================================================================

    async def list_orders(
        self,
        per_page: int = 10,
        page: int = 1,
        status: OrderStatus | None = None,
        customer: int | None = None,
        after: str | None = None,
        before: str | None = None,
    ) -> list[WooCommerceOrder]:
        """
        List WooCommerce orders.

        Args:
            per_page: Results per page
            page: Page number
            status: Filter by status
            customer: Filter by customer ID
            after: Filter orders after date (ISO 8601)
            before: Filter orders before date (ISO 8601)

        Returns:
            List of orders
        """
        params = {"per_page": per_page, "page": page}
        if status:
            params["status"] = status.value
        if customer:
            params["customer"] = customer
        if after:
            params["after"] = after
        if before:
            params["before"] = before

        data = await self._request_wc("GET", "orders", params=params)
        return [WooCommerceOrder(**item) for item in data]

    async def get_order(self, order_id: int) -> WooCommerceOrder:
        """
        Get order by ID.

        Args:
            order_id: Order ID

        Returns:
            Order data
        """
        data = await self._request_wc("GET", f"orders/{order_id}")
        return WooCommerceOrder(**data)

    async def update_order_status(
        self,
        order_id: int,
        status: OrderStatus,
    ) -> WooCommerceOrder:
        """
        Update order status.

        Args:
            order_id: Order ID
            status: New status

        Returns:
            Updated order
        """
        data = await self._request_wc(
            "PUT",
            f"orders/{order_id}",
            json={"status": status.value},
        )
        return WooCommerceOrder(**data)

    # =========================================================================
    # WooCommerce Customers
    # =========================================================================

    async def list_customers(
        self,
        per_page: int = 10,
        page: int = 1,
        search: str | None = None,
        email: str | None = None,
    ) -> list[WooCommerceCustomer]:
        """
        List WooCommerce customers.

        Args:
            per_page: Results per page
            page: Page number
            search: Search term
            email: Filter by email

        Returns:
            List of customers
        """
        params = {"per_page": per_page, "page": page}
        if search:
            params["search"] = search
        if email:
            params["email"] = email

        data = await self._request_wc("GET", "customers", params=params)
        return [WooCommerceCustomer(**item) for item in data]

    # =========================================================================
    # WordPress Posts/Pages
    # =========================================================================

    async def list_posts(
        self,
        per_page: int = 10,
        page: int = 1,
        status: str | None = None,
        search: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        List WordPress posts.

        Args:
            per_page: Results per page
            page: Page number
            status: Filter by status
            search: Search term

        Returns:
            List of posts
        """
        params = {"per_page": per_page, "page": page}
        if status:
            params["status"] = status
        if search:
            params["search"] = search

        return await self._request_wp("GET", "posts", params=params)

    async def create_post(
        self,
        title: str,
        content: str,
        status: str = "draft",
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Create WordPress post.

        Args:
            title: Post title
            content: Post content (HTML)
            status: Post status (draft, publish, etc.)
            **kwargs: Additional post fields

        Returns:
            Created post data
        """
        post_data = {
            "title": title,
            "content": content,
            "status": status,
            **kwargs,
        }
        return await self._request_wp("POST", "posts", json=post_data)

    async def test_connection(self) -> dict[str, Any]:
        """
        Test API connectivity.

        Returns:
            Connection status and site info
        """
        try:
            # Test WooCommerce API
            products = await self._request_wc("GET", "products", params={"per_page": 1})

            return {
                "success": True,
                "site_url": self.config.site_url,
                "woocommerce_connected": True,
                "products_count": len(products),
            }
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return {
                "success": False,
                "error": str(e),
            }


__all__ = [
    "WordPressWooCommerceClient",
    "WordPressConfig",
    "WordPressError",
    "AuthenticationError",
    "NotFoundError",
    "RateLimitError",
    "ValidationError",
    "WooCommerceProduct",
    "WooCommerceOrder",
    "WooCommerceCustomer",
    "ProductStatus",
    "OrderStatus",
]
