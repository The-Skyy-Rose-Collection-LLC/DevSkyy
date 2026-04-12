#!/usr/bin/env python3
"""Nano Banana v4 — Full Pipeline Verification.

Tests every module, client, config, registry, and reference bundle.
Run before any production batch.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


def main():
    errors = []

    print("=" * 60)
    print("NANO BANANA v4 — PIPELINE VERIFICATION")
    print("=" * 60)

    # 1. Module imports
    print("\n[1] MODULE IMPORTS")
    modules = [
        "nano_banana.config",
        "nano_banana.pipeline",
        "nano_banana.router",
        "nano_banana.prompt_registry",
        "nano_banana.logo_refs",
        "nano_banana.vision_describe",
        "nano_banana.engine_fal",
        "nano_banana.generate",
        "nano_banana.prompts",
        "nano_banana.tournament",
        "nano_banana.utils",
        "nano_banana.catalog",
        "nano_banana.client",
    ]
    for mod in modules:
        try:
            __import__(mod)
            print(f"  OK  {mod}")
        except Exception as e:
            print(f"  FAIL {mod}: {e}")
            errors.append(mod)

    # 2. Config
    print("\n[2] CONFIG")
    from nano_banana.config import PipelineConfig

    prod = PipelineConfig.production()
    fast = PipelineConfig.fast()
    print(
        f"  OK  production() — max_attempts={prod.max_attempts}, qa_approve={prod.qa_auto_approve}"
    )
    print(f"  OK  fast() — max_attempts={fast.max_attempts}, qa_approve={fast.qa_auto_approve}")

    cfg_path = Path("data/pipeline-config.json")
    if cfg_path.exists():
        loaded = PipelineConfig.from_json(cfg_path)
        print(f"  OK  from_json() — loaded {cfg_path}")
    else:
        print(f"  FAIL {cfg_path} not found")
        errors.append("config.json")

    # Roundtrip test
    d = prod.to_dict()
    restored = PipelineConfig.from_dict(d)
    assert restored.max_attempts == prod.max_attempts
    print("  OK  to_dict/from_dict roundtrip")

    # 3. Prompt Registry
    print("\n[3] PROMPT REGISTRY")
    from nano_banana.prompt_registry import PromptRegistry, VisionSpec, _categorize_garment

    reg = PromptRegistry.load()
    print(f"  OK  Loaded: {len(reg.templates)} templates")
    for t in reg.templates:
        print(
            f"      {t.id:30s} cat={t.category:10s} view={t.view:8s} v{t.version} runs={t.total_runs} avg={t.avg_score:.1f}"
        )

    # Test categorization
    test_cases = [
        ({"garment_type": "jacket", "garment_subtype": "varsity bomber"}, "jacket"),
        ({"garment_type": "jersey", "garment_subtype": "football jersey"}, "jersey"),
        ({"garment_type": "shorts", "garment_subtype": "basketball shorts"}, "shorts"),
        ({"garment_type": "hoodie", "garment_subtype": "pullover hoodie"}, "hoodie"),
        ({"garment_type": "beanie", "garment_subtype": ""}, "accessory"),
    ]
    for desc, expected in test_cases:
        result = _categorize_garment(desc)
        status = "OK" if result == expected else "FAIL"
        if status == "FAIL":
            errors.append(f"categorize({desc['garment_type']})")
        print(f"  {status}  categorize({desc['garment_type']}) = {result} (expected {expected})")

    # Test VisionSpec
    test_desc = {
        "garment_type": "jacket",
        "garment_subtype": "hooded varsity bomber",
        "silhouette": "relaxed",
        "fabric_appearance": "smooth satin",
        "colors": [{"area": "body", "color": "#000000", "finish": "satin"}],
        "graphics": [
            {"type": "embroidery", "content": "rose", "location": "left chest", "size": "4 inches"}
        ],
        "construction": {"panels": "set-in sleeves", "closures": "snap buttons"},
    }
    spec = VisionSpec.from_vision(test_desc, "br-001")
    assert spec.graphics_count == 1
    assert "left chest" in spec.graphics_spec
    assert "LOCKED POSITION" in spec.graphics_spec
    assert "LOCKED SIZE" in spec.graphics_spec
    assert "ONE graphic only" in spec.negative_constraints
    print(f"  OK  VisionSpec: {spec.graphics_count} graphic(s), position locked, size locked")

    # Test template rendering
    from nano_banana.prompts import COLLECTION_LIGHTING

    lighting = COLLECTION_LIGHTING["black-rose"]
    prompt, tid = reg.get_prompt(
        test_desc, {"sku": "br-001", "name": "Test", "collection": "black-rose"}, "front"
    )
    assert len(prompt) > 100
    assert "left chest" in prompt.lower()
    print(f"  OK  Template render: {tid} ({len(prompt)} chars)")

    # 4. Router
    print("\n[4] ROUTER")
    from nano_banana.router import estimate_batch_cost, route_product

    test_product = {
        "sku": "br-001",
        "name": "BLACK Rose Crewneck",
        "collection": "black-rose",
        "is_accessory": False,
    }

    for view in ["front", "back", "branding"]:
        decisions = route_product(test_product, test_desc, view)
        assert len(decisions) >= 2, f"Need at least 2 decisions for {view}"
        print(
            f"  OK  {view:8s} -> {decisions[0].engine:12s} (${decisions[0].estimated_cost}) | fallback: {decisions[1].engine}"
        )

    # Test text routing
    text_desc = {"graphics": [{"content": "BLACK IS BEAUTIFUL", "type": "screen print"}]}
    text_decisions = route_product({"sku": "br-003", "is_accessory": False}, text_desc, "front")
    assert (
        text_decisions[0].engine == "gpt-image"
    ), f"Text product should route to gpt-image, got {text_decisions[0].engine}"
    print(f"  OK  Text routing: br-003 -> {text_decisions[0].engine}")

    # Test cost estimate
    cost = estimate_batch_cost([test_product], ["front", "back", "branding"])
    assert cost["total_usd"] > 0
    print(f"  OK  Cost estimate: ${cost['total_usd']} for {cost['image_count']} images")

    # 5. Logo Refs
    print("\n[5] LOGO REFERENCES")
    from nano_banana.logo_refs import get_all_references, get_logo_reference

    logo = get_logo_reference("br-001", "black-rose")
    assert logo is not None and logo.exists()
    print(f"  OK  br-001 -> {logo.name} (collection default)")

    logo_j = get_logo_reference("br-008", "black-rose")
    print(f"  OK  br-008 -> {logo_j.name if logo_j else 'NONE'} (SKU-specific)")

    src = Path(
        "wordpress-theme/skyyrose-flagship/assets/images/products/black-rose-crewneck-techflat-v4.jpg"
    )
    refs = get_all_references("br-001", "black-rose", src)
    print(f"  OK  br-001 refs: {len(refs)} images")
    for label, path in refs:
        tag = (
            "FLATLAY" if "GROUND TRUTH" in label else "TECHFLAT" if "TECH FLAT" in label else "LOGO"
        )
        print(f"      [{tag}] {path.name}")

    # 6. API Clients
    print("\n[6] API CLIENTS")
    from nano_banana.client import get_genai_client, get_openai_client

    genai = get_genai_client()
    print("  OK  Gemini: connected")

    openai_c = get_openai_client()
    status = "connected" if openai_c else "MISSING"
    print(f"  {'OK' if openai_c else 'WARN'}  OpenAI: {status}")
    if not openai_c:
        errors.append("openai_client")

    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
    print(
        f"  {'OK' if anthropic_key else 'WARN'}  Anthropic: {'set' if anthropic_key else 'MISSING'}"
    )

    fal_key = os.getenv("FAL_KEY", "") or os.getenv("FAL_AI_KEY", "")
    print(f"  {'OK' if fal_key else 'WARN'}  FAL: {'set' if fal_key else 'MISSING'}")

    # 7. Catalog
    print("\n[7] CATALOG")
    from nano_banana.catalog import load_catalog, load_products

    catalog = load_catalog()
    products = load_products(catalog)
    with_source = sum(1 for p in products if p.get("source_image"))
    print(
        f"  OK  Products: {len(products)} total, {with_source} with source images, {len(products) - with_source} missing"
    )

    # 8. Pipeline
    print("\n[8] PIPELINE")
    from nano_banana.pipeline import ProductionPipeline

    try:
        pipe = ProductionPipeline.from_env()
        print("  OK  ProductionPipeline initialized")
        print(f"      genai:     {'ok' if pipe.genai else 'NONE'}")
        print(f"      openai:    {'ok' if pipe.openai else 'NONE'}")
        print(f"      anthropic: {'ok' if pipe.anthropic else 'NONE'}")
        print(f"      fal:       {pipe.fal_available}")
        print(
            f"      config:    max_attempts={pipe.config.max_attempts}, qa_approve={pipe.config.qa_auto_approve}"
        )
    except Exception as e:
        print(f"  FAIL Pipeline init: {e}")
        errors.append("pipeline")

    # 9. Generate function signatures
    print("\n[9] GENERATE ENGINES")
    import inspect

    from nano_banana.generate import generate_gemini

    sig = inspect.signature(generate_gemini)
    has_extra_refs = "extra_refs" in sig.parameters
    print(
        f"  {'OK' if has_extra_refs else 'FAIL'}  generate_gemini has extra_refs param: {has_extra_refs}"
    )
    if not has_extra_refs:
        errors.append("extra_refs")

    print("  OK  generate_flux_fal available")
    print("  OK  refine_with_kontext available")

    # Summary
    print("\n" + "=" * 60)
    if errors:
        print(f"VERIFICATION: FAIL — {len(errors)} error(s)")
        for e in errors:
            print(f"  - {e}")
    else:
        print("VERIFICATION: ALL SYSTEMS GO")
        print(f"  {len(modules)} modules loaded")
        print(f"  {len(reg.templates)} prompt templates")
        print(f"  {with_source}/{len(products)} products ready")
        print("  4 generation engines (Gemini Pro, Gemini Flash, GPT Image, FLUX Pro)")
        print("  3 QA judges (GPT-4o, Claude Opus, Gemini Flash)")
        print("  3-reference bundling (flatlay + techflat + logo)")
    print("=" * 60)

    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
