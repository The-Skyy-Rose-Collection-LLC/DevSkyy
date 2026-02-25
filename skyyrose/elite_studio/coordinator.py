"""
Coordinator — Orchestrates the Multi-Agent Pipeline

Directs the team of agents through the production workflow:
  1. Vision Agent (Gemini + OpenAI) -> product analysis
  2. Generator Agent (Gemini 3 Pro) -> fashion model image
  3. Quality Agent (Claude Sonnet) -> verification

Handles batch processing, rate limiting, and result reporting.
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from typing import Any, Protocol

from .agents.generator_agent import GeneratorAgent
from .agents.quality_agent import QualityAgent
from .agents.vision_agent import VisionAgent
from .config import BATCH_DELAY_SECONDS, OUTPUT_DIR
from .models import ProductionResult, SynthesizedVision
from .utils import discover_all_skus


# ---------------------------------------------------------------------------
# Logger protocol — decouples presentation from orchestration
# ---------------------------------------------------------------------------


class Logger(Protocol):
    """Minimal logging interface for coordinator output."""

    def info(self, msg: str) -> None: ...
    def step(self, step_num: int, total: int, label: str) -> None: ...
    def ok(self, msg: str) -> None: ...
    def fail(self, msg: str) -> None: ...
    def separator(self) -> None: ...


class PrintLogger:
    """Default logger that prints to stdout."""

    def info(self, msg: str) -> None:
        print(f"  {msg}")

    def step(self, step_num: int, total: int, label: str) -> None:
        print(f"\n  [{step_num}/{total}] {label}...")

    def ok(self, msg: str) -> None:
        print(f"  OK: {msg}")

    def fail(self, msg: str) -> None:
        print(f"  FAIL: {msg}")

    def separator(self) -> None:
        print(f"{'=' * 60}")


class NullLogger:
    """Silent logger for tests."""

    def info(self, msg: str) -> None:
        pass

    def step(self, step_num: int, total: int, label: str) -> None:
        pass

    def ok(self, msg: str) -> None:
        pass

    def fail(self, msg: str) -> None:
        pass

    def separator(self) -> None:
        pass


# ---------------------------------------------------------------------------
# Coordinator
# ---------------------------------------------------------------------------


class Coordinator:
    """Orchestrates the multi-agent production pipeline.

    The coordinator delegates to specialized agents and manages
    the production flow. Each agent operates independently with
    its own provider connections and retry logic.

    Agent Team:
        vision  -> VisionAgent  (Gemini Flash + OpenAI GPT-4o)
        gen     -> GeneratorAgent  (Gemini 3 Pro)
        qc      -> QualityAgent  (Claude Sonnet)
    """

    def __init__(
        self,
        vision: VisionAgent | None = None,
        generator: GeneratorAgent | None = None,
        quality: QualityAgent | None = None,
        logger: Logger | None = None,
    ):
        self.vision = vision or VisionAgent()
        self.generator = generator or GeneratorAgent()
        self.quality = quality or QualityAgent()
        self.log = logger or PrintLogger()

    def produce(self, sku: str, view: str = "front") -> ProductionResult:
        """Run full production pipeline for a single product.

        Steps:
            1. Vision analysis (dual-provider)
            2. Image generation (Gemini 3 Pro)
            3. Quality verification (Claude Sonnet)

        Each step can fail independently. If vision fails, we stop.
        If generation fails, we stop. If QC fails, we still return
        the result (the image exists, just flagged).
        """
        self.log.separator()
        self.log.info(f"ELITE PRODUCTION STUDIO — {sku.upper()} | {view}")
        self.log.separator()

        # Step 1: Vision Analysis
        self.log.step(1, 3, "Vision Analysis")
        vision_result = self.vision.analyze(sku, view)

        if not vision_result.success:
            self.log.fail(vision_result.error)
            return ProductionResult(
                sku=sku,
                view=view,
                status="error",
                step="vision",
                error=vision_result.error,
                vision=vision_result,
            )

        providers = ", ".join(vision_result.providers_used)
        self.log.ok(f"{vision_result.provider_count} providers ({providers})")

        # Step 2: Image Generation
        self.log.step(2, 3, "Image Generation")
        gen_result = self.generator.generate(
            sku=sku,
            view=view,
            generation_spec=vision_result.unified_spec,
        )

        if not gen_result.success:
            self.log.fail(gen_result.error)
            return ProductionResult(
                sku=sku,
                view=view,
                status="error",
                step="generation",
                error=gen_result.error,
                vision=vision_result,
                generation=gen_result,
            )

        self.log.ok(gen_result.output_path)

        # Step 3: Quality Control
        self.log.step(3, 3, "Quality Control")
        qc_result = self.quality.verify(
            image_path=gen_result.output_path,
            expected_spec=vision_result.unified_spec,
        )

        if qc_result.success:
            self.log.ok(f"{qc_result.overall_status} ({qc_result.recommendation})")
        else:
            self.log.info(f"QC skipped ({qc_result.error})")

        self.log.separator()
        self.log.info(f"COMPLETE: {sku.upper()}")
        self.log.separator()

        return ProductionResult(
            sku=sku,
            view=view,
            status="success",
            output_path=gen_result.output_path,
            vision=vision_result,
            generation=gen_result,
            quality=qc_result,
        )

    def produce_batch(
        self,
        skus: list[str] | None = None,
        view: str = "front",
        skip_existing: bool = True,
    ) -> list[ProductionResult]:
        """Run production for multiple products.

        Args:
            skus: List of SKUs to process. None = all products.
            view: Image view angle.
            skip_existing: Skip products that already have generated images.

        Returns:
            List of ProductionResult for each product.
        """
        all_skus = skus or discover_all_skus()

        # Filter out already-generated products
        if skip_existing:
            remaining = []
            for sku in all_skus:
                output = OUTPUT_DIR / sku / f"{sku}-model-{view}-gemini.jpg"
                if output.exists():
                    self.log.info(f"[skip] {sku} — already generated")
                else:
                    remaining.append(sku)
            all_skus = remaining

        total = len(all_skus)
        self.log.info(f"BATCH PRODUCTION — {total} products")
        self.log.separator()

        results: list[ProductionResult] = []

        for i, sku in enumerate(all_skus, 1):
            self.log.step(i, total, sku)
            try:
                result = self.produce(sku, view)
                results.append(result)
            except Exception as exc:
                self.log.fail(str(exc))
                results.append(
                    ProductionResult(
                        sku=sku,
                        view=view,
                        status="error",
                        error=str(exc),
                    )
                )

            # Rate limit between products
            if i < total:
                self.log.info(f"[pause] {BATCH_DELAY_SECONDS}s rate limit...")
                time.sleep(BATCH_DELAY_SECONDS)

        # Write report
        self._write_report(results)
        self._print_summary(results)

        return results

    def _write_report(self, results: list[ProductionResult]) -> None:
        """Write batch report to JSON."""
        report_path = OUTPUT_DIR / "BATCH_REPORT.json"
        report_data = []
        for r in results:
            entry: dict[str, Any] = {
                "id": r.sku,
                "status": r.status,
                "step": r.step,
                "output_path": r.output_path,
            }
            if r.error:
                entry["error"] = r.error
            if r.vision:
                entry["vision_providers"] = list(r.vision.providers_used)
            if r.quality and r.quality.success:
                entry["qc_status"] = r.quality.overall_status
                entry["qc_recommendation"] = r.quality.recommendation
            report_data.append(entry)

        report_path.write_text(json.dumps(report_data, indent=2))
        self.log.info(f"Report: {report_path}")

    def _print_summary(self, results: list[ProductionResult]) -> None:
        """Print batch summary."""
        success = sum(1 for r in results if r.status == "success")
        failed = len(results) - success
        self.log.separator()
        self.log.info(
            f"BATCH COMPLETE: {success}/{len(results)} succeeded, {failed} failed"
        )

        qc_pass = sum(
            1 for r in results if r.quality and r.quality.overall_status == "pass"
        )
        qc_warn = sum(
            1 for r in results if r.quality and r.quality.overall_status == "warn"
        )
        qc_fail = sum(
            1 for r in results if r.quality and r.quality.overall_status == "fail"
        )
        if qc_pass or qc_warn or qc_fail:
            self.log.info(f"QC: {qc_pass} pass, {qc_warn} warn, {qc_fail} fail")

        self.log.separator()
