"""
Imagery Module
==============

Image processing and validation for 3D model fidelity.

Components:
- ModelFidelityValidator: Validate 3D model accuracy against reference images
- ProductImageGenerator: Process and optimize product images
- FidelityReport: Detailed validation results

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from imagery.model_fidelity import (
    FidelityReport,
    ModelFidelityValidator,
    validate_model_fidelity,
)

__all__ = [
    "ModelFidelityValidator",
    "FidelityReport",
    "validate_model_fidelity",
]
