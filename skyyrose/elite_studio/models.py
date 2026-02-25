"""
Frozen dataclasses for the Elite Studio pipeline.

All results are immutable — prevents hidden side effects between pipeline stages.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ProductData:
    """Product metadata loaded from override JSON."""

    sku: str
    collection: str
    garment_type_lock: str = ""
    logo_fingerprint: dict[str, Any] = field(default_factory=dict)
    branding_tech: dict[str, Any] = field(default_factory=dict)
    reference_images: tuple[str, ...] = ()

    @classmethod
    def from_override(cls, sku: str, data: dict[str, Any]) -> ProductData:
        """Create from override JSON data."""
        return cls(
            sku=sku.strip().lower(),
            collection=data.get("collection", "unknown"),
            garment_type_lock=data.get("garmentTypeLock", ""),
            logo_fingerprint=data.get("logoFingerprint", {}),
            branding_tech=data.get("brandingTech", {}),
            reference_images=tuple(data.get("referenceImages", [])),
        )


@dataclass(frozen=True)
class VisionAnalysis:
    """Result from a single vision provider."""

    success: bool
    provider: str
    model: str
    analysis: str = ""
    error: str = ""
    char_count: int = 0


@dataclass(frozen=True)
class SynthesizedVision:
    """Merged result from multiple vision providers."""

    success: bool
    unified_spec: str = ""
    providers_used: tuple[str, ...] = ()
    individual_results: tuple[VisionAnalysis, ...] = ()
    error: str = ""

    @property
    def provider_count(self) -> int:
        return len(self.providers_used)


@dataclass(frozen=True)
class GenerationResult:
    """Result from image generation."""

    success: bool
    provider: str = ""
    model: str = ""
    output_path: str = ""
    error: str = ""


@dataclass(frozen=True)
class QualityVerification:
    """Result from quality control verification."""

    success: bool
    provider: str = ""
    model: str = ""
    overall_status: str = ""  # pass, warn, fail
    recommendation: str = ""  # approve, regenerate, manual_review
    details: dict[str, Any] = field(default_factory=dict)
    error: str = ""


@dataclass(frozen=True)
class ProductionResult:
    """Complete production result for a single product."""

    sku: str
    view: str
    status: str  # success, error
    output_path: str = ""
    vision: SynthesizedVision | None = None
    generation: GenerationResult | None = None
    quality: QualityVerification | None = None
    error: str = ""
    step: str = ""  # which step failed (vision, generation, quality)
