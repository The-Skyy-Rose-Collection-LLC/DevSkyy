"""
AI 3D Module
============

AI-powered 3D model generation and validation for production.

Components:
- AI3DModelGenerator: Generate 3D models from 2D product images
- VirtualPhotoshootGenerator: Generate lifestyle product imagery
- ModelFidelityValidator: Validate 3D model accuracy

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from ai_3d.model_generator import (
    AI3DModelGenerator,
    GeneratedModel,
    ModelGenerationError,
)
from ai_3d.virtual_photoshoot import (
    GeneratedPhotoshoot,
    PhotoshootScene,
    VirtualPhotoshootGenerator,
)

__all__ = [
    "AI3DModelGenerator",
    "GeneratedModel",
    "ModelGenerationError",
    "VirtualPhotoshootGenerator",
    "PhotoshootScene",
    "GeneratedPhotoshoot",
]
