"""
WordPress Asset Agent
=====================

Orchestrates asset upload and product attachment for SkyyRose.

Features:
- Upload 3D models (GLB) to WordPress
- Upload images to media library
- Attach assets to WooCommerce products
- Manage product galleries
- Generate model-viewer shortcodes

Dependencies:
- wordpress.client
- wordpress.media
- wordpress.products
"""

import os
import asyncio
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass, field
from enum import Enum

from pydantic import BaseModel, Field

# Import WordPress modules
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from wordpress.client import WordPressClient, WordPressConfig
from wordpress.media import MediaManager, MediaItem, MediaType
from wordpress.products import WooCommerceProducts, Product, ProductStatus

logger = logging.getLogger(__name__)


# =============================================================================
# Models
# =============================================================================

class AssetType(str, Enum):
    """Asset types"""
    IMAGE = "image"
    MODEL_3D = "model_3d"
    VIDEO = "video"
    DOCUMENT = "document"


class AssetUploadResult(BaseModel):
    """Asset upload result"""
    asset_id: int
    asset_url: str
    asset_type: AssetType
    filename: str
    product_id: Optional[int] = None
    metadata: Dict[str, Any] = {}


class ProductAssetConfig(BaseModel):
    """Configuration for product assets"""
    product_id: int
    images: List[str] = []           # Image file paths
    model_3d: Optional[str] = None   # GLB file path
    featured_image: Optional[str] = None
    gallery_images: List[str] = []


# =============================================================================
# WordPress Asset Agent
# =============================================================================

class WordPressAssetAgent:
    """
    WordPress Asset Management Agent
    
    Handles all asset operations for SkyyRose products.
    
    Usage:
        agent = WordPressAssetAgent()
        
        # Upload image
        result = await agent.upload_image(
            file_path="/path/to/image.jpg",
            title="Product Image",
            product_id=123
        )
        
        # Upload 3D model
        result = await agent.upload_3d_model(
            file_path="/path/to/model.glb",
            product_id=123,
            title="Product 3D Model"
        )
        
        # Attach all assets to product
        await agent.attach_assets_to_product(
            product_id=123,
            images=["/path/to/img1.jpg", "/path/to/img2.jpg"],
            model_3d="/path/to/model.glb"
        )
    """
    
    def __init__(
        self,
        url: str = None,
        username: str = None,
        app_password: str = None,
        wc_key: str = None,
        wc_secret: str = None,
    ):
        # WordPress credentials
        self.url = url or os.getenv("WORDPRESS_URL", "https://skyyrose.co")
        self.username = username or os.getenv("WORDPRESS_USERNAME", "")
        self.app_password = app_password or os.getenv("WORDPRESS_APP_PASSWORD", "")
        
        # WooCommerce credentials
        self.wc_key = wc_key or os.getenv("WOOCOMMERCE_KEY", "")
        self.wc_secret = wc_secret or os.getenv("WOOCOMMERCE_SECRET", "")
        
        # Initialize clients
        self._media: Optional[MediaManager] = None
        self._products: Optional[WooCommerceProducts] = None
        self._wp: Optional[WordPressClient] = None
    
    async def __aenter__(self):
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def connect(self):
        """Initialize all clients"""
        self._media = MediaManager(
            url=self.url,
            username=self.username,
            app_password=self.app_password,
        )
        await self._media.connect()
        
        self._products = WooCommerceProducts(
            url=self.url,
            consumer_key=self.wc_key,
            consumer_secret=self.wc_secret,
        )
        await self._products.connect()
        
        self._wp = WordPressClient(
            url=self.url,
            username=self.username,
            app_password=self.app_password,
        )
        await self._wp.connect()
        
        logger.info(f"WordPress Asset Agent connected to: {self.url}")
    
    async def close(self):
        """Close all clients"""
        if self._media:
            await self._media.close()
        if self._products:
            await self._products.close()
        if self._wp:
            await self._wp.close()
    
    # -------------------------------------------------------------------------
    # Image Upload
    # -------------------------------------------------------------------------
    
    async def upload_image(
        self,
        file_path: str,
        title: str = None,
        alt_text: str = None,
        caption: str = None,
        product_id: int = None,
    ) -> AssetUploadResult:
        """
        Upload image to WordPress media library
        
        Args:
            file_path: Path to image file
            title: Image title
            alt_text: Alt text for accessibility
            caption: Image caption
            product_id: Optional product to attach to
            
        Returns:
            AssetUploadResult with upload details
        """
        filename = Path(file_path).name
        
        if not title:
            title = Path(file_path).stem.replace("-", " ").replace("_", " ").title()
        
        logger.info(f"Uploading image: {filename}")
        
        # Upload to media library
        item = await self._media.upload_file(
            file_path=file_path,
            title=title,
            alt_text=alt_text or title,
            caption=caption,
            post_id=product_id,
        )
        
        result = AssetUploadResult(
            asset_id=item.id,
            asset_url=item.source_url,
            asset_type=AssetType.IMAGE,
            filename=filename,
            product_id=product_id,
            metadata={
                "title": title,
                "alt_text": alt_text or title,
                "uploaded_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        
        # Attach to product if specified
        if product_id and self._products:
            await self._add_image_to_product(product_id, item.source_url, item.id)
        
        return result
    
    async def _add_image_to_product(
        self,
        product_id: int,
        image_url: str,
        image_id: int,
    ):
        """Add image to product gallery"""
        try:
            product = await self._products.get(product_id)
            
            # Get existing images
            existing_images = [
                {"id": img.get("id"), "src": img.get("src")}
                for img in product.images
            ]
            
            # Add new image
            existing_images.append({"id": image_id, "src": image_url})
            
            # Update product
            await self._products.update(product_id, images=existing_images)
            logger.info(f"Added image to product {product_id}")
            
        except Exception as e:
            logger.error(f"Failed to add image to product: {e}")
    
    # -------------------------------------------------------------------------
    # 3D Model Upload
    # -------------------------------------------------------------------------
    
    async def upload_3d_model(
        self,
        file_path: str,
        product_id: int = None,
        title: str = None,
        meta_key: str = "_3d_model_url",
    ) -> AssetUploadResult:
        """
        Upload 3D model (GLB/GLTF) to WordPress
        
        Args:
            file_path: Path to 3D model file
            product_id: WooCommerce product ID to attach
            title: Model title
            meta_key: Product meta key for 3D model URL
            
        Returns:
            AssetUploadResult with upload details
        """
        filename = Path(file_path).name
        
        if not title:
            title = f"3D Model - {Path(file_path).stem}"
        
        logger.info(f"Uploading 3D model: {filename}")
        
        # Upload to media library
        item = await self._media.upload_3d_model(
            file_path=file_path,
            title=title,
            product_id=product_id,
        )
        
        result = AssetUploadResult(
            asset_id=item.id,
            asset_url=item.source_url,
            asset_type=AssetType.MODEL_3D,
            filename=filename,
            product_id=product_id,
            metadata={
                "title": title,
                "format": Path(file_path).suffix.lower(),
                "uploaded_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        
        # Update product meta with 3D model URL
        if product_id and item.source_url:
            await self._set_product_3d_model(product_id, item.source_url, meta_key)
        
        return result
    
    async def _set_product_3d_model(
        self,
        product_id: int,
        model_url: str,
        meta_key: str,
    ):
        """Set 3D model URL on product"""
        try:
            # Update product meta
            await self._products.update(
                product_id,
                meta_data=[
                    {"key": meta_key, "value": model_url},
                    {"key": "_3d_model_enabled", "value": "yes"},
                ]
            )
            logger.info(f"Set 3D model URL on product {product_id}")
            
        except Exception as e:
            logger.error(f"Failed to set 3D model on product: {e}")
    
    # -------------------------------------------------------------------------
    # Bulk Operations
    # -------------------------------------------------------------------------
    
    async def attach_assets_to_product(
        self,
        product_id: int,
        images: List[str] = None,
        model_3d: str = None,
        featured_image: str = None,
        concurrency: int = 3,
    ) -> Dict[str, Any]:
        """
        Attach multiple assets to a product
        
        Args:
            product_id: WooCommerce product ID
            images: List of image file paths for gallery
            model_3d: 3D model file path
            featured_image: Featured image file path
            concurrency: Max concurrent uploads
            
        Returns:
            Dictionary with upload results
        """
        results = {
            "product_id": product_id,
            "images": [],
            "model_3d": None,
            "featured_image": None,
            "errors": [],
        }
        
        semaphore = asyncio.Semaphore(concurrency)
        
        async def upload_with_limit(coro):
            async with semaphore:
                return await coro
        
        tasks = []
        
        # Upload featured image first
        if featured_image:
            tasks.append(("featured", upload_with_limit(
                self.upload_image(
                    featured_image,
                    title="Featured Image",
                    product_id=product_id,
                )
            )))
        
        # Upload gallery images
        if images:
            for i, img_path in enumerate(images):
                tasks.append((f"image_{i}", upload_with_limit(
                    self.upload_image(
                        img_path,
                        title=f"Product Image {i + 1}",
                        product_id=product_id,
                    )
                )))
        
        # Upload 3D model
        if model_3d:
            tasks.append(("model_3d", upload_with_limit(
                self.upload_3d_model(
                    model_3d,
                    product_id=product_id,
                )
            )))
        
        # Execute all uploads
        for task_name, task_coro in tasks:
            try:
                result = await task_coro
                
                if task_name == "featured":
                    results["featured_image"] = result.dict()
                    # Set as featured
                    await self._products.update(
                        product_id,
                        images=[{"id": result.asset_id, "position": 0}]
                    )
                elif task_name == "model_3d":
                    results["model_3d"] = result.dict()
                else:
                    results["images"].append(result.dict())
                    
            except Exception as e:
                logger.error(f"Upload failed ({task_name}): {e}")
                results["errors"].append({
                    "task": task_name,
                    "error": str(e),
                })
        
        return results
    
    async def bulk_upload_images(
        self,
        file_paths: List[str],
        product_id: int = None,
        title_prefix: str = "",
        concurrency: int = 5,
    ) -> List[AssetUploadResult]:
        """
        Bulk upload images
        
        Args:
            file_paths: List of image file paths
            product_id: Optional product to attach all to
            title_prefix: Prefix for image titles
            concurrency: Max concurrent uploads
            
        Returns:
            List of AssetUploadResult
        """
        semaphore = asyncio.Semaphore(concurrency)
        
        async def upload(path: str, index: int) -> AssetUploadResult:
            async with semaphore:
                title = f"{title_prefix} {Path(path).stem}".strip()
                return await self.upload_image(
                    file_path=path,
                    title=title,
                    alt_text=f"{title} - Image {index + 1}",
                    product_id=product_id,
                )
        
        tasks = [upload(p, i) for i, p in enumerate(file_paths)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        successful = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Failed to upload {file_paths[i]}: {result}")
            else:
                successful.append(result)
        
        return successful
    
    # -------------------------------------------------------------------------
    # Product Gallery Management
    # -------------------------------------------------------------------------
    
    async def set_product_gallery(
        self,
        product_id: int,
        image_ids: List[int],
        featured_id: int = None,
    ):
        """
        Set product image gallery
        
        Args:
            product_id: WooCommerce product ID
            image_ids: List of media library image IDs
            featured_id: Optional featured image ID
        """
        images = [{"id": img_id} for img_id in image_ids]
        
        if featured_id:
            # Move featured to first position
            images = [{"id": featured_id}] + [
                img for img in images if img["id"] != featured_id
            ]
        
        await self._products.update(product_id, images=images)
        logger.info(f"Updated gallery for product {product_id}: {len(images)} images")
    
    async def clear_product_gallery(self, product_id: int):
        """Remove all images from product"""
        await self._products.update(product_id, images=[])
        logger.info(f"Cleared gallery for product {product_id}")
    
    # -------------------------------------------------------------------------
    # Model Viewer Integration
    # -------------------------------------------------------------------------
    
    def generate_model_viewer_shortcode(
        self,
        model_url: str,
        poster_url: str = None,
        alt: str = "3D Model",
        ar: bool = True,
        auto_rotate: bool = True,
        camera_controls: bool = True,
        width: str = "100%",
        height: str = "500px",
    ) -> str:
        """
        Generate model-viewer shortcode for 3D model display
        
        This generates HTML for Google's <model-viewer> component.
        
        Args:
            model_url: URL to GLB model
            poster_url: Optional poster image URL
            alt: Alt text
            ar: Enable AR on supported devices
            auto_rotate: Auto-rotate model
            camera_controls: Enable camera controls
            width: Viewer width
            height: Viewer height
            
        Returns:
            HTML shortcode for embedding
        """
        attrs = [
            f'src="{model_url}"',
            f'alt="{alt}"',
            f'style="width: {width}; height: {height};"',
        ]
        
        if poster_url:
            attrs.append(f'poster="{poster_url}"')
        
        if ar:
            attrs.append('ar')
            attrs.append('ar-modes="webxr scene-viewer quick-look"')
        
        if auto_rotate:
            attrs.append('auto-rotate')
        
        if camera_controls:
            attrs.append('camera-controls')
        
        # Additional recommended attributes
        attrs.extend([
            'shadow-intensity="1"',
            'exposure="0.75"',
            'environment-image="neutral"',
        ])
        
        shortcode = f'<model-viewer {" ".join(attrs)}></model-viewer>'
        
        # Wrap with script include if needed
        full_html = f'''
<!-- Model Viewer Component -->
<script type="module" src="https://unpkg.com/@google/model-viewer/dist/model-viewer.min.js"></script>
{shortcode}
'''
        
        return full_html.strip()
    
    async def add_3d_viewer_to_product(
        self,
        product_id: int,
        model_url: str,
        poster_url: str = None,
        position: str = "after_images",  # or "before_images", "tab"
    ):
        """
        Add 3D viewer to product page
        
        This updates product description/short_description with model-viewer code.
        
        Args:
            product_id: WooCommerce product ID
            model_url: URL to GLB model
            poster_url: Optional poster image
            position: Where to add viewer
        """
        viewer_html = self.generate_model_viewer_shortcode(
            model_url=model_url,
            poster_url=poster_url,
            alt="View in 3D",
        )
        
        product = await self._products.get(product_id)
        
        if position == "before_images":
            new_description = viewer_html + "\n\n" + product.description
        elif position == "after_images":
            new_description = product.description + "\n\n" + viewer_html
        else:
            # Add as tab content via meta
            await self._products.update(
                product_id,
                meta_data=[
                    {"key": "_3d_viewer_html", "value": viewer_html},
                    {"key": "_3d_viewer_enabled", "value": "yes"},
                ]
            )
            return
        
        await self._products.update(product_id, description=new_description)
        logger.info(f"Added 3D viewer to product {product_id}")
    
    # -------------------------------------------------------------------------
    # Utility Methods
    # -------------------------------------------------------------------------
    
    async def get_product_assets(self, product_id: int) -> Dict[str, Any]:
        """Get all assets attached to a product"""
        product = await self._products.get(product_id)
        
        # Get 3D model from meta
        model_3d = None
        for meta in product.meta_data:
            if meta.get("key") == "_3d_model_url":
                model_3d = meta.get("value")
                break
        
        return {
            "product_id": product_id,
            "product_name": product.name,
            "images": [
                {"id": img.get("id"), "src": img.get("src")}
                for img in product.images
            ],
            "model_3d": model_3d,
            "featured_image": product.images[0].get("src") if product.images else None,
        }
    
    async def test_connection(self) -> Dict[str, bool]:
        """Test all connections"""
        results = {
            "wordpress": False,
            "woocommerce": False,
            "media": False,
        }
        
        try:
            await self._wp.test_connection()
            results["wordpress"] = True
        except Exception as e:
            logger.error(f"WordPress connection failed: {e}")
        
        try:
            await self._products.list(per_page=1)
            results["woocommerce"] = True
        except Exception as e:
            logger.error(f"WooCommerce connection failed: {e}")
        
        try:
            await self._media.list(per_page=1)
            results["media"] = True
        except Exception as e:
            logger.error(f"Media connection failed: {e}")
        
        return results
