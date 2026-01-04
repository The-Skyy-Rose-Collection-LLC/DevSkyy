"""Asset Quality Gate.

Central enforcement of visual fidelity thresholds.
Blocks assets that don't meet similarity requirements before upload.

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import logging
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class GateStatus(str, Enum):
    """Status of quality gate check."""

    PASSED = "passed"
    BLOCKED = "blocked"
    WARNING = "warning"
    SKIPPED = "skipped"
    ERROR = "error"


class QualityGateResult(BaseModel):
    """Result of quality gate validation."""

    status: GateStatus
    passed: bool = Field(..., description="True if asset meets threshold")
    score: float = Field(..., ge=0.0, le=100.0, description="Overall similarity score (0-100)")
    threshold: float = Field(default=90.0, description="Required threshold")

    asset_path: str | None = None
    reference_path: str | None = None
    asset_type: str | None = None

    block_reason: str | None = Field(None, description="Why asset was blocked")
    recommendations: list[str] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)

    validated_at: datetime = Field(default_factory=datetime.utcnow)
    validation_time_ms: float | None = None


class AssetFidelityError(Exception):
    """Raised when asset fails quality gate."""

    def __init__(
        self,
        message: str,
        score: float,
        threshold: float,
        recommendations: list[str] | None = None,
    ) -> None:
        super().__init__(message)
        self.score = score
        self.threshold = threshold
        self.recommendations = recommendations or []


class AssetQualityGate:
    """Central quality gate for asset fidelity enforcement.

    Validates generated assets against reference images before allowing
    upload to production (WordPress/WooCommerce).

    Default threshold: 90% similarity required to pass.

    Example:
        >>> gate = AssetQualityGate()
        >>> result = await gate.validate_asset(
        ...     "generated_model.glb",
        ...     "reference_photo.jpg",
        ...     asset_type="3d_model"
        ... )
        >>> if not result.passed:
        ...     print(f"Blocked: {result.block_reason}")
    """

    DEFAULT_THRESHOLD = 90.0  # 90% similarity required
    WARNING_THRESHOLD = 85.0  # Warn but allow above this

    def __init__(
        self,
        threshold: float = DEFAULT_THRESHOLD,
        strict_mode: bool = True,
    ) -> None:
        """Initialize quality gate.

        Args:
            threshold: Minimum similarity percentage to pass (0-100)
            strict_mode: If True, raise exception on failure. If False, return result only.
        """
        self.threshold = threshold
        self.strict_mode = strict_mode

    async def validate_3d_model(
        self,
        model_path: Path | str,
        reference_image: Path | str,
    ) -> QualityGateResult:
        """Validate 3D model against reference image.

        Renders the model and compares with reference using visual comparison.

        Args:
            model_path: Path to GLB/GLTF model
            reference_image: Path to reference product image

        Returns:
            QualityGateResult with pass/fail status
        """
        import time

        start_time = time.time()
        model_path = Path(model_path)
        reference_image = Path(reference_image)

        # Validate inputs
        if not model_path.exists():
            return QualityGateResult(
                status=GateStatus.ERROR,
                passed=False,
                score=0.0,
                threshold=self.threshold,
                asset_path=str(model_path),
                block_reason=f"Model not found: {model_path}",
            )

        if not reference_image.exists():
            return QualityGateResult(
                status=GateStatus.SKIPPED,
                passed=False,
                score=0.0,
                threshold=self.threshold,
                asset_path=str(model_path),
                reference_path=str(reference_image),
                block_reason="Reference image not found",
                recommendations=["Provide a valid reference image for comparison"],
            )

        try:
            from imagery.headless_renderer import CameraAngle, HeadlessRenderer
            from imagery.visual_comparison import VisualComparisonEngine

            # Render the 3D model
            renderer = HeadlessRenderer()
            render_dir = model_path.parent / ".quality_gate"
            render_result = renderer.render_model(
                model_path,
                render_dir,
                angles=[CameraAngle.FRONT, CameraAngle.THREE_QUARTER],
            )

            if not render_result.success:
                return QualityGateResult(
                    status=GateStatus.ERROR,
                    passed=False,
                    score=0.0,
                    threshold=self.threshold,
                    asset_path=str(model_path),
                    reference_path=str(reference_image),
                    block_reason=f"Failed to render model: {render_result.errors}",
                    recommendations=["Check model file integrity", "Ensure GLB format is valid"],
                )

            # Compare each rendered view with reference
            comparator = VisualComparisonEngine(threshold=self.threshold)
            best_score = 0.0
            best_comparison = None

            for _angle, rendered_path in render_result.images.items():
                comparison = comparator.compare(reference_image, rendered_path)
                if comparison.overall_similarity > best_score:
                    best_score = comparison.overall_similarity
                    best_comparison = comparison

            if best_comparison is None:
                return QualityGateResult(
                    status=GateStatus.ERROR,
                    passed=False,
                    score=0.0,
                    threshold=self.threshold,
                    asset_path=str(model_path),
                    reference_path=str(reference_image),
                    block_reason="No comparison could be made",
                )

            # Determine status
            passed = best_score >= self.threshold
            if passed:
                status = GateStatus.PASSED
            elif best_score >= self.WARNING_THRESHOLD:
                status = GateStatus.WARNING
            else:
                status = GateStatus.BLOCKED

            elapsed_ms = (time.time() - start_time) * 1000

            result = QualityGateResult(
                status=status,
                passed=passed,
                score=round(best_score, 2),
                threshold=self.threshold,
                asset_path=str(model_path),
                reference_path=str(reference_image),
                asset_type="3d_model",
                block_reason=(
                    None if passed else f"Similarity {best_score:.1f}% < {self.threshold}%"
                ),
                recommendations=best_comparison.recommendations if not passed else [],
                metrics={
                    "ssim": best_comparison.ssim_score,
                    "color_similarity": best_comparison.color_similarity,
                    "perceptual_similarity": best_comparison.perceptual_similarity,
                    "confidence": best_comparison.confidence.value,
                    "model_info": render_result.model_info,
                },
                validation_time_ms=round(elapsed_ms, 2),
            )

            logger.info(
                f"Quality gate: {model_path.name} - {status.value} "
                f"({best_score:.1f}% vs {self.threshold}% threshold)"
            )

            return result

        except ImportError as e:
            return QualityGateResult(
                status=GateStatus.ERROR,
                passed=False,
                score=0.0,
                threshold=self.threshold,
                asset_path=str(model_path),
                reference_path=str(reference_image),
                block_reason=f"Missing dependencies: {e}",
                recommendations=["Install: pip install scikit-image imagehash pyrender trimesh"],
            )
        except Exception as e:
            logger.exception(f"Quality gate error: {e}")
            return QualityGateResult(
                status=GateStatus.ERROR,
                passed=False,
                score=0.0,
                threshold=self.threshold,
                asset_path=str(model_path),
                reference_path=str(reference_image),
                block_reason=str(e),
            )

    async def validate_2d_image(
        self,
        generated_image: Path | str,
        reference_image: Path | str,
    ) -> QualityGateResult:
        """Validate generated 2D image against reference.

        Args:
            generated_image: Path to generated/enhanced image
            reference_image: Path to reference product image

        Returns:
            QualityGateResult with pass/fail status
        """
        import time

        start_time = time.time()
        generated_image = Path(generated_image)
        reference_image = Path(reference_image)

        if not generated_image.exists():
            return QualityGateResult(
                status=GateStatus.ERROR,
                passed=False,
                score=0.0,
                threshold=self.threshold,
                block_reason=f"Generated image not found: {generated_image}",
            )

        if not reference_image.exists():
            return QualityGateResult(
                status=GateStatus.SKIPPED,
                passed=False,
                score=0.0,
                threshold=self.threshold,
                block_reason="Reference image not found",
            )

        try:
            from imagery.visual_comparison import VisualComparisonEngine

            comparator = VisualComparisonEngine(threshold=self.threshold)
            comparison = comparator.compare(reference_image, generated_image)

            passed = comparison.passed
            if passed:
                status = GateStatus.PASSED
            elif comparison.overall_similarity >= self.WARNING_THRESHOLD:
                status = GateStatus.WARNING
            else:
                status = GateStatus.BLOCKED

            elapsed_ms = (time.time() - start_time) * 1000

            return QualityGateResult(
                status=status,
                passed=passed,
                score=comparison.overall_similarity,
                threshold=self.threshold,
                asset_path=str(generated_image),
                reference_path=str(reference_image),
                asset_type="2d_image",
                block_reason=(
                    None
                    if passed
                    else f"Similarity {comparison.overall_similarity:.1f}% < {self.threshold}%"
                ),
                recommendations=comparison.recommendations if not passed else [],
                metrics={
                    "ssim": comparison.ssim_score,
                    "color_similarity": comparison.color_similarity,
                    "perceptual_similarity": comparison.perceptual_similarity,
                    "confidence": comparison.confidence.value,
                },
                validation_time_ms=round(elapsed_ms, 2),
            )

        except Exception as e:
            logger.exception(f"Quality gate error: {e}")
            return QualityGateResult(
                status=GateStatus.ERROR,
                passed=False,
                score=0.0,
                threshold=self.threshold,
                block_reason=str(e),
            )

    async def validate_asset(
        self,
        asset_path: Path | str,
        reference_image: Path | str,
        asset_type: Literal["3d_model", "2d_image"],
    ) -> QualityGateResult:
        """Validate any asset against reference image.

        Args:
            asset_path: Path to generated asset
            reference_image: Path to reference product image
            asset_type: Type of asset ("3d_model" or "2d_image")

        Returns:
            QualityGateResult with pass/fail status

        Raises:
            AssetFidelityError: If strict_mode and asset fails gate
        """
        if asset_type == "3d_model":
            result = await self.validate_3d_model(asset_path, reference_image)
        else:
            result = await self.validate_2d_image(asset_path, reference_image)

        # Raise exception in strict mode if failed
        if self.strict_mode and not result.passed and result.status != GateStatus.SKIPPED:
            raise AssetFidelityError(
                f"Asset blocked by quality gate: {result.block_reason}",
                score=result.score,
                threshold=result.threshold,
                recommendations=result.recommendations,
            )

        return result

    def enforce(self, result: QualityGateResult) -> None:
        """Enforce quality gate result by raising exception if failed.

        Args:
            result: Previous validation result

        Raises:
            AssetFidelityError: If result indicates failure
        """
        if not result.passed and result.status not in (GateStatus.SKIPPED, GateStatus.WARNING):
            raise AssetFidelityError(
                f"Asset blocked: {result.block_reason}",
                score=result.score,
                threshold=result.threshold,
                recommendations=result.recommendations,
            )


# Convenience function
async def validate_before_upload(
    asset_path: Path | str,
    reference_image: Path | str,
    asset_type: Literal["3d_model", "2d_image"] = "3d_model",
    threshold: float = 90.0,
) -> QualityGateResult:
    """Validate asset before WordPress upload.

    Args:
        asset_path: Path to asset file
        reference_image: Path to reference product image
        asset_type: Type of asset
        threshold: Minimum similarity percentage

    Returns:
        QualityGateResult

    Example:
        >>> result = await validate_before_upload(
        ...     "model.glb",
        ...     "product_photo.jpg",
        ...     threshold=90.0
        ... )
        >>> if result.passed:
        ...     await upload_to_wordpress(asset_path)
        >>> else:
        ...     print(f"Blocked: {result.recommendations}")
    """
    gate = AssetQualityGate(threshold=threshold, strict_mode=False)
    return await gate.validate_asset(asset_path, reference_image, asset_type)


__all__ = [
    "AssetQualityGate",
    "QualityGateResult",
    "GateStatus",
    "AssetFidelityError",
    "validate_before_upload",
]
