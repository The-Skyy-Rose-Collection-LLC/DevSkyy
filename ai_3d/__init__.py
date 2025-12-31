# ai_3d/__init__.py
"""
AI-Powered 3D Generation Module for DevSkyy.

This module provides:
- Image-to-3D model generation
- Text-to-3D model generation
- 3D model enhancement and refinement
- Multi-provider support (Tripo3D, HuggingFace, Meshy)
- Quality validation with 95% fidelity enforcement
"""

from ai_3d.generation_pipeline import (
    GenerationConfig,
    GenerationResult,
    ThreeDGenerationPipeline,
    ThreeDProvider,
)
from ai_3d.providers.huggingface import HuggingFace3DClient
from ai_3d.providers.tripo import TripoClient
from ai_3d.quality_enhancer import (
    EnhancementConfig,
    ModelQualityEnhancer,
)

__all__ = [
    # Pipeline
    "ThreeDGenerationPipeline",
    "GenerationConfig",
    "GenerationResult",
    "ThreeDProvider",
    # Providers
    "TripoClient",
    "HuggingFace3DClient",
    # Enhancement
    "ModelQualityEnhancer",
    "EnhancementConfig",
]
