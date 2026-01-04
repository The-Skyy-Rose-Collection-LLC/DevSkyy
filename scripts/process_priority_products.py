#!/usr/bin/env python3
"""Process Priority Products Pipeline.

End-to-end pipeline for processing priority products:
1. Find best source photo for each product
2. Evaluate photo quality
3. Enhance if needed
4. Generate 3D model with quality gate validation
5. Upload to WordPress if passes 90% fidelity threshold

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from imagery.quality_gate import AssetQualityGate, QualityGateResult
from imagery.visual_comparison import VisualComparisonEngine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@dataclass
class ProductConfig:
    """Configuration for a priority product."""

    name: str
    source_pattern: str
    garment_type: str
    priority: int
    collection: str


@dataclass
class ProcessingResult:
    """Result of processing a single product."""

    product: ProductConfig
    status: str  # success, failed, skipped
    source_photo: Path | None = None
    photo_quality_score: float | None = None
    enhanced_photo: Path | None = None
    generated_model: Path | None = None
    fidelity_score: float | None = None
    wordpress_uploaded: bool = False
    wordpress_url: str | None = None
    error: str | None = None
    processing_time_ms: float = 0.0


@dataclass
class PipelineReport:
    """Report for entire pipeline run."""

    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    total_products: int = 0
    successful: int = 0
    failed: int = 0
    skipped: int = 0
    results: list[ProcessingResult] = field(default_factory=list)
    settings: dict[str, Any] = field(default_factory=dict)


class PriorityProductsPipeline:
    """End-to-end pipeline for priority product processing.

    Orchestrates:
    - Photo discovery and evaluation
    - Optional enhancement
    - 3D model generation
    - Quality gate validation (90% threshold)
    - WordPress upload
    """

    def __init__(
        self,
        config_path: Path,
        photos_dir: Path,
        output_dir: Path,
        fidelity_threshold: float = 90.0,
        dry_run: bool = False,
    ) -> None:
        """Initialize pipeline.

        Args:
            config_path: Path to priority_products.yaml
            photos_dir: Directory containing product photos
            output_dir: Directory for generated assets
            fidelity_threshold: Minimum fidelity score (0-100)
            dry_run: If True, skip actual generation/upload
        """
        self.config_path = config_path
        self.photos_dir = photos_dir
        self.output_dir = output_dir
        self.fidelity_threshold = fidelity_threshold
        self.dry_run = dry_run

        self.quality_gate = AssetQualityGate(
            threshold=fidelity_threshold,
            strict_mode=False,
        )
        self.comparator = VisualComparisonEngine(threshold=fidelity_threshold)

        self.products: list[ProductConfig] = []
        self.report = PipelineReport()

    def load_config(self) -> None:
        """Load priority products from YAML config."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config not found: {self.config_path}")

        with open(self.config_path) as f:
            config = yaml.safe_load(f)

        self.report.settings = config.get("settings", {})

        # Parse collections
        collections = config.get("collections", {})
        for collection_name, products in collections.items():
            for product in products:
                self.products.append(
                    ProductConfig(
                        name=product["name"],
                        source_pattern=product["source_pattern"],
                        garment_type=product["garment_type"],
                        priority=product["priority"],
                        collection=collection_name,
                    )
                )

        # Sort by priority
        self.products.sort(key=lambda p: (p.collection, p.priority))
        self.report.total_products = len(self.products)

        logger.info(f"Loaded {len(self.products)} priority products from config")

    def find_source_photo(self, product: ProductConfig) -> Path | None:
        """Find the best source photo for a product.

        Searches photos_dir for files matching the product's source_pattern.
        Returns the highest resolution match.
        """
        import glob

        pattern = str(self.photos_dir / "**" / product.source_pattern)
        matches = glob.glob(pattern, recursive=True)

        if not matches:
            logger.warning(f"No photos found for {product.name} ({product.source_pattern})")
            return None

        # Sort by file size (proxy for resolution)
        matches.sort(key=lambda p: Path(p).stat().st_size, reverse=True)

        best_match = Path(matches[0])
        logger.info(f"Found source photo for {product.name}: {best_match.name}")
        return best_match

    async def evaluate_photo_quality(self, photo_path: Path) -> dict[str, Any]:
        """Evaluate photo quality for 3D generation suitability.

        Returns quality metrics and overall score.
        """
        try:
            import cv2
            import numpy as np

            img = cv2.imread(str(photo_path))
            if img is None:
                return {"score": 0.0, "error": "Failed to load image"}

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            height, width = gray.shape

            # Blur detection (Laplacian variance)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            blur_score = min(100, laplacian_var / 5)  # Normalize

            # Brightness
            brightness = np.mean(gray)
            brightness_score = 100 - abs(brightness - 128) / 1.28

            # Contrast
            contrast = gray.std()
            contrast_score = min(100, contrast * 2)

            # Resolution
            resolution = width * height
            resolution_score = min(100, resolution / 20000)  # 2000x1000 = 100

            # Overall score
            overall = (
                blur_score * 0.35
                + brightness_score * 0.20
                + contrast_score * 0.20
                + resolution_score * 0.25
            )

            return {
                "score": round(overall, 2),
                "blur_score": round(blur_score, 2),
                "brightness_score": round(brightness_score, 2),
                "contrast_score": round(contrast_score, 2),
                "resolution_score": round(resolution_score, 2),
                "resolution": f"{width}x{height}",
                "suitable_for_3d": overall >= 70,
            }

        except Exception as e:
            logger.error(f"Photo evaluation error: {e}")
            return {"score": 0.0, "error": str(e)}

    async def enhance_photo(self, photo_path: Path, output_path: Path) -> Path | None:
        """Enhance photo for better 3D generation.

        Uses basic enhancement techniques. For production, integrate
        with AI enhancement services.
        """
        try:
            import cv2
            import numpy as np

            img = cv2.imread(str(photo_path))
            if img is None:
                return None

            # Apply CLAHE for contrast enhancement
            lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
            l_channel, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            l_enhanced = clahe.apply(l_channel)
            enhanced_lab = cv2.merge([l_enhanced, a, b])
            enhanced = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)

            # Slight sharpening
            kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
            enhanced = cv2.filter2D(enhanced, -1, kernel)

            output_path.parent.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(output_path), enhanced)

            logger.info(f"Enhanced photo saved: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Enhancement error: {e}")
            return None

    async def generate_3d_model(
        self,
        photo_path: Path,
        product: ProductConfig,
    ) -> Path | None:
        """Generate 3D model from photo using Tripo3D.

        This integrates with the existing agents/tripo_agent.py
        """
        if self.dry_run:
            logger.info(f"[DRY RUN] Would generate 3D for {product.name}")
            return None

        try:
            # Import Tripo agent
            from agents.tripo_agent import TripoAgent

            output_path = (
                self.output_dir
                / product.collection
                / f"{product.name.lower().replace(' ', '_')}.glb"
            )
            output_path.parent.mkdir(parents=True, exist_ok=True)

            agent = TripoAgent()

            # Generate from image
            result = await agent.generate_from_image(
                image_path=str(photo_path),
                output_path=str(output_path),
                product_type=product.garment_type,
            )

            if result and output_path.exists():
                logger.info(f"Generated 3D model: {output_path}")
                return output_path

            logger.error(f"3D generation failed for {product.name}")
            return None

        except ImportError:
            logger.warning("TripoAgent not available, skipping 3D generation")
            return None
        except Exception as e:
            logger.error(f"3D generation error for {product.name}: {e}")
            return None

    async def validate_fidelity(
        self,
        model_path: Path,
        reference_photo: Path,
    ) -> QualityGateResult:
        """Validate 3D model fidelity against reference photo."""
        return await self.quality_gate.validate_3d_model(model_path, reference_photo)

    async def upload_to_wordpress(
        self,
        model_path: Path,
        product: ProductConfig,
    ) -> str | None:
        """Upload validated 3D model to WordPress.

        Returns the WordPress URL if successful.
        """
        if self.dry_run:
            logger.info(f"[DRY RUN] Would upload {model_path.name} to WordPress")
            return "https://example.com/dry-run"

        try:
            from wordpress.client import WordPressClient

            client = WordPressClient()

            # Upload as media
            result = await client.upload_media(
                file_path=str(model_path),
                title=f"{product.name} 3D Model",
                alt_text=f"3D model of {product.name} from {product.collection} collection",
            )

            if result and "url" in result:
                logger.info(f"Uploaded to WordPress: {result['url']}")
                return result["url"]

            return None

        except ImportError:
            logger.warning("WordPress client not available")
            return None
        except Exception as e:
            logger.error(f"WordPress upload error: {e}")
            return None

    async def process_product(self, product: ProductConfig) -> ProcessingResult:
        """Process a single product through the entire pipeline."""
        import time

        start_time = time.time()
        result = ProcessingResult(product=product, status="pending")

        logger.info(f"\n{'='*60}")
        logger.info(f"Processing: {product.name} ({product.collection})")
        logger.info(f"{'='*60}")

        try:
            # Step 1: Find source photo
            source_photo = self.find_source_photo(product)
            if not source_photo:
                result.status = "skipped"
                result.error = "No source photo found"
                return result

            result.source_photo = source_photo

            # Step 2: Evaluate photo quality
            quality = await self.evaluate_photo_quality(source_photo)
            result.photo_quality_score = quality.get("score", 0)

            logger.info(f"Photo quality: {result.photo_quality_score:.1f}/100")

            # Step 3: Enhance if needed
            working_photo = source_photo
            if quality.get("score", 0) < 70:
                enhanced_path = self.output_dir / "enhanced" / source_photo.name
                enhanced = await self.enhance_photo(source_photo, enhanced_path)
                if enhanced:
                    result.enhanced_photo = enhanced
                    working_photo = enhanced
                    logger.info("Photo enhanced for better generation")

            # Step 4: Generate 3D model
            model_path = await self.generate_3d_model(working_photo, product)
            if not model_path:
                if self.dry_run:
                    result.status = "skipped"
                    result.error = "Dry run - generation skipped"
                else:
                    result.status = "failed"
                    result.error = "3D generation failed"
                return result

            result.generated_model = model_path

            # Step 5: Validate fidelity
            validation = await self.validate_fidelity(model_path, source_photo)
            result.fidelity_score = validation.score

            logger.info(
                f"Fidelity: {validation.score:.1f}% "
                f"(threshold: {self.fidelity_threshold}%) - {validation.status.value}"
            )

            if not validation.passed:
                result.status = "failed"
                result.error = f"Fidelity {validation.score:.1f}% < {self.fidelity_threshold}%"

                if validation.recommendations:
                    logger.warning(f"Recommendations: {validation.recommendations}")

                return result

            # Step 6: Upload to WordPress
            if self.report.settings.get("upload_to_wordpress", True):
                wp_url = await self.upload_to_wordpress(model_path, product)
                if wp_url:
                    result.wordpress_uploaded = True
                    result.wordpress_url = wp_url

            result.status = "success"

        except Exception as e:
            logger.exception(f"Pipeline error for {product.name}: {e}")
            result.status = "failed"
            result.error = str(e)

        finally:
            result.processing_time_ms = (time.time() - start_time) * 1000

        return result

    async def run(self) -> PipelineReport:
        """Run the complete pipeline for all priority products."""
        logger.info("\n" + "=" * 70)
        logger.info("PRIORITY PRODUCTS PIPELINE")
        logger.info(f"Fidelity threshold: {self.fidelity_threshold}%")
        logger.info(f"Dry run: {self.dry_run}")
        logger.info("=" * 70)

        self.load_config()

        for product in self.products:
            result = await self.process_product(product)
            self.report.results.append(result)

            if result.status == "success":
                self.report.successful += 1
            elif result.status == "failed":
                self.report.failed += 1
            else:
                self.report.skipped += 1

        self.report.completed_at = datetime.utcnow()

        # Print summary
        self._print_summary()

        return self.report

    def _print_summary(self) -> None:
        """Print pipeline summary."""
        logger.info("\n" + "=" * 70)
        logger.info("PIPELINE SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Total products: {self.report.total_products}")
        logger.info(f"Successful: {self.report.successful}")
        logger.info(f"Failed: {self.report.failed}")
        logger.info(f"Skipped: {self.report.skipped}")

        if self.report.results:
            logger.info("\nResults by product:")
            for r in self.report.results:
                status_emoji = {"success": "✓", "failed": "✗", "skipped": "○"}.get(r.status, "?")
                fidelity = f"{r.fidelity_score:.1f}%" if r.fidelity_score else "N/A"
                logger.info(
                    f"  {status_emoji} {r.product.name}: {r.status} " f"(fidelity: {fidelity})"
                )

                if r.error:
                    logger.info(f"      Error: {r.error}")

    def save_report(self, output_path: Path) -> None:
        """Save detailed report to JSON."""

        def serialize(obj: Any) -> Any:
            if isinstance(obj, datetime):
                return obj.isoformat()
            if isinstance(obj, Path):
                return str(obj)
            if hasattr(obj, "__dict__"):
                return {k: serialize(v) for k, v in obj.__dict__.items()}
            if isinstance(obj, list):
                return [serialize(i) for i in obj]
            if isinstance(obj, dict):
                return {k: serialize(v) for k, v in obj.items()}
            return obj

        report_dict = serialize(self.report)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(report_dict, f, indent=2)

        logger.info(f"\nReport saved: {output_path}")


async def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Process priority products through 3D pipeline with quality gate"
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config/priority_products.yaml"),
        help="Path to priority products config",
    )
    parser.add_argument(
        "--photos-dir",
        type=Path,
        default=Path("assets/product-photos"),
        help="Directory containing product photos",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("assets/3d-models-generated"),
        help="Output directory for generated assets",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=90.0,
        help="Minimum fidelity threshold (0-100)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without actual generation/upload",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("reports/priority_pipeline_report.json"),
        help="Path for output report",
    )

    args = parser.parse_args()

    pipeline = PriorityProductsPipeline(
        config_path=args.config,
        photos_dir=args.photos_dir,
        output_dir=args.output_dir,
        fidelity_threshold=args.threshold,
        dry_run=args.dry_run,
    )

    try:
        report = await pipeline.run()
        pipeline.save_report(args.report)

        # Exit code based on results
        if report.failed > 0:
            return 1
        return 0

    except Exception as e:
        logger.exception(f"Pipeline failed: {e}")
        return 2


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
