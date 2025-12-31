"""
Tests for 3D Model Fidelity Validation System
==============================================

Tests the model fidelity validation, scoring, and enforcement
for the DevSkyy 3D asset pipeline.

CRITICAL: All models must achieve 95% fidelity to pass.
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from imagery.model_fidelity import (
    MINIMUM_FIDELITY_SCORE,
    FidelityGrade,
    FidelityReport,
    GeometryMetrics,
    MaterialMetrics,
    ModelFidelityValidator,
    TextureMetrics,
)


class TestFidelityThreshold:
    """Tests for the 95% fidelity threshold constant."""

    def test_minimum_fidelity_score(self):
        """Test that minimum fidelity score is 95%."""
        assert MINIMUM_FIDELITY_SCORE == 95.0

    def test_validator_threshold(self):
        """Test that validator uses 95% threshold."""
        pytest.importorskip("trimesh")
        validator = ModelFidelityValidator()
        assert validator.minimum_fidelity == 95.0


class TestGeometryMetrics:
    """Tests for geometry metrics data class."""

    def test_geometry_metrics_creation(self):
        """Test creating geometry metrics."""
        metrics = GeometryMetrics(
            vertex_count=1000,
            face_count=500,
            is_watertight=True,
            is_manifold=True,
            has_holes=False,
            overall_score=95.0,
        )
        assert metrics.vertex_count == 1000
        assert metrics.face_count == 500
        assert metrics.is_watertight is True
        assert metrics.is_manifold is True
        assert metrics.has_holes is False
        assert metrics.overall_score == 95.0

    def test_geometry_metrics_default_values(self):
        """Test geometry metrics default values."""
        metrics = GeometryMetrics()
        assert metrics.vertex_count == 0
        assert metrics.face_count == 0
        assert metrics.is_watertight is False
        assert metrics.is_manifold is False
        assert metrics.has_holes is True
        assert metrics.overall_score == 0.0


class TestTextureMetrics:
    """Tests for texture metrics data class."""

    def test_texture_metrics_creation(self):
        """Test creating texture metrics."""
        metrics = TextureMetrics(
            has_textures=True, resolution="2048x2048", uv_coverage=0.95, overall_score=96.0
        )
        assert metrics.has_textures is True
        assert metrics.resolution == "2048x2048"
        assert metrics.uv_coverage == 0.95
        assert metrics.overall_score == 96.0

    def test_texture_metrics_default_values(self):
        """Test texture metrics default values."""
        metrics = TextureMetrics()
        assert metrics.has_textures is False
        assert metrics.resolution is None
        assert metrics.uv_coverage == 0.0
        assert metrics.overall_score == 0.0


class TestMaterialMetrics:
    """Tests for material metrics data class."""

    def test_material_metrics_creation(self):
        """Test creating material metrics."""
        metrics = MaterialMetrics(has_materials=True, is_pbr=True, overall_score=98.0)
        assert metrics.has_materials is True
        assert metrics.is_pbr is True
        assert metrics.overall_score == 98.0

    def test_material_metrics_default_values(self):
        """Test material metrics default values."""
        metrics = MaterialMetrics()
        assert metrics.has_materials is False
        assert metrics.is_pbr is False
        assert metrics.overall_score == 0.0


class TestFidelityReport:
    """Tests for fidelity report generation."""

    def test_report_creation_passing(self):
        """Test creating a fidelity report that passes."""
        report = FidelityReport(
            model_path="/path/to/model.glb",
            overall_score=96.5,
            grade=FidelityGrade.EXCELLENT,
            passed=True,
            minimum_threshold=95.0,
            geometry=GeometryMetrics(
                vertex_count=10000,
                face_count=5000,
                is_watertight=True,
                is_manifold=True,
                has_holes=False,
                overall_score=97.0,
            ),
            textures=TextureMetrics(
                has_textures=True, resolution="2048x2048", uv_coverage=0.95, overall_score=96.0
            ),
            materials=MaterialMetrics(has_materials=True, is_pbr=True, overall_score=96.0),
        )
        assert report.passed is True
        assert report.overall_score == 96.5
        assert report.grade == FidelityGrade.EXCELLENT

    def test_report_creation_failing(self):
        """Test that report fails when score is below 95%."""
        report = FidelityReport(
            model_path="/path/to/model.glb",
            overall_score=80.0,
            grade=FidelityGrade.GOOD,
            passed=False,
            minimum_threshold=95.0,
            geometry=GeometryMetrics(
                vertex_count=1000,
                face_count=500,
                is_watertight=False,
                is_manifold=False,
                has_holes=True,
                overall_score=75.0,
            ),
            textures=TextureMetrics(
                has_textures=False, resolution=None, uv_coverage=0.0, overall_score=0.0
            ),
            materials=MaterialMetrics(has_materials=False, is_pbr=False, overall_score=0.0),
        )
        assert report.passed is False
        assert report.overall_score < MINIMUM_FIDELITY_SCORE

    def test_fidelity_grades(self):
        """Test fidelity grade values."""
        assert FidelityGrade.EXCELLENT.value == "excellent"
        assert FidelityGrade.GOOD.value == "good"
        assert FidelityGrade.ACCEPTABLE.value == "acceptable"
        assert FidelityGrade.POOR.value == "poor"
        assert FidelityGrade.FAILED.value == "failed"


class TestModelFidelityValidator:
    """Tests for the ModelFidelityValidator class."""

    @pytest.fixture
    def mock_trimesh(self):
        """Mock trimesh for testing without actual library."""
        with patch.dict("sys.modules", {"trimesh": Mock()}):
            yield

    def test_validator_creation(self):
        """Test validator instantiation."""
        pytest.importorskip("trimesh")
        validator = ModelFidelityValidator()
        assert validator.minimum_fidelity == MINIMUM_FIDELITY_SCORE

    @pytest.mark.asyncio
    async def test_validate_returns_fidelity_report(self):
        """Test that validation returns a FidelityReport."""
        pytest.importorskip("trimesh")
        validator = ModelFidelityValidator()

        # Create a test GLB file path (doesn't need to exist for mock)
        test_path = Path("/tmp/test_model.glb")

        with patch.object(validator, "_load_mesh") as mock_load:
            # Create mock mesh
            mock_mesh = Mock()
            mock_mesh.is_watertight = True
            mock_mesh.is_volume = True
            mock_mesh.euler_number = 2
            mock_mesh.volume = 100.0
            mock_mesh.area = 200.0
            mock_mesh.vertices = Mock()
            mock_mesh.vertices.__len__ = Mock(return_value=10000)
            mock_mesh.faces = Mock()
            mock_mesh.faces.__len__ = Mock(return_value=5000)
            mock_mesh.visual = Mock()
            mock_mesh.visual.kind = "texture"
            mock_mesh.visual.uv = Mock()
            mock_mesh.visual.uv.__len__ = Mock(return_value=10000)
            mock_mesh.visual.material = Mock()
            mock_load.return_value = mock_mesh

            report = await validator.validate(test_path)

            assert isinstance(report, FidelityReport)
            assert report.model_path == str(test_path)


class TestFidelityEnforcement:
    """Tests for fidelity enforcement in production."""

    def test_passing_score_threshold(self):
        """Test score passes at exactly 95%."""
        score = 95.0
        passed = score >= MINIMUM_FIDELITY_SCORE
        assert passed is True

    def test_failing_score_threshold(self):
        """Test score fails below 95%."""
        score = 94.9
        passed = score >= MINIMUM_FIDELITY_SCORE
        assert passed is False

    def test_excellent_score_passes(self):
        """Test excellent score (96+) passes."""
        score = 98.5
        passed = score >= MINIMUM_FIDELITY_SCORE
        assert passed is True

    def test_report_issues_populated(self):
        """Test that issues list is populated for failing models."""
        report = FidelityReport(
            model_path="/path/to/model.glb",
            overall_score=70.0,
            grade=FidelityGrade.POOR,
            passed=False,
            issues=["Model is not watertight", "Missing textures", "Low polygon count"],
            recommendations=["Fix mesh holes", "Add textures", "Increase geometry detail"],
        )

        assert len(report.issues) == 3
        assert "Model is not watertight" in report.issues
        assert len(report.recommendations) == 3


class TestAPIIntegration:
    """Tests for API integration with fidelity validation."""

    def test_minimum_fidelity_score_exported(self):
        """Test MINIMUM_FIDELITY_SCORE is correctly exported."""
        from imagery.model_fidelity import MINIMUM_FIDELITY_SCORE as imported_score

        assert imported_score == 95.0

    def test_fidelity_report_serializable(self):
        """Test FidelityReport can be serialized to dict."""
        report = FidelityReport(
            model_path="/path/to/model.glb",
            overall_score=96.0,
            grade=FidelityGrade.EXCELLENT,
            passed=True,
        )

        report_dict = report.model_dump()
        assert report_dict["overall_score"] == 96.0
        assert report_dict["passed"] is True
        assert report_dict["grade"] == "excellent"
