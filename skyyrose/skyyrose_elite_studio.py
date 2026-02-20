#!/usr/bin/env python3
"""
SkyyRose Elite Production Studio — Programmatic Tool-Calling Multi-Agent System

A sophisticated multi-provider agent team where each agent intelligently uses
tools through programmatic reasoning rather than hard-coded workflows.

Architecture:
- Coordinator Agent (Claude Opus) - Strategic orchestration with tool delegation
- Vision Agents (GPT-4o, Gemini, Claude) - Each with specialized vision tools
- Generator Agents (Gemini Pro Image, DALL-E) - Generation tools
- Quality Agents (All providers) - Verification tools

Each agent can reason about which tools to use and when, creating emergent
intelligent behavior through tool composition.

Usage:
    python skyyrose_elite_studio.py produce lh-001
    python skyyrose_elite_studio.py produce-batch --all
    python skyyrose_elite_studio.py interactive
"""

import argparse
import base64
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Callable
from dataclasses import dataclass

# Load environment
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

# Google ADK imports
from google.adk.agents import LlmAgent
from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import FunctionTool
from google.genai import types as genai_types

# Provider clients
from google import genai as google_genai
import openai
import anthropic
from PIL import Image
import io

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

APP_NAME = "skyyrose_elite_studio"
OVERRIDES_DIR = Path(__file__).parent / "assets" / "data" / "prompts" / "overrides"
SOURCE_DIR = Path(__file__).parent / "assets" / "images" / "source-products"
OUTPUT_DIR = Path(__file__).parent / "assets" / "images" / "products"

# Initialize provider clients
gemini_client = google_genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# ---------------------------------------------------------------------------
# Tool Registry - All tools available to agents
# ---------------------------------------------------------------------------

@dataclass
class ToolResult:
    """Standardized tool result format."""
    success: bool
    provider: str
    data: dict[str, Any]
    error: str | None = None


# --- Product Intelligence Tools ---

def tool_load_product_data(sku: str) -> dict[str, Any]:
    """
    Load product override data including logoFingerprint and reference images.

    Returns product metadata, collection info, and ML-verified logo specifications.
    """
    try:
        sku = sku.strip().lower()
        override_path = OVERRIDES_DIR / f"{sku}.json"

        if not override_path.exists():
            return {
                "success": False,
                "error": f"No override found for {sku}",
                "available_products": [f.stem for f in OVERRIDES_DIR.glob("*.json")]
            }

        data = json.loads(override_path.read_text(encoding="utf-8"))

        return {
            "success": True,
            "sku": sku,
            "name": data.get("name", ""),
            "collection": data.get("collection", ""),
            "reference_images": data.get("referenceImages", []),
            "logo_fingerprint": data.get("logoFingerprint", {}),
            "branding_tech": data.get("brandingTech", {}),
            "model_pose": data.get("modelPose", ""),
            "setting": data.get("setting", "")
        }
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def tool_get_reference_image(sku: str, view: str = "front") -> dict[str, Any]:
    """
    Get base64-encoded reference image for a product view.

    Returns image data ready for vision model analysis.
    """
    try:
        product_data = tool_load_product_data(sku)
        if not product_data["success"]:
            return product_data

        ref_images = product_data["reference_images"]
        if not ref_images:
            return {"success": False, "error": f"No reference images for {sku}"}

        # Select image based on view
        if view == "back" and len(ref_images) > 1 and "back" in ref_images[1]:
            image_file = ref_images[1]
        else:
            image_file = ref_images[0]

        image_path = SOURCE_DIR / image_file
        if not image_path.exists():
            return {"success": False, "error": f"Image not found: {image_file}"}

        image_data = base64.b64encode(image_path.read_bytes()).decode("utf-8")

        return {
            "success": True,
            "sku": sku,
            "view": view,
            "image_file": image_file,
            "image_base64": image_data,
            "mime_type": "image/jpeg"
        }
    except Exception as exc:
        return {"success": False, "error": str(exc)}


# --- Vision Analysis Tools ---

def tool_analyze_with_gpt4_vision(
    image_base64: str,
    product_name: str,
    collection: str,
    focus: str = "comprehensive"
) -> dict[str, Any]:
    """
    Analyze product photo using GPT-4o Vision.

    Focus options: comprehensive, logos_only, colors_only, construction_only
    Returns ultra-detailed garment specifications.
    """
    try:
        focus_prompts = {
            "comprehensive": "Provide complete analysis of all aspects",
            "logos_only": "Focus ONLY on branding, logos, and graphics - location, technique, colors",
            "colors_only": "Focus ONLY on color palette - exact shades, blocking patterns",
            "construction_only": "Focus ONLY on garment construction - cut, fit, hardware"
        }

        prompt = f"""You are GPT-4o Vision analyzing a SkyyRose product.

PRODUCT: {product_name}
COLLECTION: {collection}
ANALYSIS FOCUS: {focus_prompts.get(focus, focus_prompts["comprehensive"])}

Analyze this product photo with extreme precision. Return technical specifications
in clear, structured format."""

        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}",
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
            "success": True,
            "provider": "openai",
            "model": "gpt-4o",
            "focus": focus,
            "analysis": analysis,
            "char_count": len(analysis)
        }
    except Exception as exc:
        return {"success": False, "provider": "openai", "error": str(exc)}


def tool_analyze_with_gemini_vision(
    image_base64: str,
    product_name: str,
    collection: str,
    check_type: str = "brand_consistency"
) -> dict[str, Any]:
    """
    Analyze product photo using Gemini 3 Flash Vision.

    Check types: brand_consistency, quality_markers, generation_guidance
    Returns brand-focused technical assessment.
    """
    try:
        check_prompts = {
            "brand_consistency": "Verify this matches SkyyRose brand standards and collection aesthetic",
            "quality_markers": "Identify all quality indicators visible in construction and materials",
            "generation_guidance": "List critical elements that MUST be replicated in AI generation"
        }

        prompt = f"""You are Gemini 3 Flash analyzing a SkyyRose product.

PRODUCT: {product_name}
COLLECTION: {collection}
CHECK TYPE: {check_prompts.get(check_type, check_type)}

Provide concise technical assessment focused on the check type."""

        response = gemini_client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=[
                prompt,
                genai_types.Part(
                    inline_data=genai_types.Blob(
                        mime_type="image/jpeg",
                        data=image_base64
                    )
                )
            ]
        )

        analysis = response.text

        return {
            "success": True,
            "provider": "google",
            "model": "gemini-3-flash-preview",
            "check_type": check_type,
            "analysis": analysis,
            "char_count": len(analysis)
        }
    except Exception as exc:
        return {"success": False, "provider": "google", "error": str(exc)}


def tool_analyze_with_claude_vision(
    image_base64: str,
    product_name: str,
    task: str = "critique_analysis"
) -> dict[str, Any]:
    """
    Analyze product photo using Claude Sonnet Vision.

    Tasks: critique_analysis, verify_accuracy, suggest_improvements
    Returns reasoning-focused assessment.
    """
    try:
        task_prompts = {
            "critique_analysis": "Critically review the product and identify any potential issues for AI replication",
            "verify_accuracy": "Verify all visible details match what's expected for this product type",
            "suggest_improvements": "Suggest how to improve the reference photo or what angles would be helpful"
        }

        prompt = f"""You are Claude Sonnet analyzing a SkyyRose product photo.

PRODUCT: {product_name}
TASK: {task_prompts.get(task, task)}

Provide detailed reasoning-based assessment."""

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
                            "data": image_base64
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }]
        )

        analysis = response.content[0].text

        return {
            "success": True,
            "provider": "anthropic",
            "model": "claude-sonnet-4",
            "task": task,
            "analysis": analysis,
            "char_count": len(analysis)
        }
    except Exception as exc:
        return {"success": False, "provider": "anthropic", "error": str(exc)}


# --- Generation Tools ---

def tool_generate_with_gemini_pro_image(
    sku: str,
    generation_spec: str,
    reference_image_base64: str,
    view: str = "front",
    resolution: str = "4K"
) -> dict[str, Any]:
    """
    Generate fashion model image using Gemini 3 Pro Image.

    Resolution options: 4K, 2K, 1K
    Returns path to generated 4K editorial fashion photo.
    """
    try:
        product_data = tool_load_product_data(sku)
        if not product_data["success"]:
            return product_data

        collection = product_data["collection"]
        is_kids = collection == "kids-capsule"

        collection_moods = {
            "black-rose": "Gothic romance, mysterious elegance",
            "love-hurts": "Raw street intensity, Oakland pride",
            "signature": "Editorial prestige, champagne gold luxury",
            "kids-capsule": "Joyful luxury, SPECIAL premium quality"
        }

        view_instructions = (
            "Model facing AWAY, showing BACK of garment"
            if view == "back" else
            "Model facing FORWARD, showing FRONT of garment"
        )

        prompt = f"""Create professional editorial fashion photograph for SkyyRose.

GARMENT SPECIFICATIONS:
{generation_spec}

CRITICAL: 100% exact replica - every logo, graphic, color must match.

MODEL: {"Child (8-10 years)" if is_kids else "Professional adult model"}
VIEW: {view_instructions}
STYLE: Vogue editorial, Hasselblad aesthetic
SETTING: {collection_moods.get(collection, "")}
FORMAT: 3:4 portrait, {resolution}

Generate now."""

        response = gemini_client.models.generate_content(
            model="gemini-3-pro-image-preview",
            contents=[
                prompt,
                genai_types.Part(
                    inline_data=genai_types.Blob(
                        mime_type="image/jpeg",
                        data=reference_image_base64
                    )
                )
            ],
            config=genai_types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"],
                image_config=genai_types.ImageConfig(
                    aspect_ratio="3:4",
                    image_size=resolution
                )
            )
        )

        # Extract image
        if not response.candidates or not response.candidates[0].content.parts:
            return {"success": False, "error": "No image generated"}

        for part in response.candidates[0].content.parts:
            if part.inline_data:
                output_dir = OUTPUT_DIR / sku
                output_dir.mkdir(parents=True, exist_ok=True)

                output_path = output_dir / f"{sku}-model-{view}-elite.jpg"
                output_path.write_bytes(base64.b64decode(part.inline_data.data))

                return {
                    "success": True,
                    "provider": "google",
                    "model": "gemini-3-pro-image",
                    "sku": sku,
                    "view": view,
                    "output_path": str(output_path),
                    "resolution": resolution
                }

        return {"success": False, "error": "No image data in response"}
    except Exception as exc:
        return {"success": False, "provider": "google", "error": str(exc)}


# --- Verification Tools ---

def tool_verify_image_quality(
    image_path: str,
    expected_specs: str,
    verifier: str = "claude"
) -> dict[str, Any]:
    """
    Verify generated image matches specifications.

    Verifiers: claude, gpt4, gemini, all (consensus)
    Returns quality assessment with pass/warn/fail status.
    """
    try:
        # Prepare image
        img = Image.open(image_path)
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = background

        max_size = 1568
        if max(img.size) > max_size:
            ratio = max_size / max(img.size)
            new_size = tuple(int(dim * ratio) for dim in img.size)
            img = img.resize(new_size, Image.Resampling.LANCZOS)

        img_buffer = io.BytesIO()
        img.save(img_buffer, format='JPEG', quality=85, optimize=True)
        img_buffer.seek(0)
        image_data = base64.b64encode(img_buffer.read()).decode("utf-8")

        if verifier == "claude":
            prompt = f"""You are Quality Control verifying an AI-generated fashion photo.

EXPECTED SPECIFICATIONS:
{expected_specs}

Inspect this image and return JSON:
{{
  "overall_status": "pass|warn|fail",
  "logo_accuracy": {{"status": "pass|warn|fail", "notes": "..."}},
  "garment_accuracy": {{"status": "pass|warn|fail", "notes": "..."}},
  "photo_quality": {{"status": "pass|warn|fail", "notes": "..."}},
  "recommendation": "approve|regenerate|manual_review"
}}"""

            response = anthropic_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1500,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": image_data}},
                        {"type": "text", "text": prompt}
                    ]
                }]
            )

            verification_text = response.content[0].text

            # Parse JSON
            if "```json" in verification_text:
                json_start = verification_text.find("```json") + 7
                json_end = verification_text.find("```", json_start)
                verification_text = verification_text[json_start:json_end].strip()

            try:
                verification = json.loads(verification_text)
            except:
                verification = {"raw_text": verification_text, "parsed": False}

            return {
                "success": True,
                "provider": "anthropic",
                "verifier": "claude-sonnet-4",
                "verification": verification
            }

        return {"success": False, "error": f"Unknown verifier: {verifier}"}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


# ---------------------------------------------------------------------------
# Tool Registration for ADK Agents
# ---------------------------------------------------------------------------

ALL_TOOLS = [
    tool_load_product_data,
    tool_get_reference_image,
    tool_analyze_with_gpt4_vision,
    tool_analyze_with_gemini_vision,
    tool_analyze_with_claude_vision,
    tool_generate_with_gemini_pro_image,
    tool_verify_image_quality,
]

# ---------------------------------------------------------------------------
# Elite Coordinator Agent (Claude Opus with all tools)
# ---------------------------------------------------------------------------

COORDINATOR_SYSTEM = """You are the ELITE PRODUCTION COORDINATOR for SkyyRose.

You orchestrate a multi-provider team of AI specialists to create perfect fashion photography.

## YOUR TEAM:
- GPT-4o Vision (OpenAI) - Ultra-detailed product analysis
- Gemini 3 Flash (Google) - Brand consistency verification
- Claude Sonnet (Anthropic) - Quality critique & reasoning
- Gemini 3 Pro Image (Google) - 4K editorial generation
- DALL-E 3 (OpenAI) - Alternative generation

## YOUR TOOLS (USE INTELLIGENTLY):

**Product Intelligence:**
- tool_load_product_data(sku) - Get product metadata, logoFingerprint
- tool_get_reference_image(sku, view) - Get base64 reference photo

**Vision Analysis (DELEGATE TO SPECIALISTS):**
- tool_analyze_with_gpt4_vision(image, name, collection, focus) - Ultra-detailed
- tool_analyze_with_gemini_vision(image, name, collection, check_type) - Brand check
- tool_analyze_with_claude_vision(image, name, task) - Critical reasoning

**Generation:**
- tool_generate_with_gemini_pro_image(sku, spec, ref_image, view, resolution)

**Quality Control:**
- tool_verify_image_quality(image_path, specs, verifier)

## YOUR WORKFLOW (REASON ABOUT THIS):

1. INTELLIGENCE GATHERING
   - Load product data to understand what you're working with
   - Get reference image for analysis

2. MULTI-ANGLE VISION ANALYSIS
   - Delegate to GPT-4o for ultra-detailed specs
   - Delegate to Gemini for brand consistency
   - Optionally delegate to Claude for critical review
   - SYNTHESIZE results into unified specification

3. GENERATION
   - Use unified spec to generate with Gemini 3 Pro Image
   - Save output path for verification

4. QUALITY VERIFICATION
   - Verify generated image matches specs
   - Make quality decision: approve, regenerate, or escalate

5. REPORT & DELIVER
   - Provide clear summary of what was created
   - Report any issues or deviations

## DECISION MAKING:
- You have FULL AUTONOMY to decide which tools to use
- Think strategically about which specialists to consult
- Balance thoroughness with efficiency
- Always prioritize 100% accuracy over speed

Be professional, thorough, and decisive."""


def build_coordinator_agent() -> LlmAgent:
    """Build the Elite Coordinator Agent with all tools."""
    return LlmAgent(
        name="elite_coordinator",
        model="gemini-3-flash-preview",  # Using Gemini 3 Flash (2M context)
        instruction=COORDINATOR_SYSTEM,
        tools=[FunctionTool(fn) for fn in ALL_TOOLS],
        generate_content_config=genai_types.GenerateContentConfig(
            temperature=0.6,
            max_output_tokens=4096,
        ),
    )


# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------

def run_elite_production(sku: str, view: str = "front") -> dict[str, Any]:
    """Run elite production using coordin agent with programmatic tool calling."""
    print(f"\n🎬 Elite Production Studio")
    print(f"{'='*60}")
    print(f"📦 Product: {sku.upper()}")
    print(f"👁️  View: {view}")
    print('='*60)

    # Build agent and runner
    agent = build_coordinator_agent()
    session_svc = InMemorySessionService()
    runner = Runner(agent=agent, app_name=APP_NAME, session_service=session_svc)

    # Create session
    import uuid
    session_id = str(uuid.uuid4())
    session_svc.create_session_sync(
        app_name=APP_NAME,
        user_id="cli-user",
        session_id=session_id,
    )

    # Send task to coordinator
    task_message = f"""Execute complete production workflow for product SKU '{sku}', {view} view.

Use your tools intelligently to:
1. Gather product intelligence
2. Conduct multi-provider vision analysis
3. Generate 4K editorial fashion photo
4. Verify quality
5. Report results

Think step-by-step and use the right specialists for each task."""

    content = genai_types.Content(
        role="user",
        parts=[genai_types.Part(text=task_message)],
    )

    print("\n🤖 Coordinator Agent thinking...\n")

    response_text = ""
    for event in runner.run(user_id="cli-user", session_id=session_id, new_message=content):
        if event.is_final_response():
            if event.content and event.content.parts:
                texts = [p.text for p in event.content.parts if hasattr(p, "text") and p.text]
                response_text = "\n".join(texts)
            break

    print(f"\n{'='*60}")
    print("📊 Coordinator Report:")
    print('='*60)
    print(response_text)

    return {"status": "success", "sku": sku, "view": view, "report": response_text}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="SkyyRose Elite Production Studio")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_produce = subparsers.add_parser("produce", help="Produce one image")
    p_produce.add_argument("sku", help="Product SKU")
    p_produce.add_argument("--view", default="front", help="View (front|back)")

    args = parser.parse_args()

    # Validate keys
    required_keys = ["GEMINI_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"]
    missing = [k for k in required_keys if not os.getenv(k)]
    if missing:
        print(f"❌ Missing: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)

    if args.command == "produce":
        run_elite_production(args.sku, args.view)


if __name__ == "__main__":
    main()
