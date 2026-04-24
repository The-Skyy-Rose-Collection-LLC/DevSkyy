"""
ThreeDAgent — Phase 16 Legendary 3D Architect.

Promoted to ADK SuperAgent for comprehensive "Back Data" (telemetry) and 
high-fidelity 3D replica generation using Blender + Gemini RAS.

Inherits from CreativeAgent to leverage standardized enterprise tools
and observability via Google ADK.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from adk.super_agents import CreativeAgent
from adk.base import AgentConfig, ADKProvider
from ai_3d.generation_pipeline import (
    GenerationConfig,
    GenerationQuality,
    ThreeDGenerationPipeline,
)
from ai_3d.virtual_photoshoot import VirtualPhotoshootGenerator, ScenePreset
from ..models import GenerationResult
from ..config import OUTPUT_DIR

logger = logging.getLogger(__name__)

_DEFAULT_3D_OUTPUT_DIR = "renders/3d"

class ThreeDAgent(CreativeAgent):
    """The Architect of 3D Digital Replicas - Promoted to ADK SuperAgent."""

    def __init__(
        self, 
        output_dir_3d: str = _DEFAULT_3D_OUTPUT_DIR,
        output_dir_2d: str | None = None,
        config: AgentConfig | None = None
    ) -> None:
        # Default config if not provided
        if config is None:
            config = AgentConfig(
                name="legendary_3d_architect",
                provider=ADKProvider.GOOGLE,
                model="gemini-2.0-flash",
                system_prompt="You are the Legendary 3D Architect for SkyyRose. Your mission is 100% accurate digital replicas."
            )
        
        # Initialize BaseSuperAgent/CreativeAgent
        super().__init__(config)
        
        self.output_dir_3d = Path(output_dir_3d)
        # Use canonical project output dir if not provided
        self.output_dir_2d = Path(output_dir_2d) if output_dir_2d else OUTPUT_DIR
        
        self.output_dir_3d.mkdir(parents=True, exist_ok=True)
        self.output_dir_2d.mkdir(parents=True, exist_ok=True)
        
        self.pipeline = ThreeDGenerationPipeline()
        self.photoshoot = VirtualPhotoshootGenerator(
            output_dir=self.output_dir_2d,
            models_dir=self.output_dir_3d
        )

    async def generate_replica(
        self, 
        sku: str, 
        techflat_path: str, 
        branding_spec: str,
        style: str = "flat_lay"
    ) -> dict[str, Any]:
        """
        Legendary Replica Workflow:
        1. Digitization: Image -> 3D (.glb)
        2. Scaffolding: 3D -> Headless Blender Render (.png)
        3. Synthesis: Scaffold + Techflat -> Professional Render (.webp)
        """
        # --- Stage 0: ADK Observer ---
        logger.info(f"Starting Legendary 3D-First Workflow for {sku}")
        
        # Capture "Back Data" via ADK run (non-blocking, captures reasoning)
        try:
            adk_prompt = f"REPLICA TASK: SKU={sku}, SPEC={branding_spec}"
            adk_result = await self.execute(adk_prompt)
            metadata = adk_result.to_dict() if hasattr(adk_result, "to_dict") else {}
        except Exception as e:
            logger.warning(f"ADK Telemetry failed for {sku}: {e}")
            metadata = {}
        
        sku_dir = self.output_dir_2d / sku
        sku_dir.mkdir(parents=True, exist_ok=True)

        # --- Stage 1: 3D Digitization ---
        logger.info(f"[{sku}] Stage 1: 3D Digitization (Tripo AI)...")
        config = GenerationConfig(
            quality=GenerationQuality.PRODUCTION,
            output_dir=str(self.output_dir_3d),
            texture_resolution=2048,
            mesh_quality="high",
            minimum_fidelity=40.0,
            enforce_fidelity=False
        )
        
        gen_result = await self.pipeline.generate_from_image(
            image_path=techflat_path,
            config=config,
            prompt=f"Professional 3D clothing model of {sku}. {branding_spec}"
        )

        if not gen_result.success or not gen_result.model_path:
            return {"success": False, "error": f"3D Generation failed: {gen_result.errors}"}

        generated_path = Path(gen_result.model_path)
        glb_path = self.output_dir_3d / f"{sku}.glb"
        shutil.copy2(generated_path, glb_path)
        
        # --- Stage 2: Headless Blender Scaffolding ---
        logger.info(f"[{sku}] Stage 2: Headless Blender Scaffolding...")
        scaffold_path = sku_dir / f"{sku}_scaffold.png"
        
        # Call the verified Blender script
        render_cmd = [
            "blender", "-b", "-P", "scripts/render_professional.py",
            "--", str(glb_path), str(scaffold_path), "front"
        ]
        
        try:
            subprocess.run(render_cmd, check=True, capture_output=True)
            logger.info(f"[{sku}] Scaffold generated at {scaffold_path}")
        except Exception as e:
            logger.error(f"[{sku}] Blender rendering failed: {e}")
            # Fallback to simple synthesis if Blender fails
            scaffold_path = techflat_path 

        # --- Stage 3: Agent-Augmented Synthesis (RAS) ---
        logger.info(f"[{sku}] Stage 3: Agent-Augmented Synthesis (Gemini 2.0)...")
        
        from .generator_agent import GeneratorAgent
        gen_2d = GeneratorAgent(output_dir=str(sku_dir))
        
        ras_prompt = (
            f"You are a professional luxury fashion retoucher for SkyyRose. "
            f"Product: {sku}. Specification: {branding_spec}. "
            "IMAGE 1 (Attached) is the 3D geometry scaffold. "
            "IMAGE 2 (Techflat) is your reference for exact fabric, color, and logos. "
            "Synthesize a high-fidelity professional e-commerce product render where the "
            "garment from the techflat is perfectly wrapped onto the 3D scaffold. "
            "Output MUST be a pure white background, studio lighting, hyper-realistic."
        )

        # Execute generation (RAS uses multiple images)
        synth_result = await gen_2d.generate(sku, "front", ras_prompt, reference_images=[str(scaffold_path), techflat_path])
        
        front_final = sku_dir / f"{sku}-model-front-gemini.jpg"
        shutil.move(synth_result.output_path, front_final)
        
        return {
            "success": True,
            "glb_path": str(glb_path),
            "renders": {"front": str(front_final), "scaffold": str(scaffold_path)},
            "fidelity_score": gen_result.fidelity_score,
            "provider": gen_result.provider_used.value if gen_result.provider_used else "auto",
            "adk_metadata": metadata
        }

    def generate_result_bridge(self, photoshoot_output: dict[str, Any], view: str) -> GenerationResult:
        """Helper to convert photoshoot output back to EliteStudio GenerationResult."""
        path = photoshoot_output["renders"].get(view)
        if not path:
            # Fallback to 'front' if specific view missing
            path = photoshoot_output["renders"].get("front", "")
            
        return GenerationResult(
            success=photoshoot_output["success"],
            provider=f"3d-render/{photoshoot_output.get('provider', 'unknown')}",
            model="ai_3d-replica-v1",
            output_path=path,
            metadata=photoshoot_output.get("adk_metadata", {})
        )
