"""
Tripo3D Asset Generation Agent
==============================

Generate 3D clothing models using Tripo3D API.

Features:
- Text-to-3D model generation
- Image-to-3D conversion
- Multi-view to 3D
- Automatic texture generation
- GLB/FBX/OBJ export

API Documentation: https://docs.tripo3d.ai/
SDK: pip install tripo3d

Pricing (as of Dec 2025):
- Starter: Free, 300 credits
- Professional: $19.90/month, 3,000 credits
- Enterprise: Custom pricing
"""

import os
import asyncio
import logging
import aiohttp
import aiofiles
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass, field
from enum import Enum
import json
import time

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration & Enums
# =============================================================================

class TripoTaskStatus(str, Enum):
    """Tripo task status"""
    QUEUED = "queued"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ModelFormat(str, Enum):
    """3D model output formats"""
    GLB = "glb"      # Binary glTF - recommended for web
    GLTF = "gltf"    # JSON glTF
    FBX = "fbx"      # Autodesk FBX
    OBJ = "obj"      # Wavefront OBJ
    USDZ = "usdz"    # Apple AR format
    STL = "stl"      # 3D printing


class ModelStyle(str, Enum):
    """Generation style presets"""
    REALISTIC = "realistic"
    CARTOON = "cartoon"
    ANIME = "anime"
    LOW_POLY = "low-poly"


@dataclass
class TripoConfig:
    """Tripo3D configuration"""
    api_key: str = field(default_factory=lambda: os.getenv("TRIPO_API_KEY", ""))
    base_url: str = "https://api.tripo3d.ai/v2"
    timeout: float = 300.0  # 5 minutes for generation
    poll_interval: float = 2.0
    output_dir: str = "./generated_assets/3d"
    
    @classmethod
    def from_env(cls) -> "TripoConfig":
        return cls(
            api_key=os.getenv("TRIPO_API_KEY", ""),
            output_dir=os.getenv("TRIPO_OUTPUT_DIR", "./generated_assets/3d"),
        )


# =============================================================================
# Models
# =============================================================================

class TripoTask(BaseModel):
    """Tripo generation task"""
    task_id: str
    status: TripoTaskStatus
    progress: int = 0
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: str = ""
    completed_at: Optional[str] = None
    
    # Model details
    model_url: Optional[str] = None
    texture_url: Optional[str] = None
    thumbnail_url: Optional[str] = None


class GenerationResult(BaseModel):
    """3D generation result"""
    task_id: str
    model_path: str
    model_url: str
    format: ModelFormat
    texture_path: Optional[str] = None
    thumbnail_path: Optional[str] = None
    metadata: Dict[str, Any] = {}


# =============================================================================
# SkyyRose Brand Prompts
# =============================================================================

SKYYROSE_BRAND_DNA = """
Brand: SkyyRose
Philosophy: "Where Love Meets Luxury"
Location: Oakland, California
Style: Gender-neutral luxury streetwear
Colors: Rose gold (#D4AF37), Obsidian black (#0D0D0D), Ivory (#F5F5F0)
Aesthetic: Elevated street poetry, intellectual luxury, premium materials
Quality: High-end construction, attention to detail, exclusive limited editions
"""

COLLECTION_PROMPTS = {
    "BLACK_ROSE": {
        "style": "dark elegance, limited edition, exclusive",
        "colors": "deep black, subtle rose gold accents, matte finish",
        "mood": "mysterious, sophisticated, rare",
    },
    "LOVE_HURTS": {
        "style": "emotional expression, storytelling through design",
        "colors": "deep reds, black, heart motifs",
        "mood": "passionate, vulnerable, powerful",
    },
    "SIGNATURE": {
        "style": "timeless essentials, foundation wardrobe",
        "colors": "clean neutrals, rose gold details",
        "mood": "classic, versatile, elevated basics",
    },
}

GARMENT_TEMPLATES = {
    "hoodie": "luxury streetwear hoodie, premium heavyweight cotton, relaxed fit, kangaroo pocket",
    "bomber": "premium bomber jacket, satin lining, ribbed cuffs and hem, quality hardware",
    "track_pants": "luxury track pants, side stripe detail, tapered fit, premium fabric",
    "tee": "premium t-shirt, heavyweight cotton, relaxed fit, quality construction",
    "sweatshirt": "luxury crewneck sweatshirt, heavyweight fleece, ribbed details",
    "jacket": "structured jacket, premium materials, tailored streetwear fit",
    "shorts": "luxury shorts, premium cotton, embroidered details",
    "cap": "structured cap, quality embroidery, adjustable strap",
    "beanie": "luxury knit beanie, soft premium yarn, embroidered logo",
}


# =============================================================================
# Tripo3D Agent
# =============================================================================

class TripoAssetAgent:
    """
    Tripo3D Asset Generation Agent
    
    Generates 3D clothing models for SkyyRose products.
    
    Usage:
        agent = TripoAssetAgent()
        
        # From description
        result = await agent.generate_from_description(
            product_name="Heart aRose Bomber",
            collection="BLACK_ROSE",
            garment_type="bomber",
            additional_details="Rose gold zipper, embroidered rose on back"
        )
        
        # From image
        result = await agent.generate_from_image(
            image_path="/path/to/design.jpg",
            product_name="Custom Hoodie"
        )
    """
    
    def __init__(self, config: TripoConfig = None):
        self.config = config or TripoConfig.from_env()
        self._session: Optional[aiohttp.ClientSession] = None
        
        # Ensure output directory exists
        Path(self.config.output_dir).mkdir(parents=True, exist_ok=True)
    
    async def __aenter__(self):
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def _ensure_session(self):
        """Ensure aiohttp session exists"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=aiohttp.ClientTimeout(total=self.config.timeout),
            )
    
    async def close(self):
        """Close session"""
        if self._session and not self._session.closed:
            await self._session.close()
    
    def _build_prompt(
        self,
        product_name: str,
        collection: str,
        garment_type: str,
        additional_details: str = "",
    ) -> str:
        """Build optimized prompt for 3D generation"""
        # Get collection style
        collection_style = COLLECTION_PROMPTS.get(
            collection.upper(),
            COLLECTION_PROMPTS["SIGNATURE"]
        )
        
        # Get garment template
        garment_base = GARMENT_TEMPLATES.get(
            garment_type.lower(),
            "luxury streetwear garment, premium quality"
        )
        
        # Build comprehensive prompt
        prompt_parts = [
            f"3D model of {product_name}",
            garment_base,
            f"Style: {collection_style['style']}",
            f"Colors: {collection_style['colors']}",
            "High quality mesh, clean topology, quad-based geometry",
            "Photorealistic textures, PBR materials",
            "Fashion product visualization, e-commerce ready",
        ]
        
        if additional_details:
            prompt_parts.append(additional_details)
        
        return ". ".join(prompt_parts)
    
    async def _api_request(
        self,
        method: str,
        endpoint: str,
        data: dict = None,
    ) -> dict:
        """Make API request"""
        await self._ensure_session()
        
        url = f"{self.config.base_url}/{endpoint.lstrip('/')}"
        
        async with self._session.request(method, url, json=data) as response:
            result = await response.json()
            
            if response.status >= 400:
                error_msg = result.get("message", str(result))
                raise Exception(f"Tripo API error ({response.status}): {error_msg}")
            
            return result
    
    async def _poll_task(self, task_id: str) -> TripoTask:
        """Poll task until completion"""
        while True:
            result = await self._api_request("GET", f"/task/{task_id}")
            
            task = TripoTask(
                task_id=task_id,
                status=TripoTaskStatus(result.get("status", "queued")),
                progress=result.get("progress", 0),
                result=result.get("output"),
            )
            
            if task.status == TripoTaskStatus.SUCCESS:
                task.model_url = result.get("output", {}).get("model", {}).get("url")
                task.texture_url = result.get("output", {}).get("texture", {}).get("url")
                task.thumbnail_url = result.get("output", {}).get("thumbnail", {}).get("url")
                task.completed_at = datetime.now(timezone.utc).isoformat()
                return task
            
            if task.status == TripoTaskStatus.FAILED:
                task.error = result.get("error", "Unknown error")
                raise Exception(f"Task failed: {task.error}")
            
            if task.status == TripoTaskStatus.CANCELLED:
                raise Exception("Task was cancelled")
            
            logger.debug(f"Task {task_id}: {task.status.value} ({task.progress}%)")
            await asyncio.sleep(self.config.poll_interval)
    
    async def _download_file(self, url: str, filename: str) -> str:
        """Download file to output directory"""
        await self._ensure_session()
        
        filepath = Path(self.config.output_dir) / filename
        
        async with self._session.get(url) as response:
            if response.status >= 400:
                raise Exception(f"Download failed: {response.status}")
            
            async with aiofiles.open(filepath, "wb") as f:
                async for chunk in response.content.iter_chunked(8192):
                    await f.write(chunk)
        
        logger.info(f"Downloaded: {filepath}")
        return str(filepath)
    
    # -------------------------------------------------------------------------
    # Generation Methods
    # -------------------------------------------------------------------------
    
    async def generate_from_description(
        self,
        product_name: str,
        collection: str = "SIGNATURE",
        garment_type: str = "hoodie",
        additional_details: str = "",
        output_format: ModelFormat = ModelFormat.GLB,
        texture: bool = True,
        style: ModelStyle = ModelStyle.REALISTIC,
    ) -> GenerationResult:
        """
        Generate 3D model from text description
        
        Args:
            product_name: Name of the product
            collection: SkyyRose collection (BLACK_ROSE, LOVE_HURTS, SIGNATURE)
            garment_type: Type of garment (hoodie, bomber, tee, etc.)
            additional_details: Extra details for the prompt
            output_format: Output format (GLB recommended for web)
            texture: Generate textures
            style: Style preset
            
        Returns:
            GenerationResult with model path and URLs
        """
        prompt = self._build_prompt(
            product_name=product_name,
            collection=collection,
            garment_type=garment_type,
            additional_details=additional_details,
        )
        
        logger.info(f"Generating 3D model for: {product_name}")
        logger.debug(f"Prompt: {prompt}")
        
        # Start generation task
        task_data = {
            "type": "text_to_model",
            "prompt": prompt,
            "texture": texture,
            "style": style.value,
            "output_format": output_format.value,
        }
        
        result = await self._api_request("POST", "/task", data=task_data)
        task_id = result.get("task_id")
        
        if not task_id:
            raise Exception("No task_id returned from API")
        
        logger.info(f"Started task: {task_id}")
        
        # Poll for completion
        task = await self._poll_task(task_id)
        
        # Download model
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = product_name.lower().replace(" ", "_")
        filename = f"{safe_name}_{timestamp}.{output_format.value}"
        
        model_path = await self._download_file(task.model_url, filename)
        
        # Download texture if available
        texture_path = None
        if task.texture_url:
            texture_filename = f"{safe_name}_{timestamp}_texture.png"
            texture_path = await self._download_file(task.texture_url, texture_filename)
        
        # Download thumbnail
        thumbnail_path = None
        if task.thumbnail_url:
            thumb_filename = f"{safe_name}_{timestamp}_thumb.png"
            thumbnail_path = await self._download_file(task.thumbnail_url, thumb_filename)
        
        return GenerationResult(
            task_id=task_id,
            model_path=model_path,
            model_url=task.model_url,
            format=output_format,
            texture_path=texture_path,
            thumbnail_path=thumbnail_path,
            metadata={
                "product_name": product_name,
                "collection": collection,
                "garment_type": garment_type,
                "prompt": prompt,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            },
        )
    
    async def generate_from_image(
        self,
        image_path: str,
        product_name: str,
        output_format: ModelFormat = ModelFormat.GLB,
        texture: bool = True,
    ) -> GenerationResult:
        """
        Generate 3D model from image
        
        Args:
            image_path: Path to input image
            product_name: Name for the product
            output_format: Output format
            texture: Generate textures
            
        Returns:
            GenerationResult with model details
        """
        # Read and encode image
        async with aiofiles.open(image_path, "rb") as f:
            image_data = await f.read()
        
        import base64
        image_b64 = base64.b64encode(image_data).decode()
        
        # Determine image type
        ext = Path(image_path).suffix.lower()
        mime_types = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}
        mime_type = mime_types.get(ext, "image/jpeg")
        
        logger.info(f"Generating 3D from image: {image_path}")
        
        # Start task
        task_data = {
            "type": "image_to_model",
            "image": f"data:{mime_type};base64,{image_b64}",
            "texture": texture,
            "output_format": output_format.value,
        }
        
        result = await self._api_request("POST", "/task", data=task_data)
        task_id = result.get("task_id")
        
        if not task_id:
            raise Exception("No task_id returned")
        
        # Poll and download
        task = await self._poll_task(task_id)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = product_name.lower().replace(" ", "_")
        filename = f"{safe_name}_{timestamp}.{output_format.value}"
        
        model_path = await self._download_file(task.model_url, filename)
        
        texture_path = None
        if task.texture_url:
            texture_path = await self._download_file(
                task.texture_url,
                f"{safe_name}_{timestamp}_texture.png"
            )
        
        return GenerationResult(
            task_id=task_id,
            model_path=model_path,
            model_url=task.model_url,
            format=output_format,
            texture_path=texture_path,
            metadata={
                "product_name": product_name,
                "source_image": image_path,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            },
        )
    
    async def generate_from_multiview(
        self,
        front_image: str,
        back_image: str,
        left_image: str = None,
        right_image: str = None,
        product_name: str = "product",
        output_format: ModelFormat = ModelFormat.GLB,
    ) -> GenerationResult:
        """
        Generate 3D model from multiple views
        
        Args:
            front_image: Front view image path
            back_image: Back view image path
            left_image: Optional left view
            right_image: Optional right view
            product_name: Product name
            output_format: Output format
            
        Returns:
            GenerationResult with model details
        """
        import base64
        
        async def encode_image(path: str) -> str:
            async with aiofiles.open(path, "rb") as f:
                data = await f.read()
            return base64.b64encode(data).decode()
        
        images = {
            "front": await encode_image(front_image),
            "back": await encode_image(back_image),
        }
        
        if left_image:
            images["left"] = await encode_image(left_image)
        if right_image:
            images["right"] = await encode_image(right_image)
        
        logger.info(f"Generating 3D from {len(images)} views")
        
        task_data = {
            "type": "multiview_to_model",
            "images": images,
            "output_format": output_format.value,
        }
        
        result = await self._api_request("POST", "/task", data=task_data)
        task_id = result.get("task_id")
        
        task = await self._poll_task(task_id)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = product_name.lower().replace(" ", "_")
        filename = f"{safe_name}_{timestamp}.{output_format.value}"
        
        model_path = await self._download_file(task.model_url, filename)
        
        return GenerationResult(
            task_id=task_id,
            model_path=model_path,
            model_url=task.model_url,
            format=output_format,
            metadata={
                "product_name": product_name,
                "view_count": len(images),
                "generated_at": datetime.now(timezone.utc).isoformat(),
            },
        )
    
    # -------------------------------------------------------------------------
    # Utility Methods
    # -------------------------------------------------------------------------
    
    async def get_task_status(self, task_id: str) -> TripoTask:
        """Get current task status"""
        result = await self._api_request("GET", f"/task/{task_id}")
        
        return TripoTask(
            task_id=task_id,
            status=TripoTaskStatus(result.get("status", "queued")),
            progress=result.get("progress", 0),
            result=result.get("output"),
            model_url=result.get("output", {}).get("model", {}).get("url"),
        )
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task"""
        try:
            await self._api_request("POST", f"/task/{task_id}/cancel")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel task: {e}")
            return False
    
    async def list_tasks(self, limit: int = 20) -> List[TripoTask]:
        """List recent tasks"""
        result = await self._api_request("GET", f"/tasks?limit={limit}")
        
        tasks = []
        for item in result.get("tasks", []):
            tasks.append(TripoTask(
                task_id=item.get("task_id"),
                status=TripoTaskStatus(item.get("status", "queued")),
                progress=item.get("progress", 0),
                created_at=item.get("created_at", ""),
            ))
        
        return tasks
    
    async def get_credits(self) -> dict:
        """Get remaining API credits"""
        result = await self._api_request("GET", "/account/credits")
        return {
            "remaining": result.get("remaining", 0),
            "total": result.get("total", 0),
            "used": result.get("used", 0),
        }
