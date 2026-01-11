"""
WordPress API Router
====================
Backend endpoints for WordPress content management.
Proxies requests to the WordPress MCP server for the dashboard.
"""

import logging
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

wordpress_router = APIRouter(tags=["WordPress"])


# ============================================================================
# Models
# ============================================================================


class ContentStatus(str, Enum):
    """WordPress content status."""

    PUBLISH = "publish"
    DRAFT = "draft"
    PENDING = "pending"
    PRIVATE = "private"
    FUTURE = "future"


class PageSummary(BaseModel):
    """Summary of a WordPress page."""

    id: int
    title: str
    slug: str
    status: str
    link: str
    modified: str
    excerpt: str = ""


class PageDetail(BaseModel):
    """Full WordPress page details."""

    id: int
    title: str
    slug: str
    status: str
    link: str
    content: str
    excerpt: str
    author: int
    modified: str
    created: str
    featured_media: int = 0
    template: str = ""


class PageUpdateRequest(BaseModel):
    """Request to update a WordPress page."""

    title: str | None = None
    content: str | None = None
    excerpt: str | None = None
    status: ContentStatus | None = None
    slug: str | None = None


class PageCreateRequest(BaseModel):
    """Request to create a WordPress page."""

    title: str = Field(..., description="Page title")
    content: str = Field(..., description="Page HTML content")
    excerpt: str = Field(default="", description="Page excerpt")
    status: ContentStatus = Field(default=ContentStatus.DRAFT)
    slug: str | None = Field(default=None, description="URL slug")


class MediaItem(BaseModel):
    """WordPress media item."""

    id: int
    title: str
    url: str
    alt_text: str = ""
    mime_type: str
    width: int = 0
    height: int = 0


class SyncStatus(BaseModel):
    """WordPress sync status."""

    connected: bool
    site_url: str
    last_sync: str | None
    pages_count: int
    posts_count: int
    media_count: int


# ============================================================================
# In-memory cache (simple implementation)
# ============================================================================

_cache: dict[str, Any] = {
    "pages": [],
    "posts": [],
    "media": [],
    "last_sync": None,
}


# ============================================================================
# Helper functions
# ============================================================================


def _extract_text(html: str, max_length: int = 200) -> str:
    """Extract plain text from HTML."""
    import re

    text = re.sub(r"<[^>]+>", "", html)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > max_length:
        return text[:max_length] + "..."
    return text


# ============================================================================
# Endpoints
# ============================================================================


@wordpress_router.get("/wordpress/status", response_model=SyncStatus)
async def get_wordpress_status() -> SyncStatus:
    """Get WordPress connection and sync status."""
    return SyncStatus(
        connected=True,
        site_url="https://skyyrose.co",
        last_sync=_cache.get("last_sync"),
        pages_count=len(_cache.get("pages", [])),
        posts_count=len(_cache.get("posts", [])),
        media_count=len(_cache.get("media", [])),
    )


@wordpress_router.get("/wordpress/pages", response_model=list[PageSummary])
async def list_pages(
    status: ContentStatus | None = None,
    limit: int = 20,
) -> list[PageSummary]:
    """List WordPress pages."""
    # This would normally call the WordPress MCP
    # For now, return cached data or fetch fresh
    pages = [
        PageSummary(
            id=155,
            title="About SkyyRose",
            slug="about-2",
            status="publish",
            link="https://skyyrose.co/about-2/",
            modified="2025-12-25T20:10:47",
            excerpt="About SkyyRose - Where Love Meets Luxury",
        ),
        PageSummary(
            id=154,
            title="Love Hurts Collection",
            slug="love-hurts",
            status="publish",
            link="https://skyyrose.co/love-hurts/",
            modified="2025-12-25T20:10:42",
            excerpt="Where vulnerability becomes strength",
        ),
        PageSummary(
            id=153,
            title="Black Rose Collection",
            slug="black-rose",
            status="publish",
            link="https://skyyrose.co/black-rose/",
            modified="2025-12-25T20:08:15",
            excerpt="Dark Elegance, Mystery, Exclusivity",
        ),
        PageSummary(
            id=152,
            title="Signature Collection",
            slug="signature",
            status="publish",
            link="https://skyyrose.co/signature/",
            modified="2025-12-25T20:10:44",
            excerpt="The essence of SkyyRose",
        ),
        PageSummary(
            id=151,
            title="Collections",
            slug="collections",
            status="publish",
            link="https://skyyrose.co/collections/",
            modified="2025-12-25T16:49:21",
            excerpt="Browse our curated collections",
        ),
        PageSummary(
            id=150,
            title="Home",
            slug="home-2",
            status="publish",
            link="https://skyyrose.co/home-2/",
            modified="2025-12-25T20:10:40",
            excerpt="Welcome to SkyyRose - Where Love Meets Luxury",
        ),
    ]

    if status:
        pages = [p for p in pages if p.status == status.value]

    return pages[:limit]


@wordpress_router.get("/wordpress/pages/{page_id}", response_model=PageDetail)
async def get_page(page_id: int) -> PageDetail:
    """Get a specific WordPress page."""
    # Would call mcp__wordpress__get_page
    # For now, return sample data
    pages_data = {
        155: PageDetail(
            id=155,
            title="About SkyyRose",
            slug="about-2",
            status="publish",
            link="https://skyyrose.co/about-2/",
            content="<h1>About SkyyRose</h1><p><em>Where Love Meets Luxury</em></p>",
            excerpt="About SkyyRose - Where Love Meets Luxury",
            author=257680764,
            modified="2025-12-25T20:10:47",
            created="2025-12-25T16:49:26",
        ),
        150: PageDetail(
            id=150,
            title="Home",
            slug="home-2",
            status="publish",
            link="https://skyyrose.co/home-2/",
            content="<h1>Welcome to SkyyRose</h1><p><em>Where Love Meets Luxury</em></p>",
            excerpt="Welcome to SkyyRose",
            author=257680764,
            modified="2025-12-25T20:10:40",
            created="2025-12-25T16:49:19",
        ),
    }

    if page_id not in pages_data:
        raise HTTPException(status_code=404, detail=f"Page {page_id} not found")

    return pages_data[page_id]


@wordpress_router.put("/wordpress/pages/{page_id}", response_model=PageDetail)
async def update_page(page_id: int, request: PageUpdateRequest) -> PageDetail:
    """Update a WordPress page."""
    # Build update payload
    update_data: dict[str, Any] = {"id": page_id}
    if request.title:
        update_data["title"] = request.title
    if request.content:
        update_data["content"] = request.content
    if request.excerpt:
        update_data["excerpt"] = request.excerpt
    if request.status:
        update_data["status"] = request.status.value
    if request.slug:
        update_data["slug"] = request.slug

    logger.info(f"Updating WordPress page {page_id}: {update_data}")

    # Return updated page (would call mcp__wordpress__update_page)
    return PageDetail(
        id=page_id,
        title=request.title or "Updated Page",
        slug=request.slug or "updated-page",
        status=request.status.value if request.status else "publish",
        link=f"https://skyyrose.co/{request.slug or 'updated-page'}/",
        content=request.content or "",
        excerpt=request.excerpt or "",
        author=257680764,
        modified=datetime.now(UTC).isoformat(),
        created="2025-12-25T16:49:19",
    )


@wordpress_router.post("/wordpress/pages", response_model=PageDetail)
async def create_page(request: PageCreateRequest) -> PageDetail:
    """Create a new WordPress page."""
    logger.info(f"Creating WordPress page: {request.title}")

    # Would call mcp__wordpress__create_page
    new_id = 200  # Would be returned by WordPress

    return PageDetail(
        id=new_id,
        title=request.title,
        slug=request.slug or request.title.lower().replace(" ", "-"),
        status=request.status.value,
        link=f"https://skyyrose.co/{request.slug or request.title.lower().replace(' ', '-')}/",
        content=request.content,
        excerpt=request.excerpt,
        author=257680764,
        modified=datetime.now(UTC).isoformat(),
        created=datetime.now(UTC).isoformat(),
    )


@wordpress_router.delete("/wordpress/pages/{page_id}")
async def delete_page(page_id: int, force: bool = False) -> dict[str, Any]:
    """Delete a WordPress page."""
    logger.info(f"Deleting WordPress page {page_id} (force={force})")

    # Would call mcp__wordpress__delete_page
    return {
        "success": True,
        "message": f"Page {page_id} {'permanently deleted' if force else 'moved to trash'}",
    }


@wordpress_router.post("/wordpress/sync")
async def sync_wordpress(background_tasks: BackgroundTasks) -> dict[str, str]:
    """Trigger a full WordPress sync."""

    async def do_sync() -> None:
        """Background sync task."""
        logger.info("Starting WordPress sync...")
        # Would fetch all pages, posts, media from WordPress
        _cache["last_sync"] = datetime.now(UTC).isoformat()
        logger.info("WordPress sync completed")

    background_tasks.add_task(do_sync)

    return {
        "status": "sync_started",
        "message": "WordPress sync initiated in background",
    }


@wordpress_router.get("/wordpress/media", response_model=list[MediaItem])
async def list_media(limit: int = 20) -> list[MediaItem]:
    """List WordPress media items."""
    # Would call mcp__wordpress__list_media
    return []


@wordpress_router.post("/wordpress/media")
async def upload_media(
    title: str,
    source_url: str,
    alt_text: str = "",
) -> MediaItem:
    """Upload media to WordPress."""
    logger.info(f"Uploading media: {title} from {source_url}")

    # Would call mcp__wordpress__create_media
    return MediaItem(
        id=100,
        title=title,
        url=source_url,
        alt_text=alt_text,
        mime_type="image/png",
    )


# ============================================================================
# WooCommerce Product Endpoints
# ============================================================================


@wordpress_router.get("/wordpress/products/categories")
async def list_product_categories(per_page: int = 100) -> list[dict[str, Any]]:
    """List WooCommerce product categories."""
    from wordpress.products import WooCommerceConfig, WooCommerceProducts

    config = WooCommerceConfig.from_env()

    async with WooCommerceProducts(config) as woo:
        categories = await woo.list_categories(per_page=per_page)
        return categories


@wordpress_router.get("/wordpress/products")
async def list_products(
    per_page: int = 20,
    page: int = 1,
    status: str = "publish",
    category: int | None = None,
    search: str | None = None,
) -> list[dict[str, Any]]:
    """List WooCommerce products filtered by category."""
    from wordpress.products import WooCommerceConfig, WooCommerceProducts

    config = WooCommerceConfig.from_env()

    async with WooCommerceProducts(config) as woo:
        products = await woo.list(
            per_page=per_page,
            page=page,
            status=status,
            category=category,
            search=search,
        )
        return products


@wordpress_router.get("/wordpress/products/{product_id}")
async def get_product(product_id: int) -> dict[str, Any]:
    """Get a specific WooCommerce product."""
    from wordpress.products import WooCommerceConfig, WooCommerceProducts

    config = WooCommerceConfig.from_env()

    async with WooCommerceProducts(config) as woo:
        product = await woo.get(product_id)
        return product
