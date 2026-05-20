"""TRELLIS — Microsoft's Structured 3D Latents pipeline for clothing.

End-to-end image-to-3D + text-to-3D generation tuned for garment imagery.
Backed by https://github.com/microsoft/TRELLIS (vendored at ``vendor/trellis``)
with fallback to the public HuggingFace Space ``JeffreyXiang/TRELLIS``.

Subpackages
-----------
- :mod:`config` — declarative configuration
- :mod:`garment_aware` — clothing-category knowledge & prompt templating
- :mod:`preprocess` — input image preparation (bg removal, crop, normalize)
- :mod:`client` — backend transport (HF Space / local Python / Replicate)
- :mod:`postprocess` — mesh cleanup, format conversion, AR export
- :mod:`provider` — :class:`I3DProvider` implementation used by the factory

Entry point
-----------
.. code-block:: python

    from services.three_d.trellis import TrellisProvider, TrellisConfig

    provider = TrellisProvider(TrellisConfig.from_env())
    response = await provider.generate_from_image(request)

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

from services.three_d.trellis.config import (
    TrellisBackend,
    TrellisConfig,
    TrellisQualityPreset,
)
from services.three_d.trellis.garment_aware import (
    GarmentCategory,
    GarmentKnowledge,
    build_clothing_prompt,
    classify_garment,
)
from services.three_d.trellis.postprocess import MeshPostprocessor, PostprocessResult
from services.three_d.trellis.preprocess import (
    PreprocessedImage,
    PreprocessResult,
    TrellisPreprocessor,
)
from services.three_d.trellis.provider import TrellisProvider

__all__ = [
    # Provider
    "TrellisProvider",
    # Config
    "TrellisConfig",
    "TrellisBackend",
    "TrellisQualityPreset",
    # Preprocessing
    "TrellisPreprocessor",
    "PreprocessedImage",
    "PreprocessResult",
    # Postprocessing
    "MeshPostprocessor",
    "PostprocessResult",
    # Garment knowledge
    "GarmentCategory",
    "GarmentKnowledge",
    "classify_garment",
    "build_clothing_prompt",
]
