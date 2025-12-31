# imagery/__init__.py
"""
DevSkyy Imagery Module.

This module provides:
- 3D model fidelity validation (95% threshold)
- Image processing utilities
- Virtual photoshoot automation
- Model quality metrics
"""

from imagery.image_processor import (
    BackgroundRemover,
    ImagePreprocessor,
    ImageProcessor,
)
from imagery.model_fidelity import (
    MINIMUM_FIDELITY_SCORE,
    FidelityMetrics,
    FidelityReport,
    ModelFidelityValidator,
    validate_model_fidelity,
)
from imagery.virtual_photoshoot import (
    PhotoshootConfig,
    PhotoshootResult,
    VirtualPhotoshootPipeline,
)

__all__ = [
    # Fidelity
    "ModelFidelityValidator",
    "FidelityMetrics",
    "FidelityReport",
    "validate_model_fidelity",
    "MINIMUM_FIDELITY_SCORE",
    # Image Processing
    "ImageProcessor",
    "ImagePreprocessor",
    "BackgroundRemover",
    # Virtual Photoshoot
    "VirtualPhotoshootPipeline",
    "PhotoshootConfig",
    "PhotoshootResult",
]
