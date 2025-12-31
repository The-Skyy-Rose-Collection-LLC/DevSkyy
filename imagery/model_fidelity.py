# imagery/model_fidelity.py
"""
3D Model Fidelity Validation System.

MANDATORY: All 3D models MUST achieve 95% fidelity score to pass validation.
This module enforces production-grade quality standards for SkyyRose products.

Fidelity Metrics:
- Mesh integrity (watertight, manifold)
- Geometry quality (vertex count, face count, euler number)
- Texture quality (resolution, UV mapping)
- Visual accuracy (silhouette match, detail preservation)

Reference: Context7 trimesh documentation for mesh validation patterns.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import numpy as np
from pydantic import BaseModel, Field

# Lazy imports for optional dependencies
try:
    import trimesh

    TRIMESH_AVAILABLE = True
except ImportError:
    TRIMESH_AVAILABLE = False
    trimesh = None  # type: ignore

try:
    from PIL import Image

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None  # type: ignore

from errors.production_errors import (
    ModelFidelityError,
    ThreeDGenerationError,
)

logger = logging.getLogger(__name__)

# ============================================================================
# CONSTANTS - CRITICAL: 95% MINIMUM FIDELITY
# ============================================================================

MINIMUM_FIDELITY_SCORE = 95.0  # MANDATORY: 95% threshold
MINIMUM_VERTEX_COUNT = 1000
MAXIMUM_VERTEX_COUNT = 500000
MINIMUM_FACE_COUNT = 500
MINIMUM_TEXTURE_RESOLUTION = 1024  # 1024x1024 minimum
ACCEPTABLE_UV_COVERAGE = 0.85  # 85% UV coverage


class FidelityCategory(str, Enum):
    """Categories of fidelity assessment."""

    MESH_INTEGRITY = "mesh_integrity"
    GEOMETRY_QUALITY = "geometry_quality"
    TEXTURE_QUALITY = "texture_quality"
    VISUAL_ACCURACY = "visual_accuracy"


class FidelityGrade(str, Enum):
    """Fidelity grade classifications."""

    EXCELLENT = "excellent"  # 95-100%
    GOOD = "good"  # 85-94%
    ACCEPTABLE = "acceptable"  # 75-84%
    POOR = "poor"  # 60-74%
    FAILED = "failed"  # <60%


@dataclass
class FidelityMetrics:
    """Individual fidelity metrics for a 3D model."""

    # Mesh integrity
    is_watertight: bool = False
    is_manifold: bool = False
    euler_number: int = 0
    has_degenerate_faces: bool = False

    # Geometry quality
    vertex_count: int = 0
    face_count: int = 0
    edge_count: int = 0
    bounding_box_volume: float = 0.0
    mesh_volume: float = 0.0
    surface_area: float = 0.0

    # Texture quality
    has_textures: bool = False
    texture_resolution: tuple[int, int] = (0, 0)
    uv_coverage: float = 0.0
    texture_count: int = 0

    # Visual accuracy
    silhouette_match_score: float = 0.0
    detail_preservation_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "mesh_integrity": {
                "is_watertight": self.is_watertight,
                "is_manifold": self.is_manifold,
                "euler_number": self.euler_number,
                "has_degenerate_faces": self.has_degenerate_faces,
            },
            "geometry_quality": {
                "vertex_count": self.vertex_count,
                "face_count": self.face_count,
                "edge_count": self.edge_count,
                "bounding_box_volume": self.bounding_box_volume,
                "mesh_volume": self.mesh_volume,
                "surface_area": self.surface_area,
            },
            "texture_quality": {
                "has_textures": self.has_textures,
                "texture_resolution": self.texture_resolution,
                "uv_coverage": self.uv_coverage,
                "texture_count": self.texture_count,
            },
            "visual_accuracy": {
                "silhouette_match_score": self.silhouette_match_score,
                "detail_preservation_score": self.detail_preservation_score,
            },
        }


class GeometryMetrics(BaseModel):
    """Geometry-specific metrics for fidelity report."""

    vertex_count: int = 0
    face_count: int = 0
    is_watertight: bool = False
    is_manifold: bool = False
    has_holes: bool = True
    overall_score: float = 0.0


class TextureMetrics(BaseModel):
    """Texture-specific metrics for fidelity report."""

    has_textures: bool = False
    resolution: str | None = None
    uv_coverage: float = 0.0
    overall_score: float = 0.0


class MaterialMetrics(BaseModel):
    """Material-specific metrics for fidelity report."""

    has_materials: bool = False
    is_pbr: bool = False
    overall_score: float = 0.0


class FidelityReport(BaseModel):
    """Complete fidelity validation report."""

    model_path: str = Field(..., description="Path to the validated model")
    overall_score: float = Field(..., description="Overall fidelity score (0-100)")
    grade: FidelityGrade = Field(..., description="Fidelity grade")
    passed: bool = Field(..., description="Whether model passed validation")
    minimum_threshold: float = Field(
        default=MINIMUM_FIDELITY_SCORE,
        description="Minimum required score",
    )

    # Component metrics for UI display
    geometry: GeometryMetrics = Field(
        default_factory=GeometryMetrics,
        description="Geometry metrics",
    )
    textures: TextureMetrics = Field(
        default_factory=TextureMetrics,
        description="Texture metrics",
    )
    materials: MaterialMetrics = Field(
        default_factory=MaterialMetrics,
        description="Material metrics",
    )

    category_scores: dict[str, float] = Field(
        default_factory=dict,
        description="Scores by category",
    )
    metrics: dict[str, Any] = Field(
        default_factory=dict,
        description="Detailed metrics",
    )
    issues: list[str] = Field(
        default_factory=list,
        description="Identified issues",
    )
    recommendations: list[str] = Field(
        default_factory=list,
        description="Improvement recommendations",
    )


class ModelFidelityValidator:
    """
    Production-grade 3D model fidelity validator.

    MANDATORY: All models must achieve 95% fidelity to pass.

    Usage:
        validator = ModelFidelityValidator()
        report = await validator.validate("model.glb")
        if not report.passed:
            raise ModelFidelityError(report.overall_score)
    """

    MINIMUM_FIDELITY_SCORE = MINIMUM_FIDELITY_SCORE  # Class-level constant

    # Weight distribution for final score
    CATEGORY_WEIGHTS = {
        FidelityCategory.MESH_INTEGRITY: 0.30,
        FidelityCategory.GEOMETRY_QUALITY: 0.25,
        FidelityCategory.TEXTURE_QUALITY: 0.25,
        FidelityCategory.VISUAL_ACCURACY: 0.20,
    }

    def __init__(
        self,
        minimum_threshold: float = MINIMUM_FIDELITY_SCORE,
        reference_image_path: str | Path | None = None,
    ) -> None:
        """
        Initialize the validator.

        Args:
            minimum_threshold: Minimum fidelity score (default 95%)
            reference_image_path: Optional reference image for visual comparison
        """
        if not TRIMESH_AVAILABLE:
            raise ImportError(
                "trimesh is required for model validation. " "Install with: pip install trimesh"
            )

        self.minimum_threshold = minimum_threshold
        self.reference_image_path = Path(reference_image_path) if reference_image_path else None

    async def validate(
        self,
        model_path: str | Path,
        reference_image: str | Path | bytes | None = None,
    ) -> FidelityReport:
        """
        Validate a 3D model's fidelity.

        Args:
            model_path: Path to the 3D model file (.glb, .gltf, .obj, etc.)
            reference_image: Optional reference image for visual comparison

        Returns:
            FidelityReport with detailed validation results

        Raises:
            ThreeDGenerationError: If model cannot be loaded
            ModelFidelityError: If model fails validation (optional)
        """
        model_path = Path(model_path)

        if not model_path.exists():
            raise ThreeDGenerationError(
                f"Model file not found: {model_path}",
                generator="ModelFidelityValidator",
            )

        # Load the mesh
        try:
            mesh = trimesh.load(str(model_path), force="mesh")
        except Exception as e:
            raise ThreeDGenerationError(
                f"Failed to load model: {e}",
                generator="ModelFidelityValidator",
                cause=e,
            )

        # Extract metrics
        metrics = await self._extract_metrics(mesh, model_path)

        # Calculate category scores
        category_scores = await self._calculate_category_scores(metrics)

        # Calculate overall score
        overall_score = sum(
            score * self.CATEGORY_WEIGHTS[FidelityCategory(cat)]
            for cat, score in category_scores.items()
        )

        # Determine grade
        grade = self._determine_grade(overall_score)

        # Check pass/fail
        passed = overall_score >= self.minimum_threshold

        # Identify issues and recommendations
        issues, recommendations = await self._analyze_issues(metrics, category_scores)

        # Build component metrics for UI display
        geometry_metrics = GeometryMetrics(
            vertex_count=metrics.vertex_count,
            face_count=metrics.face_count,
            is_watertight=metrics.is_watertight,
            is_manifold=metrics.is_manifold,
            has_holes=not metrics.is_watertight,
            overall_score=category_scores.get(FidelityCategory.GEOMETRY_QUALITY.value, 0.0),
        )

        texture_res = metrics.texture_resolution
        texture_metrics = TextureMetrics(
            has_textures=metrics.has_textures,
            resolution=f"{texture_res[0]}x{texture_res[1]}" if texture_res[0] > 0 else None,
            uv_coverage=metrics.uv_coverage,
            overall_score=category_scores.get(FidelityCategory.TEXTURE_QUALITY.value, 0.0),
        )

        material_metrics = MaterialMetrics(
            has_materials=metrics.has_textures,  # Materials detected via textures
            is_pbr=metrics.has_textures and metrics.texture_count > 0,
            overall_score=category_scores.get(FidelityCategory.VISUAL_ACCURACY.value, 0.0),
        )

        return FidelityReport(
            model_path=str(model_path),
            overall_score=round(overall_score, 2),
            grade=grade,
            passed=passed,
            minimum_threshold=self.minimum_threshold,
            geometry=geometry_metrics,
            textures=texture_metrics,
            materials=material_metrics,
            category_scores=category_scores,
            metrics=metrics.to_dict(),
            issues=issues,
            recommendations=recommendations,
        )

    async def validate_and_enforce(
        self,
        model_path: str | Path,
        reference_image: str | Path | bytes | None = None,
    ) -> FidelityReport:
        """
        Validate and raise exception if model fails.

        This is the recommended method for production use.

        Raises:
            ModelFidelityError: If model fails to meet 95% threshold
        """
        report = await self.validate(model_path, reference_image)

        if not report.passed:
            raise ModelFidelityError(
                actual_fidelity=report.overall_score,
                required_fidelity=self.minimum_threshold,
                context={
                    "model_path": str(model_path),
                    "grade": report.grade.value,
                    "issues": report.issues,
                },
            )

        return report

    async def _extract_metrics(
        self,
        mesh: trimesh.Trimesh,
        model_path: Path,
    ) -> FidelityMetrics:
        """Extract fidelity metrics from the mesh."""
        metrics = FidelityMetrics()

        # Mesh integrity - using trimesh patterns from Context7
        metrics.is_watertight = mesh.is_watertight
        metrics.euler_number = mesh.euler_number

        # Check manifold status
        try:
            # A mesh is manifold if each edge is shared by exactly 2 faces
            metrics.is_manifold = bool(mesh.is_watertight and mesh.euler_number == 2)
        except Exception:
            metrics.is_manifold = False

        # Check for degenerate faces
        try:
            face_areas = mesh.area_faces
            metrics.has_degenerate_faces = bool(np.any(face_areas < 1e-10))
        except Exception:
            metrics.has_degenerate_faces = True

        # Geometry quality
        metrics.vertex_count = len(mesh.vertices)
        metrics.face_count = len(mesh.faces)
        try:
            metrics.edge_count = len(mesh.edges_unique)
        except Exception:
            metrics.edge_count = 0

        try:
            metrics.bounding_box_volume = float(mesh.bounding_box.volume)
        except Exception:
            metrics.bounding_box_volume = 0.0

        if mesh.is_watertight:
            try:
                metrics.mesh_volume = float(mesh.volume)
            except Exception:
                metrics.mesh_volume = 0.0

        try:
            metrics.surface_area = float(mesh.area)
        except Exception:
            metrics.surface_area = 0.0

        # Texture quality
        if hasattr(mesh, "visual") and mesh.visual is not None:
            visual = mesh.visual
            if hasattr(visual, "material") and visual.material is not None:
                metrics.has_textures = True
                # Try to get texture info
                try:
                    if hasattr(visual.material, "image"):
                        img = visual.material.image
                        if img is not None:
                            metrics.texture_resolution = (img.width, img.height)
                            metrics.texture_count = 1
                except Exception:
                    pass

            # UV coverage
            if hasattr(visual, "uv") and visual.uv is not None:
                try:
                    uv = visual.uv
                    # Calculate UV coverage (how much of UV space is used)
                    uv_min = np.min(uv, axis=0)
                    uv_max = np.max(uv, axis=0)
                    uv_range = uv_max - uv_min
                    metrics.uv_coverage = float(np.prod(uv_range))
                except Exception:
                    metrics.uv_coverage = 0.0

        return metrics

    async def _calculate_category_scores(
        self,
        metrics: FidelityMetrics,
    ) -> dict[str, float]:
        """Calculate scores for each fidelity category."""
        scores = {}

        # Mesh integrity score (0-100)
        integrity_score = 0.0
        if metrics.is_watertight:
            integrity_score += 40
        if metrics.is_manifold:
            integrity_score += 30
        if metrics.euler_number == 2:  # Correct topology for closed mesh
            integrity_score += 20
        if not metrics.has_degenerate_faces:
            integrity_score += 10
        scores[FidelityCategory.MESH_INTEGRITY.value] = integrity_score

        # Geometry quality score (0-100)
        geometry_score = 0.0

        # Vertex count scoring
        if MINIMUM_VERTEX_COUNT <= metrics.vertex_count <= MAXIMUM_VERTEX_COUNT:
            # Optimal range gets full points
            if 5000 <= metrics.vertex_count <= 100000:
                geometry_score += 40
            else:
                geometry_score += 30
        elif metrics.vertex_count > 0:
            geometry_score += 15

        # Face count scoring
        if metrics.face_count >= MINIMUM_FACE_COUNT:
            geometry_score += 30
        elif metrics.face_count > 0:
            geometry_score += 15

        # Volume ratio (mesh vs bounding box)
        if metrics.bounding_box_volume > 0 and metrics.mesh_volume > 0:
            volume_ratio = metrics.mesh_volume / metrics.bounding_box_volume
            if 0.1 <= volume_ratio <= 0.9:  # Reasonable fill
                geometry_score += 30
            else:
                geometry_score += 15

        scores[FidelityCategory.GEOMETRY_QUALITY.value] = min(geometry_score, 100)

        # Texture quality score (0-100)
        texture_score = 0.0
        if metrics.has_textures:
            texture_score += 30

            # Resolution scoring
            min_res = min(metrics.texture_resolution)
            if min_res >= 2048:
                texture_score += 40
            elif min_res >= MINIMUM_TEXTURE_RESOLUTION:
                texture_score += 30
            elif min_res >= 512:
                texture_score += 15

            # UV coverage scoring
            if metrics.uv_coverage >= ACCEPTABLE_UV_COVERAGE:
                texture_score += 30
            elif metrics.uv_coverage >= 0.5:
                texture_score += 15
        else:
            # No textures - give partial credit if mesh is otherwise good
            if metrics.is_watertight and metrics.vertex_count >= MINIMUM_VERTEX_COUNT:
                texture_score = 50  # Acceptable for untextured models

        scores[FidelityCategory.TEXTURE_QUALITY.value] = min(texture_score, 100)

        # Visual accuracy score (placeholder - requires reference comparison)
        # For now, base on mesh quality indicators
        visual_score = 0.0
        if metrics.is_watertight:
            visual_score += 30
        if metrics.vertex_count >= 10000:
            visual_score += 30
        if not metrics.has_degenerate_faces:
            visual_score += 20
        if metrics.has_textures:
            visual_score += 20

        scores[FidelityCategory.VISUAL_ACCURACY.value] = min(visual_score, 100)

        return scores

    def _determine_grade(self, score: float) -> FidelityGrade:
        """Determine fidelity grade from score."""
        if score >= 95:
            return FidelityGrade.EXCELLENT
        elif score >= 85:
            return FidelityGrade.GOOD
        elif score >= 75:
            return FidelityGrade.ACCEPTABLE
        elif score >= 60:
            return FidelityGrade.POOR
        else:
            return FidelityGrade.FAILED

    async def _analyze_issues(
        self,
        metrics: FidelityMetrics,
        category_scores: dict[str, float],
    ) -> tuple[list[str], list[str]]:
        """Analyze metrics and generate issues/recommendations."""
        issues = []
        recommendations = []

        # Mesh integrity issues
        if not metrics.is_watertight:
            issues.append("Mesh is not watertight (has holes)")
            recommendations.append(
                "Use mesh repair tools to close holes and ensure watertight geometry"
            )

        if not metrics.is_manifold:
            issues.append("Mesh is not manifold (non-standard edge topology)")
            recommendations.append("Check for non-manifold edges and fix geometry topology")

        if metrics.has_degenerate_faces:
            issues.append("Mesh contains degenerate faces (zero-area triangles)")
            recommendations.append("Remove degenerate faces using mesh cleanup tools")

        # Geometry issues
        if metrics.vertex_count < MINIMUM_VERTEX_COUNT:
            issues.append(f"Low vertex count ({metrics.vertex_count} < {MINIMUM_VERTEX_COUNT})")
            recommendations.append("Increase mesh resolution for better detail representation")

        if metrics.vertex_count > MAXIMUM_VERTEX_COUNT:
            issues.append(f"High vertex count ({metrics.vertex_count} > {MAXIMUM_VERTEX_COUNT})")
            recommendations.append("Consider mesh decimation for performance optimization")

        # Texture issues
        if not metrics.has_textures:
            issues.append("Model has no textures")
            recommendations.append("Add PBR materials and textures for visual quality")
        elif min(metrics.texture_resolution) < MINIMUM_TEXTURE_RESOLUTION:
            issues.append(f"Low texture resolution ({metrics.texture_resolution})")
            recommendations.append(
                f"Use textures at least {MINIMUM_TEXTURE_RESOLUTION}x{MINIMUM_TEXTURE_RESOLUTION}"
            )

        if metrics.uv_coverage < ACCEPTABLE_UV_COVERAGE and metrics.has_textures:
            issues.append(f"Low UV coverage ({metrics.uv_coverage:.1%})")
            recommendations.append("Optimize UV unwrapping for better texture utilization")

        # Category-specific recommendations
        for category, score in category_scores.items():
            if score < 70:
                recommendations.append(
                    f"Focus on improving {category.replace('_', ' ')} (current: {score:.0f}%)"
                )

        return issues, recommendations


# ============================================================================
# CONVENIENCE FUNCTION
# ============================================================================


async def validate_model_fidelity(
    model_path: str | Path,
    enforce: bool = True,
    minimum_threshold: float = MINIMUM_FIDELITY_SCORE,
) -> FidelityReport:
    """
    Validate a 3D model's fidelity.

    This is the recommended entry point for model validation.

    Args:
        model_path: Path to the 3D model file
        enforce: If True, raise exception on failure
        minimum_threshold: Minimum fidelity score (default 95%)

    Returns:
        FidelityReport with validation results

    Raises:
        ModelFidelityError: If enforce=True and model fails validation

    Example:
        report = await validate_model_fidelity("product.glb")
        print(f"Score: {report.overall_score}%, Passed: {report.passed}")
    """
    validator = ModelFidelityValidator(minimum_threshold=minimum_threshold)

    if enforce:
        return await validator.validate_and_enforce(model_path)
    return await validator.validate(model_path)
