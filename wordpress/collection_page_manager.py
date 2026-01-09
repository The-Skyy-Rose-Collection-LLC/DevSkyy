"""
SkyyRose Collection Page Manager
=================================

Manages WordPress collection pages with 3D experiences, template storage,
and agent-based content management.

Features:
- Upload 3D HTML experiences to WordPress media
- Create collection pages with embedded experiences
- Store design templates for agent reference
- Manage collection metadata (colors, themes, products)
- Integration with SuperAgent content management

Collections:
1. BLACK ROSE - Dark elegance, gothic luxury
2. LOVE HURTS - Emotional expression, castle environment
3. SIGNATURE - Premium essentials, runway showcase

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import aiohttp
import structlog

logger = structlog.get_logger(__name__)


class CollectionType(str, Enum):
    """SkyyRose collection types"""

    BLACK_ROSE = "black_rose"
    LOVE_HURTS = "love_hurts"
    SIGNATURE = "signature"


@dataclass
class CollectionDesign:
    """Design specifications for a collection"""

    name: str
    slug: str
    type: CollectionType
    theme: str
    colors: dict[str, str]
    description: str
    html_file_path: str
    thumbnail_url: str | None = None
    metadata: dict[str, Any] | None = None


class CollectionDesignTemplates:
    """Store and manage design templates for agent reference"""

    TEMPLATES: dict[CollectionType, CollectionDesign] = {
        CollectionType.BLACK_ROSE: CollectionDesign(
            name="BLACK ROSE Garden",
            slug="black-rose-garden",
            type=CollectionType.BLACK_ROSE,
            theme="Dark Elegance, Mystery, Exclusivity",
            colors={
                "primary": "#000000",
                "secondary": "#C0C0C0",
                "accent": "#FFFFFF",
            },
            description="Limited edition pieces with dark elegance aesthetic. "
            "Virtual garden environment featuring gothic luxury meets modern streetwear.",
            html_file_path="skyyrose-black-rose-garden-production.html",
            metadata={
                "vibe": "Gothic luxury meets modern streetwear",
                "target_audience": "Fashion-forward, bold individuals",
                "environment": "Dark garden with spotlight effects",
                "file_size_kb": 30,
                "features": [
                    "Real-time 3D rendering",
                    "PBR materials",
                    "HDR lighting",
                    "Particle effects",
                ],
            },
        ),
        CollectionType.LOVE_HURTS: CollectionDesign(
            name="LOVE HURTS Castle",
            slug="love-hurts-castle",
            type=CollectionType.LOVE_HURTS,
            theme="Emotional Expression, Vulnerability, Strength",
            colors={
                "primary": "#8B4049",
                "secondary": "#C9356C",
                "accent": "#FF6B9D",
            },
            description="Emotional expression pieces honoring founder's family name. "
            "Castle/throne room environment with dramatic lighting.",
            html_file_path="skyyrose-love-hurts-castle-production.html",
            metadata={
                "vibe": "Raw emotion meets high fashion",
                "target_audience": "Storytellers, artists, romantics",
                "environment": "Castle interior with dramatic lighting",
                "file_size_kb": 31,
                "features": [
                    "Dramatic lighting",
                    "Castle environment",
                    "Interactive elements",
                    "Accessibility controls",
                ],
            },
        ),
        CollectionType.SIGNATURE: CollectionDesign(
            name="SIGNATURE Runway",
            slug="signature-runway",
            type=CollectionType.SIGNATURE,
            theme="Premium Essentials, Oakland Heritage",
            colors={
                "primary": "#C9A962",
                "secondary": "#FFD700",
                "accent": "#000000",
            },
            description="Premium essentials showcasing Oakland-made luxury streetwear. "
            "Runway show environment with gold accents.",
            html_file_path="skyyrose-signature-runway-production.html",
            metadata={
                "vibe": "Luxury streetwear fundamentals",
                "target_audience": "Quality-conscious, style leaders",
                "environment": "Fashion runway with gold accents",
                "file_size_kb": 19,
                "features": [
                    "Runway showcase",
                    "Gold accents",
                    "Premium presentation",
                    "Mobile optimized",
                ],
            },
        ),
    }

    @classmethod
    def get_template(cls, collection_type: CollectionType) -> CollectionDesign:
        """Get design template for a collection"""
        template = cls.TEMPLATES.get(collection_type)
        if not template:
            raise ValueError(f"No template found for {collection_type}")
        return template

    @classmethod
    def get_all_templates(cls) -> dict[CollectionType, CollectionDesign]:
        """Get all design templates"""
        return cls.TEMPLATES.copy()

    @classmethod
    def to_agent_reference(cls, collection_type: CollectionType) -> dict[str, Any]:
        """Convert template to agent reference format"""
        template = cls.get_template(collection_type)
        return {
            "name": template.name,
            "slug": template.slug,
            "theme": template.theme,
            "colors": template.colors,
            "description": template.description,
            "html_file": template.html_file_path,
            "metadata": template.metadata or {},
            "agent_instructions": f"""
You are managing the {template.name} collection for SkyyRose.

COLLECTION DETAILS:
- Theme: {template.theme}
- Description: {template.description}
- Primary Color: {template.colors.get("primary", "N/A")}
- Environment: {template.metadata.get("environment", "N/A") if template.metadata else "N/A"}

GUIDELINES:
1. Maintain brand consistency with the "{template.theme}" theme
2. Use approved color palette for all designs
3. Reference the 3D experience HTML file: {template.html_file_path}
4. Ensure all content aligns with target audience: {template.metadata.get("target_audience", "N/A") if template.metadata else "N/A"}
5. Keep copy consistent with "{template.metadata.get("vibe", "luxury") if template.metadata else "luxury"}" vibe

WHEN IN DOUBT: Reference the {template.html_file_path} file for design system,
colors, and overall aesthetic.

RECOVERY PROTOCOL: If design breaks, restore from:
- Template: CollectionDesignTemplates.get_template(CollectionType.{collection_type.name})
- Colors: {json.dumps(template.colors, indent=2)}
- Theme: {template.theme}
""",
        }


@dataclass
class WordPressConfig:
    """WordPress configuration for collection pages"""

    wp_url: str
    username: str
    app_password: str
    api_version: str = "wp/v2"
    timeout: float = 30.0
    verify_ssl: bool = True

    @property
    def base_url(self) -> str:
        """Get WordPress API base URL"""
        return f"{self.wp_url}/wp-json/{self.api_version}"


class WordPressCollectionPageManager:
    """
    Manages collection pages in WordPress with 3D experiences.

    Handles:
    - Uploading 3D HTML files as media
    - Creating collection pages
    - Embedding 3D experiences
    - Managing metadata and SEO
    """

    def __init__(self, config: WordPressConfig):
        """
        Initialize WordPress manager.

        Args:
            config: WordPress configuration
        """
        self.config = config
        self._session: aiohttp.ClientSession | None = None
        self._logger = logger.bind(wp_url=config.wp_url)

    async def __aenter__(self) -> WordPressCollectionPageManager:
        """Async context manager entry"""
        await self.connect()
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit"""
        await self.close()

    async def connect(self) -> None:
        """Initialize HTTP session"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.timeout),
                auth=aiohttp.BasicAuth(
                    self.config.username,
                    self.config.app_password,
                ),
            )
            self._logger.info("connected", username=self.config.username)

    async def close(self) -> None:
        """Close HTTP session"""
        if self._session and not self._session.closed:
            await self._session.close()
            self._logger.info("disconnected")

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
    ) -> Any:
        """
        Make WordPress API request.

        Args:
            method: HTTP method
            endpoint: API endpoint
            data: Request data
            files: Files to upload

        Returns:
            Response JSON

        Raises:
            Exception: On API error
        """
        await self.connect()
        url = f"{self.config.base_url}{endpoint}"

        try:
            if files:
                # File upload
                async with self._session.post(
                    url,
                    data=data,
                    files=files,
                    ssl=self.config.verify_ssl,
                ) as response:
                    if response.status >= 400:
                        text = await response.text()
                        raise Exception(f"API error ({response.status}): {text}")
                    return await response.json()
            else:
                # Regular request
                async with self._session.request(
                    method,
                    url,
                    json=data,
                    ssl=self.config.verify_ssl,
                ) as response:
                    if response.status >= 400:
                        text = await response.text()
                        raise Exception(f"API error ({response.status}): {text}")
                    return await response.json()

        except Exception as e:
            self._logger.error("request_failed", error=str(e))
            raise

    async def upload_3d_experience(
        self,
        file_path: str,
        collection_type: CollectionType,
    ) -> dict[str, Any]:
        """
        Upload 3D HTML experience file to WordPress media.

        Args:
            file_path: Path to HTML file
            collection_type: Collection type

        Returns:
            WordPress media object

        Raises:
            FileNotFoundError: If file not found
            Exception: On upload error
        """
        file_path_obj = Path(file_path)

        if not file_path_obj.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        template = CollectionDesignTemplates.get_template(collection_type)

        try:
            with open(file_path_obj, "rb") as f:
                files = {"file": (file_path_obj.name, f, "text/html")}

                response = await self._request(
                    "POST",
                    "/media",
                    data={
                        "title": template.name,
                        "description": template.description,
                    },
                    files=files,
                )

            self._logger.info(
                "3d_experience_uploaded",
                collection=collection_type.value,
                media_id=response.get("id"),
            )

            return response

        except Exception as e:
            self._logger.error(
                "3d_experience_upload_failed",
                collection=collection_type.value,
                error=str(e),
            )
            raise

    async def create_collection_page(
        self,
        collection_type: CollectionType,
        media_url: str,
        products: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """
        Create collection page with embedded 3D experience.

        Args:
            collection_type: Collection type
            media_url: URL of uploaded 3D HTML experience
            products: List of products in collection

        Returns:
            Created page object

        Raises:
            Exception: On page creation error
        """
        template = CollectionDesignTemplates.get_template(collection_type)

        # Build page content with embedded experience
        content = self._build_page_content(template, media_url, products or [])

        try:
            page_data = {
                "title": template.name,
                "slug": template.slug,
                "content": content,
                "status": "draft",  # Set to draft until verified
                "meta": {
                    "_collection_type": collection_type.value,
                    "_theme": template.theme,
                    "_colors": json.dumps(template.colors),
                },
            }

            response = await self._request("POST", "/pages", data=page_data)

            self._logger.info(
                "collection_page_created",
                collection=collection_type.value,
                page_id=response.get("id"),
            )

            return response

        except Exception as e:
            self._logger.error(
                "collection_page_creation_failed",
                collection=collection_type.value,
                error=str(e),
            )
            raise

    def _build_page_content(
        self,
        template: CollectionDesign,
        media_url: str,
        products: list[dict[str, Any]],
    ) -> str:
        """Build HTML content for collection page"""
        products_html = ""
        if products:
            products_html = "<div class='products'>"
            for product in products:
                products_html += f"""
                <div class='product-item'>
                    <h4>{product.get("name", "Product")}</h4>
                    <p class='price'>{product.get("price", "$TBD")}</p>
                    <p class='description'>{product.get("description", "")}</p>
                </div>
                """
            products_html += "</div>"

        return f"""
<!-- {template.name} Collection Page -->
<!-- Theme: {template.theme} -->
<!-- Colors: {json.dumps(template.colors)} -->

<div class='collection-page' style='background-color: {template.colors.get("accent", "#fff")}'>
    <div class='collection-header'>
        <h1>{template.name}</h1>
        <p class='theme'>{template.theme}</p>
        <p class='description'>{template.description}</p>
    </div>

    <!-- 3D Experience Embed -->
    <div class='experience-container' style='width: 100%; height: 600px; margin: 2rem 0;'>
        <iframe
            src="{media_url}"
            style="width: 100%; height: 100%; border: none; border-radius: 8px;"
            allow="fullscreen"
            title="{template.name} 3D Experience">
        </iframe>
    </div>

    <!-- Products Section -->
    {products_html}

    <!-- Brand Statement -->
    <div class='brand-statement' style='text-align: center; margin-top: 3rem; padding: 2rem;'>
        <h3>Where Love Meets Luxury</h3>
        <p>Explore the {template.name} collection and discover the artistry behind each piece.</p>
    </div>
</div>

<style>
    .collection-page {{
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        color: {template.colors.get("primary", "#000")};
    }}

    .collection-header {{
        text-align: center;
        padding: 3rem 2rem;
    }}

    .collection-header h1 {{
        font-size: 2.5rem;
        margin-bottom: 1rem;
        color: {template.colors.get("secondary", "#666")};
    }}

    .theme {{
        font-size: 1.2rem;
        font-style: italic;
        margin-bottom: 1rem;
    }}

    .experience-container {{
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }}

    .products {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 2rem;
        padding: 2rem;
        margin: 2rem 0;
    }}

    .product-item {{
        padding: 1.5rem;
        border: 1px solid {template.colors.get("accent", "#ddd")};
        border-radius: 8px;
        text-align: center;
    }}

    .product-item h4 {{
        font-size: 1.3rem;
        margin-bottom: 0.5rem;
        color: {template.colors.get("secondary", "#666")};
    }}

    .price {{
        font-size: 1.1rem;
        color: {template.colors.get("primary", "#000")};
        font-weight: bold;
        margin-bottom: 0.5rem;
    }}

    .brand-statement {{
        background: {template.colors.get("primary", "#000")};
        color: {template.colors.get("accent", "#fff")};
        border-radius: 8px;
    }}

    .brand-statement h3 {{
        font-size: 1.8rem;
        margin-bottom: 1rem;
    }}
</style>
"""

    async def get_page(self, page_id: int) -> dict[str, Any]:
        """Get page by ID"""
        return await self._request("GET", f"/pages/{page_id}")

    async def update_page(
        self,
        page_id: int,
        updates: dict[str, Any],
    ) -> dict[str, Any]:
        """Update page"""
        return await self._request("POST", f"/pages/{page_id}", data=updates)

    async def publish_page(self, page_id: int) -> dict[str, Any]:
        """Publish page"""
        return await self.update_page(page_id, {"status": "publish"})

    async def list_collection_pages(self) -> list[dict[str, Any]]:
        """List all collection pages"""
        return await self._request("GET", "/pages?per_page=100")


__all__ = [
    "CollectionType",
    "CollectionDesign",
    "CollectionDesignTemplates",
    "WordPressConfig",
    "WordPressCollectionPageManager",
]
