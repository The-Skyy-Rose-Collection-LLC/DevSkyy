"""
WordPress 3D Media Sync
=========================

Uploads and syncs 3D model files (GLB, USDZ, OBJ) with the
WordPress media library. Attaches models to WooCommerce products
and collection pages.

Usage:
    from wordpress.media_3d_sync import WordPress3DMediaSync

    sync = WordPress3DMediaSync(
        wp_url="https://skyyrose.co",
        username="admin",
        app_password="xxxx xxxx xxxx xxxx",
    )
    result = await sync.upload_3d_model(
        file_path="assets/models/jacket.glb",
        product_id=123,
    )
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class WordPress3DMediaSync:
    """
    Manages 3D model files in WordPress media library.

    Handles:
    - Upload GLB/USDZ/OBJ files to WordPress media library
    - Set custom meta fields for 3D model metadata
    - Attach models to WooCommerce products
    - Link models to collection pages
    """

    def __init__(
        self,
        wp_url: str = "",
        username: str = "",
        app_password: str = "",
        timeout: int = 60,
    ) -> None:
        """
        Initialize 3D media sync client.

        Args:
            wp_url: WordPress site URL.
            username: Admin username.
            app_password: WordPress application password.
            timeout: Upload timeout in seconds.
        """
        self.wp_url = wp_url.rstrip("/")
        self.username = username
        self.app_password = app_password
        self.timeout = timeout

        logger.info(
            "wordpress_3d_sync_initialized",
            extra={"wp_url": self.wp_url},
        )

    async def upload_3d_model(
        self,
        file_path: str,
        product_id: int | None = None,
        title: str = "",
        description: str = "",
        collection: str = "",
    ) -> dict[str, Any]:
        """
        Upload a 3D model file to WordPress.

        Args:
            file_path: Path to the 3D model file (GLB, USDZ, OBJ).
            product_id: WooCommerce product ID to attach model to.
            title: Media title.
            description: Media description.
            collection: Collection name for meta tagging.

        Returns:
            Upload result with media ID and URLs.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"3D model file not found: {file_path}")

        ext = path.suffix.lower()
        if ext not in {".glb", ".gltf", ".usdz", ".obj", ".fbx"}:
            raise ValueError(f"Unsupported 3D format: {ext}")

        from wordpress.client import WordPressClient

        async with WordPressClient(
            wp_url=self.wp_url,
            username=self.username,
            app_password=self.app_password,
        ) as client:
            result = await client.upload_media(
                file_path=str(path),
                title=title or path.stem,
                alt_text=f"3D model: {title or path.stem}",
            )

            media_id = result.get("id")

            # Set 3D-specific meta fields
            if media_id and product_id:
                await client.update_post_meta(
                    media_id,
                    {
                        "_skyyrose_3d_model": "true",
                        "_skyyrose_model_format": ext.lstrip("."),
                        "_skyyrose_product_id": str(product_id),
                        "_skyyrose_collection": collection,
                    },
                )

                # Attach to product
                await self._attach_to_product(client, media_id, product_id, ext)

            logger.info(
                "3d_model_uploaded",
                extra={
                    "media_id": media_id,
                    "file": path.name,
                    "format": ext,
                    "product_id": product_id,
                },
            )

            return {
                "media_id": media_id,
                "source_url": result.get("source_url", ""),
                "format": ext.lstrip("."),
                "product_id": product_id,
                "status": "uploaded",
            }

    async def _attach_to_product(
        self,
        client: Any,
        media_id: int,
        product_id: int,
        ext: str,
    ) -> None:
        """Attach a 3D model to a WooCommerce product via meta fields."""
        meta_key = "_skyyrose_3d_model_glb" if ext == ".glb" else f"_skyyrose_3d_model_{ext.lstrip('.')}"

        await client.update_post_meta(
            product_id,
            {meta_key: str(media_id)},
        )

    async def sync_product_models(
        self,
        product_id: int,
        glb_path: str = "",
        usdz_path: str = "",
    ) -> dict[str, Any]:
        """
        Sync both GLB (web) and USDZ (iOS AR) models for a product.

        Args:
            product_id: WooCommerce product ID.
            glb_path: Path to GLB file for web viewers.
            usdz_path: Path to USDZ file for iOS AR Quick Look.

        Returns:
            Sync results for both formats.
        """
        results: dict[str, Any] = {"product_id": product_id}

        if glb_path:
            results["glb"] = await self.upload_3d_model(
                file_path=glb_path,
                product_id=product_id,
                title=f"Product {product_id} - Web 3D Model",
            )

        if usdz_path:
            results["usdz"] = await self.upload_3d_model(
                file_path=usdz_path,
                product_id=product_id,
                title=f"Product {product_id} - AR Model",
            )

        return results


__all__ = [
    "WordPress3DMediaSync",
]
