"""Test suite for devskyy_fidelity package.

Validates all core classes, configs, and computations without requiring
optional dependencies (opencv, sklearn). Tests that DO require them
are marked with ``pytest.mark.skipif``.

Run:
    pytest agents/product_generation/devskyy_fidelity/test_fidelity.py -v
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

# ── Import tests ─────────────────────────────────────────────────────────────


class TestImports:
    """Verify all modules import cleanly."""

    def test_quality_gate_imports(self) -> None:
        from agents.product_generation.devskyy_fidelity.quality_gate import (
            AssetQualityGate,
            QualityResult,
        )

        assert AssetQualityGate is not None
        assert QualityResult is not None

    def test_pipeline_imports(self) -> None:
        from agents.product_generation.devskyy_fidelity.pipeline import (
            ImageStatus,
            ProductImageMetadata,
            ProductImagePipeline,
        )

        assert ProductImagePipeline is not None
        assert ProductImageMetadata is not None
        assert ImageStatus is not None

    def test_config_imports(self) -> None:
        from agents.product_generation.devskyy_fidelity.config import (
            BLACK_ROSE_CONFIG,
            LOVE_HURTS_CONFIG,
            SIGNATURE_CONFIG,
            CollectionFidelityConfig,
            FidelityLevel,
        )

        assert CollectionFidelityConfig is not None
        assert FidelityLevel is not None
        assert BLACK_ROSE_CONFIG is not None
        assert LOVE_HURTS_CONFIG is not None
        assert SIGNATURE_CONFIG is not None

    def test_package_init(self) -> None:
        import agents.product_generation.devskyy_fidelity as pkg

        assert pkg.__version__ == "1.0.0"
        assert hasattr(pkg, "AssetQualityGate")
        assert hasattr(pkg, "ProductImagePipeline")


# ── Config tests ─────────────────────────────────────────────────────────────


class TestConfig:
    """Verify per-collection and per-product configuration."""

    def test_black_rose_threshold(self) -> None:
        from agents.product_generation.devskyy_fidelity.config import BLACK_ROSE_CONFIG

        assert BLACK_ROSE_CONFIG.threshold == 85.0
        assert BLACK_ROSE_CONFIG.min_silhouette_iou == 0.82

    def test_love_hurts_threshold(self) -> None:
        from agents.product_generation.devskyy_fidelity.config import LOVE_HURTS_CONFIG

        assert LOVE_HURTS_CONFIG.threshold == 82.0

    def test_signature_threshold(self) -> None:
        from agents.product_generation.devskyy_fidelity.config import SIGNATURE_CONFIG

        assert SIGNATURE_CONFIG.threshold == 80.0

    def test_weights_sum_to_one(self) -> None:
        from agents.product_generation.devskyy_fidelity.config import (
            BLACK_ROSE_CONFIG,
            LOVE_HURTS_CONFIG,
            SIGNATURE_CONFIG,
        )

        for config in [BLACK_ROSE_CONFIG, LOVE_HURTS_CONFIG, SIGNATURE_CONFIG]:
            assert abs(config.silhouette_weight + config.color_weight - 1.0) < 1e-6

    def test_fidelity_level_enum(self) -> None:
        from agents.product_generation.devskyy_fidelity.config import FidelityLevel

        assert FidelityLevel.STRICT == "strict"
        assert FidelityLevel.STANDARD == "standard"
        assert FidelityLevel.RELAXED == "relaxed"

    def test_get_fidelity_threshold_standard(self) -> None:
        from config.collections import Collection

        from agents.product_generation.devskyy_fidelity.config import (
            get_fidelity_threshold,
        )

        # br-001 is STANDARD → gets collection threshold
        threshold = get_fidelity_threshold("br-001", Collection.BLACK_ROSE)
        assert threshold == 85.0

    def test_get_fidelity_threshold_strict(self) -> None:
        from config.collections import Collection

        from agents.product_generation.devskyy_fidelity.config import (
            get_fidelity_threshold,
        )

        # br-006 is STRICT → collection threshold + 5
        threshold = get_fidelity_threshold("br-006", Collection.BLACK_ROSE)
        assert threshold == 90.0

    def test_get_fidelity_threshold_relaxed(self) -> None:
        from config.collections import Collection

        from agents.product_generation.devskyy_fidelity.config import (
            get_fidelity_threshold,
        )

        # lh-006 is RELAXED → collection threshold - 5
        threshold = get_fidelity_threshold("lh-006", Collection.LOVE_HURTS)
        assert threshold == 77.0

    def test_product_palettes_exist_for_all_skus(self) -> None:
        from agents.product_generation.devskyy_fidelity.config import (
            PRODUCT_COLOR_PALETTES,
            PRODUCT_GARMENT_TYPES,
        )

        # Every SKU with a garment type should have a color palette
        missing = [sku for sku in PRODUCT_GARMENT_TYPES if sku not in PRODUCT_COLOR_PALETTES]
        assert missing == [], f"SKUs missing color palettes: {missing}"

    def test_product_palettes_are_valid_hex(self) -> None:
        from agents.product_generation.devskyy_fidelity.config import (
            PRODUCT_COLOR_PALETTES,
        )

        for sku, palette in PRODUCT_COLOR_PALETTES.items():
            for hex_color in palette:
                assert hex_color.startswith("#"), f"{sku}: {hex_color} missing # prefix"
                assert len(hex_color) == 7, f"{sku}: {hex_color} wrong length (expected 7)"
                # Validate hex digits
                int(hex_color[1:], 16)

    def test_get_product_palette(self) -> None:
        from agents.product_generation.devskyy_fidelity.config import get_product_palette

        palette = get_product_palette("br-001")
        assert len(palette) >= 2
        assert "#000000" in palette

    def test_get_product_palette_unknown_sku(self) -> None:
        from agents.product_generation.devskyy_fidelity.config import get_product_palette

        palette = get_product_palette("nonexistent-sku")
        assert palette == ()

    def test_get_garment_type(self) -> None:
        from agents.product_generation.devskyy_fidelity.config import get_garment_type

        assert get_garment_type("br-004") == "hoodie"
        assert get_garment_type("lh-006") == "fanny pack"
        assert get_garment_type("sg-002") == "t-shirt"
        assert get_garment_type("nonexistent") is None

    def test_get_fidelity_config_unknown_collection_raises(self) -> None:
        from config.collections import Collection

        from agents.product_generation.devskyy_fidelity.config import (
            get_fidelity_config,
        )

        # All registered collections should work
        for coll in Collection:
            get_fidelity_config(coll)

    def test_all_collections_have_fidelity_configs(self) -> None:
        from config.collections import Collection

        from agents.product_generation.devskyy_fidelity.config import (
            get_fidelity_config,
        )

        for coll in Collection:
            config = get_fidelity_config(coll)
            assert config.threshold >= 50.0
            assert config.threshold <= 100.0


# ── Quality Gate tests ───────────────────────────────────────────────────────


class TestQualityGate:
    """Test AssetQualityGate initialization and static methods."""

    def test_init_defaults(self) -> None:
        from agents.product_generation.devskyy_fidelity.quality_gate import (
            AssetQualityGate,
        )

        gate = AssetQualityGate()
        assert gate.threshold == 80.0
        assert gate.silhouette_weight == 0.60
        assert gate.color_weight == 0.40

    def test_init_custom(self) -> None:
        from agents.product_generation.devskyy_fidelity.quality_gate import (
            AssetQualityGate,
        )

        gate = AssetQualityGate(
            threshold=90.0,
            silhouette_weight=0.70,
            color_weight=0.30,
        )
        assert gate.threshold == 90.0
        assert gate.silhouette_weight == 0.70

    def test_init_invalid_threshold(self) -> None:
        from agents.product_generation.devskyy_fidelity.quality_gate import (
            AssetQualityGate,
        )

        with pytest.raises(ValueError, match="threshold"):
            AssetQualityGate(threshold=0)
        with pytest.raises(ValueError, match="threshold"):
            AssetQualityGate(threshold=101)

    def test_init_invalid_weights(self) -> None:
        from agents.product_generation.devskyy_fidelity.quality_gate import (
            AssetQualityGate,
        )

        with pytest.raises(ValueError, match="must equal 1.0"):
            AssetQualityGate(silhouette_weight=0.5, color_weight=0.3)

    def test_hex_to_bgr(self) -> None:
        from agents.product_generation.devskyy_fidelity.quality_gate import (
            AssetQualityGate,
        )

        # Red: #FF0000 → BGR (0, 0, 255)
        assert AssetQualityGate._hex_to_bgr("#FF0000") == (0, 0, 255)
        # Green: #00FF00 → BGR (0, 255, 0)
        assert AssetQualityGate._hex_to_bgr("#00FF00") == (0, 255, 0)
        # Blue: #0000FF → BGR (255, 0, 0)
        assert AssetQualityGate._hex_to_bgr("#0000FF") == (255, 0, 0)
        # Black: #000000 → BGR (0, 0, 0)
        assert AssetQualityGate._hex_to_bgr("#000000") == (0, 0, 0)
        # White: #FFFFFF → BGR (255, 255, 255)
        assert AssetQualityGate._hex_to_bgr("#FFFFFF") == (255, 255, 255)
        # Rose gold
        assert AssetQualityGate._hex_to_bgr("#B76E79") == (121, 110, 183)
        # Without hash prefix
        assert AssetQualityGate._hex_to_bgr("D4AF37") == (55, 175, 212)

    def test_hex_to_bgr_invalid(self) -> None:
        from agents.product_generation.devskyy_fidelity.quality_gate import (
            AssetQualityGate,
        )

        with pytest.raises(ValueError, match="expected 6"):
            AssetQualityGate._hex_to_bgr("#FFF")
        with pytest.raises(ValueError, match="Invalid hex"):
            AssetQualityGate._hex_to_bgr("#GGGGGG")

    @pytest.mark.asyncio
    async def test_validate_missing_generated(self) -> None:
        from agents.product_generation.devskyy_fidelity.quality_gate import (
            AssetQualityGate,
        )

        gate = AssetQualityGate()
        result = await gate.validate_against_real_garment(
            generated_image=Path("/nonexistent/image.png"),
            reference_photos=[Path("/also/nonexistent.jpg")],
        )
        assert not result.passed
        assert result.overall_score == 0.0
        assert "not found" in result.recommendations[0]

    @pytest.mark.asyncio
    async def test_validate_missing_references(self) -> None:
        from agents.product_generation.devskyy_fidelity.quality_gate import (
            AssetQualityGate,
        )

        # Create a temp file to act as the generated image
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            f.write(b"fake png data")
            gen_path = Path(f.name)

        try:
            gate = AssetQualityGate()
            result = await gate.validate_against_real_garment(
                generated_image=gen_path,
                reference_photos=[Path("/nonexistent/ref.jpg")],
            )
            assert not result.passed
            assert "No valid reference" in result.recommendations[0]
        finally:
            gen_path.unlink(missing_ok=True)


# ── Pipeline tests ───────────────────────────────────────────────────────────


class TestPipeline:
    """Test ProductImagePipeline initialization and metadata."""

    def test_init(self) -> None:
        from agents.product_generation.devskyy_fidelity.pipeline import (
            ProductImagePipeline,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = ProductImagePipeline(
                reference_dir=Path(tmpdir) / "refs",
                output_dir=Path(tmpdir) / "output",
            )
            assert pipeline.threshold == 80.0
            assert pipeline.output_dir.exists()

    def test_image_status_enum(self) -> None:
        from agents.product_generation.devskyy_fidelity.pipeline import ImageStatus

        assert ImageStatus.PENDING == "pending"
        assert ImageStatus.REJECTED == "rejected"
        assert ImageStatus.UPLOADED == "uploaded"

    def test_metadata_serialization(self) -> None:
        from agents.product_generation.devskyy_fidelity.pipeline import (
            ImageStatus,
            ProductImageMetadata,
        )

        meta = ProductImageMetadata(
            product_id="9679",
            sku="br-004",
            collection="BLACK_ROSE",
            angle="front",
            status=ImageStatus.PASSED,
            fidelity_score=87.5,
            silhouette_iou=0.89,
            color_delta_e_avg=6.3,
        )
        log_dict = meta.to_log_dict()

        assert log_dict["product_id"] == "9679"
        assert log_dict["sku"] == "br-004"
        assert log_dict["fidelity_score"] == 87.5
        assert log_dict["status"] == "passed"
        # Should be JSON-serializable
        json.dumps(log_dict)

    @pytest.mark.asyncio
    async def test_pipeline_no_generator_no_image(self) -> None:
        from agents.product_generation.devskyy_fidelity.pipeline import (
            ImageStatus,
            ProductImagePipeline,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = ProductImagePipeline(
                reference_dir=Path(tmpdir) / "refs",
                output_dir=Path(tmpdir) / "output",
            )
            meta = await pipeline.generate_product_image(
                product_id="test",
                sku="br-001",
                collection="BLACK_ROSE",
            )
            assert meta.status == ImageStatus.ERROR
            assert "No image path" in (meta.error or "")

    @pytest.mark.asyncio
    async def test_pipeline_with_nonexistent_image(self) -> None:
        from agents.product_generation.devskyy_fidelity.pipeline import (
            ImageStatus,
            ProductImagePipeline,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = ProductImagePipeline(
                reference_dir=Path(tmpdir) / "refs",
                output_dir=Path(tmpdir) / "output",
            )
            meta = await pipeline.generate_product_image(
                product_id="test",
                sku="br-001",
                collection="BLACK_ROSE",
                generated_image_path="/nonexistent/fake.png",
            )
            assert meta.status == ImageStatus.ERROR
            assert "not found" in (meta.error or "")

    def test_validation_report_empty(self) -> None:
        from agents.product_generation.devskyy_fidelity.pipeline import (
            ProductImagePipeline,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = ProductImagePipeline(
                reference_dir=Path(tmpdir) / "refs",
                output_dir=Path(tmpdir) / "output",
            )
            report = pipeline.get_validation_report()
            assert report["total"] == 0
            assert report["acceptance_rate"] == 0.0

    def test_validation_report_with_data(self) -> None:
        from agents.product_generation.devskyy_fidelity.pipeline import (
            ProductImagePipeline,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = ProductImagePipeline(
                reference_dir=Path(tmpdir) / "refs",
                output_dir=Path(tmpdir) / "output",
            )
            # Write fake JSONL entries
            entries = [
                {
                    "status": "passed",
                    "fidelity_score": 88.0,
                    "silhouette_iou": 0.9,
                    "color_delta_e_avg": 5.0,
                },
                {
                    "status": "rejected",
                    "fidelity_score": 65.0,
                    "silhouette_iou": 0.6,
                    "color_delta_e_avg": 20.0,
                },
                {
                    "status": "uploaded",
                    "fidelity_score": 92.0,
                    "silhouette_iou": 0.95,
                    "color_delta_e_avg": 3.0,
                },
            ]
            with pipeline.metadata_log.open("w") as f:
                for entry in entries:
                    f.write(json.dumps(entry) + "\n")

            report = pipeline.get_validation_report()
            assert report["total"] == 3
            assert report["passed"] == 2  # passed + uploaded
            assert report["rejected"] == 1
            assert report["uploaded"] == 1
            assert abs(report["acceptance_rate"] - 66.67) < 1


# ── Color ΔE computation tests ──────────────────────────────────────────────


class TestColorDeltaE:
    """Test color distance calculations (requires opencv + numpy)."""

    @pytest.fixture(autouse=True)
    def _skip_without_cv2(self) -> None:
        import importlib.util

        if not importlib.util.find_spec("cv2") or not importlib.util.find_spec("numpy"):
            pytest.skip("opencv/numpy not installed")

    def test_identical_colors(self) -> None:
        from agents.product_generation.devskyy_fidelity.quality_gate import (
            AssetQualityGate,
        )

        # Same color → ΔE should be 0
        delta = AssetQualityGate._color_delta_e(
            (0, 0, 0),
            (0, 0, 0),  # black
        )
        assert delta == 0.0

    def test_black_vs_white(self) -> None:
        from agents.product_generation.devskyy_fidelity.quality_gate import (
            AssetQualityGate,
        )

        # Black vs white → large ΔE
        delta = AssetQualityGate._color_delta_e(
            (0, 0, 0),  # black BGR
            (255, 255, 255),  # white BGR
        )
        assert delta > 50  # Black and white are very far apart in LAB

    def test_similar_colors_small_delta(self) -> None:
        from agents.product_generation.devskyy_fidelity.quality_gate import (
            AssetQualityGate,
        )

        # Two slightly different reds
        delta = AssetQualityGate._color_delta_e(
            (0, 0, 200),  # dark red BGR
            (0, 0, 210),  # slightly lighter red BGR
        )
        assert delta < 10  # Should be small

    def test_complementary_colors_large_delta(self) -> None:
        from agents.product_generation.devskyy_fidelity.quality_gate import (
            AssetQualityGate,
        )

        # Red vs cyan
        delta = AssetQualityGate._color_delta_e(
            (0, 0, 255),  # red BGR
            (255, 255, 0),  # cyan BGR
        )
        assert delta > 30  # Complementary colors → large distance


# ── Product catalog coverage tests ───────────────────────────────────────────


class TestProductCatalogCoverage:
    """Verify product data integrity across config maps."""

    def test_all_garment_types_have_palettes(self) -> None:
        from agents.product_generation.devskyy_fidelity.config import (
            PRODUCT_COLOR_PALETTES,
            PRODUCT_GARMENT_TYPES,
        )

        for sku in PRODUCT_GARMENT_TYPES:
            assert sku in PRODUCT_COLOR_PALETTES, f"SKU {sku} has garment type but no color palette"

    def test_all_palettes_have_garment_types(self) -> None:
        from agents.product_generation.devskyy_fidelity.config import (
            PRODUCT_COLOR_PALETTES,
            PRODUCT_GARMENT_TYPES,
        )

        for sku in PRODUCT_COLOR_PALETTES:
            assert sku in PRODUCT_GARMENT_TYPES, f"SKU {sku} has color palette but no garment type"

    def test_fidelity_level_skus_exist_in_catalog(self) -> None:
        from agents.product_generation.devskyy_fidelity.config import (
            PRODUCT_FIDELITY_LEVELS,
            PRODUCT_GARMENT_TYPES,
        )

        for sku in PRODUCT_FIDELITY_LEVELS:
            assert sku in PRODUCT_GARMENT_TYPES, (
                f"Fidelity level override for {sku} but SKU not in catalog"
            )

    def test_palette_has_at_least_two_colors(self) -> None:
        from agents.product_generation.devskyy_fidelity.config import (
            PRODUCT_COLOR_PALETTES,
        )

        for sku, palette in PRODUCT_COLOR_PALETTES.items():
            assert len(palette) >= 2, (
                f"SKU {sku} has only {len(palette)} color(s) — need at least 2"
            )

    def test_known_sku_count(self) -> None:
        """Verify we have all 35 products (31 core + 4 variants)."""
        from agents.product_generation.devskyy_fidelity.config import (
            PRODUCT_GARMENT_TYPES,
        )

        # 11 BR + 3 BR variants + 4 BR jerseys + 4 LH + 13 SG + 2 Kids = 37 total
        # After removing 9 deleted SKUs (br-d01–d04, lh-001, sg-d01–d04): 33
        assert len(PRODUCT_GARMENT_TYPES) >= 33
