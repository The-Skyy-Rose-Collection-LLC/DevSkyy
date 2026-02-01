"""WordPress.com REST API Client.

Modern client for WordPress.com sites using OAuth2 authentication.
Supports WooCommerce REST API v3.
"""

from __future__ import annotations

from typing import Any, TypedDict

import httpx
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential


class WordPressConfig(BaseModel):
    """WordPress.com site configuration."""

    site_url: str = Field(..., description="WordPress.com site URL (e.g., https://skyyrose.co)")
    api_token: str | None = Field(
        default=None, description="WordPress.com OAuth2 access token (Bearer auth)"
    )
    username: str | None = Field(
        default=None, description="WordPress username (for Application Password auth)"
    )
    app_password: str | None = Field(
        default=None, description="WordPress Application Password (Basic auth)"
    )
    timeout: int = Field(default=30, description="Request timeout in seconds")

    def model_post_init(self, __context: Any) -> None:
        """Validate that either api_token or username+app_password is provided."""
        if not self.api_token and not (self.username and self.app_password):
            raise ValueError(
                "Must provide either 'api_token' (OAuth2) or both 'username' and 'app_password' (Application Password)"
            )


class WooCommerceConfig(BaseModel):
    """WooCommerce REST API configuration."""

    consumer_key: str = Field(..., description="WooCommerce consumer key")
    consumer_secret: str = Field(..., description="WooCommerce consumer secret")
    version: str = Field(default="wc/v3", description="WooCommerce API version")


class WordPressProduct(TypedDict, total=False):
    """WooCommerce product data."""

    id: int
    name: str
    slug: str
    type: str  # simple, grouped, external, variable
    status: str  # draft, pending, private, publish
    description: str
    short_description: str
    sku: str
    price: str
    regular_price: str
    sale_price: str
    images: list[dict[str, Any]]
    categories: list[dict[str, Any]]
    tags: list[dict[str, Any]]
    attributes: list[dict[str, Any]]
    stock_quantity: int | None
    manage_stock: bool
    in_stock: bool


class WordPressComClient:
    """WordPress.com REST API client with retry logic."""

    def __init__(
        self,
        config: WordPressConfig,
        woo_config: WooCommerceConfig | None = None,
    ) -> None:
        """Initialize WordPress.com client.

        Args:
            config: WordPress site configuration
            woo_config: Optional WooCommerce configuration
        """
        self.config = config
        self.woo_config = woo_config

        # WordPress REST API client - use appropriate auth method
        if config.username and config.app_password:
            # Application Password authentication (Basic Auth)
            self.wp_client = httpx.AsyncClient(
                base_url=config.site_url,
                auth=(config.username, config.app_password),
                headers={"Content-Type": "application/json"},
                timeout=config.timeout,
            )
        elif config.api_token:
            # OAuth2 authentication (Bearer token)
            self.wp_client = httpx.AsyncClient(
                base_url=config.site_url,
                headers={
                    "Authorization": f"Bearer {config.api_token}",
                    "Content-Type": "application/json",
                },
                timeout=config.timeout,
            )
        else:
            raise ValueError("WordPress authentication not configured")

        # WooCommerce REST API client (uses Basic Auth)
        if woo_config:
            self.woo_client = httpx.AsyncClient(
                base_url=config.site_url,
                auth=(woo_config.consumer_key, woo_config.consumer_secret),
                headers={"Content-Type": "application/json"},
                timeout=config.timeout,
            )
        else:
            self.woo_client = None

    async def __aenter__(self) -> WordPressComClient:
        """Async context manager entry."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        await self.close()

    async def close(self) -> None:
        """Close HTTP clients."""
        await self.wp_client.aclose()
        if self.woo_client:
            await self.woo_client.aclose()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def _wp_request(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Make WordPress REST API request with retry.

        Args:
            method: HTTP method
            endpoint: API endpoint (e.g., /wp-json/wp/v2/posts)
            **kwargs: Additional request parameters

        Returns:
            Response JSON data

        Raises:
            httpx.HTTPStatusError: On HTTP error
        """
        response = await self.wp_client.request(method, endpoint, **kwargs)
        response.raise_for_status()
        return response.json() if response.content else {}

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def _woo_request(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        """Make WooCommerce REST API request with retry.

        Args:
            method: HTTP method
            endpoint: API endpoint (e.g., /wp-json/wc/v3/products)
            **kwargs: Additional request parameters

        Returns:
            Response JSON data

        Raises:
            ValueError: If WooCommerce not configured
            httpx.HTTPStatusError: On HTTP error
        """
        if not self.woo_client:
            raise ValueError("WooCommerce not configured")

        response = await self.woo_client.request(method, endpoint, **kwargs)
        response.raise_for_status()
        return response.json() if response.content else {}

    # =========================================================================
    # WordPress Posts API
    # =========================================================================

    async def create_post(
        self,
        title: str,
        content: str,
        status: str = "draft",
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Create WordPress post.

        Args:
            title: Post title
            content: Post content (HTML)
            status: Post status (draft, publish, pending, private)
            **kwargs: Additional post data

        Returns:
            Created post data
        """
        data = {
            "title": title,
            "content": content,
            "status": status,
            **kwargs,
        }
        return await self._wp_request("POST", "/wp-json/wp/v2/posts", json=data)

    async def get_post(self, post_id: int) -> dict[str, Any]:
        """Get WordPress post by ID."""
        return await self._wp_request("GET", f"/wp-json/wp/v2/posts/{post_id}")

    async def update_post(self, post_id: int, **kwargs: Any) -> dict[str, Any]:
        """Update WordPress post."""
        return await self._wp_request(
            "POST",
            f"/wp-json/wp/v2/posts/{post_id}",
            json=kwargs,
        )

    # =========================================================================
    # WordPress Media API
    # =========================================================================

    async def upload_media(
        self,
        file_path: str,
        title: str | None = None,
        alt_text: str | None = None,
    ) -> dict[str, Any]:
        """Upload media file to WordPress.

        Args:
            file_path: Path to file
            title: Optional media title
            alt_text: Optional alt text

        Returns:
            Uploaded media data
        """
        with open(file_path, "rb") as f:
            files = {"file": f}
            data = {}
            if title:
                data["title"] = title
            if alt_text:
                data["alt_text"] = alt_text

            response = await self.wp_client.post(
                "/wp-json/wp/v2/media",
                files=files,
                data=data,
            )
            response.raise_for_status()
            return response.json()

    # =========================================================================
    # WooCommerce Products API
    # =========================================================================

    async def create_product(self, product: WordPressProduct) -> WordPressProduct:
        """Create WooCommerce product.

        Args:
            product: Product data

        Returns:
            Created product data
        """
        result = await self._woo_request(
            "POST",
            f"/wp-json/{self.woo_config.version}/products",
            json=product,
        )
        return result  # type: ignore

    async def get_product(self, product_id: int) -> WordPressProduct:
        """Get WooCommerce product by ID."""
        result = await self._woo_request(
            "GET",
            f"/wp-json/{self.woo_config.version}/products/{product_id}",
        )
        return result  # type: ignore

    async def update_product(
        self,
        product_id: int,
        product: WordPressProduct,
    ) -> WordPressProduct:
        """Update WooCommerce product."""
        result = await self._woo_request(
            "PUT",
            f"/wp-json/{self.woo_config.version}/products/{product_id}",
            json=product,
        )
        return result  # type: ignore

    async def list_products(
        self,
        per_page: int = 100,
        page: int = 1,
        **params: Any,
    ) -> list[WordPressProduct]:
        """List WooCommerce products.

        Args:
            per_page: Products per page (max 100)
            page: Page number
            **params: Additional query parameters

        Returns:
            List of products
        """
        result = await self._woo_request(
            "GET",
            f"/wp-json/{self.woo_config.version}/products",
            params={"per_page": per_page, "page": page, **params},
        )
        return result  # type: ignore

    # =========================================================================
    # WooCommerce Orders API
    # =========================================================================

    async def get_order(self, order_id: int) -> dict[str, Any]:
        """Get WooCommerce order by ID."""
        result = await self._woo_request(
            "GET",
            f"/wp-json/{self.woo_config.version}/orders/{order_id}",
        )
        return result  # type: ignore

    async def list_orders(
        self,
        per_page: int = 100,
        page: int = 1,
        **params: Any,
    ) -> list[dict[str, Any]]:
        """List WooCommerce orders."""
        result = await self._woo_request(
            "GET",
            f"/wp-json/{self.woo_config.version}/orders",
            params={"per_page": per_page, "page": page, **params},
        )
        return result  # type: ignore


async def create_wordpress_client(
    site_url: str,
    api_token: str,
    consumer_key: str | None = None,
    consumer_secret: str | None = None,
) -> WordPressComClient:
    """Create WordPress.com client.

    Args:
        site_url: WordPress.com site URL
        api_token: WordPress.com OAuth2 access token
        consumer_key: Optional WooCommerce consumer key
        consumer_secret: Optional WooCommerce consumer secret

    Returns:
        Configured WordPress.com client
    """
    wp_config = WordPressConfig(site_url=site_url, api_token=api_token)

    woo_config = None
    if consumer_key and consumer_secret:
        woo_config = WooCommerceConfig(
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
        )

    return WordPressComClient(config=wp_config, woo_config=woo_config)
