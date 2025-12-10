"""
WordPress REST API Client
=========================

Enterprise-grade WordPress REST API client with:
- Basic auth with application passwords
- Rate limiting with exponential backoff
- Comprehensive error handling
- Async support
- Connection pooling

References:
- WordPress REST API: https://developer.wordpress.org/rest-api/
- Authentication: https://developer.wordpress.org/rest-api/using-the-rest-api/authentication/
- Application Passwords: https://make.wordpress.org/core/2020/11/05/application-passwords-integration-guide/
"""

import os
import asyncio
import logging
import base64
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass, field
from enum import Enum
import json

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from pydantic import BaseModel, Field, HttpUrl

logger = logging.getLogger(__name__)


# =============================================================================
# Exceptions
# =============================================================================

class WordPressError(Exception):
    """Base WordPress API error"""
    def __init__(self, message: str, status_code: int = None, response: dict = None):
        self.message = message
        self.status_code = status_code
        self.response = response or {}
        super().__init__(self.message)


class AuthenticationError(WordPressError):
    """Authentication failed"""
    pass


class NotFoundError(WordPressError):
    """Resource not found"""
    pass


class RateLimitError(WordPressError):
    """Rate limit exceeded"""
    pass


class ValidationError(WordPressError):
    """Validation error"""
    pass


# =============================================================================
# Configuration
# =============================================================================

@dataclass
class WordPressConfig:
    """WordPress configuration"""
    url: str
    username: str
    app_password: str
    timeout: float = 30.0
    max_retries: int = 3
    verify_ssl: bool = True
    user_agent: str = "DevSkyy/2.0 WordPress-Client"
    
    # Rate limiting
    requests_per_minute: int = 60
    
    @classmethod
    def from_env(cls) -> "WordPressConfig":
        """Load configuration from environment variables"""
        return cls(
            url=os.getenv("WORDPRESS_URL", "https://skyyrose.co"),
            username=os.getenv("WORDPRESS_USERNAME", ""),
            app_password=os.getenv("WORDPRESS_APP_PASSWORD", ""),
            verify_ssl=os.getenv("WORDPRESS_VERIFY_SSL", "true").lower() == "true",
        )
    
    @property
    def auth_header(self) -> str:
        """Generate Basic auth header"""
        credentials = f"{self.username}:{self.app_password}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"
    
    @property
    def base_url(self) -> str:
        """Get base REST API URL"""
        url = self.url.rstrip("/")
        return f"{url}/wp-json"


# =============================================================================
# Response Models
# =============================================================================

class WPUser(BaseModel):
    """WordPress user"""
    id: int
    username: str
    name: str
    email: Optional[str] = None
    roles: List[str] = []
    avatar_urls: Dict[str, str] = {}


class WPPost(BaseModel):
    """WordPress post"""
    id: int
    date: str
    date_gmt: str
    modified: str
    modified_gmt: str
    slug: str
    status: str
    type: str
    link: str
    title: Dict[str, str]
    content: Dict[str, str]
    excerpt: Dict[str, str]
    author: int
    featured_media: int = 0
    categories: List[int] = []
    tags: List[int] = []


class WPPage(BaseModel):
    """WordPress page"""
    id: int
    date: str
    slug: str
    status: str
    type: str
    link: str
    title: Dict[str, str]
    content: Dict[str, str]
    author: int
    parent: int = 0
    menu_order: int = 0
    template: str = ""


# =============================================================================
# WordPress Client
# =============================================================================

class WordPressClient:
    """
    Enterprise WordPress REST API Client
    
    Usage:
        client = WordPressClient(
            url="https://skyyrose.co",
            username="admin",
            app_password="xxxx-xxxx-xxxx-xxxx"
        )
        
        # Get posts
        posts = await client.get_posts(per_page=10)
        
        # Create post
        post = await client.create_post(
            title="New Post",
            content="Content here",
            status="publish"
        )
    """
    
    def __init__(
        self,
        url: str = None,
        username: str = None,
        app_password: str = None,
        config: WordPressConfig = None
    ):
        if config:
            self.config = config
        else:
            self.config = WordPressConfig(
                url=url or os.getenv("WORDPRESS_URL", "https://skyyrose.co"),
                username=username or os.getenv("WORDPRESS_USERNAME", ""),
                app_password=app_password or os.getenv("WORDPRESS_APP_PASSWORD", ""),
            )
        
        self._client: Optional[httpx.AsyncClient] = None
        self._request_count = 0
        self._last_request_time = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    async def connect(self):
        """Initialize HTTP client"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.config.timeout,
                verify=self.config.verify_ssl,
                headers={
                    "Authorization": self.config.auth_header,
                    "User-Agent": self.config.user_agent,
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
            )
            logger.info(f"Connected to WordPress: {self.config.url}")
    
    async def close(self):
        """Close HTTP client"""
        if self._client:
            await self._client.aclose()
            self._client = None
            logger.info("WordPress client closed")
    
    def _handle_error(self, response: httpx.Response):
        """Handle API errors"""
        status = response.status_code
        
        try:
            data = response.json()
            message = data.get("message", response.text)
            code = data.get("code", "unknown")
        except json.JSONDecodeError:
            message = response.text
            code = "unknown"
        
        if status == 401:
            raise AuthenticationError(
                f"Authentication failed: {message}",
                status_code=status,
                response={"code": code}
            )
        elif status == 403:
            raise AuthenticationError(
                f"Permission denied: {message}",
                status_code=status,
                response={"code": code}
            )
        elif status == 404:
            raise NotFoundError(
                f"Resource not found: {message}",
                status_code=status,
                response={"code": code}
            )
        elif status == 429:
            raise RateLimitError(
                f"Rate limit exceeded: {message}",
                status_code=status,
                response={"code": code}
            )
        elif status == 400:
            raise ValidationError(
                f"Validation error: {message}",
                status_code=status,
                response={"code": code}
            )
        else:
            raise WordPressError(
                f"API error ({status}): {message}",
                status_code=status,
                response={"code": code}
            )
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((RateLimitError, httpx.TimeoutException)),
    )
    async def _request(
        self,
        method: str,
        endpoint: str,
        data: dict = None,
        params: dict = None,
        files: dict = None,
    ) -> Union[dict, list]:
        """Make API request with retry logic"""
        if self._client is None:
            await self.connect()
        
        url = f"{self.config.base_url}/{endpoint.lstrip('/')}"
        
        # Build request kwargs
        kwargs = {"params": params}
        
        if files:
            # File upload - use form data
            kwargs["files"] = files
            kwargs["data"] = data
        elif data:
            kwargs["json"] = data
        
        logger.debug(f"WordPress API: {method} {url}")
        
        response = await self._client.request(method, url, **kwargs)
        
        if response.status_code >= 400:
            self._handle_error(response)
        
        # Handle empty responses
        if response.status_code == 204:
            return {}
        
        return response.json()
    
    # -------------------------------------------------------------------------
    # Core Endpoints
    # -------------------------------------------------------------------------
    
    async def get_site_info(self) -> dict:
        """Get WordPress site information"""
        return await self._request("GET", "/")
    
    async def get_current_user(self) -> WPUser:
        """Get current authenticated user"""
        data = await self._request("GET", "/wp/v2/users/me")
        return WPUser(**data)
    
    async def test_connection(self) -> bool:
        """Test API connection"""
        try:
            await self.get_current_user()
            return True
        except WordPressError:
            return False
    
    # -------------------------------------------------------------------------
    # Posts
    # -------------------------------------------------------------------------
    
    async def get_posts(
        self,
        per_page: int = 10,
        page: int = 1,
        status: str = "publish",
        categories: List[int] = None,
        tags: List[int] = None,
        search: str = None,
        orderby: str = "date",
        order: str = "desc",
    ) -> List[WPPost]:
        """Get posts with filtering"""
        params = {
            "per_page": per_page,
            "page": page,
            "status": status,
            "orderby": orderby,
            "order": order,
        }
        
        if categories:
            params["categories"] = ",".join(map(str, categories))
        if tags:
            params["tags"] = ",".join(map(str, tags))
        if search:
            params["search"] = search
        
        data = await self._request("GET", "/wp/v2/posts", params=params)
        return [WPPost(**post) for post in data]
    
    async def get_post(self, post_id: int) -> WPPost:
        """Get single post by ID"""
        data = await self._request("GET", f"/wp/v2/posts/{post_id}")
        return WPPost(**data)
    
    async def create_post(
        self,
        title: str,
        content: str,
        status: str = "draft",
        excerpt: str = None,
        categories: List[int] = None,
        tags: List[int] = None,
        featured_media: int = None,
        meta: dict = None,
    ) -> WPPost:
        """Create new post"""
        data = {
            "title": title,
            "content": content,
            "status": status,
        }
        
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
        
        result = await self._request("POST", "/wp/v2/posts", data=data)
        return WPPost(**result)
    
    async def update_post(self, post_id: int, **kwargs) -> WPPost:
        """Update existing post"""
        result = await self._request("POST", f"/wp/v2/posts/{post_id}", data=kwargs)
        return WPPost(**result)
    
    async def delete_post(self, post_id: int, force: bool = False) -> dict:
        """Delete post"""
        params = {"force": force}
        return await self._request("DELETE", f"/wp/v2/posts/{post_id}", params=params)
    
    # -------------------------------------------------------------------------
    # Pages
    # -------------------------------------------------------------------------
    
    async def get_pages(
        self,
        per_page: int = 10,
        page: int = 1,
        status: str = "publish",
        parent: int = None,
        search: str = None,
    ) -> List[WPPage]:
        """Get pages"""
        params = {
            "per_page": per_page,
            "page": page,
            "status": status,
        }
        
        if parent is not None:
            params["parent"] = parent
        if search:
            params["search"] = search
        
        data = await self._request("GET", "/wp/v2/pages", params=params)
        return [WPPage(**p) for p in data]
    
    async def get_page(self, page_id: int) -> WPPage:
        """Get single page"""
        data = await self._request("GET", f"/wp/v2/pages/{page_id}")
        return WPPage(**data)
    
    async def create_page(
        self,
        title: str,
        content: str,
        status: str = "draft",
        parent: int = None,
        template: str = None,
        meta: dict = None,
    ) -> WPPage:
        """Create new page"""
        data = {
            "title": title,
            "content": content,
            "status": status,
        }
        
        if parent:
            data["parent"] = parent
        if template:
            data["template"] = template
        if meta:
            data["meta"] = meta
        
        result = await self._request("POST", "/wp/v2/pages", data=data)
        return WPPage(**result)
    
    async def update_page(self, page_id: int, **kwargs) -> WPPage:
        """Update existing page"""
        result = await self._request("POST", f"/wp/v2/pages/{page_id}", data=kwargs)
        return WPPage(**result)
    
    # -------------------------------------------------------------------------
    # Categories & Tags
    # -------------------------------------------------------------------------
    
    async def get_categories(self, per_page: int = 100) -> List[dict]:
        """Get post categories"""
        return await self._request(
            "GET", "/wp/v2/categories",
            params={"per_page": per_page}
        )
    
    async def create_category(
        self,
        name: str,
        slug: str = None,
        description: str = None,
        parent: int = None,
    ) -> dict:
        """Create category"""
        data = {"name": name}
        if slug:
            data["slug"] = slug
        if description:
            data["description"] = description
        if parent:
            data["parent"] = parent
        
        return await self._request("POST", "/wp/v2/categories", data=data)
    
    async def get_tags(self, per_page: int = 100) -> List[dict]:
        """Get post tags"""
        return await self._request(
            "GET", "/wp/v2/tags",
            params={"per_page": per_page}
        )
    
    async def create_tag(self, name: str, slug: str = None, description: str = None) -> dict:
        """Create tag"""
        data = {"name": name}
        if slug:
            data["slug"] = slug
        if description:
            data["description"] = description
        
        return await self._request("POST", "/wp/v2/tags", data=data)
    
    # -------------------------------------------------------------------------
    # Custom Post Types (Elementor Templates)
    # -------------------------------------------------------------------------
    
    async def get_elementor_templates(self, per_page: int = 100) -> List[dict]:
        """Get Elementor templates"""
        try:
            return await self._request(
                "GET", "/wp/v2/elementor_library",
                params={"per_page": per_page}
            )
        except NotFoundError:
            logger.warning("Elementor templates endpoint not available")
            return []
    
    async def create_elementor_template(
        self,
        title: str,
        template_type: str,
        content: str,
        status: str = "publish",
    ) -> dict:
        """Create Elementor template"""
        data = {
            "title": title,
            "status": status,
            "content": content,
            "meta": {
                "_elementor_template_type": template_type,
            }
        }
        
        return await self._request("POST", "/wp/v2/elementor_library", data=data)
    
    # -------------------------------------------------------------------------
    # Settings & Options
    # -------------------------------------------------------------------------
    
    async def get_settings(self) -> dict:
        """Get site settings"""
        return await self._request("GET", "/wp/v2/settings")
    
    async def update_settings(self, **kwargs) -> dict:
        """Update site settings"""
        return await self._request("POST", "/wp/v2/settings", data=kwargs)
    
    # -------------------------------------------------------------------------
    # Search
    # -------------------------------------------------------------------------
    
    async def search(
        self,
        query: str,
        type: str = "post",
        per_page: int = 10,
    ) -> List[dict]:
        """Search site content"""
        params = {
            "search": query,
            "type": type,
            "per_page": per_page,
        }
        return await self._request("GET", "/wp/v2/search", params=params)
    
    # -------------------------------------------------------------------------
    # Plugin Status
    # -------------------------------------------------------------------------
    
    async def get_plugins(self) -> List[dict]:
        """Get installed plugins (requires admin)"""
        try:
            return await self._request("GET", "/wp/v2/plugins")
        except (AuthenticationError, NotFoundError):
            logger.warning("Cannot access plugins endpoint")
            return []
    
    async def check_woocommerce(self) -> bool:
        """Check if WooCommerce is active"""
        try:
            await self._request("GET", "/wc/v3/system_status")
            return True
        except (NotFoundError, AuthenticationError):
            return False
    
    async def check_elementor(self) -> bool:
        """Check if Elementor is active"""
        try:
            templates = await self.get_elementor_templates(per_page=1)
            return True
        except (NotFoundError, AuthenticationError):
            return False
