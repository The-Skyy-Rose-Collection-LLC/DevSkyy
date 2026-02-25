"""Shared test fixtures for Elite Studio."""

import pytest

from skyyrose.elite_studio.agents.generator_agent import GeneratorAgent
from skyyrose.elite_studio.agents.quality_agent import QualityAgent
from skyyrose.elite_studio.agents.vision_agent import VisionAgent
from skyyrose.elite_studio.coordinator import Coordinator, NullLogger
from skyyrose.elite_studio.models import (
    GenerationResult,
    ProductData,
    ProductionResult,
    QualityVerification,
    SynthesizedVision,
    VisionAnalysis,
)


# ---------------------------------------------------------------------------
# Model factories — immutable, consistent test data
# ---------------------------------------------------------------------------


def make_product(
    sku: str = "br-001", collection: str = "black-rose", **kwargs
) -> ProductData:
    """Create a test ProductData."""
    return ProductData(sku=sku, collection=collection, **kwargs)


def make_vision_analysis(
    success: bool = True,
    provider: str = "google",
    model: str = "gemini-3-flash-preview",
    analysis: str = "Detailed product analysis...",
    **kwargs,
) -> VisionAnalysis:
    """Create a test VisionAnalysis."""
    return VisionAnalysis(
        success=success,
        provider=provider,
        model=model,
        analysis=analysis,
        char_count=len(analysis) if success else 0,
        **kwargs,
    )


def make_synthesized_vision(
    success: bool = True,
    unified_spec: str = "Unified product specification...",
    providers_used: tuple[str, ...] = ("gemini", "openai"),
    **kwargs,
) -> SynthesizedVision:
    """Create a test SynthesizedVision."""
    return SynthesizedVision(
        success=success,
        unified_spec=unified_spec,
        providers_used=providers_used,
        **kwargs,
    )


def make_generation_result(
    success: bool = True,
    output_path: str = "/tmp/br-001-model-front-gemini.jpg",
    **kwargs,
) -> GenerationResult:
    """Create a test GenerationResult."""
    return GenerationResult(
        success=success,
        provider="google",
        model="gemini-3-pro-image-preview",
        output_path=output_path if success else "",
        **kwargs,
    )


def make_quality_verification(
    success: bool = True,
    overall_status: str = "pass",
    recommendation: str = "approve",
    **kwargs,
) -> QualityVerification:
    """Create a test QualityVerification."""
    return QualityVerification(
        success=success,
        provider="anthropic",
        model="claude-sonnet-4",
        overall_status=overall_status,
        recommendation=recommendation,
        **kwargs,
    )


def make_production_result(
    sku: str = "br-001",
    view: str = "front",
    status: str = "success",
    output_path: str = "/tmp/br-001-model-front-gemini.jpg",
    **kwargs,
) -> ProductionResult:
    """Create a test ProductionResult."""
    return ProductionResult(
        sku=sku,
        view=view,
        status=status,
        output_path=output_path if status == "success" else "",
        vision=make_synthesized_vision() if status == "success" else None,
        quality=make_quality_verification() if status == "success" else None,
        **kwargs,
    )


# ---------------------------------------------------------------------------
# Coordinator with NullLogger (no stdout noise in tests)
# ---------------------------------------------------------------------------


@pytest.fixture
def silent_coordinator():
    """Coordinator with silent logger for clean test output."""
    from unittest.mock import MagicMock

    return Coordinator(
        vision=MagicMock(),
        generator=MagicMock(),
        quality=MagicMock(),
        logger=NullLogger(),
    )
