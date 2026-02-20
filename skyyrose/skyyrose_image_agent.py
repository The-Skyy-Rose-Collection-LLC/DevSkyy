#!/usr/bin/env python3
"""
SkyyRose Image Generation Agent — Google ADK-powered fashion model generator.

Uses agentic reasoning with GPT-4o Vision + Gemini 3 Pro Image for maximum accuracy.

Usage:
    python skyyrose_image_agent.py generate-models lh-001
    python skyyrose_image_agent.py generate-models --all
    python skyyrose_image_agent.py verify lh-001
    python skyyrose_image_agent.py interactive
"""

import argparse
import base64
import json
import os
import sys
import time
import uuid
from pathlib import Path
from typing import Any

# Load .env before imports
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

# ADK imports
from google.adk.agents import LlmAgent
from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import FunctionTool
from google.genai import types as genai_types
from google import genai

# OpenAI for vision analysis
import openai

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

APP_NAME = "skyyrose_image_agent"
MODEL = os.getenv("SKYYROSE_MODEL", "gemini-2.0-flash")
OVERRIDES_DIR = Path(__file__).parent / "assets" / "data" / "prompts" / "overrides"
SOURCE_DIR = Path(__file__).parent / "assets" / "images" / "source-products"
OUTPUT_DIR = Path(__file__).parent / "assets" / "images" / "products"

# Initialize clients
openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# ---------------------------------------------------------------------------
# Tool functions
# ---------------------------------------------------------------------------


def get_product_override(sku: str) -> dict[str, Any]:
    """Load product override from Prompt Studio including logoFingerprint."""
    try:
        sku = sku.strip().lower()
        override_path = OVERRIDES_DIR / f"{sku}.json"

        if not override_path.exists():
            return {"status": "error", "error": f"No override found for {sku}"}

        data = json.loads(override_path.read_text(encoding="utf-8"))
        return {"status": "ok", "sku": sku, "override": data}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


def analyze_with_gpt4_vision(sku: str, view: str = "front") -> dict[str, Any]:
    """Use GPT-4o Vision to analyze source product photo for garment specifications."""
    try:
        sku = sku.strip().lower()
        override_result = get_product_override(sku)

        if override_result["status"] == "error":
            return override_result

        override = override_result["override"]
        ref_images = override.get("referenceImages", [])

        if not ref_images:
            return {"status": "error", "error": f"No reference images for {sku}"}

        # Select image based on view
        if view == "back" and len(ref_images) > 1 and "back" in ref_images[1]:
            image_file = ref_images[1]
        else:
            image_file = ref_images[0]

        image_path = SOURCE_DIR / image_file
        if not image_path.exists():
            return {"status": "error", "error": f"Image not found: {image_file}"}

        # Read and encode image
        image_data = base64.b64encode(image_path.read_bytes()).decode("utf-8")

        prompt = f"""You are a luxury fashion technical designer analyzing a garment photo for AI model generation.

PRODUCT: {override.get('name', sku)}
COLLECTION: {override.get('collection', 'unknown')}

Analyze this product photo and provide EXACT specifications for an AI model generation:

1. GARMENT TYPE & CUT
   - Exact silhouette (fitted, oversized, athletic, etc.)
   - Length (cropped, standard, extended, etc.)
   - Neckline/collar style
   - Sleeve type and length
   - Any unique construction details

2. FABRIC & TEXTURE
   - Material type (cotton fleece, satin, mesh, etc.)
   - Texture (smooth, ribbed, sherpa, etc.)
   - Weight appearance (lightweight, midweight, heavy)
   - Finish (matte, glossy, heathered, etc.)

3. COLOR PALETTE (be SPECIFIC)
   - Base color(s) with exact shade names
   - Accent colors
   - Color blocking if applicable

4. BRANDING & LOGOS (CRITICAL - describe EXACTLY what you see)
   - Location of each logo/graphic
   - Size (small, medium, large)
   - Technique (embroidered, printed, silicone, patch)
   - Colors used in logo
   - Exact text if readable

5. DETAILS & HARDWARE
   - Ribbing (cuffs, hem, collar)
   - Drawstrings, pockets
   - Zippers, buttons, snaps
   - Any other visible details

6. FIT & DRAPE
   - How it should hang on a model
   - Key fit points to emphasize

Return ONLY the analysis in clear, detailed paragraphs. Be extremely specific about logo placement and branding."""

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
            temperature=0.3
        )

        analysis = response.choices[0].message.content

        return {
            "status": "ok",
            "sku": sku,
            "view": view,
            "analysis": analysis,
            "char_count": len(analysis),
            "image_file": image_file
        }
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


def generate_model_image_with_gemini(
    sku: str,
    gpt4_analysis: str,
    view: str = "front"
) -> dict[str, Any]:
    """Generate fashion model image using Gemini 3 Pro Image with GPT-4 analysis."""
    try:
        sku = sku.strip().lower()
        override_result = get_product_override(sku)

        if override_result["status"] == "error":
            return override_result

        override = override_result["override"]
        ref_images = override.get("referenceImages", [])

        # Select reference image
        if view == "back" and len(ref_images) > 1 and "back" in ref_images[1]:
            image_file = ref_images[1]
        else:
            image_file = ref_images[0]

        image_path = SOURCE_DIR / image_file
        if not image_path.exists():
            return {"status": "error", "error": f"Image not found: {image_file}"}

        # Read reference image
        ref_image_data = base64.b64encode(image_path.read_bytes()).decode("utf-8")

        collection_mood = {
            "black-rose": "Gothic romance, mysterious elegance, dark florals. Rose gold #B76E79 accents.",
            "love-hurts": "Dramatic passion, bold intensity. Deep crimson #8B0000 with black leather.",
            "signature": "High fashion prestige, editorial excellence. Champagne gold #D4AF37 luxury.",
            "kids-capsule": "Joyful luxury, elevated kids editorial. Vibrant, SPECIAL, premium quality."
        }

        collection = override.get("collection", "signature")
        is_kids = collection == "kids-capsule"

        view_instructions = (
            "Model is facing AWAY from camera, showing the BACK of the garment. Back of head and shoulders visible. Full back view from head to below waist."
            if view == "back" else
            "Model is facing FORWARD toward camera, showing the FRONT of the garment. Face visible, confident expression. Full front view from head to below waist."
        )

        prompt = f"""Create a professional editorial fashion photograph for a luxury streetwear brand.

REFERENCE PRODUCT (match this EXACTLY):
{gpt4_analysis}

CRITICAL ACCURACY REQUIREMENTS:
- The garment must be a 100% IDENTICAL REPLICA of the reference image
- Every logo, graphic, text, and branding element must match EXACTLY in:
  * Placement, size, color, and technique
  * NO additions, NO changes, NO creative interpretation
- Fabric texture, color, and drape must match the reference perfectly
- This is for product sales - accuracy is MANDATORY

MODEL & POSE:
- {"Child model (8-10 years old appearance)" if is_kids else "Adult professional fashion model"}
- {view_instructions}
- Editorial pose: {override.get("modelPose", "Standing confidently, natural elegant stance")}
- Expression: {"Joyful, warm, playful but premium" if is_kids else "Confident, sophisticated, high fashion"}

PHOTOGRAPHY STYLE:
- Editorial quality: Vogue/Harper's Bazaar standard
- Medium format camera aesthetic (Hasselblad)
- Professional lighting: soft key light, subtle rim light in brand color
- Setting: {override.get("setting", collection_mood.get(collection, ""))}
- Shallow depth of field, subject in sharp focus
- Aspect ratio: 3:4 portrait orientation

FINAL CHECK:
✓ Garment is identical to reference (logos, colors, details)
✓ {view.upper()} view is clearly shown
✓ Professional editorial quality
✓ Brand aesthetic matches collection mood

Generate the image now."""

        # Generate with Gemini 3 Pro Image
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

        # Extract generated image
        if not response.candidates or not response.candidates[0].content.parts:
            return {"status": "error", "error": "No image generated in response"}

        for part in response.candidates[0].content.parts:
            if part.inline_data:
                # Save image
                output_dir = OUTPUT_DIR / sku
                output_dir.mkdir(parents=True, exist_ok=True)

                output_path = output_dir / f"{sku}-model-{view}.jpg"
                output_path.write_bytes(base64.b64decode(part.inline_data.data))

                # Also save GPT-4 analysis
                analysis_path = output_dir / f"{sku}-gpt4-analysis-{view}.txt"
                analysis_path.write_text(gpt4_analysis, encoding="utf-8")

                return {
                    "status": "ok",
                    "sku": sku,
                    "view": view,
                    "output_path": str(output_path),
                    "resolution": "4K",
                    "analysis_path": str(analysis_path)
                }

        return {"status": "error", "error": "No image data found in response"}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


def verify_generated_image(sku: str, view: str = "front") -> dict[str, Any]:
    """Use Gemini Flash Vision to verify the generated image matches specifications."""
    try:
        sku = sku.strip().lower()

        # Load the generated image
        image_path = OUTPUT_DIR / sku / f"{sku}-model-{view}.jpg"
        if not image_path.exists():
            return {"status": "error", "error": f"Generated image not found: {image_path}"}

        # Load the product override for logoFingerprint
        override_result = get_product_override(sku)
        if override_result["status"] == "error":
            return override_result

        override = override_result["override"]
        logo_fingerprint = override.get("logoFingerprint", {})

        # Read generated image
        image_data = base64.b64encode(image_path.read_bytes()).decode("utf-8")

        verification_prompt = f"""You are a quality control inspector for luxury fashion ecommerce.

Analyze this AI-generated model photo and verify it meets accuracy requirements for product SKU: {sku}

REQUIRED SPECIFICATIONS FROM LOGO FINGERPRINT:
{json.dumps(logo_fingerprint.get('logos', []), indent=2) if logo_fingerprint else "No fingerprint data available"}

VERIFICATION CHECKLIST:
1. Logo Placement - Are all logos in the correct locations?
2. Logo Technique - Does the technique (embroidered/silicone/printed) appear correct?
3. Logo Colors - Do logo colors match the specifications?
4. Garment Color - Does the base garment color match?
5. Garment Style - Does the silhouette and fit match the product type?

For each item, rate as:
- PASS: Matches specifications
- WARN: Close but slight deviation
- FAIL: Does not match specifications

Return a JSON object with:
{{
  "overall_status": "pass" | "warn" | "fail",
  "logo_placement": {{"status": "pass|warn|fail", "notes": "..."}},
  "logo_technique": {{"status": "pass|warn|fail", "notes": "..."}},
  "logo_colors": {{"status": "pass|warn|fail", "notes": "..."}},
  "garment_color": {{"status": "pass|warn|fail", "notes": "..."}},
  "garment_style": {{"status": "pass|warn|fail", "notes": "..."}},
  "recommendation": "approve" | "regenerate" | "manual_review"
}}"""

        response = gemini_client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=[
                verification_prompt,
                genai_types.Part(
                    inline_data=genai_types.Blob(
                        mime_type="image/jpeg",
                        data=image_data
                    )
                )
            ]
        )

        verification_text = response.text

        # Try to parse JSON from response
        try:
            # Extract JSON from markdown code blocks if present
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
            "sku": sku,
            "view": view,
            "verification": verification_result,
            "image_path": str(image_path)
        }
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


def list_all_products() -> dict[str, Any]:
    """List all products that have overrides."""
    try:
        products = sorted([
            f.stem for f in OVERRIDES_DIR.glob("*.json")
        ])
        return {"status": "ok", "products": products, "count": len(products)}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


TOOL_FUNCTIONS = [
    get_product_override,
    analyze_with_gpt4_vision,
    generate_model_image_with_gemini,
    verify_generated_image,
    list_all_products,
]

# ---------------------------------------------------------------------------
# System instruction
# ---------------------------------------------------------------------------

SYSTEM_INSTRUCTION = """You are the SkyyRose Image Generation Director — an AI agent specialized in creating accurate, high-quality fashion model photography using a coordinated dual-vision pipeline.

## Mission: 100% Product Accuracy for Ecommerce

You orchestrate two powerful vision models working together to achieve perfect product replication:
- **GPT-4o Vision** (OpenAI) - Expert at analyzing product photos with extreme detail
- **Gemini 3 Pro Image** (Google) - Generates 4K editorial fashion photography

## Dual-Vision Pipeline Workflow (ALWAYS FOLLOW THIS ORDER)

### Stage 1: Product Intelligence Gathering
1. **Call `get_product_override(sku)`** - Load product data including logoFingerprint (ML-verified specs)
2. **Study the logoFingerprint** - This contains AI-verified logo placement, technique, and colors
3. **Plan your approach** - Think about what details are critical for this specific product

### Stage 2: GPT-4o Vision Analysis
4. **Call `analyze_with_gpt4_vision(sku, 'front')`** - Get ultra-detailed garment specifications
5. **Review the analysis** - Check that GPT-4o captured all logos, colors, textures correctly
6. **Cross-check with logoFingerprint** - Verify GPT-4o's analysis matches the ML fingerprint

### Stage 3: Gemini 3 Pro Image Generation
7. **Call `generate_model_image_with_gemini(sku, analysis, 'front')`** - Generate 4K model photo
8. **Confirm generation success** - Check that the image was saved successfully

### Stage 4: Quality Verification (CRITICAL)
9. **Call `verify_generated_image(sku, 'front')`** - Use Gemini Flash Vision to inspect the output
10. **Evaluate verification results**:
    - **PASS**: Approve and move to back view (if available)
    - **WARN**: Note issues but proceed (minor deviations acceptable)
    - **FAIL**: You MUST regenerate - call `generate_model_image_with_gemini` again with refined instructions

### Stage 5: Back View (if applicable)
11. **Check if back reference exists** - Look at product override referenceImages array
12. **Repeat stages 2-4 for view='back'** if back reference is available

## Self-Correction Protocol

If verification returns "fail" or "regenerate":
1. **Analyze what went wrong** - Read the verification notes carefully
2. **Identify the specific issue** - Logo placement? Wrong technique? Color mismatch?
3. **Regenerate with corrections** - Call generate_model_image_with_gemini again
4. **Re-verify** - Call verify_generated_image to confirm the fix
5. **Maximum 2 retries** - If still failing after 2 attempts, report the issue to the user

## Critical Accuracy Rules

- Every logo, graphic, and text must match the source photo EXACTLY
- Branding technique (embroidered, silicone, printed, etc.) must be visually correct
- Fabric color, texture, and drape must be identical to source
- NO hallucinations, NO creative additions, NO modifications
- This is for ecommerce product sales — false advertising is illegal

## Collections DNA

- **black-rose**: Gothic luxury, dark romance, rose gold #B76E79 accents
- **love-hurts**: Raw street intensity, deep crimson #8B0000, Oakland pride
- **signature**: Editorial prestige, champagne gold #D4AF37, couture quality
- **kids-capsule**: Joyful luxury, vibrant colors, elevated kids editorial (make it SPECIAL)

## Output Requirements

After processing each view, report:
1. Output path where image was saved
2. Verification status (pass/warn/fail)
3. Any quality issues detected
4. Whether regeneration was needed

Think step-by-step. Use your reasoning to ensure every generated image is perfect."""

# ---------------------------------------------------------------------------
# Agent + Runner construction
# ---------------------------------------------------------------------------


def build_agent() -> LlmAgent:
    """Build the SkyyRose Image Generation Director LlmAgent."""
    return LlmAgent(
        name="skyyrose_image_director",
        model=MODEL,
        instruction=SYSTEM_INSTRUCTION,
        tools=[FunctionTool(fn) for fn in TOOL_FUNCTIONS],
        generate_content_config=genai_types.GenerateContentConfig(
            temperature=0.5,  # Lower temp for more consistent image generation
            max_output_tokens=4096,
        ),
    )


def build_runner(agent: LlmAgent, session_svc: InMemorySessionService) -> Runner:
    """Build the ADK Runner."""
    return Runner(
        agent=agent,
        app_name=APP_NAME,
        session_service=session_svc,
    )


def run_turn(
    runner: Runner,
    session_svc: InMemorySessionService,
    message: str,
    session_id: str,
    user_id: str = "cli-user",
) -> str:
    """Send one message and return the final text response."""
    content = genai_types.Content(
        role="user",
        parts=[genai_types.Part(text=message)],
    )
    response_text = ""
    for event in runner.run(
        user_id=user_id,
        session_id=session_id,
        new_message=content,
    ):
        if event.is_final_response():
            if event.content and event.content.parts:
                texts = [p.text for p in event.content.parts if hasattr(p, "text") and p.text]
                response_text = "\n".join(texts)
            break
    return response_text


def make_session(session_svc: InMemorySessionService, user_id: str = "cli-user") -> str:
    """Create a new session and return its ID."""
    session_id = str(uuid.uuid4())
    session_svc.create_session_sync(
        app_name=APP_NAME,
        user_id=user_id,
        session_id=session_id,
    )
    return session_id


# ---------------------------------------------------------------------------
# CLI Commands
# ---------------------------------------------------------------------------


def cmd_generate_models(sku: str | None = None, generate_all: bool = False) -> None:
    """Generate fashion model images for one product or all products."""
    agent = build_agent()
    session_svc = InMemorySessionService()
    runner = build_runner(agent, session_svc)

    if generate_all:
        # Get all products
        result = list_all_products()
        if result["status"] == "error":
            print(f"Error: {result['error']}")
            sys.exit(1)

        skus = result["products"]
        print(f"Generating model images for {len(skus)} products...\n")
    elif sku:
        skus = [sku]
    else:
        print("Error: Must specify --sku or --all")
        sys.exit(1)

    for i, current_sku in enumerate(skus, 1):
        print(f"[{i}/{len(skus)}] {current_sku}")
        session_id = make_session(session_svc)

        message = (
            f"Generate fashion model images for product SKU '{current_sku}'. "
            f"Follow the 2-vision pipeline: "
            f"1. Call get_product_override('{current_sku}') to load product data. "
            f"2. Call analyze_with_gpt4_vision('{current_sku}', 'front') for front view analysis. "
            f"3. Call generate_model_image_with_gemini('{current_sku}', <analysis>, 'front'). "
            f"4. If the product has a back reference image, repeat steps 2-3 for view='back'. "
            f"Report the output paths when done."
        )

        response = run_turn(runner, session_svc, message, session_id)
        print(response)

        if i < len(skus):
            print(f"\n  ⏸️  Rate limiting (5s)...\n")
            time.sleep(5)

    print(f"\nDone. {len(skus)} products processed.")


def cmd_interactive() -> None:
    """Start an interactive multi-turn session."""
    print("SkyyRose Image Generation Agent — Interactive Mode")
    print("Type 'exit' or 'quit' to end the session.\n")

    agent = build_agent()
    session_svc = InMemorySessionService()
    runner = build_runner(agent, session_svc)
    session_id = make_session(session_svc)
    user_id = "cli-user"

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nSession ended.")
            break

        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit"}:
            print("Session ended.")
            break

        response = run_turn(runner, session_svc, user_input, session_id, user_id)
        print(f"\nAgent: {response}\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="SkyyRose Image Generation Agent — ADK-powered fashion model generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # generate-models
    p_generate = subparsers.add_parser("generate-models", help="Generate model images")
    group = p_generate.add_mutually_exclusive_group(required=True)
    group.add_argument("--sku", help="Single product SKU (e.g. lh-001)")
    group.add_argument("--all", action="store_true", help="Generate all products")

    # interactive
    subparsers.add_parser("interactive", help="Start an interactive multi-turn session")

    args = parser.parse_args()

    # Validate API keys
    openai_key = os.getenv("OPENAI_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")

    if not openai_key:
        print("Error: OPENAI_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    if not gemini_key or gemini_key.startswith("AIza..."):
        print("Error: GEMINI_API_KEY not set or is a placeholder", file=sys.stderr)
        sys.exit(1)

    if args.command == "generate-models":
        cmd_generate_models(sku=args.sku, generate_all=args.all)
    elif args.command == "interactive":
        cmd_interactive()


if __name__ == "__main__":
    main()
