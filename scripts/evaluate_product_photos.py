#!/usr/bin/env python3
"""Product Photo Evaluation Script.

Evaluates existing product photos for 3D generation suitability.
Analyzes blur, resolution, lighting, and other quality factors.

Usage:
    python scripts/evaluate_product_photos.py --collection signature
    python scripts/evaluate_product_photos.py --all
    python scripts/evaluate_product_photos.py --path assets/3d-models/

Output: PHOTO_EVALUATION_REPORT.json
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Supported image extensions
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".tiff", ".bmp"}


class PhotoQuality(str, Enum):
    """Overall photo quality rating."""

    EXCELLENT = "excellent"  # Ready for 3D generation
    GOOD = "good"  # Usable with minor enhancements
    FAIR = "fair"  # Needs enhancement
    POOR = "poor"  # Consider reshoot
    UNUSABLE = "unusable"  # Requires reshoot


@dataclass
class PhotoMetrics:
    """Quality metrics for a single photo."""

    path: Path
    filename: str
    collection: str

    # Dimensions
    width: int = 0
    height: int = 0
    megapixels: float = 0.0
    aspect_ratio: float = 0.0

    # Quality metrics (0-100)
    resolution_score: float = 0.0
    blur_score: float = 0.0  # Higher = sharper
    brightness_score: float = 0.0
    contrast_score: float = 0.0
    color_richness_score: float = 0.0

    # Overall
    overall_score: float = 0.0
    quality: PhotoQuality = PhotoQuality.POOR
    usable_for_3d: bool = False

    # Issues and recommendations
    issues: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)

    error: str | None = None


@dataclass
class CollectionSummary:
    """Summary for a collection's photos."""

    collection: str
    total_photos: int = 0
    excellent: int = 0
    good: int = 0
    fair: int = 0
    poor: int = 0
    unusable: int = 0
    usable_for_3d: int = 0
    average_score: float = 0.0


class PhotoEvaluator:
    """Evaluates product photos for 3D generation suitability."""

    # Minimum requirements for 3D generation
    MIN_RESOLUTION = 512  # pixels (min dimension)
    IDEAL_RESOLUTION = 1024  # pixels (ideal min dimension)
    MIN_MEGAPIXELS = 0.5
    IDEAL_MEGAPIXELS = 2.0

    # Quality thresholds
    EXCELLENT_THRESHOLD = 85.0
    GOOD_THRESHOLD = 70.0
    FAIR_THRESHOLD = 55.0
    POOR_THRESHOLD = 40.0

    def __init__(self) -> None:
        """Initialize evaluator."""
        self._opencv_available = False
        try:
            import cv2

            self._opencv_available = True
        except ImportError:
            logger.warning("OpenCV not available. Some metrics will be limited.")

    def _compute_blur_score(self, image: Image.Image) -> float:
        """Compute blur/sharpness score using Laplacian variance.

        Higher score = sharper image.
        """
        if not self._opencv_available:
            # Fallback: use PIL edge detection
            from PIL import ImageFilter

            edges = image.convert("L").filter(ImageFilter.FIND_EDGES)
            edge_arr = np.array(edges)
            variance = np.var(edge_arr)
            # Normalize to 0-100 (empirically tuned)
            return min(100.0, variance / 10.0)

        import cv2

        # Convert to grayscale numpy array
        gray = np.array(image.convert("L"))

        # Laplacian variance (higher = sharper)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        variance = laplacian.var()

        # Normalize to 0-100 (empirically tuned)
        # Typical range: 0-500 for variance
        score = min(100.0, variance / 5.0)
        return score

    def _compute_brightness_score(self, image: Image.Image) -> float:
        """Compute brightness score.

        Target: 40-60% average brightness (not too dark, not too bright).
        """
        arr = np.array(image.convert("L"))
        mean_brightness = arr.mean() / 255.0  # 0-1 range

        # Penalize both too dark and too bright
        # Ideal is around 0.5 (50% brightness)
        deviation = abs(mean_brightness - 0.5)
        score = max(0.0, 100.0 - (deviation * 200.0))
        return score

    def _compute_contrast_score(self, image: Image.Image) -> float:
        """Compute contrast score.

        Higher standard deviation = better contrast.
        """
        arr = np.array(image.convert("L"))
        std = arr.std()

        # Typical range: 0-80 for std
        # Good contrast: std > 40
        score = min(100.0, (std / 80.0) * 100.0)
        return score

    def _compute_color_richness(self, image: Image.Image) -> float:
        """Compute color richness/saturation score."""
        # Convert to HSV and check saturation
        hsv = image.convert("HSV")
        s_channel = np.array(hsv.split()[1])

        mean_saturation = s_channel.mean() / 255.0
        # Good saturation: 20-80%
        if mean_saturation < 0.1:
            return 30.0  # Very desaturated
        elif mean_saturation > 0.8:
            return 70.0  # Over-saturated
        else:
            return 50.0 + (mean_saturation * 50.0)

    def _compute_resolution_score(
        self,
        width: int,
        height: int,
    ) -> float:
        """Compute resolution adequacy score."""
        min_dim = min(width, height)
        megapixels = (width * height) / 1_000_000

        # Score based on minimum dimension
        if min_dim >= self.IDEAL_RESOLUTION:
            dim_score = 100.0
        elif min_dim >= self.MIN_RESOLUTION:
            dim_score = (
                50.0
                + ((min_dim - self.MIN_RESOLUTION) / (self.IDEAL_RESOLUTION - self.MIN_RESOLUTION))
                * 50.0
            )
        else:
            dim_score = (min_dim / self.MIN_RESOLUTION) * 50.0

        # Score based on megapixels
        if megapixels >= self.IDEAL_MEGAPIXELS:
            mp_score = 100.0
        elif megapixels >= self.MIN_MEGAPIXELS:
            mp_score = (
                50.0
                + (
                    (megapixels - self.MIN_MEGAPIXELS)
                    / (self.IDEAL_MEGAPIXELS - self.MIN_MEGAPIXELS)
                )
                * 50.0
            )
        else:
            mp_score = (megapixels / self.MIN_MEGAPIXELS) * 50.0

        # Combine
        return dim_score * 0.6 + mp_score * 0.4

    def evaluate_photo(self, photo_path: Path, collection: str = "unknown") -> PhotoMetrics:
        """Evaluate a single photo.

        Args:
            photo_path: Path to image file
            collection: Collection name for categorization

        Returns:
            PhotoMetrics with quality scores
        """
        metrics = PhotoMetrics(
            path=photo_path,
            filename=photo_path.name,
            collection=collection,
        )

        try:
            # Load image
            image = Image.open(photo_path)
            if image.mode == "RGBA":
                # Convert RGBA to RGB (drop alpha)
                image = image.convert("RGB")
            elif image.mode not in ("RGB", "L"):
                image = image.convert("RGB")

            # Basic dimensions
            metrics.width, metrics.height = image.size
            metrics.megapixels = (metrics.width * metrics.height) / 1_000_000
            metrics.aspect_ratio = metrics.width / metrics.height if metrics.height > 0 else 0

            # Compute quality metrics
            metrics.resolution_score = self._compute_resolution_score(metrics.width, metrics.height)
            metrics.blur_score = self._compute_blur_score(image)
            metrics.brightness_score = self._compute_brightness_score(image)
            metrics.contrast_score = self._compute_contrast_score(image)
            metrics.color_richness_score = self._compute_color_richness(image)

            # Weighted overall score
            metrics.overall_score = (
                metrics.resolution_score * 0.25
                + metrics.blur_score * 0.30
                + metrics.brightness_score * 0.15
                + metrics.contrast_score * 0.15
                + metrics.color_richness_score * 0.15
            )

            # Determine quality grade
            if metrics.overall_score >= self.EXCELLENT_THRESHOLD:
                metrics.quality = PhotoQuality.EXCELLENT
            elif metrics.overall_score >= self.GOOD_THRESHOLD:
                metrics.quality = PhotoQuality.GOOD
            elif metrics.overall_score >= self.FAIR_THRESHOLD:
                metrics.quality = PhotoQuality.FAIR
            elif metrics.overall_score >= self.POOR_THRESHOLD:
                metrics.quality = PhotoQuality.POOR
            else:
                metrics.quality = PhotoQuality.UNUSABLE

            # Usability for 3D generation
            metrics.usable_for_3d = (
                metrics.quality in (PhotoQuality.EXCELLENT, PhotoQuality.GOOD)
                and min(metrics.width, metrics.height) >= self.MIN_RESOLUTION
            )

            # Identify issues and recommendations
            self._identify_issues(metrics)

        except Exception as e:
            metrics.error = str(e)
            metrics.quality = PhotoQuality.UNUSABLE
            metrics.issues.append(f"Failed to load image: {e}")

        return metrics

    def _identify_issues(self, metrics: PhotoMetrics) -> None:
        """Identify issues and provide recommendations."""
        # Resolution issues
        if min(metrics.width, metrics.height) < self.MIN_RESOLUTION:
            metrics.issues.append(f"Resolution too low: {metrics.width}x{metrics.height}")
            metrics.recommendations.append("Reshoot at higher resolution (min 512px)")
        elif min(metrics.width, metrics.height) < self.IDEAL_RESOLUTION:
            metrics.recommendations.append("Consider higher resolution for better results")

        # Blur issues
        if metrics.blur_score < 30:
            metrics.issues.append("Image is blurry")
            metrics.recommendations.append("Reshoot with better focus or stabilization")
        elif metrics.blur_score < 50:
            metrics.recommendations.append("Slight blur detected - may affect 3D detail")

        # Brightness issues
        if metrics.brightness_score < 40:
            metrics.issues.append("Poor lighting (too dark or too bright)")
            metrics.recommendations.append("Adjust lighting for even illumination")

        # Contrast issues
        if metrics.contrast_score < 30:
            metrics.issues.append("Low contrast")
            metrics.recommendations.append("Improve lighting contrast or post-process")

        # Color issues
        if metrics.color_richness_score < 40:
            metrics.recommendations.append("Colors appear washed out - check white balance")


class PhotoEvaluationReport:
    """Generates comprehensive photo evaluation report."""

    def __init__(self, evaluator: PhotoEvaluator) -> None:
        """Initialize report generator."""
        self.evaluator = evaluator
        self.metrics: list[PhotoMetrics] = []
        self.summaries: dict[str, CollectionSummary] = {}

    def evaluate_directory(
        self,
        directory: Path,
        collection: str | None = None,
    ) -> list[PhotoMetrics]:
        """Evaluate all photos in a directory.

        Args:
            directory: Directory containing photos
            collection: Collection name (inferred from path if not provided)

        Returns:
            List of PhotoMetrics
        """
        directory = Path(directory)
        if not directory.exists():
            logger.warning(f"Directory not found: {directory}")
            return []

        # Infer collection from path if not provided
        if collection is None:
            collection = directory.name

        results = []
        image_files = [
            f for f in directory.rglob("*") if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS
        ]

        logger.info(f"Evaluating {len(image_files)} photos in {directory}")

        for image_file in image_files:
            # Skip hidden files and renders
            if image_file.name.startswith(".") or ".renders" in str(image_file):
                continue

            metrics = self.evaluator.evaluate_photo(image_file, collection)
            results.append(metrics)
            self.metrics.append(metrics)

            # Log progress
            status_icon = "✓" if metrics.usable_for_3d else "✗"
            logger.debug(
                f"  {status_icon} {metrics.filename}: {metrics.quality.value} ({metrics.overall_score:.1f})"
            )

        return results

    def evaluate_collections(self, base_path: Path) -> dict[str, CollectionSummary]:
        """Evaluate all collections in base path.

        Args:
            base_path: Base directory containing collection subdirectories

        Returns:
            Dictionary of collection summaries
        """
        base_path = Path(base_path)
        collections = ["signature", "black-rose", "love-hurts"]

        for collection in collections:
            collection_path = base_path / collection
            if collection_path.exists():
                self.evaluate_directory(collection_path, collection)

        return self._compute_summaries()

    def _compute_summaries(self) -> dict[str, CollectionSummary]:
        """Compute summaries by collection."""
        from collections import defaultdict

        by_collection = defaultdict(list)
        for m in self.metrics:
            by_collection[m.collection].append(m)

        self.summaries = {}
        for collection, photos in by_collection.items():
            summary = CollectionSummary(collection=collection)
            summary.total_photos = len(photos)

            scores = []
            for p in photos:
                if p.error:
                    continue
                scores.append(p.overall_score)

                if p.quality == PhotoQuality.EXCELLENT:
                    summary.excellent += 1
                elif p.quality == PhotoQuality.GOOD:
                    summary.good += 1
                elif p.quality == PhotoQuality.FAIR:
                    summary.fair += 1
                elif p.quality == PhotoQuality.POOR:
                    summary.poor += 1
                else:
                    summary.unusable += 1

                if p.usable_for_3d:
                    summary.usable_for_3d += 1

            summary.average_score = sum(scores) / len(scores) if scores else 0.0
            self.summaries[collection] = summary

        return self.summaries

    def get_priority_photos(self, limit: int = 20) -> list[PhotoMetrics]:
        """Get top priority photos for 3D generation.

        Returns photos sorted by quality score that are usable for 3D.
        """
        usable = [m for m in self.metrics if m.usable_for_3d]
        usable.sort(key=lambda x: x.overall_score, reverse=True)
        return usable[:limit]

    def generate_report(self, output_path: Path | None = None) -> dict[str, Any]:
        """Generate comprehensive evaluation report.

        Args:
            output_path: Path to save JSON report

        Returns:
            Report dictionary
        """
        self._compute_summaries()

        report = {
            "generated_at": datetime.utcnow().isoformat(),
            "total_photos": len(self.metrics),
            "usable_for_3d": sum(1 for m in self.metrics if m.usable_for_3d),
            "summaries": {
                name: {
                    "total": s.total_photos,
                    "excellent": s.excellent,
                    "good": s.good,
                    "fair": s.fair,
                    "poor": s.poor,
                    "unusable": s.unusable,
                    "usable_for_3d": s.usable_for_3d,
                    "average_score": round(s.average_score, 2),
                }
                for name, s in self.summaries.items()
            },
            "priority_photos": [
                {
                    "path": str(m.path),
                    "collection": m.collection,
                    "score": round(m.overall_score, 2),
                    "quality": m.quality.value,
                    "dimensions": f"{m.width}x{m.height}",
                }
                for m in self.get_priority_photos(20)
            ],
            "photos_needing_reshoot": [
                {
                    "path": str(m.path),
                    "collection": m.collection,
                    "score": round(m.overall_score, 2),
                    "issues": m.issues,
                    "recommendations": m.recommendations,
                }
                for m in self.metrics
                if m.quality in (PhotoQuality.POOR, PhotoQuality.UNUSABLE)
            ],
            "all_photos": [
                {
                    "path": str(m.path),
                    "filename": m.filename,
                    "collection": m.collection,
                    "dimensions": f"{m.width}x{m.height}",
                    "megapixels": round(m.megapixels, 2),
                    "scores": {
                        "resolution": round(m.resolution_score, 2),
                        "sharpness": round(m.blur_score, 2),
                        "brightness": round(m.brightness_score, 2),
                        "contrast": round(m.contrast_score, 2),
                        "color": round(m.color_richness_score, 2),
                        "overall": round(m.overall_score, 2),
                    },
                    "quality": m.quality.value,
                    "usable_for_3d": m.usable_for_3d,
                    "issues": m.issues,
                    "recommendations": m.recommendations,
                    "error": m.error,
                }
                for m in sorted(self.metrics, key=lambda x: x.overall_score, reverse=True)
            ],
        }

        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w") as f:
                json.dump(report, f, indent=2)
            logger.info(f"Report saved to: {output_path}")

        return report


def main() -> None:
    """Run photo evaluation CLI."""
    parser = argparse.ArgumentParser(description="Evaluate product photos for 3D generation")
    parser.add_argument(
        "--collection",
        choices=["signature", "black-rose", "love-hurts"],
        help="Evaluate specific collection",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Evaluate all collections",
    )
    parser.add_argument(
        "--path",
        type=Path,
        help="Evaluate specific directory",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("assets/PHOTO_EVALUATION_REPORT.json"),
        help="Output report path",
    )

    args = parser.parse_args()

    if not any([args.collection, args.all, args.path]):
        print("Please specify --collection, --all, or --path")
        parser.print_help()
        sys.exit(1)

    evaluator = PhotoEvaluator()
    report_gen = PhotoEvaluationReport(evaluator)

    base_path = Path("assets/3d-models")

    if args.all:
        report_gen.evaluate_collections(base_path)
    elif args.collection:
        collection_path = base_path / args.collection
        report_gen.evaluate_directory(collection_path, args.collection)
    elif args.path:
        report_gen.evaluate_directory(args.path)

    # Generate and save report
    report = report_gen.generate_report(args.output)

    # Print summary
    print("\n" + "=" * 60)
    print("PHOTO EVALUATION SUMMARY")
    print("=" * 60)

    total = report["total_photos"]
    usable = report["usable_for_3d"]
    print(f"\nTotal photos evaluated: {total}")
    print(f"Usable for 3D generation: {usable} ({usable / total * 100:.1f}%)" if total > 0 else "")

    print("\nBy Collection:")
    for name, summary in report["summaries"].items():
        print(f"\n  {name.upper()}:")
        print(f"    Total: {summary['total']}")
        print(f"    Excellent: {summary['excellent']}")
        print(f"    Good: {summary['good']}")
        print(f"    Fair: {summary['fair']}")
        print(f"    Poor: {summary['poor']}")
        print(f"    Unusable: {summary['unusable']}")
        print(f"    Ready for 3D: {summary['usable_for_3d']}")
        print(f"    Average Score: {summary['average_score']:.1f}")

    print("\n" + "=" * 60)
    print(f"Top {len(report['priority_photos'])} Priority Photos:")
    print("=" * 60)
    for i, photo in enumerate(report["priority_photos"][:10], 1):
        print(f"  {i}. {photo['path'].split('/')[-1]} ({photo['score']:.1f}) - {photo['quality']}")

    reshoot_count = len(report["photos_needing_reshoot"])
    if reshoot_count > 0:
        print(f"\nPhotos needing reshoot: {reshoot_count}")

    print(f"\nFull report saved to: {args.output}")


if __name__ == "__main__":
    main()
