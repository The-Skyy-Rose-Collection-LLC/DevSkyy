"""Tests for Elite Studio models — frozen dataclasses."""

import pytest

from skyyrose.elite_studio.models import (
    GenerationResult,
    ProductData,
    ProductionResult,
    QualityVerification,
    SynthesizedVision,
    VisionAnalysis,
)


class TestProductData:
    def test_frozen(self):
        p = ProductData(sku="br-001", collection="black-rose")
        with pytest.raises(AttributeError):
            p.sku = "br-002"  # type: ignore[misc]

    def test_from_override(self):
        data = {
            "collection": "black-rose",
            "garmentTypeLock": "Crewneck Sweatshirt",
            "logoFingerprint": {"technique": "embossed"},
            "brandingTech": {"technique": "embossed"},
            "referenceImages": ["black-rose/br-001-crewneck-front.png"],
        }
        p = ProductData.from_override("BR-001", data)
        assert p.sku == "br-001"
        assert p.collection == "black-rose"
        assert p.garment_type_lock == "Crewneck Sweatshirt"
        assert p.reference_images == ("black-rose/br-001-crewneck-front.png",)

    def test_from_override_defaults(self):
        p = ProductData.from_override("test-001", {})
        assert p.sku == "test-001"
        assert p.collection == "unknown"
        assert p.garment_type_lock == ""


class TestVisionAnalysis:
    def test_frozen(self):
        v = VisionAnalysis(success=True, provider="google", model="flash")
        with pytest.raises(AttributeError):
            v.success = False  # type: ignore[misc]

    def test_success(self):
        v = VisionAnalysis(
            success=True,
            provider="google",
            model="gemini-3-flash-preview",
            analysis="Detailed analysis...",
            char_count=20,
        )
        assert v.success
        assert v.provider == "google"

    def test_failure(self):
        v = VisionAnalysis(
            success=False,
            provider="openai",
            model="gpt-4o",
            error="Rate limited",
        )
        assert not v.success
        assert v.error == "Rate limited"


class TestSynthesizedVision:
    def test_provider_count(self):
        sv = SynthesizedVision(
            success=True,
            unified_spec="...",
            providers_used=("gemini", "openai"),
        )
        assert sv.provider_count == 2

    def test_single_provider(self):
        sv = SynthesizedVision(
            success=True,
            unified_spec="...",
            providers_used=("gemini",),
        )
        assert sv.provider_count == 1


class TestGenerationResult:
    def test_success(self):
        g = GenerationResult(
            success=True,
            provider="google",
            model="gemini-3-pro-image-preview",
            output_path="/tmp/test.jpg",
        )
        assert g.output_path == "/tmp/test.jpg"


class TestQualityVerification:
    def test_pass(self):
        q = QualityVerification(
            success=True,
            provider="anthropic",
            model="claude-sonnet-4",
            overall_status="pass",
            recommendation="approve",
        )
        assert q.overall_status == "pass"

    def test_fail(self):
        q = QualityVerification(
            success=True,
            provider="anthropic",
            model="claude-sonnet-4",
            overall_status="fail",
            recommendation="regenerate",
        )
        assert q.recommendation == "regenerate"


class TestProductionResult:
    def test_success(self):
        r = ProductionResult(
            sku="br-001",
            view="front",
            status="success",
            output_path="/tmp/br-001.jpg",
        )
        assert r.status == "success"

    def test_error(self):
        r = ProductionResult(
            sku="br-001",
            view="front",
            status="error",
            step="vision",
            error="No reference image",
        )
        assert r.step == "vision"
