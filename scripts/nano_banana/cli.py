"""CLI entry point — argparse with subcommands.

Usage:
    python scripts/nano-banana-run.py generate --sku br-001
    python scripts/nano-banana-run.py generate --step all
    python scripts/nano-banana-run.py composite --sku br-001
    python scripts/nano-banana-run.py dry-run
    python scripts/nano-banana-run.py generate --pro --step branding
"""

from __future__ import annotations

import argparse
import logging
import time
from pathlib import Path

log = logging.getLogger("nano-banana")

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
MAX_RETRIES = 3
RETRY_DELAY = 5


def _resolve_views(step: str) -> list[str]:
    """Map step name to list of views to generate."""
    return {
        "front": ["front"],
        "back": ["back"],
        "branding": ["branding"],
        "all": ["front", "back", "branding"],
        "front_back": ["front", "back"],
    }.get(step, ["front", "back", "branding"])


def cmd_dry_run(args):
    """Show what would be generated without making API calls."""
    from nano_banana.catalog import PRODUCTS_DIR, load_catalog, load_products

    catalog = load_catalog()
    products = load_products(
        catalog, sku_filter=args.sku, collection_filter=getattr(args, "collection", None)
    )
    views = _resolve_views(args.step)

    print(f"\n{'=' * 60}")
    print("Nano Banana 2 — DRY RUN")
    print(f"Products: {len(products)} | Views: {views}")
    print(f"Output dir: {PRODUCTS_DIR}")
    print(f"{'=' * 60}\n")

    found = 0
    missing = 0
    for p in products:
        src = p["source_image"]
        status = f"SOURCE: {src.name}" if src else "NO SOURCE"
        icon = "+" if src else "x"
        print(f"  [{icon}] {p['sku']:20s} {p['name']:40s} {status}")
        if src:
            found += 1
        else:
            missing += 1

    print(f"\nReady: {found} | Missing source: {missing} | Total: {len(products)}")


def cmd_generate(args):
    """Generate product images."""
    from nano_banana.catalog import (
        PRODUCTS_DIR,
        find_back_source,
        get_material_spec,
        load_catalog,
        load_products,
    )
    from nano_banana.client import get_genai_client, get_openai_client, get_together_client
    from nano_banana.generate import (
        GEMINI_FAST,
        GEMINI_PRO,
        generate_flux,
        generate_gemini,
        generate_gpt,
    )
    from nano_banana.prompts import flux_prompt, get_prompt
    from nano_banana.qa import vision_compare
    from nano_banana.utils import get_output_filename, quality_gate, save_image

    catalog = load_catalog()
    products = load_products(
        catalog, sku_filter=args.sku, collection_filter=getattr(args, "collection", None)
    )
    views = _resolve_views(args.step)
    model = GEMINI_PRO if args.pro else args.model or GEMINI_FAST
    engine = args.engine

    # Initialize clients
    genai_client = get_genai_client()
    together_client = get_together_client() if engine in ("flux", "auto") else None
    openai_client = get_openai_client() if engine == "gpt-image" else None

    tech_flat_skus = {sku for sku, p in catalog.items() if p.get("is_tech_flat")}

    log.info(
        "Starting: %d products, views=%s, model=%s, engine=%s",
        len(products),
        views,
        model,
        engine,
    )

    success_count = 0
    for i, product in enumerate(products, 1):
        sku = product["sku"]
        src = product["source_image"]

        use_flux = engine == "flux" or (engine == "auto" and sku in tech_flat_skus)
        use_gpt = engine == "gpt-image"

        if not use_flux and not use_gpt and not src:
            log.warning("[%d/%d] SKIP %s: no source image", i, len(products), sku)
            continue

        engine_label = "FLUX" if use_flux else "GPT-Image" if use_gpt else f"Gemini ({model})"
        log.info("[%d/%d] %s — %s", i, len(products), sku, engine_label)

        product_ok = True
        for view in views:
            if product["is_accessory"] and view == "back":
                continue

            out_path = PRODUCTS_DIR / get_output_filename(sku, view, product["output_slug"])

            # Get view-specific source
            view_src = src
            if view == "back":
                back = find_back_source(sku, catalog)
                if back:
                    view_src = back

            prompt = get_prompt(product, view)
            image_bytes = None

            # Load bundle reference images (logo, patches, product photos)
            from nano_banana.pipeline import _find_bundle_dir

            extra_refs = []
            bundle_dir = _find_bundle_dir(product["name"], sku)
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
                            extra_refs.append((label, f))
                            break

            for attempt in range(1, MAX_RETRIES + 1):
                if use_flux:
                    fp = flux_prompt(product["name"], view)
                    image_bytes = generate_flux(together_client, fp, use_free=args.free)
                elif use_gpt:
                    image_bytes = generate_gpt(openai_client, prompt, view_src)
                else:
                    image_bytes = generate_gemini(
                        genai_client,
                        view_src,
                        prompt,
                        model=model,
                        enhanced=(attempt > 1),
                        extra_refs=extra_refs if extra_refs else None,
                    )

                if image_bytes and quality_gate(image_bytes, sku, view):
                    # Optional vision QA
                    if args.qa and view_src and not use_flux:
                        qa_result = vision_compare(
                            genai_client, view_src, image_bytes, product["name"], view
                        )
                        if not qa_result.get("pass", True) and attempt < MAX_RETRIES:
                            issues = qa_result.get("issues", [])
                            log.warning(
                                "QA FAIL %s %s (score=%s): %s",
                                sku,
                                view,
                                qa_result.get("score"),
                                issues,
                            )
                            image_bytes = None
                            time.sleep(RETRY_DELAY)
                            continue
                    break

                if attempt < MAX_RETRIES:
                    log.info("Retry %d/%d for %s %s", attempt, MAX_RETRIES, sku, view)
                    time.sleep(RETRY_DELAY)
                image_bytes = None

            if image_bytes:
                save_image(image_bytes, out_path)
            else:
                log.error("FAILED %s %s after %d attempts", sku, view, MAX_RETRIES)
                product_ok = False

            # Rate limit between views
            time.sleep(3)

        if product_ok:
            success_count += 1

    log.info("COMPLETE: %d/%d products successful", success_count, len(products))


def cmd_composite(args):
    """Composite real branding onto AI lifestyle shots."""
    from nano_banana.catalog import PRODUCTS_DIR, load_catalog, load_products
    from nano_banana.client import get_genai_client
    from nano_banana.generate import GEMINI_FAST, GEMINI_PRO, composite_gemini
    from nano_banana.prompts import composite_prompt
    from nano_banana.utils import quality_gate, save_image

    catalog = load_catalog()
    products = load_products(
        catalog, sku_filter=args.sku, collection_filter=getattr(args, "collection", None)
    )
    model = GEMINI_PRO if args.pro else GEMINI_FAST
    client = get_genai_client()

    views = ["front", "back", "branding"] if args.step == "composite_all" else ["front"]

    log.info("Compositing: %d products, views=%s, model=%s", len(products), views, model)

    for i, product in enumerate(products, 1):
        sku = product["sku"]
        src = product["source_image"]
        if not src:
            log.warning("[%d/%d] SKIP %s: no source", i, len(products), sku)
            continue

        for view in views:
            suffix = {
                "front": "front-model.webp",
                "back": "back-model.webp",
                "branding": "branding.webp",
            }[view]
            ai_render = PRODUCTS_DIR / f"{sku}-{suffix}"
            if not ai_render.exists():
                log.warning("SKIP %s %s: no AI render at %s", sku, view, ai_render.name)
                continue

            log.info("[%d/%d] Compositing %s %s...", i, len(products), sku, view)
            prompt = composite_prompt(product["name"], sku, view)

            image_bytes = None
            for attempt in range(1, MAX_RETRIES + 1):
                image_bytes = composite_gemini(client, ai_render, src, prompt, model=model)
                if image_bytes and quality_gate(image_bytes, sku, f"composite_{view}"):
                    break
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY)
                image_bytes = None

            if image_bytes:
                out_path = PRODUCTS_DIR / f"{product['output_slug']}-composite-{view}.webp"
                save_image(image_bytes, out_path)
            else:
                log.error("FAILED composite %s %s", sku, view)

            time.sleep(3)


def cmd_verify_generate(args):
    """Run full verified generation pipeline for one SKU+view."""
    from nano_banana.catalog import find_back_source, find_source_image, load_catalog
    from nano_banana.verify_pipeline import (
        promote_winner_to_production,
        save_verify_result,
        verify_generate,
    )

    catalog = load_catalog()
    if args.sku not in catalog:
        log.error("SKU %s not in catalog", args.sku)
        return

    info = catalog[args.sku]
    if args.view == "back":
        src = find_back_source(args.sku, catalog) or find_source_image(args.sku, catalog)
    else:
        src = find_source_image(args.sku, catalog)

    if not src:
        log.error("No source image for %s", args.sku)
        return

    log.info("Starting verified generation: %s %s", args.sku, args.view)
    result = verify_generate(
        sku=args.sku,
        view=args.view,
        source_path=src,
        collection=info["collection"],
        max_cycles=args.cycles,
        n_candidates=args.candidates,
        passing_threshold=args.threshold,
    )

    save_verify_result(result)

    log.info("=" * 60)
    log.info("RESULT: %s %s", args.sku, args.view)
    log.info("  Cycles run:       %d", result.cycles_run)
    log.info("  Total candidates: %d", result.total_candidates)
    log.info("  Winner score:     %.1f", result.winner_score)
    log.info("  Passed 98%%:      %s", result.passed_98)
    log.info("  All scores:       %s", [round(s, 1) for s in result.all_scores])
    log.info("=" * 60)

    if args.promote and result.winner_path:
        promote_winner_to_production(result, info["output_slug"])


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    parser = argparse.ArgumentParser(
        prog="nano-banana",
        description="Nano Banana 2 — SkyyRose AI Image Pipeline (Official Google genai SDK)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # -- dry-run --
    dr = sub.add_parser("dry-run", help="Preview what would be generated")
    dr.add_argument("--sku", type=str, default=None, help="Single SKU to process")
    dr.add_argument(
        "--collection",
        type=str,
        default=None,
        help="Filter by collection slug (e.g. black-rose, signature, love-hurts, kids-capsule)",
    )
    dr.add_argument(
        "--step",
        type=str,
        default="all",
        choices=["front", "back", "branding", "all", "front_back"],
    )

    # -- generate --
    gen = sub.add_parser("generate", help="Generate product images")
    gen.add_argument("--sku", type=str, default=None, help="Single SKU to process")
    gen.add_argument(
        "--collection",
        type=str,
        default=None,
        help="Filter by collection slug (e.g. black-rose, signature, love-hurts, kids-capsule)",
    )
    gen.add_argument(
        "--step",
        type=str,
        default="all",
        choices=["front", "back", "branding", "all", "front_back"],
    )
    gen.add_argument(
        "--engine", type=str, default="gemini", choices=["gemini", "flux", "gpt-image", "auto"]
    )
    gen.add_argument("--model", type=str, default=None, help="Override Gemini model ID")
    gen.add_argument(
        "--pro", action="store_true", help="Use Nano Banana Pro (gemini-3-pro-image-preview)"
    )
    gen.add_argument("--qa", action="store_true", help="Run Gemini vision QA after generation")
    gen.add_argument("--free", action="store_true", help="Use free FLUX model (lower quality)")

    # -- generate-async --
    ga = sub.add_parser("generate-async", help="Async parallel generation (3 concurrent)")
    ga.add_argument("--sku", type=str, default=None, help="Single SKU to process")
    ga.add_argument(
        "--collection",
        type=str,
        default=None,
        help="Filter by collection slug (e.g. black-rose, signature, love-hurts, kids-capsule)",
    )
    ga.add_argument(
        "--step",
        type=str,
        default="all",
        choices=["front", "back", "branding", "all", "front_back"],
    )
    ga.add_argument("--model", type=str, default=None, help="Override Gemini model ID")
    ga.add_argument(
        "--pro", action="store_true", help="Use Nano Banana Pro (gemini-3-pro-image-preview)"
    )
    ga.add_argument(
        "--concurrency", type=int, default=3, help="Max concurrent API calls (default 3)"
    )

    # -- composite --
    comp = sub.add_parser("composite", help="Composite real branding onto AI shots")
    comp.add_argument("--sku", type=str, default=None, help="Single SKU to process")
    comp.add_argument(
        "--collection",
        type=str,
        default=None,
        help="Filter by collection slug (e.g. black-rose, signature, love-hurts, kids-capsule)",
    )
    comp.add_argument(
        "--step", type=str, default="composite", choices=["composite", "composite_all"]
    )
    comp.add_argument("--pro", action="store_true", help="Use Nano Banana Pro model")

    # -- verify-generate --
    vg = sub.add_parser(
        "verify-generate", help="Full verified generation pipeline (DNA + tournament + regen)"
    )
    vg.add_argument("--sku", type=str, required=True, help="Product SKU")
    vg.add_argument("--view", type=str, default="front", choices=["front", "back", "branding"])
    vg.add_argument("--cycles", type=int, default=3, help="Max regen cycles (default 3)")
    vg.add_argument("--candidates", type=int, default=3, help="Candidates per cycle (default 3)")
    vg.add_argument(
        "--threshold", type=float, default=92.0, help="Passing score threshold (default 92)"
    )
    vg.add_argument("--promote", action="store_true", help="Copy winner to production directory")

    # -- produce (v4 production pipeline — sequential) --
    prod = sub.add_parser("produce", help="V4 production pipeline — sequential (legacy)")
    prod.add_argument("--sku", type=str, default=None, help="Single SKU to process")
    prod.add_argument(
        "--collection",
        type=str,
        default=None,
        help="Filter by collection slug (e.g. black-rose, signature, love-hurts, kids-capsule)",
    )
    prod.add_argument(
        "--views", type=str, default="front,back,branding", help="Comma-separated views"
    )
    prod.add_argument(
        "--fast", action="store_true", help="Use fast preset (lower quality, lower cost)"
    )
    prod.add_argument("--config", type=str, default=None, help="Path to pipeline-config.json")
    prod.add_argument(
        "--cost-only", action="store_true", help="Show cost estimate without generating"
    )

    # -- produce-async (staged production pipeline) --
    pa = sub.add_parser(
        "produce-async", help="Staged async production — vision → generate → QA → refine"
    )
    pa.add_argument("--sku", type=str, default=None, help="Single SKU to process")
    pa.add_argument(
        "--collection",
        type=str,
        default=None,
        help="Filter by collection slug (e.g. black-rose, signature, love-hurts, kids-capsule)",
    )
    pa.add_argument("--views", type=str, default="front,back", help="Comma-separated views")
    pa.add_argument("--concurrency", type=int, default=3, help="Max concurrent API calls per stage")
    pa.add_argument("--model", type=str, default=None, help="Override generation model")

    args = parser.parse_args()

    if args.command == "dry-run":
        cmd_dry_run(args)
    elif args.command == "generate":
        cmd_generate(args)
    elif args.command == "generate-async":
        import asyncio

        asyncio.run(cmd_generate_async(args))
    elif args.command == "composite":
        cmd_composite(args)
    elif args.command == "verify-generate":
        cmd_verify_generate(args)
    elif args.command == "produce":
        cmd_produce(args)
    elif args.command == "produce-async":
        import asyncio

        asyncio.run(cmd_produce_async(args))


async def cmd_generate_async(args):
    """Async parallel generation with error boundaries."""
    import asyncio

    from nano_banana.catalog import (
        PRODUCTS_DIR,
        find_back_source,
        get_material_spec,
        load_catalog,
        load_products,
    )
    from nano_banana.client import get_genai_client
    from nano_banana.generate import GEMINI_FAST, GEMINI_PRO, generate_gemini_async
    from nano_banana.pipeline import _find_bundle_dir
    from nano_banana.prompts import get_prompt
    from nano_banana.utils import get_output_filename, quality_gate, save_image

    catalog = load_catalog()
    products = load_products(
        catalog, sku_filter=args.sku, collection_filter=getattr(args, "collection", None)
    )
    views = _resolve_views(args.step)
    model = GEMINI_PRO if args.pro else args.model or GEMINI_FAST
    concurrency = args.concurrency
    client = get_genai_client()

    semaphore = asyncio.Semaphore(concurrency)
    results: dict[str, str] = {}  # "sku-view" -> "PASS" | "FAIL" | "SKIP"

    async def generate_one(product: dict, view: str) -> None:
        sku = product["sku"]
        key = f"{sku}-{view}"
        src = product["source_image"]

        if product["is_accessory"] and view == "back":
            results[key] = "SKIP"
            return

        if not src:
            log.warning("SKIP %s %s: no source", sku, view)
            results[key] = "SKIP"
            return

        view_src = src
        if view == "back":
            back = find_back_source(sku, catalog)
            if back:
                view_src = back

        prompt = get_prompt(product, view)

        # Load bundle refs
        extra_refs = []
        bundle_dir = _find_bundle_dir(product["name"], sku)
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
                        extra_refs.append((label, f))
                        break

        out_path = PRODUCTS_DIR / get_output_filename(sku, view, product["output_slug"])

        async with semaphore:
            for attempt in range(1, MAX_RETRIES + 1):
                try:
                    img_bytes = await generate_gemini_async(
                        client,
                        view_src,
                        prompt,
                        model=model,
                        enhanced=(attempt > 1),
                        extra_refs=extra_refs if extra_refs else None,
                    )
                except Exception as exc:
                    log.error("[%s %s] attempt %d error: %s", sku, view, attempt, exc)
                    img_bytes = None

                if img_bytes and quality_gate(img_bytes, sku, view):
                    save_image(img_bytes, out_path)
                    log.info("PASS %s %s: %.1fKB", sku, view, len(img_bytes) / 1024)
                    results[key] = "PASS"
                    return

                if attempt < MAX_RETRIES:
                    log.info("Retry %d/%d for %s %s", attempt, MAX_RETRIES, sku, view)
                    await asyncio.sleep(RETRY_DELAY)

            log.error("FAIL %s %s after %d attempts", sku, view, MAX_RETRIES)
            results[key] = "FAIL"

    # Build task list
    tasks = []
    for product in products:
        for view in views:
            tasks.append(generate_one(product, view))

    total = len(tasks)
    log.info("ASYNC: %d tasks, %d concurrent, model=%s", total, concurrency, model)

    await asyncio.gather(*tasks)

    # Summary
    passed = sum(1 for v in results.values() if v == "PASS")
    failed = sum(1 for v in results.values() if v == "FAIL")
    skipped = sum(1 for v in results.values() if v == "SKIP")
    log.info("COMPLETE: %d passed / %d failed / %d skipped", passed, failed, skipped)

    if failed:
        log.info("Failed:")
        for k, v in results.items():
            if v == "FAIL":
                log.info("  %s", k)


async def cmd_produce_async(args):
    """Staged async production pipeline — maximum throughput."""
    import asyncio as _asyncio

    from nano_banana.catalog import load_catalog, load_products
    from nano_banana.produce_async import run_production

    catalog = load_catalog()
    products = load_products(
        catalog, sku_filter=args.sku, collection_filter=getattr(args, "collection", None)
    )
    views = [v.strip() for v in args.views.split(",")]

    if not products:
        log.error("No products found")
        return

    # Global batch timeout: 30 min for full catalog, 10 min per collection, 5 min per SKU
    collection = getattr(args, "collection", None)
    batch_timeout = 300 if args.sku else (600 if collection else 1800)

    log.info("=== STAGED ASYNC PRODUCTION ===")
    log.info(
        "Products: %d | Views: %s | Concurrency: %d | Timeout: %ds",
        len(products),
        views,
        args.concurrency,
        batch_timeout,
    )

    try:
        jobs = await _asyncio.wait_for(
            run_production(
                products=products,
                views=views,
                catalog=catalog,
                concurrency=args.concurrency,
                model_override=args.model,
            ),
            timeout=batch_timeout,
        )
    except TimeoutError:
        log.error(
            "BATCH TIMEOUT after %ds — partial results may exist in output dir", batch_timeout
        )
        return

    # Final status
    passed = sum(1 for j in jobs if j.qa_passed)
    total = len(jobs)
    log.info("\nDONE: %d/%d passed QA", passed, total)


def cmd_produce(args):
    """V4 production pipeline — vision-first, intelligent routing, QA, refinement."""
    from nano_banana.catalog import load_catalog, load_products
    from nano_banana.config import PipelineConfig
    from nano_banana.pipeline import ProductionPipeline
    from nano_banana.router import estimate_batch_cost

    # Load config
    if args.config:
        config = PipelineConfig.from_json(Path(args.config))
    elif args.fast:
        config = PipelineConfig.fast()
    else:
        config = PipelineConfig.production()

    views = [v.strip() for v in args.views.split(",")]
    catalog = load_catalog()
    products = load_products(
        catalog, sku_filter=args.sku, collection_filter=getattr(args, "collection", None)
    )

    if not products:
        log.error("No products found")
        return

    # Cost estimate
    cost = estimate_batch_cost(products, views)
    log.info("\n--- Cost Estimate ---")
    log.info("Images: %d", cost["image_count"])
    log.info("Estimated cost: $%.2f", cost["total_usd"])
    for engine, amount in cost["per_engine"].items():
        log.info("  %s: $%.2f", engine, amount)

    if args.cost_only:
        return

    log.info("\n--- Starting Production Pipeline (v4) ---")
    log.info(
        "Products: %d | Views: %s | Config: %s",
        len(products),
        views,
        "fast" if args.fast else "production",
    )

    # Initialize pipeline
    pipeline = ProductionPipeline.from_env()
    pipeline.config = config

    # Run batch
    results = pipeline.run_batch(products, views=views)

    # Print summary
    passed = [r for r in results if r.qa_passed]
    review = [r for r in results if r.output_path and not r.qa_passed]
    failed = [r for r in results if not r.output_path]

    log.info("\n--- FINAL SUMMARY ---")
    for r in results:
        status = "PASS" if r.qa_passed else "REVIEW" if r.output_path else "FAIL"
        log.info(
            "  %s %-20s %-8s engine=%-12s score=%.1f $%.3f %s",
            status,
            r.sku,
            r.view,
            r.engine_used,
            r.qa_score,
            r.cost_usd,
            "[refined]" if r.refinement_applied else "",
        )


if __name__ == "__main__":
    main()
