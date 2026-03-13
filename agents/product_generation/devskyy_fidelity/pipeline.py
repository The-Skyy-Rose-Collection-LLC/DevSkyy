"""Product image pipeline — generate, validate, upload (or reject).

Orchestrates the full lifecycle of a product image:

1. Generate image via AI API (pluggable — caller provides the generator)
2. Validate against reference photos via :class:`AssetQualityGate`
3. If passed → upload to CDN (pluggable — caller provides the uploader)
4. If failed → reject, log, and return actionable recommendations
5. Log every validation to a JSONL audit trail

The pipeline is async and supports both single-image and batch modes.
"""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Callable, Coroutine
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from config.collections import get_collection
from pydantic import BaseModel, Field

from agents.product_generation.devskyy_fidelity.config import (
    get_fidelity_threshold,
    get_product_palette,
)
from agents.product_generation.devskyy_fidelity.quality_gate import (
    AssetQualityGate,
)

logger = logging.getLogger(__name__)


# ── Enums & models ───────────────────────────────────────────────────────────


class ImageStatus(StrEnum):
    """Lifecycle status of a product image."""

    PENDING = "pending"
    GENERATING = "generating"
    VALIDATING = "validating"
    PASSED = "passed"
    REJECTED = "rejected"
    UPLOADED = "uploaded"
    ERROR = "error"


class ProductImageMetadata(BaseModel):
    """Metadata record for a single product image lifecycle.

    Written to the JSONL audit log after every validation.
    """

    product_id: str
    sku: str
    collection: str
    angle: str = "front"
    status: ImageStatus = ImageStatus.PENDING
    fidelity_score: float = 0.0
    silhouette_iou: float = 0.0
    color_delta_e_avg: float = 0.0
    threshold: float = 80.0
    cdn_url: str | None = None
    error: str | None = None
    recommendations: list[str] = Field(default_factory=list)
    generated_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    validation_time_ms: float = 0.0

    def to_log_dict(self) -> dict[str, Any]:
        """Serialize for JSONL logging."""
        return self.model_dump(exclude_none=True)


# ── Type aliases for pluggable callbacks ─────────────────────────────────────

GeneratorFn = Callable[..., Coroutine[Any, Any, Path | None]]
UploaderFn = Callable[[Path, str], Coroutine[Any, Any, str | None]]


# ── Pipeline ─────────────────────────────────────────────────────────────────


class ProductImagePipeline:
    """Full product image generation + validation pipeline.

    Usage::

        pipeline = ProductImagePipeline(
            reference_dir=Path("reference_photos"),
            output_dir=Path("generated_images"),
            threshold=80.0,
        )

        result = await pipeline.generate_product_image(
            product_id="9679",
            sku="br-004",
            collection="BLACK_ROSE",
            angle="front",
            prompt="...",
            reference_photos=[Path("ref_front.jpg")],
            expected_colors=["#000000", "#303331"],
        )

    Pluggable components:
        - ``generator_fn``: async callable that generates an image → Path
        - ``uploader_fn``: async callable that uploads a file → CDN URL
    """

    def __init__(
        self,
        reference_dir: Path | str,
        output_dir: Path | str,
        threshold: float = 80.0,
        generator_fn: GeneratorFn | None = None,
        uploader_fn: UploaderFn | None = None,
        metadata_log_path: Path | str | None = None,
    ) -> None:
        self.reference_dir = Path(reference_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.threshold = threshold
        self.generator_fn = generator_fn
        self.uploader_fn = uploader_fn

        # JSONL audit log
        if metadata_log_path is None:
            self.metadata_log = self.output_dir / "metadata.jsonl"
        else:
            self.metadata_log = Path(metadata_log_path)

        # Core quality gate
        self._gate = AssetQualityGate(threshold=threshold)

    # ── Single image pipeline ────────────────────────────────────────────────

    async def generate_product_image(
        self,
        product_id: str,
        sku: str,
        collection: str,
        angle: str = "front",
        prompt: str = "",
        reference_photos: list[Path | str] | None = None,
        expected_colors: list[str] | None = None,
        generated_image_path: Path | str | None = None,
    ) -> ProductImageMetadata:
        """Run the full pipeline for a single product image.

        If ``generated_image_path`` is provided, skips generation and
        jumps straight to validation (useful for re-validating existing
        images).

        Args:
            product_id: WooCommerce product ID.
            sku: Product SKU (e.g. ``"br-004"``).
            collection: Collection name (e.g. ``"BLACK_ROSE"``).
            angle: Camera angle (``"front"``, ``"back"``, ``"branding"``).
            prompt: Generation prompt (ignored if image already exists).
            reference_photos: Paths to reference product photos.
            expected_colors: Hex color palette. Auto-looked up from
                :data:`PRODUCT_COLOR_PALETTES` if not provided.
            generated_image_path: Path to an already-generated image
                (skips the generation step).

        Returns:
            ProductImageMetadata with final status and scores.
        """
        # Resolve collection
        try:
            coll = get_collection(collection)
        except ValueError:
            coll = None

        # Determine threshold
        if coll is not None:
            effective_threshold = get_fidelity_threshold(sku, coll)
        else:
            effective_threshold = self.threshold

        # Auto-lookup color palette
        if expected_colors is None:
            palette = get_product_palette(sku)
            expected_colors = list(palette) if palette else None

        meta = ProductImageMetadata(
            product_id=product_id,
            sku=sku,
            collection=collection,
            angle=angle,
            threshold=effective_threshold,
        )

        # ── Step 1: Generate (or use existing) ───────────────────────────────
        if generated_image_path is not None:
            image_path = Path(generated_image_path)
            if not image_path.exists():
                meta.status = ImageStatus.ERROR
                meta.error = f"Provided image not found: {image_path}"
                self._log_metadata(meta)
                return meta
        elif self.generator_fn is not None:
            meta.status = ImageStatus.GENERATING
            try:
                image_path = await self.generator_fn(
                    sku=sku,
                    angle=angle,
                    prompt=prompt,
                    output_dir=self.output_dir,
                )
                if image_path is None or not Path(image_path).exists():
                    meta.status = ImageStatus.ERROR
                    meta.error = "Image generation returned no output"
                    self._log_metadata(meta)
                    return meta
                image_path = Path(image_path)
            except Exception as e:
                meta.status = ImageStatus.ERROR
                meta.error = f"Generation failed: {e}"
                self._log_metadata(meta)
                return meta
        else:
            meta.status = ImageStatus.ERROR
            meta.error = "No image path and no generator configured"
            self._log_metadata(meta)
            return meta

        # ── Step 2: Validate ─────────────────────────────────────────────────
        meta.status = ImageStatus.VALIDATING
        refs = [Path(r) for r in (reference_photos or [])]

        # Auto-discover references from reference_dir
        if not refs and self.reference_dir.exists():
            sku_dir = self.reference_dir / collection / sku
            if sku_dir.exists():
                refs = sorted(sku_dir.glob("*.jpg")) + sorted(sku_dir.glob("*.png"))

        if not refs:
            # No references → skip validation, mark as passed with warning
            meta.status = ImageStatus.PASSED
            meta.fidelity_score = 0.0
            meta.recommendations = [
                "No reference photos available — validation skipped. "
                "Set up reference photos for proper fidelity checking."
            ]
            self._log_metadata(meta)
            return meta

        gate = AssetQualityGate(
            threshold=effective_threshold,
            silhouette_weight=self._gate.silhouette_weight,
            color_weight=self._gate.color_weight,
        )

        result = await gate.validate_against_real_garment(
            generated_image=image_path,
            reference_photos=refs,
            color_hex_palette=expected_colors,
        )

        meta.fidelity_score = result.overall_score
        meta.silhouette_iou = result.silhouette_iou
        meta.color_delta_e_avg = result.color_delta_e_avg
        meta.validation_time_ms = result.validation_time_ms
        meta.recommendations = result.recommendations

        if not result.passed:
            meta.status = ImageStatus.REJECTED
            self._log_metadata(meta)
            return meta

        meta.status = ImageStatus.PASSED

        # ── Step 3: Upload (if uploader configured) ──────────────────────────
        if self.uploader_fn is not None:
            try:
                cdn_key = f"{sku}/{angle}/{image_path.name}"
                cdn_url = await self.uploader_fn(image_path, cdn_key)
                if cdn_url:
                    meta.cdn_url = cdn_url
                    meta.status = ImageStatus.UPLOADED
            except Exception as e:
                logger.warning("CDN upload failed for %s: %s", sku, e)
                meta.recommendations.append(f"CDN upload failed: {e}")

        self._log_metadata(meta)
        return meta

    # ── Batch validation ─────────────────────────────────────────────────────

    async def validate_batch(
        self,
        items: list[dict[str, Any]],
        max_concurrency: int = 5,
    ) -> list[ProductImageMetadata]:
        """Validate multiple images in parallel.

        Each item in ``items`` should be a dict with keys matching
        :meth:`generate_product_image` arguments.

        Args:
            items: List of validation specs.
            max_concurrency: Max parallel validations.

        Returns:
            List of ProductImageMetadata results.
        """
        semaphore = asyncio.Semaphore(max_concurrency)

        async def _validate_one(item: dict[str, Any]) -> ProductImageMetadata:
            async with semaphore:
                return await self.generate_product_image(**item)

        tasks = [_validate_one(item) for item in items]
        return await asyncio.gather(*tasks)

    # ── Reporting ────────────────────────────────────────────────────────────

    def get_validation_report(self) -> dict[str, Any]:
        """Generate statistics from the metadata audit log.

        Returns:
            Dict with acceptance_rate, total, passed, rejected,
            avg_score, avg_iou, avg_delta_e.
        """
        if not self.metadata_log.exists():
            return {
                "total": 0,
                "passed": 0,
                "rejected": 0,
                "uploaded": 0,
                "acceptance_rate": 0.0,
            }

        entries: list[dict[str, Any]] = []
        with self.metadata_log.open("r") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue

        if not entries:
            return {
                "total": 0,
                "passed": 0,
                "rejected": 0,
                "uploaded": 0,
                "acceptance_rate": 0.0,
            }

        total = len(entries)
        passed = sum(
            1 for e in entries if e.get("status") in (ImageStatus.PASSED, ImageStatus.UPLOADED)
        )
        rejected = sum(1 for e in entries if e.get("status") == ImageStatus.REJECTED)
        uploaded = sum(1 for e in entries if e.get("status") == ImageStatus.UPLOADED)

        scores = [e.get("fidelity_score", 0) for e in entries if e.get("fidelity_score")]
        ious = [e.get("silhouette_iou", 0) for e in entries if e.get("silhouette_iou")]
        delta_es = [e.get("color_delta_e_avg", 0) for e in entries if e.get("color_delta_e_avg")]

        return {
            "total": total,
            "passed": passed,
            "rejected": rejected,
            "uploaded": uploaded,
            "acceptance_rate": (passed / total * 100) if total > 0 else 0.0,
            "avg_score": sum(scores) / len(scores) if scores else 0.0,
            "avg_iou": sum(ious) / len(ious) if ious else 0.0,
            "avg_delta_e": sum(delta_es) / len(delta_es) if delta_es else 0.0,
        }

    # ── Audit log ────────────────────────────────────────────────────────────

    def _log_metadata(self, meta: ProductImageMetadata) -> None:
        """Append a metadata record to the JSONL audit log."""
        try:
            self.metadata_log.parent.mkdir(parents=True, exist_ok=True)
            with self.metadata_log.open("a") as f:
                f.write(json.dumps(meta.to_log_dict(), default=str) + "\n")
        except Exception:
            logger.exception("Failed to write metadata log")


__all__ = [
    "ProductImagePipeline",
    "ProductImageMetadata",
    "ImageStatus",
]
