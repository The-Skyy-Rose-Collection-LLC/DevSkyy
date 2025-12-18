"""
WordPress Asset Agent
=====================

Manage media uploads and product attachments in WordPress/WooCommerce.

Features:
- Media upload to WordPress
- Image optimization before upload
- Product image attachment
- Gallery management
- 3D model attachment for product pages

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import logging
import mimetypes
import os
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import aiofiles
import aiohttp
from pydantic import BaseModel, Field

from base import (
    AgentCapability,
    AgentConfig,
    ExecutionResult,
    LLMCategory,
    PlanStep,
    RetrievalContext,
    SuperAgent,
    ValidationResult,
)
from runtime.tools import (
    ToolCallContext,
    ToolCategory,
    ToolRegistry,
    ToolSeverity,
    ToolSpec,
    get_tool_registry,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================


@dataclass
class WordPressAssetConfig:
    """WordPress asset management configuration."""

    # WordPress REST API
    site_url: str = field(default_factory=lambda: os.getenv("WP_SITE_URL", ""))
    username: str = field(default_factory=lambda: os.getenv("WP_USERNAME", ""))
    app_password: str = field(default_factory=lambda: os.getenv("WP_APP_PASSWORD", ""))

    # WooCommerce REST API
    wc_consumer_key: str = field(default_factory=lambda: os.getenv("WC_CONSUMER_KEY", ""))
    wc_consumer_secret: str = field(default_factory=lambda: os.getenv("WC_CONSUMER_SECRET", ""))

    # Settings
    timeout: float = 60.0
    max_retries: int = 3
    max_file_size_mb: float = 10.0

    # Image optimization
    optimize_images: bool = True
    max_image_dimension: int = 2048
    jpeg_quality: int = 85

    @classmethod
    def from_env(cls) -> WordPressAssetConfig:
        """Create config from environment variables."""
        return cls(
            site_url=os.getenv("WP_SITE_URL", ""),
            username=os.getenv("WP_USERNAME", ""),
            app_password=os.getenv("WP_APP_PASSWORD", ""),
            wc_consumer_key=os.getenv("WC_CONSUMER_KEY", ""),
            wc_consumer_secret=os.getenv("WC_CONSUMER_SECRET", ""),
        )


# =============================================================================
# Models
# =============================================================================


class MediaUploadResult(BaseModel):
    """WordPress media upload result."""

    id: int
    url: str
    title: str
    mime_type: str
    file_size: int = 0
    width: int | None = None
    height: int | None = None
    alt_text: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProductAssetResult(BaseModel):
    """Product asset attachment result."""

    product_id: int
    media_id: int
    media_url: str
    position: int = 0
    is_featured: bool = False
    asset_type: str = "image"  # image, 3d_model, video


class GalleryResult(BaseModel):
    """Product gallery update result."""

    product_id: int
    featured_image_id: int | None = None
    gallery_image_ids: list[int] = Field(default_factory=list)
    total_images: int = 0


class Model3DUploadResult(BaseModel):
    """3D model upload result."""

    media_id: int
    glb_url: str | None = None
    usdz_url: str | None = None
    thumbnail_url: str | None = None
    product_id: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


# =============================================================================
# WordPress Asset Agent
# =============================================================================


class WordPressAssetAgent(SuperAgent):
    """
    WordPress Asset Management Agent.

    Handles media uploads and product asset attachment.

    Usage:
        agent = WordPressAssetAgent()

        # Upload media
        result = await agent.run({
            "action": "upload_media",
            "file_path": "/path/to/image.jpg",
            "title": "Product Image",
            "alt_text": "SkyyRose Black Rose Hoodie",
        })

        # Attach to product
        result = await agent.run({
            "action": "attach_to_product",
            "product_id": 123,
            "media_id": 456,
            "is_featured": True,
        })

        # Upload and attach
        result = await agent.run({
            "action": "upload_and_attach",
            "file_path": "/path/to/image.jpg",
            "product_id": 123,
            "title": "Product Image",
            "is_featured": True,
        })
    """

    def __init__(
        self,
        config: WordPressAssetConfig | None = None,
        registry: ToolRegistry | None = None,
    ) -> None:
        agent_config = AgentConfig(
            name="wordpress_asset",
            description="WordPress/WooCommerce asset management agent",
            version="1.0.0",
            capabilities={
                AgentCapability.WORDPRESS_MANAGEMENT,
                AgentCapability.PRODUCT_MANAGEMENT,
                AgentCapability.IMAGE_EDITING,
            },
            llm_category=LLMCategory.CATEGORY_B,
            tool_category=ToolCategory.CONTENT,
            default_timeout=60.0,
        )

        super().__init__(agent_config, registry or get_tool_registry())

        self.wp_config = config or WordPressAssetConfig.from_env()
        self._session: aiohttp.ClientSession | None = None

    def _register_tools(self) -> None:
        """Register WordPress asset tools."""
        self.registry.register(
            ToolSpec(
                name="wp_upload_media",
                description="Upload media file to WordPress",
                category=ToolCategory.CONTENT,
                severity=ToolSeverity.MEDIUM,
                timeout_seconds=60.0,
            ),
            self._tool_upload_media,
        )

        self.registry.register(
            ToolSpec(
                name="wp_attach_to_product",
                description="Attach media to WooCommerce product",
                category=ToolCategory.COMMERCE,
                severity=ToolSeverity.MEDIUM,
            ),
            self._tool_attach_to_product,
        )

        self.registry.register(
            ToolSpec(
                name="wp_update_product_gallery",
                description="Update product image gallery",
                category=ToolCategory.COMMERCE,
                severity=ToolSeverity.MEDIUM,
            ),
            self._tool_update_gallery,
        )

        self.registry.register(
            ToolSpec(
                name="wp_get_media",
                description="Get media details from WordPress",
                category=ToolCategory.CONTENT,
                severity=ToolSeverity.READ_ONLY,
            ),
            self._tool_get_media,
        )

    # -------------------------------------------------------------------------
    # SuperAgent Implementation
    # -------------------------------------------------------------------------

    async def _plan(
        self,
        request: dict[str, Any],
        context: ToolCallContext,
    ) -> list[PlanStep]:
        """Create execution plan based on request action."""
        action = request.get("action", "upload_media")

        if action == "upload_media":
            return [
                PlanStep(
                    step_id="upload",
                    tool_name="wp_upload_media",
                    description="Upload media to WordPress",
                    inputs={
                        "file_path": request.get("file_path"),
                        "title": request.get("title", ""),
                        "alt_text": request.get("alt_text", ""),
                        "caption": request.get("caption", ""),
                    },
                    priority=0,
                ),
            ]
        elif action == "attach_to_product":
            return [
                PlanStep(
                    step_id="attach",
                    tool_name="wp_attach_to_product",
                    description="Attach media to product",
                    inputs={
                        "product_id": request.get("product_id"),
                        "media_id": request.get("media_id"),
                        "is_featured": request.get("is_featured", False),
                        "position": request.get("position", 0),
                    },
                    priority=0,
                ),
            ]
        elif action == "upload_and_attach":
            return [
                PlanStep(
                    step_id="upload",
                    tool_name="wp_upload_media",
                    description="Upload media to WordPress",
                    inputs={
                        "file_path": request.get("file_path"),
                        "title": request.get("title", ""),
                        "alt_text": request.get("alt_text", ""),
                    },
                    priority=0,
                ),
                PlanStep(
                    step_id="attach",
                    tool_name="wp_attach_to_product",
                    description="Attach uploaded media to product",
                    inputs={
                        "product_id": request.get("product_id"),
                        "media_id": "{upload.id}",
                        "is_featured": request.get("is_featured", False),
                    },
                    depends_on=["upload"],
                    priority=1,
                ),
            ]
        elif action == "update_gallery":
            return [
                PlanStep(
                    step_id="gallery",
                    tool_name="wp_update_product_gallery",
                    description="Update product gallery",
                    inputs={
                        "product_id": request.get("product_id"),
                        "featured_image_id": request.get("featured_image_id"),
                        "gallery_image_ids": request.get("gallery_image_ids", []),
                    },
                    priority=0,
                ),
            ]
        else:
            raise ValueError(f"Unknown action: {action}")

    async def _retrieve(
        self,
        request: dict[str, Any],
        plan: list[PlanStep],
        context: ToolCallContext,
    ) -> RetrievalContext:
        """Retrieve context (no RAG needed for WordPress operations)."""
        return RetrievalContext(
            query=f"WordPress asset {request.get('action', 'upload')}",
            documents=[],
        )

    async def _execute_step(
        self,
        step: PlanStep,
        retrieval_context: RetrievalContext,
        context: ToolCallContext,
    ) -> ExecutionResult:
        """Execute a single step."""
        started_at = datetime.now(UTC)

        try:
            result = await self.registry.execute(
                step.tool_name,
                step.inputs,
                context,
            )

            return ExecutionResult(
                tool_name=step.tool_name,
                step_id=step.step_id,
                success=result.success,
                result=result.result,
                error=result.error,
                duration_seconds=result.duration_seconds,
                started_at=started_at,
                completed_at=datetime.now(UTC),
            )
        except Exception as e:
            return ExecutionResult(
                tool_name=step.tool_name,
                step_id=step.step_id,
                success=False,
                error=str(e),
                error_type=type(e).__name__,
                started_at=started_at,
                completed_at=datetime.now(UTC),
            )

    async def _validate(
        self,
        results: list[ExecutionResult],
        context: ToolCallContext,
    ) -> ValidationResult:
        """Validate execution results."""
        validation = ValidationResult(is_valid=True)

        for result in results:
            if not result.success:
                validation.add_error(f"{result.tool_name} failed: {result.error}")

        if not validation.errors:
            validation.quality_score = 1.0
            validation.confidence_score = 0.95

        return validation

    async def _emit(
        self,
        results: list[ExecutionResult],
        validation: ValidationResult,
        context: ToolCallContext,
    ) -> dict[str, Any]:
        """Emit final structured output."""
        output = {
            "status": "success" if validation.is_valid else "error",
            "agent": self.name,
            "request_id": context.request_id,
            "validation": validation.to_dict(),
        }

        # Collect all results
        data = {}
        for result in results:
            if result.success and result.result:
                data[result.step_id] = result.result

        output["data"] = data
        output["results"] = [r.to_dict() for r in results]

        return output

    # -------------------------------------------------------------------------
    # Tool Implementations
    # -------------------------------------------------------------------------

    async def _tool_upload_media(
        self,
        file_path: str,
        title: str = "",
        alt_text: str = "",
        caption: str = "",
    ) -> dict[str, Any]:
        """Upload media file to WordPress."""
        await self._ensure_session()

        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Check file size
        file_size = path.stat().st_size
        max_size = self.wp_config.max_file_size_mb * 1024 * 1024
        if file_size > max_size:
            raise ValueError(
                f"File too large: {file_size / (1024*1024):.1f}MB > {self.wp_config.max_file_size_mb}MB"
            )

        # Determine content type
        content_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"

        # Read file
        async with aiofiles.open(file_path, "rb") as f:
            file_data = await f.read()

        # Upload to WordPress
        url = f"{self.wp_config.site_url}/wp-json/wp/v2/media"

        headers = {
            "Content-Disposition": f'attachment; filename="{path.name}"',
            "Content-Type": content_type,
        }

        async with self._session.post(
            url,
            data=file_data,
            headers=headers,
            auth=aiohttp.BasicAuth(self.wp_config.username, self.wp_config.app_password),
        ) as response:
            if response.status >= 400:
                error_text = await response.text()
                raise Exception(f"Upload failed ({response.status}): {error_text}")

            result = await response.json()

        media_id = result.get("id")

        # Update metadata if provided
        if title or alt_text or caption:
            await self._update_media_metadata(media_id, title, alt_text, caption)

        return MediaUploadResult(
            id=media_id,
            url=result.get("source_url", ""),
            title=result.get("title", {}).get("rendered", title),
            mime_type=result.get("mime_type", content_type),
            file_size=file_size,
            width=result.get("media_details", {}).get("width"),
            height=result.get("media_details", {}).get("height"),
            alt_text=alt_text,
            metadata=result.get("media_details", {}),
        ).model_dump()

    async def _update_media_metadata(
        self,
        media_id: int,
        title: str = "",
        alt_text: str = "",
        caption: str = "",
    ) -> None:
        """Update media metadata."""
        url = f"{self.wp_config.site_url}/wp-json/wp/v2/media/{media_id}"

        data = {}
        if title:
            data["title"] = title
        if alt_text:
            data["alt_text"] = alt_text
        if caption:
            data["caption"] = caption

        if data:
            async with self._session.post(
                url,
                json=data,
                auth=aiohttp.BasicAuth(self.wp_config.username, self.wp_config.app_password),
            ) as response:
                if response.status >= 400:
                    logger.warning(f"Failed to update media metadata: {response.status}")

    async def _tool_attach_to_product(
        self,
        product_id: int,
        media_id: int,
        is_featured: bool = False,
        position: int = 0,
    ) -> dict[str, Any]:
        """Attach media to WooCommerce product."""
        await self._ensure_session()

        # Get current product data
        product = await self._get_product(product_id)

        # Prepare update
        images = product.get("images", [])

        # Get media URL
        media = await self._tool_get_media(media_id)
        media_url = media.get("url", "")

        new_image = {
            "id": media_id,
            "src": media_url,
            "position": position,
        }

        if is_featured:
            # Insert at beginning
            images.insert(0, new_image)
        else:
            # Append to gallery
            images.append(new_image)

        # Update product
        url = f"{self.wp_config.site_url}/wp-json/wc/v3/products/{product_id}"

        async with self._session.put(
            url,
            json={"images": images},
            auth=aiohttp.BasicAuth(
                self.wp_config.wc_consumer_key, self.wp_config.wc_consumer_secret
            ),
        ) as response:
            if response.status >= 400:
                error_text = await response.text()
                raise Exception(f"Product update failed ({response.status}): {error_text}")

            await response.json()

        return ProductAssetResult(
            product_id=product_id,
            media_id=media_id,
            media_url=media_url,
            position=position,
            is_featured=is_featured,
            asset_type="image",
        ).model_dump()

    async def _tool_update_gallery(
        self,
        product_id: int,
        featured_image_id: int | None = None,
        gallery_image_ids: list[int] | None = None,
    ) -> dict[str, Any]:
        """Update product image gallery."""
        await self._ensure_session()

        images = []

        # Add featured image first
        if featured_image_id:
            media = await self._tool_get_media(featured_image_id)
            images.append(
                {
                    "id": featured_image_id,
                    "src": media.get("url", ""),
                    "position": 0,
                }
            )

        # Add gallery images
        if gallery_image_ids:
            for i, media_id in enumerate(gallery_image_ids):
                media = await self._tool_get_media(media_id)
                images.append(
                    {
                        "id": media_id,
                        "src": media.get("url", ""),
                        "position": i + 1,
                    }
                )

        # Update product
        url = f"{self.wp_config.site_url}/wp-json/wc/v3/products/{product_id}"

        async with self._session.put(
            url,
            json={"images": images},
            auth=aiohttp.BasicAuth(
                self.wp_config.wc_consumer_key, self.wp_config.wc_consumer_secret
            ),
        ) as response:
            if response.status >= 400:
                error_text = await response.text()
                raise Exception(f"Gallery update failed ({response.status}): {error_text}")

            await response.json()

        return GalleryResult(
            product_id=product_id,
            featured_image_id=featured_image_id,
            gallery_image_ids=gallery_image_ids or [],
            total_images=len(images),
        ).model_dump()

    async def _tool_get_media(self, media_id: int) -> dict[str, Any]:
        """Get media details from WordPress."""
        await self._ensure_session()

        url = f"{self.wp_config.site_url}/wp-json/wp/v2/media/{media_id}"

        async with self._session.get(
            url,
            auth=aiohttp.BasicAuth(self.wp_config.username, self.wp_config.app_password),
        ) as response:
            if response.status >= 400:
                raise Exception(f"Failed to get media ({response.status})")

            result = await response.json()

        return MediaUploadResult(
            id=result.get("id"),
            url=result.get("source_url", ""),
            title=result.get("title", {}).get("rendered", ""),
            mime_type=result.get("mime_type", ""),
            width=result.get("media_details", {}).get("width"),
            height=result.get("media_details", {}).get("height"),
            alt_text=result.get("alt_text", ""),
        ).model_dump()

    async def _get_product(self, product_id: int) -> dict[str, Any]:
        """Get WooCommerce product."""
        url = f"{self.wp_config.site_url}/wp-json/wc/v3/products/{product_id}"

        async with self._session.get(
            url,
            auth=aiohttp.BasicAuth(
                self.wp_config.wc_consumer_key, self.wp_config.wc_consumer_secret
            ),
        ) as response:
            if response.status >= 400:
                raise Exception(f"Failed to get product ({response.status})")

            return await response.json()

    async def upload_3d_model(
        self,
        glb_path: str | None = None,
        usdz_path: str | None = None,
        thumbnail_path: str | None = None,
        product_id: int | None = None,
        title: str = "",
        alt_text: str = "",
    ) -> dict[str, Any]:
        """
        Upload 3D model files (GLB and/or USDZ) to WordPress.

        Args:
            glb_path: Path to GLB file (web/Android)
            usdz_path: Path to USDZ file (iOS/AR Quick Look)
            thumbnail_path: Path to thumbnail image
            product_id: Optional WooCommerce product ID to attach to
            title: Media title
            alt_text: Alt text for accessibility

        Returns:
            Model3DUploadResult with URLs for all uploaded files
        """
        await self._ensure_session()

        result = Model3DUploadResult(
            media_id=0,
            metadata={
                "format_glb": glb_path is not None,
                "format_usdz": usdz_path is not None,
            },
        )

        # Upload GLB file
        if glb_path:
            glb_result = await self._tool_upload_media(
                file_path=glb_path,
                title=f"{title} (GLB)" if title else "",
                alt_text=alt_text,
            )
            result.glb_url = glb_result.get("url")
            result.media_id = glb_result.get("id", 0)
            result.metadata["glb_media_id"] = glb_result.get("id")

        # Upload USDZ file
        if usdz_path:
            usdz_result = await self._tool_upload_media(
                file_path=usdz_path,
                title=f"{title} (USDZ)" if title else "",
                alt_text=alt_text,
            )
            result.usdz_url = usdz_result.get("url")
            result.metadata["usdz_media_id"] = usdz_result.get("id")
            if not result.media_id:
                result.media_id = usdz_result.get("id", 0)

        # Upload thumbnail
        if thumbnail_path:
            thumb_result = await self._tool_upload_media(
                file_path=thumbnail_path,
                title=f"{title} (3D Preview)" if title else "",
                alt_text=f"3D model preview: {alt_text}" if alt_text else "",
            )
            result.thumbnail_url = thumb_result.get("url")
            result.metadata["thumbnail_media_id"] = thumb_result.get("id")

        # Attach to product if specified
        if product_id and result.thumbnail_url:
            result.product_id = product_id
            # Add thumbnail to product gallery
            await self._tool_attach_to_product(
                product_id=product_id,
                media_id=result.metadata.get("thumbnail_media_id", 0),
                is_featured=False,
            )

            # Store 3D model URLs in product meta (requires custom WooCommerce setup)
            await self._update_product_3d_meta(
                product_id=product_id,
                glb_url=result.glb_url,
                usdz_url=result.usdz_url,
            )

        return result.model_dump()

    async def _update_product_3d_meta(
        self,
        product_id: int,
        glb_url: str | None = None,
        usdz_url: str | None = None,
    ) -> None:
        """Update product with 3D model metadata."""
        url = f"{self.wp_config.site_url}/wp-json/wc/v3/products/{product_id}"

        meta_data = []
        if glb_url:
            meta_data.append({"key": "_3d_model_glb_url", "value": glb_url})
        if usdz_url:
            meta_data.append({"key": "_3d_model_usdz_url", "value": usdz_url})

        if meta_data:
            async with self._session.put(
                url,
                json={"meta_data": meta_data},
                auth=aiohttp.BasicAuth(
                    self.wp_config.wc_consumer_key, self.wp_config.wc_consumer_secret
                ),
            ) as response:
                if response.status >= 400:
                    logger.warning(f"Failed to update product 3D meta: {response.status}")

    # -------------------------------------------------------------------------
    # HTTP Client Methods
    # -------------------------------------------------------------------------

    async def _ensure_session(self) -> None:
        """Ensure aiohttp session exists."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.wp_config.timeout),
            )

    async def close(self) -> None:
        """Close HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "WordPressAssetAgent",
    "WordPressAssetConfig",
    "MediaUploadResult",
    "ProductAssetResult",
    "GalleryResult",
    "Model3DUploadResult",
]
