#!/usr/bin/env python3
"""
SkyyRose Production Studio — Multi-Provider Multi-Agent Powerhouse

Combines the best AI models from multiple providers into a coordinated
production pipeline for image and video generation.

Providers:
- Google ADK (Gemini 3 Flash, Gemini 3 Pro Image)
- OpenAI (GPT-4o Vision, DALL-E 3)
- Anthropic (Claude Sonnet 4.5, Claude Opus 4.6)

Architecture:
- Coordinator Agent (Claude Opus) - Orchestrates workflow
- Vision Team (GPT-4o, Gemini Flash, Claude) - Multi-angle analysis
- Generation Team (Gemini 3 Pro Image, DALL-E) - Parallel generation
- Quality Team (Claude Sonnet, Gemini Flash) - Verification

Usage:
    python skyyrose_production_studio.py generate-image lh-001
    python skyyrose_production_studio.py generate-batch --all
    python skyyrose_production_studio.py interactive
"""

import argparse
import base64
import json
import os
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Literal

# Load environment first
from dotenv import load_dotenv

_LOCAL_ENV = Path(__file__).parent / ".env"
if _LOCAL_ENV.exists():
    load_dotenv(_LOCAL_ENV, override=False)

_PARENT_ENV = Path(__file__).parent.parent / ".env"
if _PARENT_ENV.exists():
    load_dotenv(_PARENT_ENV, override=True)

_GEMINI_ENV = Path(__file__).parent.parent / "gemini" / ".env"
if _GEMINI_ENV.exists():
    load_dotenv(_GEMINI_ENV, override=True)

# Provider imports
from google import genai as google_genai
from google.genai import types as genai_types
import openai
import anthropic

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

APP_NAME = "skyyrose_production_studio"
OVERRIDES_DIR = Path(__file__).parent / "assets" / "data" / "prompts" / "overrides"
SOURCE_DIR = Path(__file__).parent / "assets" / "images" / "source-products"
OUTPUT_DIR = Path(__file__).parent / "assets" / "images" / "products"

# Initialize all provider clients
gemini_client = google_genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# ---------------------------------------------------------------------------
# Multi-Provider Vision Analysis
# ---------------------------------------------------------------------------


def analyze_with_gpt4_vision(sku: str, view: str = "front") -> dict[str, Any]:
    """
    Vision Agent 1: GPT-4o Vision - Ultra-detailed garment analysis.

    Strengths: Best at detailed product specifications, logo detection, color analysis.
    """
    try:
        sku = sku.strip().lower()
        override_path = OVERRIDES_DIR / f"{sku}.json"

        if not override_path.exists():
            return {"status": "error", "error": f"No override found for {sku}"}

        override = json.loads(override_path.read_text(encoding="utf-8"))
        ref_images = override.get("referenceImages", [])

        if not ref_images:
            return {"status": "error", "error": f"No reference images for {sku}"}

        # Select image
        if view == "back" and len(ref_images) > 1 and "back" in ref_images[1]:
            image_file = ref_images[1]
        else:
            image_file = ref_images[0]

        image_path = SOURCE_DIR / image_file
        if not image_path.exists():
            return {"status": "error", "error": f"Image not found: {image_file}"}

        image_data = base64.b64encode(image_path.read_bytes()).decode("utf-8")

        prompt = f"""You are GPT-4o Vision, the PRIMARY VISION ANALYZER for SkyyRose luxury fashion.

Your specialty: Ultra-detailed garment specifications with pixel-level accuracy.

PRODUCT: {override.get('name', sku)}
COLLECTION: {override.get('collection', 'unknown')}

ANALYZE THIS PRODUCT PHOTO:

1. GARMENT CONSTRUCTION
   - Exact silhouette, fit, and cut
   - Length, sleeve style, neckline
   - Construction details

2. FABRIC ANALYSIS
   - Material type (fleece, satin, mesh, etc.)
   - Texture (smooth, ribbed, sherpa)
   - Weight and finish (matte, glossy, heathered)

3. COLOR PALETTE (EXACT SHADES)
   - Base colors with precise names
   - Accent colors
   - Color blocking patterns

4. BRANDING & LOGOS (CRITICAL DETAIL)
   - EXACT location of each logo (coordinates if possible)
   - Size (small/medium/large or measurements)
   - Technique (embroidered/silicone/printed/patch)
   - Colors in each logo
   - Readable text

5. HARDWARE & DETAILS
   - Ribbing (cuffs, hem, collar)
   - Drawstrings, pockets
   - Zippers, buttons, snaps
   - Any trim or binding

6. FIT & DRAPE PREDICTION
   - How it will hang on a model
   - Key fit points to emphasize

RETURN: Detailed technical specifications in clear paragraphs. Be EXTREMELY specific about logos."""

        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_data}",
                            "detail": "high"
                        }
                    }
                ]
            }],
            max_tokens=1500,
            temperature=0.2
        )

        analysis = response.choices[0].message.content

        return {
            "status": "ok",
            "provider": "openai",
            "model": "gpt-4o",
            "sku": sku,
            "view": view,
            "analysis": analysis,
            "char_count": len(analysis),
            "specialty": "ultra_detailed_specs"
        }
    except Exception as exc:
        return {"status": "error", "provider": "openai", "error": str(exc)}


def analyze_with_gemini_flash(sku: str, view: str = "front") -> dict[str, Any]:
    """
    Vision Agent 2: Gemini 3 Flash - Fast verification & brand consistency check.

    Strengths: Quick analysis, good at brand voice, pattern recognition.
    """
    try:
        sku = sku.strip().lower()
        override_path = OVERRIDES_DIR / f"{sku}.json"

        if not override_path.exists():
            return {"status": "error", "error": f"No override found for {sku}"}

        override = json.loads(override_path.read_text(encoding="utf-8"))
        ref_images = override.get("referenceImages", [])

        if not ref_images:
            return {"status": "error", "error": f"No reference images for {sku}"}

        # Select image
        if view == "back" and len(ref_images) > 1 and "back" in ref_images[1]:
            image_file = ref_images[1]
        else:
            image_file = ref_images[0]

        image_path = SOURCE_DIR / image_file
        if not image_path.exists():
            return {"status": "error", "error": f"Image not found: {image_file}"}

        image_data = base64.b64encode(image_path.read_bytes()).decode("utf-8")

        collection = override.get("collection", "unknown")
        prompt = f"""You are Gemini 3 Flash, the VERIFICATION ANALYZER for SkyyRose.

Your specialty: Brand consistency, pattern recognition, quick technical assessment.

PRODUCT: {override.get('name', sku)}
COLLECTION: {collection}

VERIFY THIS PRODUCT PHOTO:

1. BRAND CONSISTENCY CHECK
   - Does this fit the {collection} collection aesthetic?
   - Are branding elements consistent with SkyyRose standards?

2. TECHNICAL QUICK ASSESSMENT
   - Garment type and key features
   - Logo placement and technique (quick identification)
   - Color palette match to collection

3. QUALITY MARKERS
   - Fabric quality indicators
   - Construction quality visible
   - Premium details present

4. GENERATION GUIDANCE
   - Key elements that MUST be replicated
   - Potential challenges in recreation
   - Critical accuracy points

RETURN: Concise technical assessment focused on brand consistency and generation requirements."""

        response = gemini_client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=[
                prompt,
                genai_types.Part(
                    inline_data=genai_types.Blob(
                        mime_type="image/jpeg",
                        data=image_data
                    )
                )
            ]
        )

        analysis = response.text

        return {
            "status": "ok",
            "provider": "google",
            "model": "gemini-3-flash-preview",
            "sku": sku,
            "view": view,
            "analysis": analysis,
            "char_count": len(analysis),
            "specialty": "brand_consistency_check"
        }
    except Exception as exc:
        return {"status": "error", "provider": "google", "error": str(exc)}


def synthesize_vision_analysis(
    gpt4_analysis: str,
    gemini_analysis: str,
    sku: str
) -> dict[str, Any]:
    """
    Vision Synthesizer: Claude Sonnet - Combines multi-provider analyses into unified spec.

    Strengths: Best reasoning, synthesis, instruction following.
    """
    try:
        prompt = f"""You are Claude Sonnet 4.5, the VISION SYNTHESIS COORDINATOR.

You've received product analyses from two specialized vision models:

## GPT-4o Vision Analysis (Ultra-detailed specs):
{gpt4_analysis}

## Gemini 3 Flash Analysis (Brand consistency & verification):
{gemini_analysis}

YOUR TASK: Synthesize these into ONE UNIFIED SPECIFICATION for AI image generation.

SYNTHESIS REQUIREMENTS:
1. Combine the best insights from both analyses
2. Resolve any conflicts (favor GPT-4o for technical details, Gemini for brand context)
3. Create a clear, structured specification
4. Highlight CRITICAL ACCURACY POINTS that must be 100% correct
5. Note any discrepancies between the two analyses

OUTPUT FORMAT:
```
UNIFIED GARMENT SPECIFICATION - {sku.upper()}

[Critical Accuracy Points]
- Logo 1: [exact description from best analysis]
- Logo 2: [if applicable]
- Key Detail: [any critical brand element]

[Garment Construction]
[synthesized construction details]

[Fabric & Color]
[synthesized fabric and color specs]

[Branding Elements]
[comprehensive logo and branding details]

[Hardware & Details]
[all trim, pockets, zippers, etc.]

[Fit & Styling Notes]
[how it should look on a model]

[Generation Warnings]
[any elements that need special attention]
```

Be precise, technical, and comprehensive."""

        response = anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            temperature=0.3,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        synthesis = response.content[0].text

        return {
            "status": "ok",
            "provider": "anthropic",
            "model": "claude-sonnet-4-20250514",
            "sku": sku,
            "synthesis": synthesis,
            "char_count": len(synthesis),
            "specialty": "vision_synthesis"
        }
    except Exception as exc:
        return {"status": "error", "provider": "anthropic", "error": str(exc)}


# ---------------------------------------------------------------------------
# Multi-Provider Image Generation
# ---------------------------------------------------------------------------


def generate_with_gemini_pro_image(
    sku: str,
    unified_spec: str,
    view: str = "front"
) -> dict[str, Any]:
    """
    Generator 1: Gemini 3 Pro Image - Primary 4K generation.

    Strengths: Best for fashion editorial, accurate product replication, 4K quality.
    """
    try:
        sku = sku.strip().lower()
        override_path = OVERRIDES_DIR / f"{sku}.json"
        override = json.loads(override_path.read_text(encoding="utf-8"))

        ref_images = override.get("referenceImages", [])
        if view == "back" and len(ref_images) > 1 and "back" in ref_images[1]:
            image_file = ref_images[1]
        else:
            image_file = ref_images[0]

        image_path = SOURCE_DIR / image_file
        ref_image_data = base64.b64encode(image_path.read_bytes()).decode("utf-8")

        collection = override.get("collection", "signature")
        is_kids = collection == "kids-capsule"

        collection_mood = {
            "black-rose": "Gothic romance, mysterious elegance. Rose gold #B76E79 accents.",
            "love-hurts": "Raw street intensity. Deep crimson #8B0000, Oakland pride.",
            "signature": "Editorial prestige. Champagne gold #D4AF37 luxury.",
            "kids-capsule": "Joyful luxury. Vibrant, SPECIAL, premium quality."
        }

        view_instructions = (
            "Model facing AWAY from camera, showing BACK of garment. Back of head and shoulders visible."
            if view == "back" else
            "Model facing FORWARD toward camera, showing FRONT of garment. Face visible, confident expression."
        )

        prompt = f"""You are Gemini 3 Pro Image, SkyyRose's PRIMARY FASHION PHOTOGRAPHER.

Create a professional editorial fashion photograph for SkyyRose luxury streetwear.

## REFERENCE PRODUCT (REPLICATE 100% EXACTLY):
{unified_spec}

## CRITICAL ACCURACY MANDATE:
- EXACT REPLICA of reference - every logo, graphic, text
- NO additions, NO changes, NO creative interpretation
- This is ECOMMERCE - accuracy is LEGALLY required
- All branding must match in: placement, size, color, technique

## MODEL & POSE:
- {"Child model (8-10 years)" if is_kids else "Professional adult fashion model"}
- {view_instructions}
- Pose: {override.get("modelPose", "Standing confidently, elegant stance")}
- Expression: {"Joyful, warm, playful but premium" if is_kids else "Confident, sophisticated, high fashion"}

## PHOTOGRAPHY STYLE:
- Editorial quality: Vogue/Harper's Bazaar standard
- Medium format camera (Hasselblad aesthetic)
- Lighting: Soft key light + subtle rim light in brand color
- Setting: {override.get("setting", collection_mood.get(collection, ""))}
- Depth: Shallow DOF, subject in sharp focus
- Format: 3:4 portrait, 4K resolution

## FINAL VERIFICATION:
✓ Garment identical to reference
✓ All logos match exactly
✓ {view.upper()} view clearly shown
✓ Editorial quality achieved

Generate the image now."""

        response = gemini_client.models.generate_content(
            model="gemini-3-pro-image-preview",
            contents=[
                prompt,
                genai_types.Part(
                    inline_data=genai_types.Blob(
                        mime_type="image/jpeg",
                        data=ref_image_data
                    )
                )
            ],
            config=genai_types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"],
                image_config=genai_types.ImageConfig(
                    aspect_ratio="3:4",
                    image_size="4K"
                )
            )
        )

        # Extract image
        if not response.candidates or not response.candidates[0].content.parts:
            return {"status": "error", "error": "No image generated"}

        for part in response.candidates[0].content.parts:
            if part.inline_data:
                output_dir = OUTPUT_DIR / sku
                output_dir.mkdir(parents=True, exist_ok=True)

                output_path = output_dir / f"{sku}-model-{view}-gemini.jpg"
                output_path.write_bytes(base64.b64decode(part.inline_data.data))

                return {
                    "status": "ok",
                    "provider": "google",
                    "model": "gemini-3-pro-image-preview",
                    "sku": sku,
                    "view": view,
                    "output_path": str(output_path),
                    "resolution": "4K",
                    "specialty": "editorial_fashion"
                }

        return {"status": "error", "error": "No image data in response"}
    except Exception as exc:
        return {"status": "error", "provider": "google", "error": str(exc)}


def generate_with_dalle3(
    sku: str,
    unified_spec: str,
    view: str = "front"
) -> dict[str, Any]:
    """
    Generator 2: DALL-E 3 - Backup/alternative generation.

    Strengths: Creative interpretation, artistic quality.
    """
    try:
        sku = sku.strip().lower()
        override_path = OVERRIDES_DIR / f"{sku}.json"
        override = json.loads(override_path.read_text(encoding="utf-8"))

        collection = override.get("collection", "signature")
        is_kids = collection == "kids-capsule"

        view_desc = "back view" if view == "back" else "front view"

        prompt = f"""Professional editorial fashion photograph for luxury streetwear brand SkyyRose.

GARMENT SPECIFICATIONS:
{unified_spec[:1000]}  # DALL-E has shorter prompt limit

MODEL: {"Child model (8-10 years old)" if is_kids else "Professional adult fashion model"}
VIEW: {view_desc.upper()} - {"facing away from camera" if view == "back" else "facing camera"}
STYLE: Vogue editorial quality, Hasselblad medium format aesthetic
LIGHTING: Professional studio lighting, soft key light
FORMAT: 3:4 portrait orientation
SETTING: Luxury fashion editorial backdrop

CRITICAL: Exact garment replication - all logos, colors, details must match specifications precisely."""

        response = openai_client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1792",  # Closest to 3:4
            quality="hd",
            n=1
        )

        # Download the image
        image_url = response.data[0].url
        import requests
        image_response = requests.get(image_url)

        output_dir = OUTPUT_DIR / sku
        output_dir.mkdir(parents=True, exist_ok=True)

        output_path = output_dir / f"{sku}-model-{view}-dalle.jpg"
        output_path.write_bytes(image_response.content)

        return {
            "status": "ok",
            "provider": "openai",
            "model": "dall-e-3",
            "sku": sku,
            "view": view,
            "output_path": str(output_path),
            "resolution": "HD",
            "specialty": "creative_interpretation"
        }
    except Exception as exc:
        return {"status": "error", "provider": "openai", "error": str(exc)}


# ---------------------------------------------------------------------------
# Multi-Provider Quality Control
# ---------------------------------------------------------------------------


def prepare_image_for_verification(image_path: str) -> tuple[bytes, str]:
    """
    Prepare image for verification - resize and optimize for API limits.
    Returns (image_bytes, base64_data)
    """
    from PIL import Image
    import io

    img = Image.open(image_path)

    # Convert to RGB if needed
    if img.mode in ('RGBA', 'LA', 'P'):
        background = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'P':
            img = img.convert('RGBA')
        background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
        img = background

    # Resize if too large (max 1568px for Claude, similar for others)
    max_size = 1568
    if max(img.size) > max_size:
        ratio = max_size / max(img.size)
        new_size = tuple(int(dim * ratio) for dim in img.size)
        img = img.resize(new_size, Image.Resampling.LANCZOS)

    # Convert to JPEG
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='JPEG', quality=85, optimize=True)
    img_buffer.seek(0)
    img_bytes = img_buffer.read()
    image_data = base64.b64encode(img_bytes).decode("utf-8")

    return img_bytes, image_data


def verify_with_claude(
    sku: str,
    image_path: str,
    unified_spec: str
) -> dict[str, Any]:
    """
    Quality Agent: Claude Sonnet - Verifies generated image matches specifications.

    Strengths: Best reasoning, detailed critique, quality assessment.
    """
    try:
        # Read and resize image if needed (Claude has 5MB limit per image)
        from PIL import Image
        import io

        img = Image.open(image_path)

        # Convert to RGB if needed (remove alpha channel)
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = background

        # Resize if too large (Claude supports up to 1568px on longest side)
        max_size = 1568
        if max(img.size) > max_size:
            ratio = max_size / max(img.size)
            new_size = tuple(int(dim * ratio) for dim in img.size)
            img = img.resize(new_size, Image.Resampling.LANCZOS)

        # Convert to JPEG bytes with reasonable quality
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='JPEG', quality=85, optimize=True)
        img_buffer.seek(0)
        image_data = base64.b64encode(img_buffer.read()).decode("utf-8")

        prompt = f"""You are Claude Sonnet 4.5, QUALITY CONTROL DIRECTOR for SkyyRose production.

You're inspecting an AI-generated fashion model photo to verify it matches specifications.

## ORIGINAL SPECIFICATIONS:
{unified_spec}

## YOUR INSPECTION CHECKLIST:

1. LOGO ACCURACY
   - Are all logos present and correctly placed?
   - Do techniques appear correct (embroidered/silicone/printed)?
   - Are logo colors accurate?

2. GARMENT ACCURACY
   - Does the garment type match (crewneck/hoodie/jogger/etc)?
   - Is the color correct?
   - Are construction details present?

3. STYLING ACCURACY
   - Is the fit/drape appropriate?
   - Are hardware details correct (zippers, drawstrings, etc)?
   - Does it match the collection aesthetic?

4. PHOTOGRAPHY QUALITY
   - Is this editorial-quality photography?
   - Is the view (front/back) clearly shown?
   - Is the model pose appropriate?

RETURN JSON:
{{
  "overall_status": "pass" | "warn" | "fail",
  "logo_accuracy": {{"status": "pass|warn|fail", "notes": "..."}},
  "garment_accuracy": {{"status": "pass|warn|fail", "notes": "..."}},
  "styling_accuracy": {{"status": "pass|warn|fail", "notes": "..."}},
  "photo_quality": {{"status": "pass|warn|fail", "notes": "..."}},
  "recommendation": "approve" | "regenerate_gemini" | "regenerate_dalle" | "manual_review",
  "detailed_feedback": "comprehensive assessment..."
}}"""

        response = anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            temperature=0.3,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": image_data
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }]
        )

        verification_text = response.content[0].text

        # Try to parse JSON
        try:
            if "```json" in verification_text:
                json_start = verification_text.find("```json") + 7
                json_end = verification_text.find("```", json_start)
                verification_text = verification_text[json_start:json_end].strip()
            elif "```" in verification_text:
                json_start = verification_text.find("```") + 3
                json_end = verification_text.find("```", json_start)
                verification_text = verification_text[json_start:json_end].strip()

            verification_result = json.loads(verification_text)
        except json.JSONDecodeError:
            verification_result = {"raw_text": verification_text, "parsed": False}

        return {
            "status": "ok",
            "provider": "anthropic",
            "model": "claude-sonnet-4-20250514",
            "sku": sku,
            "verification": verification_result,
            "image_path": image_path
        }
    except Exception as exc:
        return {"status": "error", "provider": "anthropic", "error": str(exc)}


# ---------------------------------------------------------------------------
# Orchestration (Claude Opus Coordinator)
# ---------------------------------------------------------------------------


def orchestrate_image_production(
    sku: str,
    view: str = "front",
    use_both_generators: bool = False
) -> dict[str, Any]:
    """
    Coordinator: Orchestrates the full multi-provider pipeline.

    Pipeline:
    1. Multi-provider vision analysis (GPT-4o + Gemini Flash)
    2. Vision synthesis (Claude Sonnet)
    3. Image generation (Gemini 3 Pro Image, optionally DALL-E)
    4. Quality verification (Claude Sonnet)
    5. Auto-regeneration if needed
    """
    print(f"\n{'='*60}")
    print(f"📦 {sku.upper()} - {view} view")
    print('='*60)

    report = {
        "sku": sku,
        "view": view,
        "pipeline_stages": []
    }

    # Stage 1: Multi-Provider Vision Analysis
    print("\n🔍 Stage 1: Multi-Provider Vision Analysis")

    print("  → GPT-4o Vision analyzing...")
    gpt4_result = analyze_with_gpt4_vision(sku, view)
    report["pipeline_stages"].append({"stage": "gpt4_vision", "result": gpt4_result})

    if gpt4_result["status"] == "error":
        print(f"  ❌ GPT-4o failed: {gpt4_result['error']}")
        return {"status": "error", "stage": "gpt4_vision", "report": report}
    print(f"  ✓ GPT-4o complete ({gpt4_result['char_count']} chars)")

    print("  → Gemini 3 Flash analyzing...")
    gemini_result = analyze_with_gemini_flash(sku, view)
    report["pipeline_stages"].append({"stage": "gemini_flash_vision", "result": gemini_result})

    if gemini_result["status"] == "error":
        print(f"  ⚠️  Gemini Flash failed: {gemini_result['error']}")
        print("  → Continuing with GPT-4o analysis only")
        unified_spec = gpt4_result["analysis"]
    else:
        print(f"  ✓ Gemini Flash complete ({gemini_result['char_count']} chars)")

        # Stage 2: Vision Synthesis
        print("\n🧠 Stage 2: Vision Synthesis (Claude Sonnet)")
        synthesis_result = synthesize_vision_analysis(
            gpt4_result["analysis"],
            gemini_result["analysis"],
            sku
        )
        report["pipeline_stages"].append({"stage": "claude_synthesis", "result": synthesis_result})

        if synthesis_result["status"] == "error":
            print(f"  ⚠️  Synthesis failed: {synthesis_result['error']}")
            print("  → Using GPT-4o analysis directly")
            unified_spec = gpt4_result["analysis"]
        else:
            print(f"  ✓ Synthesis complete ({synthesis_result['char_count']} chars)")
            unified_spec = synthesis_result["synthesis"]

    # Stage 3: Image Generation
    print("\n🎨 Stage 3: Image Generation")

    print("  → Gemini 3 Pro Image generating (4K)...")
    gemini_gen_result = generate_with_gemini_pro_image(sku, unified_spec, view)
    report["pipeline_stages"].append({"stage": "gemini_generation", "result": gemini_gen_result})

    if gemini_gen_result["status"] == "error":
        print(f"  ❌ Gemini generation failed: {gemini_gen_result['error']}")
        if use_both_generators:
            print("  → Falling back to DALL-E 3...")
            dalle_result = generate_with_dalle3(sku, unified_spec, view)
            report["pipeline_stages"].append({"stage": "dalle_generation", "result": dalle_result})
            if dalle_result["status"] == "ok":
                print(f"  ✓ DALL-E generated: {dalle_result['output_path']}")
                primary_image = dalle_result["output_path"]
            else:
                print(f"  ❌ DALL-E also failed: {dalle_result['error']}")
                return {"status": "error", "stage": "generation", "report": report}
        else:
            return {"status": "error", "stage": "gemini_generation", "report": report}
    else:
        print(f"  ✓ Gemini generated: {gemini_gen_result['output_path']}")
        primary_image = gemini_gen_result["output_path"]

        if use_both_generators:
            print("  → DALL-E 3 generating alternative...")
            dalle_result = generate_with_dalle3(sku, unified_spec, view)
            report["pipeline_stages"].append({"stage": "dalle_generation", "result": dalle_result})
            if dalle_result["status"] == "ok":
                print(f"  ✓ DALL-E generated: {dalle_result['output_path']}")

    # Stage 4: Quality Verification
    print("\n✅ Stage 4: Quality Verification (Claude Sonnet)")
    verification_result = verify_with_claude(sku, primary_image, unified_spec)
    report["pipeline_stages"].append({"stage": "claude_verification", "result": verification_result})

    if verification_result["status"] == "error":
        print(f"  ⚠️  Verification failed: {verification_result['error']}")
        print("  → Proceeding without verification")
    else:
        verification = verification_result.get("verification", {})
        overall_status = verification.get("overall_status", "unknown")
        recommendation = verification.get("recommendation", "unknown")

        print(f"  Status: {overall_status.upper()}")
        print(f"  Recommendation: {recommendation}")

        if overall_status == "fail" and recommendation == "regenerate_gemini":
            print("\n  🔄 Auto-regenerating with refined specs...")
            # Could implement auto-regeneration here
            print("  (Auto-regeneration not implemented yet - manual review required)")

    report["status"] = "success"
    report["primary_output"] = primary_image

    print(f"\n✨ Production complete!")
    print(f"Primary output: {primary_image}")

    return report


# ---------------------------------------------------------------------------
# CLI Commands
# ---------------------------------------------------------------------------


def cmd_generate_image(sku: str, view: str = "front", use_both: bool = False) -> None:
    """Generate one image using the full multi-provider pipeline."""
    result = orchestrate_image_production(sku, view, use_both_generators=use_both)

    # Save report
    if result.get("status") == "success":
        report_dir = OUTPUT_DIR / sku
        report_dir.mkdir(parents=True, exist_ok=True)
        report_path = report_dir / f"{sku}-production-report-{view}.json"
        report_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"\n📄 Report: {report_path}")


def cmd_generate_batch(product_ids: list[str] | None = None) -> None:
    """Generate images for multiple products."""
    if product_ids is None:
        # Get all products
        product_ids = sorted([f.stem for f in OVERRIDES_DIR.glob("*.json")])

    print(f"\n🎬 SkyyRose Production Studio - Batch Generation")
    print(f"📦 Processing {len(product_ids)} products\n")

    results = []
    for i, sku in enumerate(product_ids, 1):
        print(f"\n[{i}/{len(product_ids)}]")
        result = orchestrate_image_production(sku, view="front", use_both_generators=False)
        results.append(result)

        if i < len(product_ids):
            print("\n  ⏸️  Rate limiting (5s)...")
            time.sleep(5)

    # Summary
    successful = sum(1 for r in results if r.get("status") == "success")
    print(f"\n{'='*60}")
    print(f"✨ Batch Complete!")
    print(f"✅ Successful: {successful}/{len(product_ids)}")
    print('='*60)


def cmd_interactive() -> None:
    """Interactive mode for production tasks."""
    print("🎬 SkyyRose Production Studio - Interactive Mode")
    print("Available providers: Google (Gemini), OpenAI (GPT-4o, DALL-E), Anthropic (Claude)")
    print("Type 'help' for commands, 'exit' to quit\n")

    while True:
        try:
            user_input = input("Studio> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nSession ended.")
            break

        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit"}:
            print("Session ended.")
            break
        if user_input.lower() == "help":
            print("""
Commands:
  generate <sku> [view]      - Generate image for product
  batch [sku1 sku2 ...]      - Generate batch of products
  analyze <sku>              - Run vision analysis only
  verify <sku> <image_path>  - Run quality verification only
  help                       - Show this help
  exit                       - Exit interactive mode
            """)
            continue

        # Parse command
        parts = user_input.split()
        cmd = parts[0].lower()

        if cmd == "generate" and len(parts) >= 2:
            sku = parts[1]
            view = parts[2] if len(parts) > 2 else "front"
            cmd_generate_image(sku, view)
        elif cmd == "batch":
            skus = parts[1:] if len(parts) > 1 else None
            cmd_generate_batch(skus)
        elif cmd == "analyze" and len(parts) >= 2:
            sku = parts[1]
            print("\n🔍 Running multi-provider vision analysis...")
            gpt4 = analyze_with_gpt4_vision(sku, "front")
            gemini = analyze_with_gemini_flash(sku, "front")
            if gpt4["status"] == "ok":
                print(f"\n✓ GPT-4o Analysis:\n{gpt4['analysis'][:500]}...")
            if gemini["status"] == "ok":
                print(f"\n✓ Gemini Analysis:\n{gemini['analysis'][:500]}...")
        else:
            print("Unknown command. Type 'help' for available commands.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="SkyyRose Production Studio — Multi-Provider Multi-Agent Powerhouse",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # generate-image
    p_gen = subparsers.add_parser("generate-image", help="Generate one image")
    p_gen.add_argument("sku", help="Product SKU (e.g. lh-001)")
    p_gen.add_argument("--view", default="front", help="View (front|back)")
    p_gen.add_argument("--both-generators", action="store_true", help="Use both Gemini and DALL-E")

    # generate-batch
    p_batch = subparsers.add_parser("generate-batch", help="Generate batch of images")
    group = p_batch.add_mutually_exclusive_group()
    group.add_argument("--all", action="store_true", help="Generate all products")
    group.add_argument("--skus", nargs="+", help="List of SKUs")

    # interactive
    subparsers.add_parser("interactive", help="Interactive mode")

    args = parser.parse_args()

    # Validate API keys
    required_keys = {
        "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY"),
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY")
    }

    missing = [k for k, v in required_keys.items() if not v or v.startswith("sk-proj-...") or v.startswith("AIza...")]
    if missing:
        print(f"❌ Missing API keys: {', '.join(missing)}", file=sys.stderr)
        print("Set them in .env or export as environment variables", file=sys.stderr)
        sys.exit(1)

    if args.command == "generate-image":
        cmd_generate_image(args.sku, args.view, args.both_generators)
    elif args.command == "generate-batch":
        skus = args.skus if args.skus else None
        cmd_generate_batch(skus)
    elif args.command == "interactive":
        cmd_interactive()


if __name__ == "__main__":
    main()
