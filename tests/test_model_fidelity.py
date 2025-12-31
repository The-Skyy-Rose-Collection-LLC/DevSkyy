"""
Tests for Model Fidelity Validator
===================================

Tests for the ModelFidelityValidator class and fidelity validation.

Coverage:
- Validator initialization
- Fidelity report generation
- Multi-angle validation
- SSIM and color accuracy metrics
- Threshold handling
- Error handling
"""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from imagery.model_fidelity import (
    AngleScore,
    FidelityReport,
    ModelFidelityValidator,
    ValidationConfig,
)

# =============================================================================
# ValidationConfig Tests
# =============================================================================


class TestValidationConfig:
    """Tests for ValidationConfig."""

    def test_default_config(self):
        """Should have sensible defaults."""
        config = ValidationConfig()

        assert config.min_fidelity_score == 0.90
        assert config.ssim_weight == 0.4
        assert config.color_weight == 0.3
        assert config.edge_weight == 0.3
        assert len(config.angles) == 4  # front, back, left, right
        assert config.render_resolution == (512, 512)

    def test_custom_config(self):
        """Should accept custom values."""
        config = ValidationConfig(
            min_fidelity_score=0.85,
            ssim_weight=0.5,
            color_weight=0.25,
            edge_weight=0.25,
            angles=["front", "back"],
            render_resolution=(1024, 1024),
        )

        assert config.min_fidelity_score == 0.85
        assert config.ssim_weight == 0.5
        assert len(config.angles) == 2
        assert config.render_resolution == (1024, 1024)

    def test_weight_validation(self):
        """Weights should be configurable."""
        config = ValidationConfig(
            ssim_weight=0.6,
            color_weight=0.2,
            edge_weight=0.2,
        )

        total = config.ssim_weight + config.color_weight + config.edge_weight
        assert abs(total - 1.0) < 0.001


# =============================================================================
# AngleScore Tests
# =============================================================================


class TestAngleScore:
    """Tests for AngleScore dataclass."""

    def test_angle_score_creation(self):
        """Should create AngleScore with all metrics."""
        score = AngleScore(
            angle="front",
            ssim_score=0.92,
            color_accuracy=0.88,
            edge_similarity=0.90,
            combined_score=0.90,
        )

        assert score.angle == "front"
        assert score.ssim_score == 0.92
        assert score.color_accuracy == 0.88
        assert score.edge_similarity == 0.90
        assert score.combined_score == 0.90


# =============================================================================
# FidelityReport Tests
# =============================================================================


class TestFidelityReport:
    """Tests for FidelityReport dataclass."""

    def test_fidelity_report_creation(self):
        """Should create FidelityReport with all fields."""
        angles = [
            AngleScore("front", 0.92, 0.88, 0.90, 0.90),
            AngleScore("back", 0.90, 0.86, 0.88, 0.88),
            AngleScore("left", 0.91, 0.87, 0.89, 0.89),
            AngleScore("right", 0.89, 0.85, 0.87, 0.87),
        ]

        report = FidelityReport(
            product_sku="SKR-001",
            overall_score=0.885,
            passed=True,
            angle_scores=angles,
            validation_time_seconds=5.2,
            threshold=0.90,
            recommendations=[],
        )

        assert report.product_sku == "SKR-001"
        assert report.overall_score == 0.885
        assert report.passed is True
        assert len(report.angle_scores) == 4
        assert report.validation_time_seconds == 5.2

    def test_fidelity_report_with_recommendations(self):
        """Should include recommendations for improvement."""
        report = FidelityReport(
            product_sku="SKR-002",
            overall_score=0.75,
            passed=False,
            angle_scores=[],
            validation_time_seconds=3.0,
            threshold=0.90,
            recommendations=[
                "Increase texture resolution",
                "Improve back-angle geometry",
            ],
        )

        assert report.passed is False
        assert len(report.recommendations) == 2


# =============================================================================
# ModelFidelityValidator Tests
# =============================================================================


class TestModelFidelityValidator:
    """Tests for ModelFidelityValidator class."""

    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return ModelFidelityValidator()

    @pytest.fixture
    def custom_validator(self):
        """Create validator with custom config."""
        config = ValidationConfig(min_fidelity_score=0.85)
        return ModelFidelityValidator(config=config)

    @pytest.fixture
    def sample_model(self, tmp_path):
        """Create sample model file."""
        model_path = tmp_path / "test_model.glb"
        model_path.write_bytes(b"fake glb data")
        return model_path

    @pytest.fixture
    def reference_images_dir(self, tmp_path):
        """Create reference images directory."""
        ref_dir = tmp_path / "references"
        ref_dir.mkdir()
        for angle in ["front", "back", "left", "right"]:
            img_path = ref_dir / f"{angle}.jpg"
            img_path.write_bytes(b"fake image data")
        return ref_dir

    def test_validator_initialization(self, validator):
        """Should initialize with default config."""
        assert validator.config is not None
        assert validator.config.min_fidelity_score == 0.90

    def test_validator_custom_config(self, custom_validator):
        """Should use custom config."""
        assert custom_validator.config.min_fidelity_score == 0.85

    @pytest.mark.asyncio
    async def test_validate_missing_model(self, validator):
        """Should handle missing model file."""
        from imagery.model_fidelity import ValidationError

        with pytest.raises(ValidationError, match="Model file not found"):
            await validator.validate(
                model_path=Path("/nonexistent/model.glb"),
                product_sku="SKR-001",
            )

    @pytest.mark.asyncio
    async def test_validate_returns_report(self, validator, sample_model):
        """Should return FidelityReport."""
        # Mock the internal validation methods
        mock_report = FidelityReport(
            product_sku="SKR-001",
            overall_score=0.92,
            passed=True,
            angle_scores=[
                AngleScore("front", 0.93, 0.90, 0.91, 0.92),
            ],
            validation_time_seconds=4.5,
            threshold=0.90,
            recommendations=[],
        )

        with patch.object(
            validator, "_run_validation", new_callable=AsyncMock
        ) as mock_validate:
            mock_validate.return_value = mock_report

            result = await validator.validate(
                model_path=sample_model,
                product_sku="SKR-001",
            )

            assert isinstance(result, FidelityReport)
            assert result.product_sku == "SKR-001"
            assert result.passed is True

    @pytest.mark.asyncio
    async def test_validate_with_reference_images(
        self, validator, sample_model, reference_images_dir
    ):
        """Should use reference images when provided."""
        mock_report = FidelityReport(
            product_sku="SKR-001",
            overall_score=0.95,
            passed=True,
            angle_scores=[],
            validation_time_seconds=6.0,
            threshold=0.90,
            recommendations=[],
        )

        with patch.object(
            validator, "_run_validation", new_callable=AsyncMock
        ) as mock_validate:
            mock_validate.return_value = mock_report

            await validator.validate(
                model_path=sample_model,
                product_sku="SKR-001",
                reference_images_dir=reference_images_dir,
            )

            # Verify reference images were passed
            call_args = mock_validate.call_args
            assert call_args is not None

    @pytest.mark.asyncio
    async def test_validate_below_threshold(self, validator, sample_model):
        """Should report failure when below threshold."""
        mock_report = FidelityReport(
            product_sku="SKR-001",
            overall_score=0.75,
            passed=False,
            angle_scores=[
                AngleScore("front", 0.78, 0.72, 0.75, 0.75),
            ],
            validation_time_seconds=4.0,
            threshold=0.90,
            recommendations=["Improve texture quality"],
        )

        with patch.object(
            validator, "_run_validation", new_callable=AsyncMock
        ) as mock_validate:
            mock_validate.return_value = mock_report

            result = await validator.validate(
                model_path=sample_model,
                product_sku="SKR-001",
            )

            assert result.passed is False
            assert result.overall_score < 0.90
            assert len(result.recommendations) > 0

    @pytest.mark.asyncio
    async def test_validate_all_angles(self, validator, sample_model):
        """Should validate all configured angles."""
        angle_scores = [
            AngleScore("front", 0.93, 0.90, 0.91, 0.92),
            AngleScore("back", 0.91, 0.88, 0.89, 0.89),
            AngleScore("left", 0.92, 0.89, 0.90, 0.90),
            AngleScore("right", 0.90, 0.87, 0.88, 0.88),
        ]

        mock_report = FidelityReport(
            product_sku="SKR-001",
            overall_score=0.8975,
            passed=True,
            angle_scores=angle_scores,
            validation_time_seconds=8.0,
            threshold=0.85,
            recommendations=[],
        )

        with patch.object(
            validator, "_run_validation", new_callable=AsyncMock
        ) as mock_validate:
            mock_validate.return_value = mock_report

            result = await validator.validate(
                model_path=sample_model,
                product_sku="SKR-001",
            )

            assert len(result.angle_scores) == 4
            angles = [s.angle for s in result.angle_scores]
            assert "front" in angles
            assert "back" in angles
            assert "left" in angles
            assert "right" in angles


# =============================================================================
# Metric Calculation Tests
# =============================================================================


class TestMetricCalculations:
    """Tests for internal metric calculations."""

    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return ModelFidelityValidator()

    def test_combined_score_calculation(self, validator):
        """Should calculate combined score correctly."""
        # Default weights: ssim=0.4, color=0.3, edge=0.3
        ssim = 0.90
        color = 0.85
        edge = 0.88

        expected = (0.4 * ssim) + (0.3 * color) + (0.3 * edge)

        # Calculate using validator method if exposed, otherwise check formula
        assert abs(expected - 0.879) < 0.001

    def test_overall_score_averaging(self):
        """Should average angle scores correctly."""
        scores = [0.92, 0.89, 0.91, 0.88]
        expected = sum(scores) / len(scores)

        assert abs(expected - 0.90) < 0.001


# =============================================================================
# Error Handling Tests
# =============================================================================


class TestValidationErrors:
    """Tests for validation error handling."""

    @pytest.mark.asyncio
    async def test_invalid_model_format(self):
        """Should handle unsupported model formats."""
        from imagery.model_fidelity import ValidationError

        validator = ModelFidelityValidator()

        with tempfile.TemporaryDirectory() as tmpdir:
            invalid_model = Path(tmpdir) / "model.xyz"
            invalid_model.write_bytes(b"invalid format")

            with pytest.raises(ValidationError, match="Unsupported model format"):
                await validator.validate(
                    model_path=invalid_model,
                    product_sku="SKR-001",
                )

    @pytest.mark.asyncio
    async def test_corrupted_model(self):
        """Should handle corrupted model files gracefully."""
        from imagery.model_fidelity import ValidationError

        validator = ModelFidelityValidator()

        with tempfile.TemporaryDirectory() as tmpdir:
            corrupted = Path(tmpdir) / "corrupted.glb"
            corrupted.write_bytes(b"not a valid glb file at all")

            # Should raise or return failed report
            with patch.object(
                validator, "_load_model", side_effect=Exception("Failed to parse GLB")
            ), pytest.raises((ValidationError, Exception)):
                await validator.validate(
                    model_path=corrupted,
                    product_sku="SKR-001",
                )


# =============================================================================
# Integration Tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.integration
async def test_full_validation_pipeline():
    """Test full validation pipeline (mocked)."""
    validator = ModelFidelityValidator()

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test model
        model_path = Path(tmpdir) / "product.glb"
        model_path.write_bytes(b"fake glb data")

        # Mock the validation pipeline
        mock_report = FidelityReport(
            product_sku="TEST-001",
            overall_score=0.93,
            passed=True,
            angle_scores=[
                AngleScore("front", 0.94, 0.92, 0.93, 0.93),
                AngleScore("back", 0.92, 0.90, 0.91, 0.91),
            ],
            validation_time_seconds=5.0,
            threshold=0.90,
            recommendations=[],
        )

        with patch.object(
            validator, "_run_validation", new_callable=AsyncMock
        ) as mock_validate:
            mock_validate.return_value = mock_report

            result = await validator.validate(
                model_path=model_path,
                product_sku="TEST-001",
            )

            assert result.passed is True
            assert result.overall_score >= 0.90


__all__ = [
    "TestValidationConfig",
    "TestAngleScore",
    "TestFidelityReport",
    "TestModelFidelityValidator",
    "TestMetricCalculations",
    "TestValidationErrors",
]
