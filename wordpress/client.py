"""
DevSkyy WordPress Integration Layer
Production-ready WordPress.com/WooCommerce REST API client
"""

import os
from typing import Any, Dict, List, Optional

import requests
from requests.auth import HTTPBasicAuth
from tenacity import retry, stop_after_attempt, wait_exponential

try:
    import structlog

    logger = structlog.get_logger()
except ImportError:
    import logging

    logger = logging.getLogger(__name__)


class WordPressAPIError(Exception):
    """Custom exception for WordPress API errors"""

    pass


class WordPressClient:
    """
    WordPress REST API client with authentication and error handling
    Supports both WordPress.com sites and self-hosted WordPress
    """

    def __init__(self, site_url: str, username: str, app_password: str, timeout: int = 30):
        """
        Initialize WordPress API client

        Args:
            site_url: Full WordPress site URL (e.g., https://skyyrose.co)
            username: WordPress username
            app_password: Application password (generate in WP admin)
            timeout: Request timeout in seconds
        """
        self.site_url = site_url.rstrip("/")
        self.api_base = f"{self.site_url}/wp-json/wp/v2"
        self.wc_api_base = f"{self.site_url}/wp-json/wc/v3"
        self.auth = HTTPBasicAuth(username, app_password)
        self.timeout = timeout
        self.session = requests.Session()
        self.session.auth = self.auth

        if hasattr(logger, "info"):
            logger.info("wordpress_client_initialized", site_url=site_url)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json: Optional[Dict] = None,
        use_wc_api: bool = False,
    ) -> Dict[str, Any]:
        """Make authenticated request to WordPress REST API with retry logic"""
        base_url = self.wc_api_base if use_wc_api else self.api_base
        url = f"{base_url}/{endpoint.lstrip('/')}"

        try:
            response = self.session.request(
                method=method.upper(), url=url, params=params, json=json, timeout=self.timeout
            )

            response.raise_for_status()

            if hasattr(logger, "info"):
                logger.info(
                    "wordpress_api_success",
                    method=method,
                    endpoint=endpoint,
                    status_code=response.status_code,
                )

            return response.json()

        except requests.exceptions.HTTPError as e:
            error_detail = e.response.json() if e.response.text else {}
            if hasattr(logger, "error"):
                logger.error(
                    "wordpress_api_http_error",
                    method=method,
                    endpoint=endpoint,
                    status_code=e.response.status_code,
                    error=error_detail,
                )
            raise WordPressAPIError(f"HTTP {e.response.status_code}: {error_detail}")

        except requests.exceptions.RequestException as e:
            if hasattr(logger, "error"):
                logger.error("wordpress_api_request_error", method=method, endpoint=endpoint, error=str(e))
            raise WordPressAPIError(f"Request failed: {str(e)}")

    # ==================== POSTS ====================

    def get_posts(
        self,
        per_page: int = 10,
        page: int = 1,
        search: Optional[str] = None,
        status: str = "publish",
        order: str = "desc",
        orderby: str = "date",
    ) -> List[Dict[str, Any]]:
        """Fetch posts with filtering and pagination"""
        params = {"per_page": per_page, "page": page, "status": status, "order": order, "orderby": orderby}
        if search:
            params["search"] = search

        return self._request("GET", "posts", params=params)

    def get_post(self, post_id: int) -> Dict[str, Any]:
        """Get single post by ID"""
        return self._request("GET", f"posts/{post_id}")

    def create_post(
        self,
        title: str,
        content: str,
        status: str = "draft",
        excerpt: Optional[str] = None,
        categories: Optional[List[int]] = None,
        tags: Optional[List[int]] = None,
        featured_media: Optional[int] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create new post"""
        data = {"title": title, "content": content, "status": status}

        if excerpt:
            data["excerpt"] = excerpt
        if categories:
            data["categories"] = categories
        if tags:
            data["tags"] = tags
        if featured_media:
            data["featured_media"] = featured_media
        if meta:
            data["meta"] = meta

        return self._request("POST", "posts", json=data)

    def update_post(
        self,
        post_id: int,
        title: Optional[str] = None,
        content: Optional[str] = None,
        status: Optional[str] = None,
        excerpt: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Update existing post"""
        data = {}

        if title:
            data["title"] = title
        if content:
            data["content"] = content
        if status:
            data["status"] = status
        if excerpt:
            data["excerpt"] = excerpt
        if meta:
            data["meta"] = meta

        return self._request("POST", f"posts/{post_id}", json=data)

    def delete_post(self, post_id: int, force: bool = False) -> Dict[str, Any]:
        """Delete post (move to trash or permanent)"""
        params = {"force": force}
        return self._request("DELETE", f"posts/{post_id}", params=params)

    # ==================== PAGES ====================

    def get_pages(
        self, per_page: int = 10, page: int = 1, search: Optional[str] = None, status: str = "publish"
    ) -> List[Dict[str, Any]]:
        """Fetch pages"""
        params = {"per_page": per_page, "page": page, "status": status}
        if search:
            params["search"] = search

        return self._request("GET", "pages", params=params)

    def create_page(
        self,
        title: str,
        content: str,
        status: str = "draft",
        parent: Optional[int] = None,
        template: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create new page"""
        data = {"title": title, "content": content, "status": status}

        if parent:
            data["parent"] = parent
        if template:
            data["template"] = template
        if meta:
            data["meta"] = meta

        return self._request("POST", "pages", json=data)

    # ==================== WOOCOMMERCE PRODUCTS ====================

    def get_products(
        self,
        per_page: int = 10,
        page: int = 1,
        search: Optional[str] = None,
        category: Optional[int] = None,
        status: str = "publish",
    ) -> List[Dict[str, Any]]:
        """Fetch WooCommerce products"""
        params = {"per_page": per_page, "page": page, "status": status}
        if search:
            params["search"] = search
        if category:
            params["category"] = category

        return self._request("GET", "products", params=params, use_wc_api=True)

    def get_product(self, product_id: int) -> Dict[str, Any]:
        """Get single product by ID"""
        return self._request("GET", f"products/{product_id}", use_wc_api=True)

    def create_product(
        self,
        name: str,
        type: str = "simple",
        regular_price: str = "",
        description: str = "",
        short_description: str = "",
        categories: Optional[List[Dict[str, int]]] = None,
        images: Optional[List[Dict[str, str]]] = None,
        attributes: Optional[List[Dict[str, Any]]] = None,
        meta_data: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Create new WooCommerce product"""
        data = {
            "name": name,
            "type": type,
            "regular_price": regular_price,
            "description": description,
            "short_description": short_description,
        }

        if categories:
            data["categories"] = categories
        if images:
            data["images"] = images
        if attributes:
            data["attributes"] = attributes
        if meta_data:
            data["meta_data"] = meta_data

        return self._request("POST", "products", json=data, use_wc_api=True)

    def update_product(
        self,
        product_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        short_description: Optional[str] = None,
        regular_price: Optional[str] = None,
        sale_price: Optional[str] = None,
        meta_data: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Update existing product"""
        data = {}

        if name:
            data["name"] = name
        if description:
            data["description"] = description
        if short_description:
            data["short_description"] = short_description
        if regular_price:
            data["regular_price"] = regular_price
        if sale_price:
            data["sale_price"] = sale_price
        if meta_data:
            data["meta_data"] = meta_data

        return self._request("PUT", f"products/{product_id}", json=data, use_wc_api=True)

    def delete_product(self, product_id: int, force: bool = False) -> Dict[str, Any]:
        """Delete product"""
        params = {"force": force}
        return self._request("DELETE", f"products/{product_id}", params=params, use_wc_api=True)

    # ==================== UTILITY METHODS ====================

    def test_connection(self) -> bool:
        """Test API connection and authentication"""
        try:
            self._request("GET", "/")
            if hasattr(logger, "info"):
                logger.info("wordpress_connection_test_success")
            return True
        except Exception as e:
            if hasattr(logger, "error"):
                logger.error("wordpress_connection_test_failed", error=str(e))
            return False

    def get_site_info(self) -> Dict[str, Any]:
        """Get site information"""
        url = f"{self.site_url}/wp-json"
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        return response.json()
