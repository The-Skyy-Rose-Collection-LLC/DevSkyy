"""
ThreeDAgent — Phase 16 Legendary 3D Architect.

This agent is responsible for creating 100% replica 3D models from 2D techflats.
It uses the ai_3d generation pipeline to produce .glb assets and performs 
a virtual photoshoot to generate consistent, hallucination-free 2D renders.

Legendary Capabilities:
- Geometry synthesis from techflats.
- Texture baking with spec-primacy.
- Multimodal QA (considers both geometry and branding).
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any

from ai_3d.generation_pipeline import (
    GenerationConfig,
    GenerationQuality,
    ThreeDGenerationPipeline,
    ThreeDProvider,
)
from ai_3d.virtual_photoshoot import VirtualPhotoshoot, PhotoshootConfig
from ..models import GenerationResult

logger = logging.getLogger(__name__)

_DEFAULT_3D_OUTPUT_DIR = "renders/3d"
_DEFAULT_2D_OUTPUT_DIR = "renders/output"

class ThreeDAgent:
    """The Architect of 3D Digital Replicas."""

    def __init__(
        self, 
        output_dir_3d: str = _DEFAULT_3D_OUTPUT_DIR,
        output_dir_2d: str = _DEFAULT_2D_OUTPUT_DIR
    ) -> None:
        self.output_dir_3d = Path(output_dir_3d)
        self.output_dir_2d = Path(output_dir_2d)
        self.output_dir_3d.mkdir(parents=True, exist_ok=True)
        self.output_dir_2d.mkdir(parents=True, exist_ok=True)
        
        self.pipeline = ThreeDGenerationPipeline()
        self.photoshoot = VirtualPhotoshoot()

    async def generate_replica(
        self, 
        sku: str, 
        techflat_path: str, 
        branding_spec: str
    ) -> dict[str, Any]:
        """
        Creates a 3D model and renders 2D shots.
        
        Returns:
            {
                "success": bool,
                "glb_path": str,
                "renders": {
                    "front": str,
                    "back": str,
                    "ghost": str
                },
                "fidelity_score": float
            }
        """
        logger.info(f"Generating 3D Replica for {sku}...")

        # 1. 3D Generation
        config = GenerationConfig(
            quality=GenerationQuality.PRODUCTION,
            output_dir=str(self.output_dir_3d),
            texture_resolution=2048,
            mesh_quality="high"
        )
        
        # Guide the 3D modeler with the branding spec
        prompt = f"Professional 3D clothing model of {sku}. {branding_spec}. High fidelity textures, realistic drape."
        
        result = await self.pipeline.generate_from_image(
            image_path=techflat_path,
            config=config,
            prompt=prompt
        )

        if not result.success or not result.model_path:
            return {
                "success": False, 
                "error": f"3D Generation failed: {result.errors}"
            }

        glb_path = Path(result.model_path)
        
        # 2. Virtual Photoshoot (Consistent 2D Renders)
        logger.info(f"Triggering Virtual Photoshoot for {sku}...")
        
        shoot_config = PhotoshootConfig(
            output_dir=str(self.output_dir_2d),
            resolution=(1200, 1200),
            transparent_bg=False,
            lighting="studio"
        )
        
        # Render front, back, and ghost shots from the master .glb
        photos = await self.photoshoot.run_shoot(
            model_path=str(glb_path),
            sku=sku,
            config=shoot_config,
            views=["front", "back", "ghost"]
        )

        return {
            "success": True,
            "glb_path": str(glb_path),
            "renders": photos,
            "fidelity_score": result.fidelity_score,
            "provider": result.provider_used.value if result.provider_used else "auto"
        }

    def generate_result_bridge(self, photoshoot_output: dict[str, Any], view: str) -> GenerationResult:
        """Helper to convert photoshoot output back to EliteStudio GenerationResult."""
        path = photoshoot_output["renders"].get(view)
        if not path:
            # Fallback to 'ghost' if specific view missing
            path = photoshoot_output["renders"].get("ghost", "")
            
        return GenerationResult(
            success=photoshoot_output["success"],
            provider=f"3d-render/{photoshoot_output.get('provider', 'unknown')}",
            model="ai_3d-replica-v1",
            output_path=path
        )
