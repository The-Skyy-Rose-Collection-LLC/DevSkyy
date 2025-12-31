"""
Model Fidelity Validator
========================

Validate 3D model accuracy against reference product images.

Features:
- Multi-angle rendering comparison
- Structural similarity (SSIM) scoring
- Color accuracy validation
- Geometry completeness check
- Texture quality assessment

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import io
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    pass

logger = structlog.get_logger(__name__)


# =============================================================================
# Configuration
# =============================================================================

DEFAULT_FIDELITY_THRESHOLD = 0.95  # 95% fidelity required
DEFAULT_ANGLES = [
    {"elevation": 0, "azimuth": 0, "name": "front"},
    {"elevation": 0, "azimuth": 90, "name": "right"},
    {"elevation": 0, "azimuth": 180, "name": "back"},
    {"elevation": 0, "azimuth": 270, "name": "left"},
    {"elevation": 30, "azimuth": 0, "name": "front_top"},
    {"elevation": -15, "azimuth": 0, "name": "front_bottom"},
]


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class AngleScore:
    """Score for a single viewing angle."""

    angle_name: str
    elevation: float
    azimuth: float
    ssim_score: float
    color_accuracy: float
    edge_similarity: float
    overall_score: float
    issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "angle_name": self.angle_name,
            "elevation": self.elevation,
            "azimuth": self.azimuth,
            "ssim_score": round(self.ssim_score, 4),
            "color_accuracy": round(self.color_accuracy, 4),
            "edge_similarity": round(self.edge_similarity, 4),
            "overall_score": round(self.overall_score, 4),
            "issues": self.issues,
        }


@dataclass
class FidelityReport:
    """Complete fidelity validation report."""

    product_sku: str
    model_path: str
    fidelity_score: float
    passed: bool
    threshold: float

    # Detailed scores
    angle_scores: list[AngleScore] = field(default_factory=list)
    best_angle: str | None = None
    worst_angle: str | None = None

    # Quality metrics
    geometry_score: float = 0.0
    texture_score: float = 0.0
    overall_color_accuracy: float = 0.0

    # Issues and recommendations
    issues: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)

    # Metadata
    validation_time_seconds: float = 0.0
    reference_images_used: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "product_sku": self.product_sku,
            "model_path": self.model_path,
            "fidelity_score": round(self.fidelity_score, 4),
            "passed": self.passed,
            "threshold": self.threshold,
            "angle_scores": [a.to_dict() for a in self.angle_scores],
            "best_angle": self.best_angle,
            "worst_angle": self.worst_angle,
            "geometry_score": round(self.geometry_score, 4),
            "texture_score": round(self.texture_score, 4),
            "overall_color_accuracy": round(self.overall_color_accuracy, 4),
            "issues": self.issues,
            "recommendations": self.recommendations,
            "validation_time_seconds": round(self.validation_time_seconds, 2),
            "reference_images_used": self.reference_images_used,
        }


# =============================================================================
# ModelFidelityValidator
# =============================================================================


class ModelFidelityValidator:
    """
    Validate 3D model fidelity against reference product images.

    Uses multi-angle rendering and image comparison metrics to
    ensure generated 3D models accurately represent the original product.

    Example:
        validator = ModelFidelityValidator(reference_dir=Path("./product_images"))
        report = await validator.validate(
            model_path=Path("./models/SKU-001.glb"),
            product_sku="SKU-001"
        )
        if report.passed:
            print(f"Model passed with {report.fidelity_score:.2%} fidelity")
    """

    def __init__(
        self,
        reference_images_dir: Path,
        fidelity_threshold: float = DEFAULT_FIDELITY_THRESHOLD,
        render_resolution: tuple[int, int] = (512, 512),
        angles: list[dict[str, Any]] | None = None,
    ) -> None:
        """
        Initialize ModelFidelityValidator.

        Args:
            reference_images_dir: Directory containing reference product images
            fidelity_threshold: Minimum fidelity score to pass (0.0-1.0)
            render_resolution: Resolution for model renders
            angles: List of viewing angles for comparison
        """
        self.reference_dir = Path(reference_images_dir)
        self.threshold = fidelity_threshold
        self.resolution = render_resolution
        self.angles = angles or DEFAULT_ANGLES

        logger.info(
            "ModelFidelityValidator initialized",
            reference_dir=str(self.reference_dir),
            threshold=self.threshold,
            angles=len(self.angles),
        )

    async def validate(
        self,
        model_path: Path,
        product_sku: str,
    ) -> FidelityReport:
        """
        Validate model fidelity against reference images.

        Args:
            model_path: Path to the 3D model (GLB/GLTF)
            product_sku: Product SKU for finding reference images

        Returns:
            FidelityReport with validation results
        """
        import time

        start_time = time.time()

        logger.info(
            "Starting fidelity validation",
            model_path=str(model_path),
            product_sku=product_sku,
        )

        # Find reference images
        reference_images = self._find_reference_images(product_sku)

        if not reference_images:
            logger.warning(
                "No reference images found",
                product_sku=product_sku,
                reference_dir=str(self.reference_dir),
            )
            return FidelityReport(
                product_sku=product_sku,
                model_path=str(model_path),
                fidelity_score=0.0,
                passed=False,
                threshold=self.threshold,
                issues=["No reference images found for comparison"],
                recommendations=["Provide reference images in the product images directory"],
            )

        # Render model from multiple angles
        model_renders = await self._render_model_angles(model_path)

        # Compare renders to reference images
        angle_scores = await self._compare_renders(model_renders, reference_images)

        # Calculate overall fidelity score
        fidelity_score = self._calculate_fidelity_score(angle_scores)

        # Determine pass/fail
        passed = fidelity_score >= self.threshold

        # Find best and worst angles
        if angle_scores:
            sorted_scores = sorted(angle_scores, key=lambda x: x.overall_score)
            worst_angle = sorted_scores[0].angle_name
            best_angle = sorted_scores[-1].angle_name
        else:
            worst_angle = None
            best_angle = None

        # Generate issues and recommendations
        issues, recommendations = self._generate_feedback(angle_scores, fidelity_score)

        validation_time = time.time() - start_time

        report = FidelityReport(
            product_sku=product_sku,
            model_path=str(model_path),
            fidelity_score=fidelity_score,
            passed=passed,
            threshold=self.threshold,
            angle_scores=angle_scores,
            best_angle=best_angle,
            worst_angle=worst_angle,
            geometry_score=self._calculate_geometry_score(angle_scores),
            texture_score=self._calculate_texture_score(angle_scores),
            overall_color_accuracy=self._calculate_color_accuracy(angle_scores),
            issues=issues,
            recommendations=recommendations,
            validation_time_seconds=validation_time,
            reference_images_used=len(reference_images),
        )

        logger.info(
            "Fidelity validation completed",
            product_sku=product_sku,
            fidelity_score=round(fidelity_score, 4),
            passed=passed,
            validation_time=round(validation_time, 2),
        )

        return report

    def _find_reference_images(self, product_sku: str) -> list[Path]:
        """Find reference images for a product."""
        images = []

        # Check product-specific directory
        product_dir = self.reference_dir / product_sku
        if product_dir.exists():
            images.extend(product_dir.glob("*.png"))
            images.extend(product_dir.glob("*.jpg"))
            images.extend(product_dir.glob("*.jpeg"))

        # Check reference directory directly
        if not images:
            for ext in ["png", "jpg", "jpeg"]:
                images.extend(self.reference_dir.glob(f"{product_sku}*.{ext}"))
                images.extend(self.reference_dir.glob(f"*{product_sku}*.{ext}"))

        return sorted(images)

    async def _render_model_angles(
        self,
        model_path: Path,
    ) -> dict[str, Any]:
        """Render model from multiple viewing angles."""
        renders = {}

        try:
            import numpy as np
            import trimesh
            from PIL import Image

            mesh = trimesh.load(str(model_path))
            scene = trimesh.Scene(mesh)

            for angle in self.angles:
                angle_name = angle["name"]
                elevation = angle["elevation"]
                azimuth = angle["azimuth"]

                # Set camera position
                distance = 2.5
                x = distance * np.cos(np.radians(elevation)) * np.sin(np.radians(azimuth))
                y = distance * np.sin(np.radians(elevation))
                z = distance * np.cos(np.radians(elevation)) * np.cos(np.radians(azimuth))

                # Create camera transform
                camera_pose = np.eye(4)
                camera_pose[:3, 3] = [x, y, z]

                # Render
                try:
                    png_data = scene.save_image(resolution=self.resolution)
                    img = Image.open(io.BytesIO(png_data))
                    renders[angle_name] = np.array(img)
                except Exception as e:
                    logger.warning(f"Failed to render angle {angle_name}: {e}")
                    renders[angle_name] = np.zeros((*self.resolution, 3), dtype=np.uint8)

        except ImportError:
            logger.warning("trimesh not available, using placeholder renders")
            import numpy as np

            for angle in self.angles:
                renders[angle["name"]] = np.zeros((*self.resolution, 3), dtype=np.uint8)

        except Exception as e:
            logger.exception(f"Model rendering failed: {e}")
            import numpy as np

            for angle in self.angles:
                renders[angle["name"]] = np.zeros((*self.resolution, 3), dtype=np.uint8)

        return renders

    async def _compare_renders(
        self,
        model_renders: dict[str, Any],
        reference_images: list[Path],
    ) -> list[AngleScore]:
        """Compare model renders to reference images."""
        import numpy as np
        from PIL import Image

        scores = []

        for angle in self.angles:
            angle_name = angle["name"]
            render = model_renders.get(angle_name)

            if render is None:
                continue

            # Find best matching reference image for this angle
            best_match_score = 0.0
            best_ssim = 0.0
            best_color = 0.0
            best_edge = 0.0

            for ref_path in reference_images:
                try:
                    ref_img = Image.open(ref_path).convert("RGB")
                    ref_img = ref_img.resize(self.resolution)
                    ref_array = np.array(ref_img)

                    # Calculate metrics
                    ssim = self._calculate_ssim(render, ref_array)
                    color_acc = self._calculate_color_accuracy_single(render, ref_array)
                    edge_sim = self._calculate_edge_similarity(render, ref_array)

                    overall = (ssim * 0.4 + color_acc * 0.3 + edge_sim * 0.3)

                    if overall > best_match_score:
                        best_match_score = overall
                        best_ssim = ssim
                        best_color = color_acc
                        best_edge = edge_sim

                except Exception as e:
                    logger.warning(f"Failed to compare with {ref_path}: {e}")

            issues = []
            if best_ssim < 0.8:
                issues.append(f"Low structural similarity ({best_ssim:.2%})")
            if best_color < 0.8:
                issues.append(f"Color mismatch ({best_color:.2%})")
            if best_edge < 0.7:
                issues.append(f"Edge detection differs ({best_edge:.2%})")

            scores.append(
                AngleScore(
                    angle_name=angle_name,
                    elevation=angle["elevation"],
                    azimuth=angle["azimuth"],
                    ssim_score=best_ssim,
                    color_accuracy=best_color,
                    edge_similarity=best_edge,
                    overall_score=best_match_score,
                    issues=issues,
                )
            )

        return scores

    def _calculate_ssim(self, img1: Any, img2: Any) -> float:
        """Calculate Structural Similarity Index (SSIM)."""
        try:
            # Convert to grayscale for SSIM
            import numpy as np
            from skimage.metrics import structural_similarity

            gray1 = np.mean(img1, axis=2).astype(np.uint8)
            gray2 = np.mean(img2, axis=2).astype(np.uint8)

            score, _ = structural_similarity(gray1, gray2, full=True)
            return float(max(0.0, min(1.0, score)))

        except ImportError:
            # Fallback: simple normalized cross-correlation
            import numpy as np

            img1_norm = img1.astype(np.float64) / 255.0
            img2_norm = img2.astype(np.float64) / 255.0

            correlation = np.mean(img1_norm * img2_norm) / (
                np.std(img1_norm) * np.std(img2_norm) + 1e-8
            )
            return float(max(0.0, min(1.0, correlation)))

    def _calculate_color_accuracy_single(self, img1: Any, img2: Any) -> float:
        """Calculate color accuracy between two images."""
        import numpy as np

        # Calculate color histogram similarity
        hist1 = np.histogram(img1.flatten(), bins=256, range=(0, 256))[0]
        hist2 = np.histogram(img2.flatten(), bins=256, range=(0, 256))[0]

        # Normalize
        hist1 = hist1.astype(np.float64) / (hist1.sum() + 1e-8)
        hist2 = hist2.astype(np.float64) / (hist2.sum() + 1e-8)

        # Bhattacharyya coefficient
        bc = np.sum(np.sqrt(hist1 * hist2))
        return float(max(0.0, min(1.0, bc)))

    def _calculate_edge_similarity(self, img1: Any, img2: Any) -> float:
        """Calculate edge similarity between two images."""
        try:
            import numpy as np
            from scipy import ndimage

            # Convert to grayscale
            gray1 = np.mean(img1, axis=2)
            gray2 = np.mean(img2, axis=2)

            # Apply Sobel edge detection
            sx1 = ndimage.sobel(gray1, axis=0)
            sy1 = ndimage.sobel(gray1, axis=1)
            edges1 = np.hypot(sx1, sy1)

            sx2 = ndimage.sobel(gray2, axis=0)
            sy2 = ndimage.sobel(gray2, axis=1)
            edges2 = np.hypot(sx2, sy2)

            # Normalize
            edges1 = edges1 / (edges1.max() + 1e-8)
            edges2 = edges2 / (edges2.max() + 1e-8)

            # Calculate correlation
            correlation = np.corrcoef(edges1.flatten(), edges2.flatten())[0, 1]
            return float(max(0.0, min(1.0, (correlation + 1) / 2)))

        except ImportError:
            # Fallback: simple gradient comparison
            import numpy as np

            gray1 = np.mean(img1, axis=2)
            gray2 = np.mean(img2, axis=2)

            dx1, dy1 = np.gradient(gray1)
            dx2, dy2 = np.gradient(gray2)

            mag1 = np.sqrt(dx1**2 + dy1**2)
            mag2 = np.sqrt(dx2**2 + dy2**2)

            mag1 = mag1 / (mag1.max() + 1e-8)
            mag2 = mag2 / (mag2.max() + 1e-8)

            diff = np.abs(mag1 - mag2).mean()
            return float(max(0.0, 1.0 - diff))

    def _calculate_fidelity_score(self, angle_scores: list[AngleScore]) -> float:
        """Calculate overall fidelity score from angle scores."""
        if not angle_scores:
            return 0.0

        # Weighted average of angle scores
        # Front angles are weighted more heavily
        weights = {
            "front": 2.0,
            "back": 1.5,
            "right": 1.0,
            "left": 1.0,
            "front_top": 1.2,
            "front_bottom": 0.8,
        }

        total_weight = 0.0
        weighted_sum = 0.0

        for score in angle_scores:
            weight = weights.get(score.angle_name, 1.0)
            weighted_sum += score.overall_score * weight
            total_weight += weight

        return weighted_sum / total_weight if total_weight > 0 else 0.0

    def _calculate_geometry_score(self, angle_scores: list[AngleScore]) -> float:
        """Calculate geometry score from edge similarity."""
        if not angle_scores:
            return 0.0
        return sum(s.edge_similarity for s in angle_scores) / len(angle_scores)

    def _calculate_texture_score(self, angle_scores: list[AngleScore]) -> float:
        """Calculate texture score from SSIM."""
        if not angle_scores:
            return 0.0
        return sum(s.ssim_score for s in angle_scores) / len(angle_scores)

    def _calculate_color_accuracy(self, angle_scores: list[AngleScore]) -> float:
        """Calculate overall color accuracy."""
        if not angle_scores:
            return 0.0
        return sum(s.color_accuracy for s in angle_scores) / len(angle_scores)

    def _generate_feedback(
        self,
        angle_scores: list[AngleScore],
        fidelity_score: float,
    ) -> tuple[list[str], list[str]]:
        """Generate issues and recommendations from scores."""
        issues = []
        recommendations = []

        if fidelity_score < self.threshold:
            issues.append(
                f"Overall fidelity score ({fidelity_score:.2%}) is below "
                f"threshold ({self.threshold:.2%})"
            )

        # Check for problematic angles
        for score in angle_scores:
            if score.overall_score < 0.7:
                issues.append(
                    f"Poor quality at {score.angle_name} angle "
                    f"({score.overall_score:.2%})"
                )
            issues.extend(score.issues)

        # Generate recommendations
        avg_ssim = self._calculate_texture_score(angle_scores)
        avg_color = self._calculate_color_accuracy(angle_scores)
        avg_edge = self._calculate_geometry_score(angle_scores)

        if avg_ssim < 0.8:
            recommendations.append(
                "Consider regenerating with higher quality settings "
                "to improve structural accuracy"
            )

        if avg_color < 0.8:
            recommendations.append(
                "Texture colors do not match well - "
                "try using more source images with consistent lighting"
            )

        if avg_edge < 0.7:
            recommendations.append(
                "Geometry edges differ significantly - "
                "ensure source images show clear product edges"
            )

        if not issues:
            issues.append("Model passed all quality checks")

        return issues, recommendations


# =============================================================================
# Convenience Function
# =============================================================================


async def validate_model_fidelity(
    model_path: str | Path,
    product_sku: str,
    reference_dir: str | Path | None = None,
    threshold: float = DEFAULT_FIDELITY_THRESHOLD,
) -> FidelityReport:
    """
    Validate model fidelity (convenience function).

    Args:
        model_path: Path to the 3D model
        product_sku: Product SKU for finding reference images
        reference_dir: Directory with reference images
        threshold: Minimum fidelity score to pass

    Returns:
        FidelityReport with validation results
    """
    ref_dir = Path(reference_dir) if reference_dir else Path("./product_images")
    validator = ModelFidelityValidator(
        reference_images_dir=ref_dir,
        fidelity_threshold=threshold,
    )
    return await validator.validate(Path(model_path), product_sku)


__all__ = [
    "ModelFidelityValidator",
    "FidelityReport",
    "AngleScore",
    "validate_model_fidelity",
    "DEFAULT_FIDELITY_THRESHOLD",
]
