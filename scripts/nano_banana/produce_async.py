"""Async staged production pipeline — maximum throughput with error boundaries.

Every stage isolates failures per-job. One product failing never kills the batch.
All sync API calls wrapped in asyncio.to_thread. All gather calls use return_exceptions.

Stage 1: Vision analysis (async, N concurrent)
Stage 2: Route + prompt (CPU-only, try/except per job)
Stage 3: Generate images (async, N concurrent, 3 retries per job)
Stage 4: QA tournament (thread pool, 3 judges, compare vs real product photo)
Stage 5: Refine failures only (async, N concurrent)

Usage:
    python scripts/nano-banana-run.py produce-async --views front,back --concurrency 3
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from dataclasses import dataclass, field
from pathlib import Path

log = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Timeouts per stage (seconds) — if a thread hangs, we kill the job, not the batch
VISION_TIMEOUT = 60
GENERATE_TIMEOUT = 120
QA_TIMEOUT = 90
REFINE_TIMEOUT = 90


async def safe_thread(fn, *args, timeout: float = 120, label: str = "task"):
    """Run sync function in thread with timeout and proper error capture.

    - TimeoutError: logs, returns None (thread may still be running but job moves on)
    - Exception: logs full traceback, returns None
    - Success: returns the function result
    """
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(fn, *args),
            timeout=timeout,
        )
    except TimeoutError:
        log.error("TIMEOUT (%ds) on %s — thread orphaned, job skipped", timeout, label)
        return None
    except asyncio.CancelledError:
        log.warning("CANCELLED %s", label)
        return None
    except Exception as exc:
        log.error("THREAD DIED on %s: %s", label, exc, exc_info=True)
        return None


@dataclass
class ImageJob:
    """Tracks one product+view through the pipeline."""

    sku: str
    name: str
    collection: str
    view: str
    source_path: Path | None
    output_slug: str
    is_accessory: bool = False
    product: dict = field(default_factory=dict)

    # Filled by pipeline stages
    vision: dict = field(default_factory=dict)
    route_engine: str = ""
    route_fallback: str = ""
    prompt: str = ""
    extra_refs: list = field(default_factory=list)
    output_path: Path | None = None
    qa_score: float = 0.0
    qa_passed: bool = False
    qa_issues: list = field(default_factory=list)
    refined: bool = False
    error: str = ""
    status: str = "pending"


async def run_production(
    products: list[dict],
    views: list[str],
    catalog: dict,
    concurrency: int = 3,
    model_override: str | None = None,
) -> list[ImageJob]:
    """Run the full staged production pipeline with error boundaries."""
    from nano_banana.catalog import find_back_source, get_material_spec
    from nano_banana.client import get_genai_client, get_openai_client
    from nano_banana.generate import GEMINI_PRO, generate_gemini_async
    from nano_banana.pipeline import _find_bundle_dir, _load_bundle_refs
    from nano_banana.prompts import get_prompt
    from nano_banana.router import route_product
    from nano_banana.tournament import run_tournament
    from nano_banana.utils import get_output_filename, quality_gate, save_image
    from nano_banana.vision_describe import describe_product

    PRODUCTS_DIR = (
        PROJECT_ROOT / "wordpress-theme" / "skyyrose-flagship" / "assets" / "images" / "products"
    )

    # ── Init clients (with error boundaries) ─────────────────────────
    try:
        client = get_genai_client()
    except Exception as exc:
        log.error("FATAL: Cannot create Gemini client: %s", exc)
        return []

    try:
        openai_client = get_openai_client()
    except Exception as exc:
        log.warning("OpenAI client failed: %s — GPT judge/generation unavailable", exc)
        openai_client = None

    anthropic_client = None
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if anthropic_key:
        try:
            import anthropic

            anthropic_client = anthropic.Anthropic(api_key=anthropic_key)
        except Exception as exc:
            log.warning("Anthropic client failed: %s — Claude judge unavailable", exc)

    tournament_clients = {
        "openai": openai_client,
        "anthropic": anthropic_client,
        "gemini": client,
    }

    # ── Build job list (with null checks + error boundaries) ──────────
    jobs: list[ImageJob] = []
    skipped = 0
    for product in products:
        sku = product.get("sku")
        if not sku:
            log.warning("Product missing SKU — skipped")
            skipped += 1
            continue
        name = product.get("name", sku)
        collection = product.get("collection", "")
        src = product.get("source_image")

        if not src or not Path(str(src)).exists():
            log.warning("SKIP %s: no source image", sku)
            skipped += 1
            continue

        for view in views:
            try:
                if product.get("is_accessory") and view == "back":
                    continue

                view_src = src
                if view == "back":
                    try:
                        back = find_back_source(sku, catalog)
                        if back and Path(str(back)).exists():
                            view_src = back
                    except Exception as exc:
                        log.warning("find_back_source failed for %s: %s", sku, exc)

                jobs.append(
                    ImageJob(
                        sku=sku,
                        name=name,
                        collection=collection,
                        view=view,
                        source_path=Path(str(view_src)),
                        output_slug=product.get("output_slug", sku),
                        is_accessory=product.get("is_accessory", False),
                        product=product,
                    )
                )
            except Exception as exc:
                log.error("Job creation failed for %s %s: %s", sku, view, exc)

    if skipped:
        log.warning("Skipped %d products (no source image or missing SKU)", skipped)

    total = len(jobs)
    log.info(
        "PRODUCTION: %d images to generate (%d products × %s views)", total, len(products), views
    )

    # ── Stage 1: Vision analysis ─────────────────────────────────────
    log.info("\n=== STAGE 1: VISION ANALYSIS ===")
    vision_sem = asyncio.Semaphore(concurrency + 2)
    vision_cache: dict[str, dict] = {}
    cache_dir = PROJECT_ROOT / "data" / "product-vision"
    cache_dir.mkdir(parents=True, exist_ok=True)

    async def analyze_vision(job: ImageJob) -> None:
        if job.sku in vision_cache:
            job.vision = vision_cache[job.sku]
            return

        # Disk cache
        cache_file = cache_dir / f"{job.sku}-vision.json"
        if cache_file.exists():
            try:
                job.vision = json.loads(cache_file.read_text())
                vision_cache[job.sku] = job.vision
                return
            except (json.JSONDecodeError, OSError):
                pass

        async with vision_sem:
            try:
                # describe_product is sync — run in thread pool
                desc = await safe_thread(
                    describe_product,
                    client,
                    job.source_path,
                    job.product,
                    timeout=VISION_TIMEOUT,
                    label=f"vision-{job.sku}",
                )
                if desc:
                    job.vision = desc
                    vision_cache[job.sku] = desc
                    cache_file.write_text(json.dumps(desc, indent=2))
                    log.info("Vision: %s — %s", job.sku, desc.get("garment_type", "?"))
                else:
                    log.warning("Vision returned empty for %s", job.sku)
                    job.vision = {}
            except Exception as exc:
                log.error("Vision failed for %s: %s", job.sku, exc)
                job.vision = {}

    # Deduplicate — one vision call per SKU
    seen_skus: set[str] = set()
    vision_tasks = []
    for job in jobs:
        if job.sku not in seen_skus:
            seen_skus.add(job.sku)
            vision_tasks.append(analyze_vision(job))

    await asyncio.gather(*vision_tasks, return_exceptions=True)

    # Copy vision results to all jobs with same SKU
    for job in jobs:
        if not job.vision and job.sku in vision_cache:
            job.vision = vision_cache[job.sku]

    analyzed = sum(1 for s in seen_skus if s in vision_cache)
    log.info("Vision: %d/%d SKUs analyzed", analyzed, len(seen_skus))

    # ── Stage 2: Route + Prompt (CPU-only, per-job error boundary) ───
    log.info("\n=== STAGE 2: ROUTING + PROMPTS ===")
    for job in jobs:
        try:
            decisions = route_product(job.product, job.vision, job.view)
            if decisions:
                job.route_engine = decisions[0].engine
                job.route_fallback = decisions[1].engine if len(decisions) > 1 else ""
            else:
                job.route_engine = "gemini-pro"
        except Exception as exc:
            log.warning(
                "Route failed for %s %s: %s — defaulting to gemini-pro", job.sku, job.view, exc
            )
            job.route_engine = "gemini-pro"

        try:
            job.prompt = get_prompt(job.product, job.view)
        except Exception as exc:
            log.error("Prompt failed for %s %s: %s", job.sku, job.view, exc)
            job.prompt = f"Generate a photorealistic product render of {job.name}, {job.view} view."

        try:
            job.extra_refs = _load_bundle_refs(job.name, job.sku, job.source_path, job.view)
        except Exception as exc:
            log.warning("Bundle refs failed for %s: %s", job.sku, exc)
            job.extra_refs = []

    log.info("Routed %d jobs", len(jobs))

    # ── Stage 3: Generate (async, bounded concurrency, retries) ──────
    log.info("\n=== STAGE 3: GENERATE ===")
    gen_sem = asyncio.Semaphore(concurrency)
    gen_count = 0

    async def generate_one(job: ImageJob) -> None:
        nonlocal gen_count
        if not job.source_path or not job.source_path.exists():
            job.status = "failed"
            job.error = "No source image"
            gen_count += 1
            log.error("[%d/%d] SKIP %s %s: source missing", gen_count, total, job.sku, job.view)
            return
        if not job.prompt:
            job.status = "failed"
            job.error = "No prompt generated"
            gen_count += 1
            log.error("[%d/%d] SKIP %s %s: empty prompt", gen_count, total, job.sku, job.view)
            return
        job.status = "generating"
        model = model_override or GEMINI_PRO
        out_path = PRODUCTS_DIR / get_output_filename(job.sku, job.view, job.output_slug)

        async with gen_sem:
            for attempt in range(1, 4):
                try:
                    img_bytes = await asyncio.wait_for(
                        generate_gemini_async(
                            client,
                            job.source_path,
                            job.prompt,
                            model=model,
                            enhanced=(attempt > 1),
                            extra_refs=job.extra_refs if job.extra_refs else None,
                        ),
                        timeout=GENERATE_TIMEOUT,
                    )
                except TimeoutError:
                    log.error(
                        "[%s %s] attempt %d TIMEOUT (%ds)",
                        job.sku,
                        job.view,
                        attempt,
                        GENERATE_TIMEOUT,
                    )
                    img_bytes = None
                except asyncio.CancelledError:
                    log.warning("[%s %s] attempt %d CANCELLED", job.sku, job.view, attempt)
                    img_bytes = None
                except Exception as exc:
                    log.error("[%s %s] attempt %d: %s", job.sku, job.view, attempt, exc)
                    img_bytes = None

                if img_bytes:
                    try:
                        if quality_gate(img_bytes, job.sku, job.view):
                            save_image(img_bytes, out_path)
                            job.output_path = out_path
                            job.status = "generated"
                            gen_count += 1
                            log.info(
                                "[%d/%d] PASS %s %s (%.1fKB)",
                                gen_count,
                                total,
                                job.sku,
                                job.view,
                                len(img_bytes) / 1024,
                            )
                            return
                    except Exception as exc:
                        log.error("[%s %s] save/quality_gate error: %s", job.sku, job.view, exc)

                if attempt < 3:
                    await asyncio.sleep(3)

            job.status = "failed"
            job.error = "Generation failed after 3 attempts"
            gen_count += 1
            log.error("[%d/%d] FAIL %s %s", gen_count, total, job.sku, job.view)

    results = await asyncio.gather(*(generate_one(j) for j in jobs), return_exceptions=True)
    # Log any unexpected exceptions from gather
    for i, r in enumerate(results):
        if isinstance(r, Exception):
            log.error("Unexpected error in generate job %d: %s", i, r)
            if i < len(jobs):
                jobs[i].status = "failed"
                jobs[i].error = str(r)

    generated = [j for j in jobs if j.status == "generated"]
    failed_gen = [j for j in jobs if j.status == "failed"]
    log.info("Generated: %d passed, %d failed", len(generated), len(failed_gen))

    if not generated:
        log.error("No images generated — skipping QA and refine stages")
        _save_report(jobs, total)
        return jobs

    # ── Stage 4: QA Tournament ───────────────────────────────────────
    log.info("\n=== STAGE 4: QA TOURNAMENT ===")
    qa_sem = asyncio.Semaphore(max(1, concurrency - 1))

    async def qa_one(job: ImageJob) -> None:
        if not job.output_path:
            return
        job.status = "qa"

        # Use real product photo for comparison when available
        qa_source = job.source_path
        try:
            bundle_dir = _find_bundle_dir(job.name, job.sku)
            if bundle_dir:
                for tag in ("photo-front", "source-photo"):
                    for f in bundle_dir.glob(f"{tag}.*"):
                        if f.exists():
                            qa_source = f
                            break
                    if qa_source != job.source_path:
                        break
        except Exception as exc:
            log.warning("Bundle lookup for QA source failed %s: %s", job.sku, exc)

        async with qa_sem:
            result = await safe_thread(
                run_tournament,
                tournament_clients,
                qa_source,
                job.output_path,
                job.vision,
                80.0,
                timeout=QA_TIMEOUT,
                label=f"qa-{job.sku}-{job.view}",
            )
            if result is not None:
                job.qa_score = result.aggregate_score
                job.qa_passed = result.passed_98
                job.qa_issues = result.top_issues
                log.info(
                    "QA %s %s: %.1f — %s",
                    job.sku,
                    job.view,
                    job.qa_score,
                    "PASS" if job.qa_passed else "REVIEW",
                )
            else:
                log.error("QA returned None for %s %s (timeout or thread death)", job.sku, job.view)
                job.qa_score = 0.0
                job.error = "QA timeout or thread death"
            job.status = "qa_done"

    qa_results = await asyncio.gather(*(qa_one(j) for j in generated), return_exceptions=True)
    for i, r in enumerate(qa_results):
        if isinstance(r, Exception):
            log.error("Unexpected QA error job %d: %s", i, r)

    passed = [j for j in generated if j.qa_passed]
    needs_review = [j for j in generated if not j.qa_passed and j.qa_score >= 50]
    auto_reject = [j for j in generated if not j.qa_passed and j.qa_score < 50]
    log.info(
        "QA: %d passed, %d review, %d rejected", len(passed), len(needs_review), len(auto_reject)
    )

    # ── Stage 5: Refine (only jobs scoring 30-79) ────────────────────
    to_refine = [j for j in generated if not j.qa_passed and j.qa_score >= 30]
    if to_refine:
        log.info("\n=== STAGE 5: REFINE (%d images) ===", len(to_refine))
        from nano_banana.generate import composite_gemini
        from nano_banana.prompts import composite_prompt

        async def refine_one(job: ImageJob) -> None:
            if not job.output_path or not job.output_path.exists():
                log.warning("SKIP refine %s %s: no output to refine", job.sku, job.view)
                return
            if not job.source_path or not job.source_path.exists():
                log.warning("SKIP refine %s %s: no source for composite", job.sku, job.view)
                return
            async with gen_sem:
                try:
                    comp_prompt = composite_prompt(job.name, job.sku, job.view)
                    refined = await safe_thread(
                        composite_gemini,
                        client,
                        job.output_path,
                        job.source_path,
                        comp_prompt,
                        timeout=REFINE_TIMEOUT,
                        label=f"refine-{job.sku}-{job.view}",
                    )
                    if refined and quality_gate(refined, job.sku, f"{job.view}-refined"):
                        save_image(refined, job.output_path)
                        job.refined = True
                        log.info("REFINED %s %s", job.sku, job.view)
                except Exception as exc:
                    log.error("Refine failed %s %s: %s", job.sku, job.view, exc)

        refine_results = await asyncio.gather(
            *(refine_one(j) for j in to_refine), return_exceptions=True
        )
        for i, r in enumerate(refine_results):
            if isinstance(r, Exception):
                log.error("Unexpected refine error job %d: %s", i, r)

    # ── Report ───────────────────────────────────────────────────────
    _save_report(jobs, total)
    return jobs


def _save_report(jobs: list[ImageJob], total: int) -> None:
    """Save production report to disk."""
    final_pass = sum(1 for j in jobs if j.qa_passed)
    final_review = sum(
        1 for j in jobs if j.status == "qa_done" and not j.qa_passed and j.qa_score >= 50
    )
    final_fail = sum(
        1 for j in jobs if j.status == "failed" or (j.status == "qa_done" and j.qa_score < 50)
    )
    refined_count = sum(1 for j in jobs if j.refined)

    log.info("\n" + "=" * 60)
    log.info("PRODUCTION COMPLETE")
    log.info("=" * 60)
    log.info("  PASSED:   %d", final_pass)
    log.info("  REVIEW:   %d", final_review)
    log.info("  FAILED:   %d", final_fail)
    log.info("  REFINED:  %d", refined_count)
    log.info("  TOTAL:    %d", total)

    report_dir = PROJECT_ROOT / "data" / "verify-results"
    report_dir.mkdir(parents=True, exist_ok=True)
    ts = int(time.time())
    report = {
        "timestamp": ts,
        "summary": {
            "total": total,
            "passed": final_pass,
            "review": final_review,
            "failed": final_fail,
            "refined": refined_count,
        },
        "results": [
            {
                "sku": j.sku,
                "view": j.view,
                "engine": j.route_engine,
                "qa_score": round(j.qa_score, 1),
                "passed": j.qa_passed,
                "refined": j.refined,
                "status": j.status,
                "issues": j.qa_issues[:3],
                "error": j.error,
            }
            for j in jobs
        ],
    }
    report_path = report_dir / f"production-report-{ts}.json"
    report_path.write_text(json.dumps(report, indent=2))
    log.info("Report: %s", report_path)
