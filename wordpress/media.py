"""
WordPress Media Library Module
==============================

Media upload and management for WordPress including:
- Image uploads (JPG, PNG, WebP)
- 3D model uploads (GLB, GLTF)
- Video uploads
- Bulk uploads
- Media attachment to products

References:
- WordPress Media API: https://developer.wordpress.org/rest-api/reference/media/
"""

import os
import logging
import mimetypes
import base64
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Union, BinaryIO
from dataclasses import dataclass
from enum import Enum
import asyncio
import aiofiles

import httpx
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# =============================================================================
# Enums & Models
# =============================================================================

class MediaType(str, Enum):
    """Media type categories"""
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    APPLICATION = "application"
    MODEL = "model"


class MediaItem(BaseModel):
    """WordPress media item"""
    id: int
    date: str
    slug: str
    type: str
    link: str
    title: Dict[str, str]
    author: int
    caption: Dict[str, str] = {}
    alt_text: str = ""
    media_type: str = ""
    mime_type: str = ""
    source_url: str = ""
    media_details: Dict[str, Any] = {}


# MIME type mappings including 3D models
MIME_TYPES = {
    # Images
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".svg": "image/svg+xml",
    ".ico": "image/x-icon",
    
    # Video
    ".mp4": "video/mp4",
    ".webm": "video/webm",
    ".mov": "video/quicktime",
    ".avi": "video/x-msvideo",
    
    # Audio
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
    ".ogg": "audio/ogg",
    
    # Documents
    ".pdf": "application/pdf",
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    
    # 3D Models
    ".glb": "model/gltf-binary",
    ".gltf": "model/gltf+json",
    ".obj": "model/obj",
    ".fbx": "application/octet-stream",
    ".stl": "model/stl",
    ".usdz": "model/vnd.usdz+zip",
}


# =============================================================================
# Media Manager
# =============================================================================

class MediaManager:
    """
    WordPress Media Library Manager
    
    Usage:
        media = MediaManager(
            url="https://skyyrose.co",
            username="admin",
            app_password="xxxx-xxxx-xxxx-xxxx"
        )
        
        # Upload image
        item = await media.upload_file(
            file_path="/path/to/image.jpg",
            title="Product Image",
            alt_text="Heart aRose Bomber - Front View"
        )
        
        # Upload 3D model
        model = await media.upload_3d_model(
            file_path="/path/to/model.glb",
            title="Product 3D Model"
        )
        
        # Get media
        item = await media.get(item.id)
        
        # Delete
        await media.delete(item.id)
    """
    
    def __init__(
        self,
        url: str = None,
        username: str = None,
        app_password: str = None,
        timeout: float = 60.0,
        verify_ssl: bool = True,
    ):
        self.url = (url or os.getenv("WORDPRESS_URL", "https://skyyrose.co")).rstrip("/")
        self.username = username or os.getenv("WORDPRESS_USERNAME", "")
        self.app_password = app_password or os.getenv("WORDPRESS_APP_PASSWORD", "")
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self._client: Optional[httpx.AsyncClient] = None
        
        self.base_url = f"{self.url}/wp-json/wp/v2"
    
    @property
    def auth_header(self) -> str:
        """Generate Basic auth header"""
        credentials = f"{self.username}:{self.app_password}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"
    
    async def __aenter__(self):
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def connect(self):
        """Initialize HTTP client"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                verify=self.verify_ssl,
                headers={
                    "Authorization": self.auth_header,
                    "User-Agent": "DevSkyy/2.0 Media-Manager",
                },
            )
            logger.info(f"Media manager connected to: {self.url}")
    
    async def close(self):
        """Close HTTP client"""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    def _get_mime_type(self, file_path: str) -> str:
        """Get MIME type for file"""
        ext = Path(file_path).suffix.lower()
        
        # Check our custom mappings first
        if ext in MIME_TYPES:
            return MIME_TYPES[ext]
        
        # Fall back to mimetypes module
        mime_type, _ = mimetypes.guess_type(file_path)
        return mime_type or "application/octet-stream"
    
    def _get_media_type(self, mime_type: str) -> MediaType:
        """Determine media type from MIME type"""
        if mime_type.startswith("image/"):
            return MediaType.IMAGE
        elif mime_type.startswith("video/"):
            return MediaType.VIDEO
        elif mime_type.startswith("audio/"):
            return MediaType.AUDIO
        elif mime_type.startswith("model/"):
            return MediaType.MODEL
        else:
            return MediaType.APPLICATION
    
    # -------------------------------------------------------------------------
    # Upload Operations
    # -------------------------------------------------------------------------
    
    async def upload_file(
        self,
        file_path: str,
        title: str = None,
        caption: str = None,
        alt_text: str = None,
        description: str = None,
        post_id: int = None,
    ) -> MediaItem:
        """
        Upload file to WordPress media library
        
        Args:
            file_path: Path to file
            title: Media title
            caption: Media caption
            alt_text: Alt text for images
            description: Media description
            post_id: Attach to post/product ID
            
        Returns:
            MediaItem with upload details
        """
        if self._client is None:
            await self.connect()
        
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        filename = path.name
        mime_type = self._get_mime_type(file_path)
        
        # Use title or filename
        if not title:
            title = path.stem.replace("-", " ").replace("_", " ").title()
        
        # Read file content
        async with aiofiles.open(file_path, "rb") as f:
            file_content = await f.read()
        
        # Build multipart form data
        files = {
            "file": (filename, file_content, mime_type),
        }
        
        data = {
            "title": title,
            "status": "inherit",
        }
        
        if caption:
            data["caption"] = caption
        if alt_text:
            data["alt_text"] = alt_text
        if description:
            data["description"] = description
        if post_id:
            data["post"] = post_id
        
        # Upload request
        response = await self._client.post(
            f"{self.base_url}/media",
            files=files,
            data=data,
        )
        
        if response.status_code >= 400:
            error_msg = response.text
            try:
                error_data = response.json()
                error_msg = error_data.get("message", error_msg)
            except:
                pass
            raise Exception(f"Upload failed ({response.status_code}): {error_msg}")
        
        result = response.json()
        logger.info(f"Uploaded media: {result.get('id')} - {filename}")
        
        return MediaItem(**result)
    
    async def upload_from_url(
        self,
        source_url: str,
        title: str = None,
        alt_text: str = None,
        filename: str = None,
    ) -> MediaItem:
        """
        Upload media from external URL
        
        This downloads the file first, then uploads to WordPress.
        WordPress doesn't support direct URL imports via REST API.
        """
        if self._client is None:
            await self.connect()
        
        # Download file
        response = await self._client.get(source_url)
        
        if response.status_code >= 400:
            raise Exception(f"Failed to download from URL: {source_url}")
        
        content = response.content
        
        # Determine filename
        if not filename:
            from urllib.parse import urlparse
            parsed = urlparse(source_url)
            filename = Path(parsed.path).name or "upload"
        
        # Determine MIME type
        content_type = response.headers.get("content-type", "")
        mime_type = content_type.split(";")[0] if content_type else self._get_mime_type(filename)
        
        if not title:
            title = Path(filename).stem.replace("-", " ").replace("_", " ").title()
        
        # Upload
        files = {
            "file": (filename, content, mime_type),
        }
        
        data = {
            "title": title,
            "status": "inherit",
        }
        
        if alt_text:
            data["alt_text"] = alt_text
        
        response = await self._client.post(
            f"{self.base_url}/media",
            files=files,
            data=data,
        )
        
        if response.status_code >= 400:
            raise Exception(f"Upload failed: {response.text}")
        
        result = response.json()
        logger.info(f"Uploaded from URL: {result.get('id')} - {filename}")
        
        return MediaItem(**result)
    
    async def upload_3d_model(
        self,
        file_path: str,
        title: str = None,
        product_id: int = None,
        meta_key: str = "_3d_model_url",
    ) -> MediaItem:
        """
        Upload 3D model (GLB/GLTF) to WordPress
        
        Args:
            file_path: Path to 3D model file
            title: Model title
            product_id: WooCommerce product ID to attach to
            meta_key: Product meta key for 3D model URL
            
        Returns:
            MediaItem with model details
        """
        # Upload the model
        item = await self.upload_file(
            file_path=file_path,
            title=title,
            alt_text=f"3D Model: {title or Path(file_path).stem}",
            description="3D model for product visualization",
            post_id=product_id,
        )
        
        # If product_id provided, update product meta
        if product_id and item.source_url:
            try:
                # Update product meta via WooCommerce API
                # This requires WooCommerce module
                logger.info(f"3D model uploaded. Update product {product_id} with URL: {item.source_url}")
            except Exception as e:
                logger.warning(f"Could not update product meta: {e}")
        
        return item
    
    async def upload_bytes(
        self,
        content: bytes,
        filename: str,
        mime_type: str = None,
        title: str = None,
        alt_text: str = None,
    ) -> MediaItem:
        """Upload raw bytes as media"""
        if self._client is None:
            await self.connect()
        
        if not mime_type:
            mime_type = self._get_mime_type(filename)
        
        if not title:
            title = Path(filename).stem.replace("-", " ").replace("_", " ").title()
        
        files = {
            "file": (filename, content, mime_type),
        }
        
        data = {
            "title": title,
            "status": "inherit",
        }
        
        if alt_text:
            data["alt_text"] = alt_text
        
        response = await self._client.post(
            f"{self.base_url}/media",
            files=files,
            data=data,
        )
        
        if response.status_code >= 400:
            raise Exception(f"Upload failed: {response.text}")
        
        result = response.json()
        return MediaItem(**result)
    
    # -------------------------------------------------------------------------
    # CRUD Operations
    # -------------------------------------------------------------------------
    
    async def get(self, media_id: int) -> MediaItem:
        """Get media item by ID"""
        if self._client is None:
            await self.connect()
        
        response = await self._client.get(f"{self.base_url}/media/{media_id}")
        
        if response.status_code == 404:
            raise Exception(f"Media not found: {media_id}")
        
        if response.status_code >= 400:
            raise Exception(f"Failed to get media: {response.text}")
        
        return MediaItem(**response.json())
    
    async def list(
        self,
        per_page: int = 10,
        page: int = 1,
        media_type: MediaType = None,
        mime_type: str = None,
        search: str = None,
        parent: int = None,
        orderby: str = "date",
        order: str = "desc",
    ) -> List[MediaItem]:
        """List media items"""
        if self._client is None:
            await self.connect()
        
        params = {
            "per_page": per_page,
            "page": page,
            "orderby": orderby,
            "order": order,
        }
        
        if media_type:
            params["media_type"] = media_type.value
        if mime_type:
            params["mime_type"] = mime_type
        if search:
            params["search"] = search
        if parent is not None:
            params["parent"] = parent
        
        response = await self._client.get(
            f"{self.base_url}/media",
            params=params,
        )
        
        if response.status_code >= 400:
            raise Exception(f"Failed to list media: {response.text}")
        
        return [MediaItem(**item) for item in response.json()]
    
    async def update(
        self,
        media_id: int,
        title: str = None,
        caption: str = None,
        alt_text: str = None,
        description: str = None,
    ) -> MediaItem:
        """Update media item"""
        if self._client is None:
            await self.connect()
        
        data = {}
        if title:
            data["title"] = title
        if caption:
            data["caption"] = caption
        if alt_text:
            data["alt_text"] = alt_text
        if description:
            data["description"] = description
        
        response = await self._client.post(
            f"{self.base_url}/media/{media_id}",
            json=data,
        )
        
        if response.status_code >= 400:
            raise Exception(f"Failed to update media: {response.text}")
        
        return MediaItem(**response.json())
    
    async def delete(self, media_id: int, force: bool = True) -> dict:
        """Delete media item"""
        if self._client is None:
            await self.connect()
        
        response = await self._client.delete(
            f"{self.base_url}/media/{media_id}",
            params={"force": force},
        )
        
        if response.status_code >= 400:
            raise Exception(f"Failed to delete media: {response.text}")
        
        logger.info(f"Deleted media: {media_id}")
        return response.json()
    
    # -------------------------------------------------------------------------
    # Bulk Operations
    # -------------------------------------------------------------------------
    
    async def bulk_upload(
        self,
        file_paths: List[str],
        title_prefix: str = "",
        alt_text_template: str = None,
        concurrency: int = 3,
    ) -> List[MediaItem]:
        """
        Upload multiple files concurrently
        
        Args:
            file_paths: List of file paths
            title_prefix: Prefix for titles
            alt_text_template: Template for alt text (use {index} and {filename})
            concurrency: Max concurrent uploads
            
        Returns:
            List of uploaded MediaItems
        """
        semaphore = asyncio.Semaphore(concurrency)
        
        async def upload_with_limit(file_path: str, index: int) -> MediaItem:
            async with semaphore:
                filename = Path(file_path).stem
                title = f"{title_prefix} {filename}".strip()
                
                alt_text = None
                if alt_text_template:
                    alt_text = alt_text_template.format(
                        index=index,
                        filename=filename,
                    )
                
                return await self.upload_file(
                    file_path=file_path,
                    title=title,
                    alt_text=alt_text,
                )
        
        tasks = [
            upload_with_limit(path, i)
            for i, path in enumerate(file_paths)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        items = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Failed to upload {file_paths[i]}: {result}")
            else:
                items.append(result)
        
        return items
    
    # -------------------------------------------------------------------------
    # Search & Filter
    # -------------------------------------------------------------------------
    
    async def search(self, query: str, per_page: int = 20) -> List[MediaItem]:
        """Search media by query"""
        return await self.list(search=query, per_page=per_page)
    
    async def get_images(self, per_page: int = 20) -> List[MediaItem]:
        """Get only images"""
        return await self.list(media_type=MediaType.IMAGE, per_page=per_page)
    
    async def get_3d_models(self, per_page: int = 20) -> List[MediaItem]:
        """Get 3D model files"""
        # WordPress doesn't have a native 3D model media type
        # Search by MIME type instead
        glb_items = await self.list(mime_type="model/gltf-binary", per_page=per_page)
        gltf_items = await self.list(mime_type="model/gltf+json", per_page=per_page)
        
        return glb_items + gltf_items
    
    async def get_by_post(self, post_id: int, per_page: int = 100) -> List[MediaItem]:
        """Get media attached to a post/product"""
        return await self.list(parent=post_id, per_page=per_page)
