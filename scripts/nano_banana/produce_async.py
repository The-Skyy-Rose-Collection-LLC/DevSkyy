"""Async staged production pipeline — maximum throughput.

Stage 1: Vision analysis (async, N concurrent)
Stage 2: Route all products (instant, CPU-only)
Stage 3: Generate images (async, N concurrent, error boundaries)
Stage 4: QA tournament (3 judges per image, thread pool)
Stage 5: Refine failures only (async, N concurrent)

Usage:
    python scripts/nano-banana-run.py produce-async --views front,back --concurrency 3
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path

log = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


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
    template_id: str = ""
    extra_refs: list = field(default_factory=list)
    output_path: Path | None = None
    image_bytes: bytes | None = None
    qa_score: float = 0.0
    qa_passed: bool = False
    qa_issues: list = field(default_factory=list)
    refined: bool = False
    error: str = ""
    status: str = "pending"  # pending → generating → qa → refining → done → failed


async def run_production(
    products: list[dict],
    views: list[str],
    catalog: dict,
    concurrency: int = 3,
    model_override: str | None = None,
) -> list[ImageJob]:
    """Run the full staged production pipeline."""
    from nano_banana.catalog import find_back_source, find_source_image, get_material_spec
    from nano_banana.client import get_genai_client, get_openai_client
    from nano_banana.generate import GEMINI_FAST, GEMINI_PRO, generate_gemini_async
    from nano_banana.pipeline import _find_bundle_dir
    from nano_banana.prompts import get_prompt
    from nano_banana.router import route_product
    from nano_banana.tournament import run_tournament
    from nano_banana.utils import get_output_filename, quality_gate, save_image
    from nano_banana.vision_describe import describe_product

    PRODUCTS_DIR = (
        PROJECT_ROOT / "wordpress-theme" / "skyyrose-flagship" / "assets" / "images" / "products"
    )

    client = get_genai_client()
    openai_client = get_openai_client()

    anthropic_client = None
    import os
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if anthropic_key:
        try:
            import anthropic
            anthropic_client = anthropic.Anthropic(api_key=anthropic_key)
        except ImportError:
            pass

    tournament_clients = {
        "openai": openai_client,
        "anthropic": anthropic_client,
        "gemini": client,
    }

    # ── Build job list ───────────────────────────────────────────────
    jobs: list[ImageJob] = []
    for product in products:
        sku = product["sku"]
        for view in views:
            if product.get("is_accessory") and view == "back":
                continue

            src = product.get("source_image")
            if view == "back":
                back = find_back_source(sku, catalog)
                if back:
                    src = back

            if not src:
                continue

            jobs.append(ImageJob(
                sku=sku,
                name=product["name"],
                collection=product["collection"],
                view=view,
                source_path=src,
                output_slug=product.get("output_slug", sku),
                is_accessory=product.get("is_accessory", False),
                product=product,
            ))

    total = len(jobs)
    log.info("PRODUCTION: %d images to generate (%d products × %s views)", total, len(products), views)

    # ── Stage 1: Vision analysis (async, batched) ────────────────────
    log.info("\n=== STAGE 1: VISION ANALYSIS ===")
    sem = asyncio.Semaphore(concurrency + 2)  # vision is lightweight, allow more
    vision_cache: dict[str, dict] = {}
    cache_dir = PROJECT_ROOT / "data" / "product-vision"
    cache_dir.mkdir(parents=True, exist_ok=True)

    async def analyze_vision(job: ImageJob) -> None:
        if job.sku in vision_cache:
            job.vision = vision_cache[job.sku]
            return
        cache_file = cache_dir / f"{job.sku}-vision.json"
        if cache_file.exists():
            try:
                job.vision = json.loads(cache_file.read_text())
                vision_cache[job.sku] = job.vision
                return
            except (json.JSONDecodeError, OSError):
                pass
        async with sem:
            try:
                desc = describe_product(client, job.source_path, job.product)
                if desc:
                    job.vision = desc
                    vision_cache[job.sku] = desc
                    cache_file.write_text(json.dumps(desc, indent=2))
            except Exception as exc:
                log.error("Vision failed for %s: %s", job.sku, exc)
                job.vision = {}

    # Deduplicate — only analyze each SKU once
    seen_skus = set()
    vision_tasks = []
    for job in jobs:
        if job.sku not in seen_skus:
            seen_skus.add(job.sku)
            vision_tasks.append(analyze_vision(job))

    await asyncio.gather(*vision_tasks)

    # Copy vision to all jobs with same SKU
    for job in jobs:
        if not job.vision and job.sku in vision_cache:
            job.vision = vision_cache[job.sku]

    analyzed = sum(1 for s in seen_skus if s in vision_cache)
    log.info("Vision: %d/%d SKUs analyzed", analyzed, len(seen_skus))

    # ── Stage 2: Route + Prompt (CPU-only, instant) ──────────────────
    log.info("\n=== STAGE 2: ROUTING + PROMPTS ===")
    for job in jobs:
        # Route
        decisions = route_product(job.product, job.vision, job.view)
        if decisions:
            job.route_engine = decisions[0].engine
            job.route_fallback = decisions[1].engine if len(decisions) > 1 else ""

        # Prompt
        job.prompt = get_prompt(job.product, job.view)
        material_spec = get_material_spec(job.sku)
        if material_spec:
            job.prompt += f"\n\nMATERIAL SPEC: {material_spec}"

        # Bundle refs
        bundle_dir = _find_bundle_dir(job.name, job.sku)
        if bundle_dir:
            for tag, label in [
                ("logo-ref", "REFERENCE — EXACT LOGO ART (copy this precisely)"),
                ("logo-heart-rose", "REFERENCE — EXACT LOGO ART (copy this precisely)"),
                ("patch-ref", "REFERENCE — EXACT PATCH DESIGN (reproduce this patch)"),
                ("photo-front", "REFERENCE — REAL PRODUCT PHOTO (match this exactly)"),
                ("source-photo", "REFERENCE — REAL PRODUCT PHOTO (match this exactly)"),
            ]:
                for f in bundle_dir.glob(f"{tag}.*"):
                    if f.exists():
                        job.extra_refs.append((label, f))
                        break

    log.info("Routed %d jobs", len(jobs))

    # ── Stage 3: Generate images (async, bounded concurrency) ────────
    log.info("\n=== STAGE 3: GENERATE ===")
    gen_sem = asyncio.Semaphore(concurrency)
    done_count = 0

    async def generate_one(job: ImageJob) -> None:
        nonlocal done_count
        job.status = "generating"
        model = model_override or GEMINI_PRO
        out_path = PRODUCTS_DIR / get_output_filename(job.sku, job.view, job.output_slug)

        async with gen_sem:
            for attempt in range(1, 4):
                try:
                    img_bytes = await generate_gemini_async(
                        client,
                        job.source_path,
                        job.prompt,
                        model=model,
                        enhanced=(attempt > 1),
                        extra_refs=job.extra_refs if job.extra_refs else None,
                    )
                except Exception as exc:
                    log.error("[%s %s] attempt %d: %s", job.sku, job.view, attempt, exc)
                    img_bytes = None

                if img_bytes and quality_gate(img_bytes, job.sku, job.view):
                    save_image(img_bytes, out_path)
                    job.output_path = out_path
                    job.image_bytes = img_bytes
                    job.status = "generated"
                    done_count += 1
                    log.info("[%d/%d] PASS %s %s (%.1fKB)", done_count, total, job.sku, job.view, len(img_bytes) / 1024)
                    return

                if attempt < 3:
                    await asyncio.sleep(3)

        job.status = "failed"
        job.error = "Generation failed after 3 attempts"
        done_count += 1
        log.error("[%d/%d] FAIL %s %s", done_count, total, job.sku, job.view)

    await asyncio.gather(*(generate_one(j) for j in jobs))

    generated = [j for j in jobs if j.status == "generated"]
    failed_gen = [j for j in jobs if j.status == "failed"]
    log.info("Generated: %d passed, %d failed", len(generated), len(failed_gen))

    # ── Stage 4: QA Tournament (thread pool, 3 judges per image) ─────
    log.info("\n=== STAGE 4: QA TOURNAMENT ===")
    # Lower concurrency — each QA runs 3 judge API calls internally
    qa_sem = asyncio.Semaphore(max(1, concurrency - 1))

    async def qa_one(job: ImageJob) -> None:
        if not job.output_path:
            return
        job.status = "qa"

        # Use real product photo for QA comparison when available (not the techflat)
        qa_source = job.source_path
        bundle_dir = _find_bundle_dir(job.name, job.sku)
        if bundle_dir:
            for tag in ("photo-front", "source-photo"):
                for f in bundle_dir.glob(f"{tag}.*"):
                    if f.exists():
                        qa_source = f
                        break
                if qa_source != job.source_path:
                    break

        async with qa_sem:
            try:
                result = await asyncio.to_thread(
                    run_tournament,
                    clients=tournament_clients,
                    source_path=qa_source,
                    candidate_path=job.output_path,
                    dna=job.vision,
                    passing_threshold=80.0,
                )
                job.qa_score = result.aggregate_score
                job.qa_passed = result.passed_98
                job.qa_issues = result.top_issues
                job.status = "qa_done"
                log.info("QA %s %s: %.1f — %s", job.sku, job.view, job.qa_score, "PASS" if job.qa_passed else "REVIEW")
            except Exception as exc:
                log.error("QA failed %s %s: %s", job.sku, job.view, exc)
                job.qa_score = 0.0
                job.status = "qa_done"

    await asyncio.gather(*(qa_one(j) for j in generated))

    passed = [j for j in generated if j.qa_passed]
    needs_review = [j for j in generated if not j.qa_passed and j.qa_score >= 50]
    auto_reject = [j for j in generated if not j.qa_passed and j.qa_score < 50]

    log.info("QA: %d passed, %d review, %d rejected", len(passed), len(needs_review), len(auto_reject))

    # ── Stage 5: Refine rejected (async) ─────────────────────────────
    to_refine = [j for j in generated if not j.qa_passed and j.qa_score >= 30]
    if to_refine:
        log.info("\n=== STAGE 5: REFINE (%d images) ===", len(to_refine))
        from nano_banana.generate import composite_gemini
        from nano_banana.prompts import composite_prompt

        async def refine_one(job: ImageJob) -> None:
            async with gen_sem:
                try:
                    comp_prompt = composite_prompt(job.name, job.sku, job.view)
                    refined = await asyncio.to_thread(
                        composite_gemini,
                        client,
                        job.output_path,
                        job.source_path,
                        comp_prompt,
                    )
                    if refined and quality_gate(refined, job.sku, f"{job.view}-refined"):
                        save_image(refined, job.output_path)
                        job.refined = True
                        log.info("REFINED %s %s", job.sku, job.view)
                except Exception as exc:
                    log.error("Refine failed %s %s: %s", job.sku, job.view, exc)

        await asyncio.gather(*(refine_one(j) for j in to_refine))

    # ── Summary ──────────────────────────────────────────────────────
    log.info("\n" + "=" * 60)
    log.info("PRODUCTION COMPLETE")
    log.info("=" * 60)

    final_pass = sum(1 for j in jobs if j.qa_passed)
    final_review = sum(1 for j in jobs if j.status == "qa_done" and not j.qa_passed and j.qa_score >= 50)
    final_fail = sum(1 for j in jobs if j.status == "failed" or j.qa_score < 50)
    refined_count = sum(1 for j in jobs if j.refined)

    log.info("  PASSED:   %d", final_pass)
    log.info("  REVIEW:   %d", final_review)
    log.info("  FAILED:   %d", final_fail)
    log.info("  REFINED:  %d", refined_count)
    log.info("  TOTAL:    %d", total)

    # Save batch report
    report_dir = PROJECT_ROOT / "data" / "verify-results"
    report_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "timestamp": int(time.time()),
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
                "qa_score": j.qa_score,
                "passed": j.qa_passed,
                "refined": j.refined,
                "status": j.status,
                "issues": j.qa_issues[:3],
                "error": j.error,
            }
            for j in jobs
        ],
    }
    report_path = report_dir / f"production-report-{int(time.time())}.json"
    report_path.write_text(json.dumps(report, indent=2))
    log.info("Report: %s", report_path)

    return jobs
