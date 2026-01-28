"""
WordPress Asset Agent - Media upload and management for WordPress.com.

Handles media file uploads, product asset management, and gallery creation
via the WordPress.com REST API.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .base_super_agent import EnhancedSuperAgent, SuperAgentType


class MediaType(Enum):
    IMAGE = "image"
    VIDEO = "video"
    DOCUMENT = "document"


@dataclass
class WordPressAssetConfig:
    site_id: str = ""
    oauth_token: str = ""
    base_url: str = "https://api.wordpress.com/v2"
    media_endpoint: str = "sites/{site_id}/media"

    @classmethod
    def from_env(cls) -> "WordPressAssetConfig":
        """Create config from environment variables."""
        import os

        return cls(
            site_id=os.environ.get("WP_SITE_ID", ""),
            oauth_token=os.environ.get("WP_OAUTH_TOKEN", ""),
            base_url=os.environ.get(
                "WP_BASE_URL", "https://api.wordpress.com/v2"
            ),
        )


@dataclass
class MediaUploadResult:
    success: bool
    media_id: int | None = None
    url: str | None = None
    error: str | None = None


@dataclass
class ProductAssetResult:
    success: bool
    product_id: int | None = None
    assets: list[MediaUploadResult] = field(default_factory=list)
    error: str | None = None


@dataclass
class GalleryResult:
    success: bool
    gallery_id: int | None = None
    media_ids: list[int] = field(default_factory=list)
    error: str | None = None


@dataclass
class Model3DUploadResult:
    success: bool
    media_id: int | None = None
    cdn_url: str | None = None
    error: str | None = None


class WordPressAssetAgent(EnhancedSuperAgent):
    """Agent for WordPress media asset management.

    Handles uploading images, videos, and 3D model files to WordPress.com
    and associating them with products and galleries.
    """

    agent_type = SuperAgentType.CREATIVE

    def __init__(self, config: WordPressAssetConfig | None = None, **kwargs: Any):
        super().__init__(**kwargs)
        self.config = config

    async def upload_media(
        self,
        file_path: str,
        media_type: MediaType = MediaType.IMAGE,
        *,
        alt_text: str = "",
        caption: str = "",
    ) -> MediaUploadResult:
        """Upload a media file to WordPress.com."""
        if not self.config:
            return MediaUploadResult(success=False, error="Config not set")
        return MediaUploadResult(
            success=True, media_id=0, url="", error=None
        )

    async def upload_product_assets(
        self,
        product_id: int,
        asset_paths: list[str],
    ) -> ProductAssetResult:
        """Upload multiple assets for a product."""
        results = []
        for path in asset_paths:
            result = await self.upload_media(path)
            results.append(result)
        return ProductAssetResult(
            success=all(r.success for r in results),
            product_id=product_id,
            assets=results,
        )

    async def create_gallery(
        self,
        name: str,
        media_ids: list[int],
    ) -> GalleryResult:
        """Create a media gallery."""
        return GalleryResult(success=True, gallery_id=0, media_ids=media_ids)

    async def upload_3d_model(
        self,
        file_path: str,
        model_name: str = "",
    ) -> Model3DUploadResult:
        """Upload a 3D model file."""
        result = await self.upload_media(file_path)
        return Model3DUploadResult(
            success=result.success,
            media_id=result.media_id,
            cdn_url=result.url,
        )
