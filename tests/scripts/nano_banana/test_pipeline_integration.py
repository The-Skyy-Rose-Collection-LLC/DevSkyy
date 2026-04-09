"""Integration tests for the nano_banana async production pipeline.

Tests the 5-stage pipeline (vision -> route -> generate -> QA -> refine)
with mocked API clients. Verifies job state transitions, quality gates,
error isolation, and report generation.
"""

from __future__ import annotations

import asyncio
import io
import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Import targets — these live under scripts/nano_banana/
from nano_banana.produce_async import ImageJob, run_production, safe_thread
from nano_banana.tournament import JudgmentScore, TournamentResult
from nano_banana.utils import quality_gate


def _make_fake_webp(size: tuple[int, int] = (500, 500)) -> bytes:
    """Generate a valid WebP image >15KB for quality_gate to pass.

    Uses random noise so WebP compression cannot shrink it below threshold.
    Solid-color images compress to ~500 bytes which fails the gate.
    """
    import random

    from PIL import Image

    random.seed(42)
    pixels = bytes(random.randint(0, 255) for _ in range(size[0] * size[1] * 3))
    img = Image.frombytes("RGB", size, pixels)
    buf = io.BytesIO()
    img.save(buf, format="WEBP", quality=95)
    return buf.getvalue()


def _make_small_webp() -> bytes:
    """Generate a tiny WebP image that will fail quality_gate (<15KB)."""
    from PIL import Image

    img = Image.new("RGB", (10, 10), "red")
    buf = io.BytesIO()
    img.save(buf, format="WEBP", quality=1)
    return buf.getvalue()


def _make_source_image(directory: Path, name: str = "source.jpg") -> Path:
    """Create a minimal JPEG source image in the given directory."""
    from PIL import Image

    path = directory / name
    img = Image.new("RGB", (100, 100), "green")
    img.save(path, format="JPEG")
    return path


def _make_tournament_result(
    score: float = 95.0,
    passed: bool = True,
    candidate_path: str = "/tmp/candidate.webp",
) -> TournamentResult:
    """Build a TournamentResult with sensible defaults."""
    judge = JudgmentScore(
        judge="mock-judge",
        garment_type=95,
        color_accuracy=95,
        text_accuracy=95,
        logo_accuracy=95,
        construction_accuracy=95,
        no_hallucinations=95,
        overall=int(score),
        issues=[],
        suggested_fixes=[],
    )
    return TournamentResult(
        candidate_path=candidate_path,
        judges=[judge],
        aggregate_score=score,
        passed_98=passed,
        top_issues=[],
        all_fixes=[],
    )


# ---------------------------------------------------------------------------
# Test 1: ImageJob dataclass
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestImageJob:
    """Verify ImageJob dataclass field defaults and state tracking."""

    def test_image_job_defaults(self):
        """Dataclass fields default correctly for a new job."""
        job = ImageJob(
            sku="br-001",
            name="Test Hoodie",
            collection="black-rose",
            view="front",
            source_path=Path("/tmp/src.jpg"),
            output_slug="test-hoodie",
        )
        assert job.status == "pending"
        assert job.qa_passed is False
        assert job.qa_score == 0.0
        assert job.vision == {}
        assert job.prompt == ""
        assert job.error == ""
        assert job.refined is False
        assert job.extra_refs == []
        assert job.output_path is None
        assert job.is_accessory is False

    def test_image_job_tracks_state(self):
        """Status transitions: pending -> generating -> qa_done."""
        job = ImageJob(
            sku="br-002",
            name="Test Jersey",
            collection="black-rose",
            view="front",
            source_path=Path("/tmp/src.jpg"),
            output_slug="test-jersey",
        )
        assert job.status == "pending"

        job.status = "generating"
        assert job.status == "generating"

        job.status = "qa_done"
        assert job.status == "qa_done"


# ---------------------------------------------------------------------------
# Test 2: safe_thread
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestSafeThread:
    """Verify safe_thread wraps sync functions with timeout + error handling."""

    def test_safe_thread_success(self):
        """Returns function result when it completes normally."""

        def add(a, b):
            return a + b

        result = asyncio.get_event_loop().run_until_complete(
            safe_thread(add, 3, 4, timeout=5, label="test-add")
        )
        assert result == 7

    def test_safe_thread_timeout(self):
        """Returns None on timeout without raising."""
        import time

        def slow():
            time.sleep(10)
            return "never"

        result = asyncio.get_event_loop().run_until_complete(
            safe_thread(slow, timeout=0.1, label="test-slow")
        )
        assert result is None

    def test_safe_thread_exception(self):
        """Returns None when function raises, does not propagate."""

        def boom():
            raise ValueError("kaboom")

        result = asyncio.get_event_loop().run_until_complete(
            safe_thread(boom, timeout=5, label="test-boom")
        )
        assert result is None


# ---------------------------------------------------------------------------
# Test 3: quality_gate
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestQualityGate:
    """Verify quality_gate size checks."""

    def test_quality_gate_valid_image(self):
        """Valid WebP bytes (>15KB threshold) passes."""
        big_bytes = _make_fake_webp()
        assert len(big_bytes) > 15 * 1024, "Fixture must be >15KB"
        assert quality_gate(big_bytes, "test-sku", "front") is True

    def test_quality_gate_too_small(self):
        """Bytes under MIN_FILE_SIZE_KB threshold fails."""
        small_bytes = _make_small_webp()
        assert len(small_bytes) < 15 * 1024, "Fixture must be <15KB"
        assert quality_gate(small_bytes, "test-sku", "front") is False

    def test_quality_gate_empty(self):
        """Empty bytes fails."""
        assert quality_gate(b"", "test-sku", "front") is False


# ---------------------------------------------------------------------------
# Test 4: Full pipeline (run_production)
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestFullPipeline:
    """Integration test for run_production with all external deps mocked."""

    def _build_product(self, source_path: Path, sku: str = "br-001") -> dict:
        return {
            "sku": sku,
            "name": "Test Hoodie",
            "collection": "black-rose",
            "is_accessory": False,
            "source_image": source_path,
            "output_slug": "test-hoodie",
        }

    def test_run_production_happy_path(self, tmp_path: Path):
        """Mock ALL external deps, run 1 product x 1 view, verify pass."""
        source = _make_source_image(tmp_path)
        product = self._build_product(source)
        fake_webp = _make_fake_webp()
        tournament = _make_tournament_result(score=95.0, passed=True)

        products_dir = tmp_path / "products"
        products_dir.mkdir()

        with (
            patch("nano_banana.client.get_genai_client", return_value=MagicMock()),
            patch("nano_banana.client.get_openai_client", return_value=MagicMock()),
            patch(
                "nano_banana.vision_describe.describe_product",
                return_value={"garment_type": "hoodie"},
            ),
            patch(
                "nano_banana.generate.generate_gemini_async",
                new_callable=AsyncMock,
                return_value=fake_webp,
            ),
            patch("nano_banana.tournament.run_tournament", return_value=tournament),
            patch("nano_banana.catalog.find_back_source", return_value=None),
            patch("nano_banana.catalog.get_material_spec", return_value=""),
            patch("nano_banana.router.route_product", return_value=[]),
            patch("nano_banana.prompts.get_prompt", return_value="Generate a test image"),
            patch("nano_banana.pipeline._find_bundle_dir", return_value=None),
            patch("nano_banana.pipeline._load_bundle_refs", return_value=[]),
            patch("nano_banana.produce_async.PROJECT_ROOT", tmp_path),
        ):
            # Create the output directory structure the pipeline expects
            out_dir = (
                tmp_path
                / "wordpress-theme"
                / "skyyrose-flagship"
                / "assets"
                / "images"
                / "products"
            )
            out_dir.mkdir(parents=True)
            data_dir = tmp_path / "data" / "product-vision"
            data_dir.mkdir(parents=True)
            report_dir = tmp_path / "data" / "verify-results"
            report_dir.mkdir(parents=True)

            jobs = asyncio.get_event_loop().run_until_complete(
                run_production(
                    products=[product],
                    views=["front"],
                    catalog={"br-001": product},
                    concurrency=1,
                )
            )

        assert len(jobs) == 1
        job = jobs[0]
        assert job.qa_passed is True
        assert job.status == "qa_done"
        assert job.output_path is not None
        assert job.output_path.exists()

    def test_run_production_generation_failure(self, tmp_path: Path):
        """Mock generate returns None -> job.status == 'failed'."""
        source = _make_source_image(tmp_path)
        product = self._build_product(source)

        with (
            patch("nano_banana.client.get_genai_client", return_value=MagicMock()),
            patch("nano_banana.client.get_openai_client", return_value=MagicMock()),
            patch(
                "nano_banana.vision_describe.describe_product",
                return_value={"garment_type": "hoodie"},
            ),
            patch(
                "nano_banana.generate.generate_gemini_async",
                new_callable=AsyncMock,
                return_value=None,
            ),
            patch("nano_banana.tournament.run_tournament", return_value=None),
            patch("nano_banana.catalog.find_back_source", return_value=None),
            patch("nano_banana.catalog.get_material_spec", return_value=""),
            patch("nano_banana.router.route_product", return_value=[]),
            patch("nano_banana.prompts.get_prompt", return_value="Generate a test image"),
            patch("nano_banana.pipeline._find_bundle_dir", return_value=None),
            patch("nano_banana.pipeline._load_bundle_refs", return_value=[]),
            patch("nano_banana.produce_async.PROJECT_ROOT", tmp_path),
        ):
            out_dir = (
                tmp_path
                / "wordpress-theme"
                / "skyyrose-flagship"
                / "assets"
                / "images"
                / "products"
            )
            out_dir.mkdir(parents=True)
            (tmp_path / "data" / "product-vision").mkdir(parents=True)
            (tmp_path / "data" / "verify-results").mkdir(parents=True)

            jobs = asyncio.get_event_loop().run_until_complete(
                run_production(
                    products=[product],
                    views=["front"],
                    catalog={"br-001": product},
                    concurrency=1,
                )
            )

        assert len(jobs) == 1
        assert jobs[0].status == "failed"

    def test_error_isolation(self, tmp_path: Path):
        """2 products: first generate raises, second succeeds -> batch continues."""
        source1 = _make_source_image(tmp_path, "source1.jpg")
        source2 = _make_source_image(tmp_path, "source2.jpg")

        product1 = {
            "sku": "br-err",
            "name": "Error Hoodie",
            "collection": "black-rose",
            "is_accessory": False,
            "source_image": source1,
            "output_slug": "error-hoodie",
        }
        product2 = {
            "sku": "br-ok",
            "name": "OK Hoodie",
            "collection": "black-rose",
            "is_accessory": False,
            "source_image": source2,
            "output_slug": "ok-hoodie",
        }

        fake_webp = _make_fake_webp()
        tournament = _make_tournament_result(score=95.0, passed=True)

        call_count = 0

        async def mock_generate(client, source_path, prompt, **kwargs):
            nonlocal call_count
            call_count += 1
            # First 3 calls (3 retries for product1) raise, rest succeed
            if str(source_path).endswith("source1.jpg"):
                raise RuntimeError("API exploded")
            return fake_webp

        with (
            patch("nano_banana.client.get_genai_client", return_value=MagicMock()),
            patch("nano_banana.client.get_openai_client", return_value=MagicMock()),
            patch(
                "nano_banana.vision_describe.describe_product",
                return_value={"garment_type": "hoodie"},
            ),
            patch("nano_banana.generate.generate_gemini_async", side_effect=mock_generate),
            patch("nano_banana.tournament.run_tournament", return_value=tournament),
            patch("nano_banana.catalog.find_back_source", return_value=None),
            patch("nano_banana.catalog.get_material_spec", return_value=""),
            patch("nano_banana.router.route_product", return_value=[]),
            patch("nano_banana.prompts.get_prompt", return_value="Generate a test image"),
            patch("nano_banana.pipeline._find_bundle_dir", return_value=None),
            patch("nano_banana.pipeline._load_bundle_refs", return_value=[]),
            patch("nano_banana.produce_async.PROJECT_ROOT", tmp_path),
        ):
            out_dir = (
                tmp_path
                / "wordpress-theme"
                / "skyyrose-flagship"
                / "assets"
                / "images"
                / "products"
            )
            out_dir.mkdir(parents=True)
            (tmp_path / "data" / "product-vision").mkdir(parents=True)
            (tmp_path / "data" / "verify-results").mkdir(parents=True)

            jobs = asyncio.get_event_loop().run_until_complete(
                run_production(
                    products=[product1, product2],
                    views=["front"],
                    catalog={"br-err": product1, "br-ok": product2},
                    concurrency=2,
                )
            )

        assert len(jobs) == 2
        statuses = {j.sku: j.status for j in jobs}
        assert statuses["br-err"] == "failed"
        assert statuses["br-ok"] == "qa_done"


# ---------------------------------------------------------------------------
# Test 5: Report generation
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestReportGeneration:
    """Verify report JSON structure after run_production."""

    def test_report_json_structure(self, tmp_path: Path):
        """After run_production, report JSON has summary.total, summary.passed, results array."""
        source = _make_source_image(tmp_path)
        product = {
            "sku": "br-rpt",
            "name": "Report Hoodie",
            "collection": "black-rose",
            "is_accessory": False,
            "source_image": source,
            "output_slug": "report-hoodie",
        }
        fake_webp = _make_fake_webp()
        tournament = _make_tournament_result(score=95.0, passed=True)

        with (
            patch("nano_banana.client.get_genai_client", return_value=MagicMock()),
            patch("nano_banana.client.get_openai_client", return_value=MagicMock()),
            patch(
                "nano_banana.vision_describe.describe_product",
                return_value={"garment_type": "hoodie"},
            ),
            patch(
                "nano_banana.generate.generate_gemini_async",
                new_callable=AsyncMock,
                return_value=fake_webp,
            ),
            patch("nano_banana.tournament.run_tournament", return_value=tournament),
            patch("nano_banana.catalog.find_back_source", return_value=None),
            patch("nano_banana.catalog.get_material_spec", return_value=""),
            patch("nano_banana.router.route_product", return_value=[]),
            patch("nano_banana.prompts.get_prompt", return_value="Generate a test image"),
            patch("nano_banana.pipeline._find_bundle_dir", return_value=None),
            patch("nano_banana.pipeline._load_bundle_refs", return_value=[]),
            patch("nano_banana.produce_async.PROJECT_ROOT", tmp_path),
        ):
            out_dir = (
                tmp_path
                / "wordpress-theme"
                / "skyyrose-flagship"
                / "assets"
                / "images"
                / "products"
            )
            out_dir.mkdir(parents=True)
            (tmp_path / "data" / "product-vision").mkdir(parents=True)
            report_dir = tmp_path / "data" / "verify-results"
            report_dir.mkdir(parents=True)

            asyncio.get_event_loop().run_until_complete(
                run_production(
                    products=[product],
                    views=["front"],
                    catalog={"br-rpt": product},
                    concurrency=1,
                )
            )

        # Find the report file
        reports = list(report_dir.glob("production-report-*.json"))
        assert len(reports) == 1, f"Expected 1 report, found {len(reports)}"

        report = json.loads(reports[0].read_text())
        assert "summary" in report
        assert "total" in report["summary"]
        assert "passed" in report["summary"]
        assert "results" in report
        assert isinstance(report["results"], list)
        assert len(report["results"]) == 1
        assert report["results"][0]["sku"] == "br-rpt"
        assert report["summary"]["total"] == 1
