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
import json
import logging
import sys
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
    from nano_banana.catalog import PRODUCTS_DIR, find_source_image, load_catalog, load_products

    catalog = load_catalog()
    products = load_products(catalog, sku_filter=args.sku)
    views = _resolve_views(args.step)

    print(f"\n{'='*60}")
    print(f"Nano Banana 2 — DRY RUN")
    print(f"Products: {len(products)} | Views: {views}")
    print(f"Output dir: {PRODUCTS_DIR}")
    print(f"{'='*60}\n")

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
        load_catalog,
        load_products,
    )
    from nano_banana.client import get_genai_client, get_openai_client, get_together_client
    from nano_banana.generate import GEMINI_FAST, GEMINI_PRO, generate_flux, generate_gemini, generate_gpt
    from nano_banana.prompts import flux_prompt, get_prompt
    from nano_banana.qa import vision_compare
    from nano_banana.utils import get_output_filename, quality_gate, save_image

    catalog = load_catalog()
    products = load_products(catalog, sku_filter=args.sku)
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
        len(products), views, model, engine,
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

            for attempt in range(1, MAX_RETRIES + 1):
                if use_flux:
                    fp = flux_prompt(product["name"], view)
                    image_bytes = generate_flux(together_client, fp, use_free=args.free)
                elif use_gpt:
                    image_bytes = generate_gpt(openai_client, prompt, view_src)
                else:
                    image_bytes = generate_gemini(
                        genai_client, view_src, prompt,
                        model=model, enhanced=(attempt > 1),
                    )

                if image_bytes and quality_gate(image_bytes, sku, view):
                    # Optional vision QA
                    if args.qa and view_src and not use_flux:
                        qa_result = vision_compare(genai_client, view_src, image_bytes, product["name"], view)
                        if not qa_result.get("pass", True) and attempt < MAX_RETRIES:
                            issues = qa_result.get("issues", [])
                            log.warning("QA FAIL %s %s (score=%s): %s", sku, view, qa_result.get("score"), issues)
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
    products = load_products(catalog, sku_filter=args.sku)
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
            suffix = {"front": "front-model.webp", "back": "back-model.webp", "branding": "branding.webp"}[view]
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
    dr.add_argument("--step", type=str, default="all", choices=["front", "back", "branding", "all", "front_back"])

    # -- generate --
    gen = sub.add_parser("generate", help="Generate product images")
    gen.add_argument("--sku", type=str, default=None, help="Single SKU to process")
    gen.add_argument("--step", type=str, default="all", choices=["front", "back", "branding", "all", "front_back"])
    gen.add_argument("--engine", type=str, default="gemini", choices=["gemini", "flux", "gpt-image", "auto"])
    gen.add_argument("--model", type=str, default=None, help="Override Gemini model ID")
    gen.add_argument("--pro", action="store_true", help="Use Nano Banana Pro (gemini-3-pro-image-preview)")
    gen.add_argument("--qa", action="store_true", help="Run Gemini vision QA after generation")
    gen.add_argument("--free", action="store_true", help="Use free FLUX model (lower quality)")

    # -- composite --
    comp = sub.add_parser("composite", help="Composite real branding onto AI shots")
    comp.add_argument("--sku", type=str, default=None, help="Single SKU to process")
    comp.add_argument("--step", type=str, default="composite", choices=["composite", "composite_all"])
    comp.add_argument("--pro", action="store_true", help="Use Nano Banana Pro model")

    args = parser.parse_args()

    if args.command == "dry-run":
        cmd_dry_run(args)
    elif args.command == "generate":
        cmd_generate(args)
    elif args.command == "composite":
        cmd_composite(args)


if __name__ == "__main__":
    main()
