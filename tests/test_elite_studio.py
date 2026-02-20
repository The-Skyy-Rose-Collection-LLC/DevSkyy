"""
Tests for SkyyRose Elite Production Studio v2.0

Tests the Pydantic models, image utilities, retry logic, and pipeline
orchestration without requiring actual API credentials.
"""

import asyncio
import json
import os
import tempfile
import uuid
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Test Pydantic Models
# ---------------------------------------------------------------------------


class TestPydanticModels:
    """Verify structured data flow models."""

    def test_stage_metrics_defaults(self):
        from skyyrose.skyyrose_elite_studio import StageMetrics

        m = StageMetrics(stage="vision", provider="openai", model="gpt-4o")
        assert m.stage == "vision"
        assert m.provider == "openai"
        assert m.success is True
        assert m.error is None
        assert m.latency_ms == 0.0

    def test_provider_analysis(self):
        from skyyrose.skyyrose_elite_studio import ProviderAnalysis

        a = ProviderAnalysis(
            provider="openai",
            model="gpt-4o",
            role="detail_extraction",
            analysis="Detailed garment analysis...",
            latency_ms=1234.5,
        )
        assert a.provider == "openai"
        assert a.role == "detail_extraction"
        assert a.latency_ms == 1234.5

    def test_vision_spec(self):
        from skyyrose.skyyrose_elite_studio import ProviderAnalysis, VisionSpec

        spec = VisionSpec(
            sku="br-001",
            view="front",
            unified_spec="Full garment specification...",
            generation_warnings=["Low resolution reference"],
        )
        assert spec.sku == "br-001"
        assert len(spec.generation_warnings) == 1
        assert spec.provider_analyses == []

    def test_generation_result(self):
        from skyyrose.skyyrose_elite_studio import GenerationResult

        gen = GenerationResult(
            sku="br-001",
            view="front",
            output_path="/tmp/test.jpg",
            provider="google",
            model="gemini-3-pro-image-preview",
        )
        assert gen.fallback_used is False
        assert gen.attempt == 1
        assert gen.resolution == "4K"

    def test_quality_status_enum(self):
        from skyyrose.skyyrose_elite_studio import QualityStatus

        assert QualityStatus.PASS == "pass"
        assert QualityStatus.WARN == "warn"
        assert QualityStatus.FAIL == "fail"

    def test_quality_decision_enum(self):
        from skyyrose.skyyrose_elite_studio import QualityDecision

        assert QualityDecision.APPROVE == "approve"
        assert QualityDecision.REGENERATE == "regenerate"
        assert QualityDecision.MANUAL_REVIEW == "manual_review"

    def test_quality_check_item(self):
        from skyyrose.skyyrose_elite_studio import QualityCheckItem, QualityStatus

        item = QualityCheckItem(
            category="logo_accuracy",
            status=QualityStatus.PASS,
            notes="Logo matches reference exactly",
        )
        assert item.category == "logo_accuracy"
        assert item.status == QualityStatus.PASS

    def test_quality_report_defaults(self):
        from skyyrose.skyyrose_elite_studio import (
            QualityDecision,
            QualityReport,
            QualityStatus,
        )

        report = QualityReport()
        assert report.overall_status == QualityStatus.WARN
        assert report.decision == QualityDecision.MANUAL_REVIEW
        assert report.checks == []

    def test_production_result_auto_correlation_id(self):
        from skyyrose.skyyrose_elite_studio import ProductionResult

        r1 = ProductionResult(sku="br-001", view="front")
        r2 = ProductionResult(sku="br-001", view="front")
        assert r1.correlation_id != r2.correlation_id
        assert len(r1.correlation_id) == 8

    def test_production_result_defaults(self):
        from skyyrose.skyyrose_elite_studio import ProductionResult

        result = ProductionResult(sku="br-001", view="front")
        assert result.status == "pending"
        assert result.attempts == 0
        assert result.output_path == ""
        assert result.error is None
        assert result.total_latency_ms == 0.0


# ---------------------------------------------------------------------------
# Test Image Utilities
# ---------------------------------------------------------------------------


class TestImageUtilities:
    """Test utility functions without external deps."""

    def test_load_product_data_missing(self):
        from skyyrose.skyyrose_elite_studio import load_product_data

        result = load_product_data("nonexistent-sku-999")
        assert "error" in result

    def test_get_reference_image_path_missing(self):
        from skyyrose.skyyrose_elite_studio import get_reference_image_path

        path = get_reference_image_path("nonexistent-sku-999", "front")
        assert path == ""

    def test_list_available_skus(self):
        from skyyrose.skyyrose_elite_studio import list_available_skus

        skus = list_available_skus()
        # Should return a list (possibly empty if no overrides dir)
        assert isinstance(skus, list)

    def test_list_available_skus_with_collection(self):
        from skyyrose.skyyrose_elite_studio import list_available_skus

        skus = list_available_skus("nonexistent-collection")
        assert isinstance(skus, list)
        assert len(skus) == 0


# ---------------------------------------------------------------------------
# Test Quality JSON Parsing
# ---------------------------------------------------------------------------


class TestQualityParsing:
    """Test the quality JSON parsing logic."""

    def test_parse_clean_json(self):
        from skyyrose.skyyrose_elite_studio import QualityPipeline, QualityStatus

        pipeline = QualityPipeline()
        raw = json.dumps(
            {
                "logo_accuracy": {"status": "pass", "notes": "Looks good"},
                "garment_accuracy": {"status": "warn", "notes": "Minor issue"},
            }
        )
        checks = pipeline._parse_quality_json(raw)
        assert len(checks) == 2
        assert checks[0].category == "logo_accuracy"
        assert checks[0].status == QualityStatus.PASS
        assert checks[1].status == QualityStatus.WARN

    def test_parse_json_with_markdown_fences(self):
        from skyyrose.skyyrose_elite_studio import QualityPipeline, QualityStatus

        pipeline = QualityPipeline()
        raw = '```json\n{"photo_quality": {"status": "fail", "notes": "Blurry"}}\n```'
        checks = pipeline._parse_quality_json(raw)
        assert len(checks) == 1
        assert checks[0].status == QualityStatus.FAIL
        assert checks[0].category == "photo_quality"

    def test_parse_invalid_json(self):
        from skyyrose.skyyrose_elite_studio import QualityPipeline, QualityStatus

        pipeline = QualityPipeline()
        checks = pipeline._parse_quality_json("not valid json at all")
        assert len(checks) == 1
        assert checks[0].category == "parse_error"
        assert checks[0].status == QualityStatus.WARN

    def test_parse_unknown_status(self):
        from skyyrose.skyyrose_elite_studio import QualityPipeline, QualityStatus

        pipeline = QualityPipeline()
        raw = json.dumps(
            {"test": {"status": "unknown_status", "notes": "test"}}
        )
        checks = pipeline._parse_quality_json(raw)
        assert len(checks) == 1
        assert checks[0].status == QualityStatus.WARN  # Falls back to WARN


# ---------------------------------------------------------------------------
# Test Retry Logic
# ---------------------------------------------------------------------------


class TestRetryLogic:
    """Test exponential backoff retry."""

    def test_retry_succeeds_first_try(self):
        from skyyrose.skyyrose_elite_studio import retry_async

        call_count = 0

        async def succeed():
            nonlocal call_count
            call_count += 1
            return "ok"

        result = asyncio.run(retry_async(succeed, attempts=3, base_delay=0.01))
        assert result == "ok"
        assert call_count == 1

    def test_retry_succeeds_after_failures(self):
        from skyyrose.skyyrose_elite_studio import retry_async

        call_count = 0

        async def fail_then_succeed():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("transient")
            return "recovered"

        result = asyncio.run(
            retry_async(fail_then_succeed, attempts=3, base_delay=0.01)
        )
        assert result == "recovered"
        assert call_count == 3

    def test_retry_exhausted(self):
        from skyyrose.skyyrose_elite_studio import retry_async

        async def always_fail():
            raise ValueError("permanent")

        with pytest.raises(ValueError, match="permanent"):
            asyncio.run(retry_async(always_fail, attempts=2, base_delay=0.01))


# ---------------------------------------------------------------------------
# Test Provider Clients (Lazy Init)
# ---------------------------------------------------------------------------


class TestProviderClients:
    """Test lazy client initialization."""

    def test_clients_instance_exists(self):
        from skyyrose.skyyrose_elite_studio import clients

        assert clients is not None

    def test_clients_lazy_properties(self):
        from skyyrose.skyyrose_elite_studio import ProviderClients

        c = ProviderClients()
        assert c._gemini is None
        assert c._openai is None
        assert c._anthropic is None


# ---------------------------------------------------------------------------
# Test Orchestrator Construction
# ---------------------------------------------------------------------------


class TestOrchestratorConstruction:
    """Test orchestrator builds correctly."""

    def test_orchestrator_init(self):
        from skyyrose.skyyrose_elite_studio import EliteStudioOrchestrator

        orch = EliteStudioOrchestrator()
        assert orch.vision is not None
        assert orch.generation is not None
        assert orch.quality is not None

    def test_vision_pipeline_init(self):
        from skyyrose.skyyrose_elite_studio import VisionPipeline

        vp = VisionPipeline()
        assert vp is not None

    def test_generation_pipeline_init(self):
        from skyyrose.skyyrose_elite_studio import GenerationPipeline

        gp = GenerationPipeline()
        assert gp is not None

    def test_quality_pipeline_init(self):
        from skyyrose.skyyrose_elite_studio import QualityPipeline

        qp = QualityPipeline()
        assert qp is not None


# ---------------------------------------------------------------------------
# Test ADK Tool Wrappers
# ---------------------------------------------------------------------------


class TestADKToolWrappers:
    """Test the synchronous tool wrappers return proper format."""

    def test_tool_list_products(self):
        from skyyrose.skyyrose_elite_studio import tool_list_products

        result = tool_list_products()
        assert result["success"] is True
        assert "count" in result
        assert "skus" in result
        assert isinstance(result["skus"], list)

    def test_tool_list_products_with_filter(self):
        from skyyrose.skyyrose_elite_studio import tool_list_products

        result = tool_list_products(collection="nonexistent")
        assert result["success"] is True
        assert result["count"] == 0


# ---------------------------------------------------------------------------
# Test Constants
# ---------------------------------------------------------------------------


class TestConstants:
    """Verify configuration constants."""

    def test_version(self):
        from skyyrose.skyyrose_elite_studio import VERSION

        assert VERSION == "2.0.0"

    def test_max_regen_attempts(self):
        from skyyrose.skyyrose_elite_studio import MAX_REGEN_ATTEMPTS

        assert MAX_REGEN_ATTEMPTS == 3

    def test_batch_delay(self):
        from skyyrose.skyyrose_elite_studio import BATCH_DELAY_SECONDS

        assert BATCH_DELAY_SECONDS == 8

    def test_retry_attempts(self):
        from skyyrose.skyyrose_elite_studio import RETRY_ATTEMPTS

        assert RETRY_ATTEMPTS == 3

    def test_max_image_size(self):
        from skyyrose.skyyrose_elite_studio import MAX_IMAGE_SIZE_PX

        assert MAX_IMAGE_SIZE_PX == 1568
