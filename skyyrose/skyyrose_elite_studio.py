#!/usr/bin/env python3
"""
SkyyRose Elite Production Studio — Hierarchical Multi-Agent System

Solves context window limits by using specialized sub-agents instead of
a single coordinator with all tools.

Architecture:
- Lightweight Coordinator (orchestration only)
- Vision Analyst Sub-Agent (GPT-4o + Gemini + Claude vision)
- Generator Sub-Agent (Gemini 3 Pro Image generation)
- Quality Sub-Agent (multi-provider verification)

Each sub-agent operates independently with its own context window.
Coordinator delegates tasks and synthesizes results.

Usage:
    python skyyrose_elite_studio.py produce br-001
    python skyyrose_elite_studio.py produce-batch --all
"""

import argparse
import base64
import json
import os
import sys
import time
from pathlib import Path
from typing import Any
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

# Shared state for sub-agents to communicate results
_shared_state = {}

# ---------------------------------------------------------------------------
# Utility Functions (used by sub-agents)
# ---------------------------------------------------------------------------

def load_product_data(sku: str) -> dict[str, Any]:
    """Load product override data including logoFingerprint."""
    sku = sku.strip().lower()
    override_path = OVERRIDES_DIR / f"{sku}.json"

    if not override_path.exists():
        return {"error": f"Product {sku} not found"}

    with open(override_path, 'r') as f:
        data = json.load(f)

    return {
        "sku": sku,
        "collection": data.get("collection", "unknown"),
        "garmentTypeLock": data.get("garmentTypeLock", ""),
        "logoFingerprint": data.get("logoFingerprint", {}),
        "brandingTech": data.get("brandingTech", {})
    }


def get_reference_image_path(sku: str, view: str) -> str:
    """Get path to reference product image."""
    sku = sku.strip().lower()
    product_data = load_product_data(sku)
    collection = product_data.get("collection", "")

    # Try multiple naming patterns
    patterns = [
        SOURCE_DIR / collection / f"{sku}-{view}.jpg",
        SOURCE_DIR / collection / f"{sku}-{view}.jpeg",
        SOURCE_DIR / collection / f"{sku}-{view}.png",
    ]

    for path in patterns:
        if path.exists():
            return str(path)

    return ""


def image_to_base64(image_path: str) -> str:
    """Convert image file to base64 string."""
    with open(image_path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')


# ---------------------------------------------------------------------------
# Vision Analyst Sub-Agent (GPT-4o, Gemini, Claude)
# ---------------------------------------------------------------------------

def tool_analyze_vision(sku: str, view: str, providers: str = "all") -> dict[str, Any]:
    """
    Analyze product reference image using multiple vision providers.

    Args:
        sku: Product SKU (e.g., 'br-001')
        view: Image view ('front', 'back')
        providers: Which providers to use ('gpt4', 'gemini', 'claude', 'all')

    Returns:
        Combined analysis from all requested providers
    """
    try:
        product_data = load_product_data(sku)
        image_path = get_reference_image_path(sku, view)

        if not image_path:
            return {"success": False, "error": f"No reference image found for {sku} {view}"}

        image_base64 = image_to_base64(image_path)
        results = {}

        # GPT-4o Vision - Ultra-detailed specs
        if providers in ("all", "gpt4"):
            prompt = f"""Analyze this SkyyRose product photo in extreme detail.

PRODUCT: {product_data.get('garmentTypeLock', sku.upper())}
COLLECTION: {product_data.get('collection', 'unknown')}

Provide ultra-detailed garment specifications:
1. Construction details (silhouette, fit, cut, length, sleeves, neckline)
2. Fabric analysis (material, texture, weight, finish)
3. Color palette (exact shades, blocking patterns)
4. Branding & logos (location, size, technique, colors)
5. Hardware & details (ribbing, drawstrings, pockets, zippers, trim)
6. Fit & drape prediction

Be extremely detailed - this drives AI generation accuracy."""

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
                max_tokens=2000,
                temperature=0.2
            )

            results["gpt4"] = {
                "provider": "openai",
                "model": "gpt-4o",
                "analysis": response.choices[0].message.content
            }

        # Gemini Flash Vision - Brand consistency
        if providers in ("all", "gemini"):
            prompt = f"""Verify this SkyyRose product matches brand standards.

PRODUCT: {product_data.get('garmentTypeLock', sku.upper())}
COLLECTION: {product_data.get('collection', 'unknown')}

Check:
1. Brand consistency - Does it match SkyyRose aesthetic?
2. Collection alignment - Fits {product_data.get('collection')} theme?
3. Logo/branding technique - What method? (embroidered, silicone, printed, etc.)
4. Quality markers - Premium construction indicators
5. Critical elements for AI replication

Be specific about branding techniques."""

            response = gemini_client.models.generate_content(
                model="gemini-3-flash-preview",
                contents=[
                    prompt,
                    genai_types.Part(
                        inline_data=genai_types.Blob(
                            mime_type="image/jpeg",
                            data=base64.b64decode(image_base64)
                        )
                    )
                ]
            )

            results["gemini"] = {
                "provider": "google",
                "model": "gemini-3-flash-preview",
                "analysis": response.text
            }

        # Claude Sonnet Vision - Critical reasoning
        if providers in ("all", "claude"):
            # Resize image for Claude (max 1568px, optimize)
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
            claude_image_data = base64.b64encode(img_buffer.read()).decode("utf-8")

            prompt = f"""Critically analyze this SkyyRose product photo.

PRODUCT: {product_data.get('garmentTypeLock', sku.upper())}

Provide:
1. Critical assessment - Any issues for AI replication?
2. Accuracy verification - Do visible details match expectations?
3. Improvement suggestions - Better angles needed?
4. Risk factors - What could go wrong in generation?

Use detailed reasoning."""

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
                                "data": claude_image_data
                            }
                        },
                        {"type": "text", "text": prompt}
                    ]
                }]
            )

            results["claude"] = {
                "provider": "anthropic",
                "model": "claude-sonnet-4",
                "analysis": response.content[0].text
            }

        return {
            "success": True,
            "sku": sku,
            "view": view,
            "analyses": results
        }

    except Exception as exc:
        return {"success": False, "error": str(exc)}


VISION_ANALYST_SYSTEM = """You are the VISION ANALYST for SkyyRose production.

Your job: Analyze product reference photos using multiple AI vision providers
and synthesize their analyses into a unified specification for generation.

YOU HAVE ONE TOOL:
- tool_analyze_vision(sku, view, providers) - Runs vision analysis

WORKFLOW:
1. When given a product SKU and view, call tool_analyze_vision
2. Review all provider analyses (GPT-4o, Gemini, Claude)
3. Synthesize into unified specification highlighting:
   - Critical accuracy points (logos, branding technique)
   - Garment construction details
   - Color specifications
   - Quality markers
   - Generation warnings

Return a concise unified spec that will drive perfect AI generation."""


def build_vision_analyst() -> LlmAgent:
    """Build Vision Analyst sub-agent."""
    return LlmAgent(
        name="vision_analyst",
        model="gemini-2.0-flash",
        instruction=VISION_ANALYST_SYSTEM,
        tools=[FunctionTool(tool_analyze_vision)],
        generate_content_config=genai_types.GenerateContentConfig(
            temperature=0.4,
            max_output_tokens=3000,
            tool_config=genai_types.ToolConfig(
                function_calling_config=genai_types.FunctionCallingConfig(
                    mode='ANY'  # FORCE tool calling
                )
            ),
        ),
    )


# ---------------------------------------------------------------------------
# Generator Sub-Agent (Gemini 3 Pro Image)
# ---------------------------------------------------------------------------

def tool_generate_image(
    sku: str,
    view: str,
    generation_spec: str,
    resolution: str = "4K"
) -> dict[str, Any]:
    """
    Generate fashion model image using Gemini 3 Pro Image.

    Args:
        sku: Product SKU
        view: View angle (front, back)
        generation_spec: Detailed specification from vision analysis
        resolution: Output resolution (4K, HD)

    Returns:
        Path to generated image
    """
    try:
        # Get reference image
        image_path = get_reference_image_path(sku, view)
        if not image_path:
            return {"success": False, "error": f"No reference image for {sku} {view}"}

        ref_image_base64 = image_to_base64(image_path)

        # Build generation prompt
        prompt = f"""Generate a professional editorial fashion photograph.

REFERENCE PRODUCT:
{generation_spec}

REQUIREMENTS:
- Professional fashion model wearing this exact product
- Editorial lighting (soft, directional, high-end fashion aesthetic)
- Clean neutral background (studio white or subtle gradient)
- Model pose: natural, confident, fashion editorial style
- View: {view} angle
- Focus on garment details and branding
- {resolution} resolution, high quality

CRITICAL:
- Logo and branding must match the reference EXACTLY
- All garment details must be accurate to the specification
- No hallucinations - only what's specified

Generate the image."""

        # Call Gemini 3 Pro Image
        response = gemini_client.models.generate_content(
            model="gemini-3-pro-image-preview",
            contents=[
                prompt,
                genai_types.Part(
                    inline_data=genai_types.Blob(
                        mime_type="image/jpeg",
                        data=base64.b64decode(ref_image_base64)
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

        # Extract generated image
        output_path = OUTPUT_DIR / sku / f"{sku}-model-{view}-gemini.jpg"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        for part in response.candidates[0].content.parts:
            if hasattr(part, 'inline_data') and part.inline_data:
                image_data = part.inline_data.data
                with open(output_path, 'wb') as f:
                    f.write(image_data)

                return {
                    "success": True,
                    "provider": "google",
                    "model": "gemini-3-pro-image-preview",
                    "output_path": str(output_path),
                    "resolution": resolution
                }

        return {"success": False, "error": "No image in response"}

    except Exception as exc:
        return {"success": False, "error": str(exc)}


GENERATOR_SYSTEM = """You are the GENERATOR for SkyyRose production.

Your job: Generate 4K editorial fashion model images using Gemini 3 Pro Image.

YOU HAVE ONE TOOL:
- tool_generate_image(sku, view, generation_spec, resolution)

WORKFLOW:
1. Receive unified specification from Vision Analyst
2. Call tool_generate_image with the spec
3. Return the output path

Keep it simple - just generate the image as specified."""


def build_generator() -> LlmAgent:
    """Build Generator sub-agent."""
    return LlmAgent(
        name="generator",
        model="gemini-2.0-flash",
        instruction=GENERATOR_SYSTEM,
        tools=[FunctionTool(tool_generate_image)],
        generate_content_config=genai_types.GenerateContentConfig(
            temperature=0.3,
            max_output_tokens=1000,
            tool_config=genai_types.ToolConfig(
                function_calling_config=genai_types.FunctionCallingConfig(
                    mode='ANY'  # FORCE tool calling
                )
            ),
        ),
    )


# ---------------------------------------------------------------------------
# Quality Sub-Agent (Multi-provider verification)
# ---------------------------------------------------------------------------

def tool_verify_quality(
    image_path: str,
    expected_spec: str,
    verifier: str = "claude"
) -> dict[str, Any]:
    """
    Verify generated image quality and accuracy.

    Args:
        image_path: Path to generated image
        expected_spec: What the image should contain
        verifier: Which provider ('claude', 'gpt4', 'gemini')

    Returns:
        Quality assessment with pass/warn/fail status
    """
    try:
        # Prepare image for verification
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
            prompt = f"""Quality Control: Verify this AI-generated fashion photo.

EXPECTED SPECIFICATIONS:
{expected_spec}

Inspect the image and return JSON:
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


QUALITY_SYSTEM = """You are QUALITY CONTROL for SkyyRose production.

Your job: Verify generated images match specifications and approve/reject.

YOU HAVE ONE TOOL:
- tool_verify_quality(image_path, expected_spec, verifier)

WORKFLOW:
1. Receive image path and specification
2. Call tool_verify_quality
3. Review the verification results
4. Make final decision: APPROVE, REGENERATE, or MANUAL_REVIEW

Return clear decision with reasoning."""


def build_quality_agent() -> LlmAgent:
    """Build Quality sub-agent."""
    return LlmAgent(
        name="quality_control",
        model="gemini-2.0-flash",
        instruction=QUALITY_SYSTEM,
        tools=[FunctionTool(tool_verify_quality)],
        generate_content_config=genai_types.GenerateContentConfig(
            temperature=0.2,
            max_output_tokens=1000,
            tool_config=genai_types.ToolConfig(
                function_calling_config=genai_types.FunctionCallingConfig(
                    mode='ANY'  # FORCE tool calling
                )
            ),
        ),
    )


# ---------------------------------------------------------------------------
# Coordinator Agent (Lightweight orchestration)
# ---------------------------------------------------------------------------

def tool_delegate_to_vision_analyst(sku: str, view: str) -> dict[str, Any]:
    """Delegate vision analysis to Vision Analyst sub-agent."""
    try:
        print(f"\n🔬 Delegating to Vision Analyst...")
        print(f"   SKU: {sku}, View: {view}")

        agent = build_vision_analyst()
        session_svc = InMemorySessionService()
        runner = Runner(agent=agent, app_name=f"{APP_NAME}_vision", session_service=session_svc)

        import uuid
        session_id = str(uuid.uuid4())
        session_svc.create_session_sync(
            app_name=f"{APP_NAME}_vision",
            user_id="coordinator",
            session_id=session_id,
        )

        task_msg = f"Analyze product {sku}, {view} view. Use all providers and synthesize unified specification."
        print(f"   Task: {task_msg}")

        content = genai_types.Content(
            role="user",
            parts=[genai_types.Part(text=task_msg)],
        )

        # Extract final response
        final_response = ""
        event_count = 0
        print(f"   Running Vision Analyst agent...")

        for event in runner.run(
            user_id="coordinator",
            session_id=session_id,
            new_message=content
        ):
            event_count += 1
            print(f"   Event {event_count}: {type(event).__name__}")

            if event.is_final_response():
                print(f"   ✓ Final response received")
                if event.content and event.content.parts:
                    texts = [p.text for p in event.content.parts if hasattr(p, "text") and p.text]
                    final_response = "\n".join(texts)
                    print(f"   ✓ Extracted {len(final_response)} chars")
                break

        if not final_response:
            print(f"   ⚠️  No response text extracted after {event_count} events")
            return {"success": False, "error": "No response from Vision Analyst"}

        # Store in shared state
        _shared_state[f"{sku}_{view}_spec"] = final_response
        print(f"   ✓ Stored specification in shared state")

        return {
            "success": True,
            "agent": "vision_analyst",
            "specification": final_response[:200] + "..." if len(final_response) > 200 else final_response
        }

    except Exception as exc:
        print(f"   ❌ Error: {exc}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(exc)}


def tool_delegate_to_generator(sku: str, view: str) -> dict[str, Any]:
    """Delegate image generation to Generator sub-agent."""
    try:
        print(f"\n🎨 Delegating to Generator...")

        # Get spec from shared state
        spec = _shared_state.get(f"{sku}_{view}_spec", "")
        if not spec:
            return {"success": False, "error": "No specification available - run vision analysis first"}

        agent = build_generator()
        session_svc = InMemorySessionService()
        runner = Runner(agent=agent, app_name=f"{APP_NAME}_generator", session_service=session_svc)

        import uuid
        session_id = str(uuid.uuid4())
        session_svc.create_session_sync(
            app_name=f"{APP_NAME}_generator",
            user_id="coordinator",
            session_id=session_id,
        )

        task_msg = f"Generate image for {sku}, {view} view using this specification:\n\n{spec}"

        content = genai_types.Content(
            role="user",
            parts=[genai_types.Part(text=task_msg)],
        )

        # Extract output path from tool results
        output_path = ""
        for event in runner.run(
            user_id="coordinator",
            session_id=session_id,
            new_message=content
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, 'function_response'):
                        response_data = part.function_response.response
                        if isinstance(response_data, dict) and 'output_path' in response_data:
                            output_path = response_data['output_path']

        if output_path:
            _shared_state[f"{sku}_{view}_image"] = output_path
            return {
                "success": True,
                "agent": "generator",
                "output_path": output_path
            }

        return {"success": False, "error": "No output path in generator response"}

    except Exception as exc:
        return {"success": False, "error": str(exc)}


def tool_delegate_to_quality(sku: str, view: str) -> dict[str, Any]:
    """Delegate quality verification to Quality sub-agent."""
    try:
        print(f"\n✅ Delegating to Quality Control...")

        # Get image path and spec from shared state
        image_path = _shared_state.get(f"{sku}_{view}_image", "")
        spec = _shared_state.get(f"{sku}_{view}_spec", "")

        if not image_path or not spec:
            return {"success": False, "error": "Missing image or spec"}

        agent = build_quality_agent()
        session_svc = InMemorySessionService()
        runner = Runner(agent=agent, app_name=f"{APP_NAME}_quality", session_service=session_svc)

        import uuid
        session_id = str(uuid.uuid4())
        session_svc.create_session_sync(
            app_name=f"{APP_NAME}_quality",
            user_id="coordinator",
            session_id=session_id,
        )

        task_msg = f"Verify quality of generated image at {image_path} against specification:\n\n{spec}"

        content = genai_types.Content(
            role="user",
            parts=[genai_types.Part(text=task_msg)],
        )

        # Extract final decision
        final_response = ""
        for event in runner.run(
            user_id="coordinator",
            session_id=session_id,
            new_message=content
        ):
            if event.is_final_response():
                if event.content and event.content.parts:
                    texts = [p.text for p in event.content.parts if hasattr(p, "text") and p.text]
                    final_response = "\n".join(texts)

        return {
            "success": True,
            "agent": "quality_control",
            "decision": final_response
        }

    except Exception as exc:
        return {"success": False, "error": str(exc)}


COORDINATOR_SYSTEM = """You are the PRODUCTION COORDINATOR for SkyyRose Elite Studio.

CRITICAL: You MUST actually CALL the delegation tools using function calling.
DO NOT just write out tool names - INVOKE them.

YOUR WORKFLOW (EXECUTE THESE TOOL CALLS):

Step 1: CALL tool_delegate_to_vision_analyst(sku, view)
  → This runs multi-provider vision analysis
  → Returns unified specification

Step 2: CALL tool_delegate_to_generator(sku, view)
  → This generates the 4K fashion model image
  → Returns output path

Step 3: CALL tool_delegate_to_quality(sku, view)
  → This verifies image quality
  → Returns approval decision

Step 4: Report results to user

IMPORTANT: Use function calling - don't describe tools, CALL them."""


def build_coordinator() -> LlmAgent:
    """Build lightweight Coordinator agent."""
    return LlmAgent(
        name="production_coordinator",
        model="gemini-2.0-flash",
        instruction=COORDINATOR_SYSTEM,
        tools=[
            FunctionTool(tool_delegate_to_vision_analyst),
            FunctionTool(tool_delegate_to_generator),
            FunctionTool(tool_delegate_to_quality),
        ],
        generate_content_config=genai_types.GenerateContentConfig(
            temperature=0.5,
            max_output_tokens=2000,
            tool_config=genai_types.ToolConfig(
                function_calling_config=genai_types.FunctionCallingConfig(
                    mode='ANY'  # FORCE tool calling - don't just describe tools
                )
            ),
        ),
    )


# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------

def run_elite_production(sku: str, view: str = "front") -> dict[str, Any]:
    """Run elite production using hierarchical multi-agent system."""
    print(f"\n🎬 Elite Production Studio - Hierarchical Architecture")
    print(f"{'='*60}")
    print(f"📦 Product: {sku.upper()}")
    print(f"👁️  View: {view}")
    print('='*60)

    # Clear shared state
    _shared_state.clear()

    # Build coordinator and runner
    coordinator = build_coordinator()
    session_svc = InMemorySessionService()
    runner = Runner(agent=coordinator, app_name=APP_NAME, session_service=session_svc)

    # Create session
    import uuid
    session_id = str(uuid.uuid4())
    session_svc.create_session_sync(
        app_name=APP_NAME,
        user_id="cli-user",
        session_id=session_id,
    )

    # Send task to coordinator
    task_message = f"Execute complete production workflow for product {sku}, {view} view."

    print(f"\n🎯 Coordinator orchestrating sub-agents...")

    try:
        # Wrap message
        content = genai_types.Content(
            role="user",
            parts=[genai_types.Part(text=task_message)],
        )

        # Extract final report
        print(f"\n{'='*60}")
        print(f"📊 Production Report:")
        print(f"{'='*60}")

        for event in runner.run(
            user_id="cli-user",
            session_id=session_id,
            new_message=content
        ):
            if event.is_final_response():
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            print(part.text)

        # Get final output
        output_path = _shared_state.get(f"{sku}_{view}_image", "")

        return {
            "status": "success",
            "sku": sku,
            "view": view,
            "output_path": output_path,
            "shared_state": dict(_shared_state)
        }

    except Exception as exc:
        print(f"\n❌ Error: {exc}")
        return {
            "status": "error",
            "error": str(exc)
        }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="SkyyRose Elite Production Studio")
    parser.add_argument("command", choices=["produce", "produce-batch"], help="Command to run")
    parser.add_argument("sku", nargs="?", help="Product SKU (e.g., br-001)")
    parser.add_argument("--view", default="front", choices=["front", "back"], help="View angle")
    parser.add_argument("--all", action="store_true", help="Process all products (for produce-batch)")

    args = parser.parse_args()

    if args.command == "produce":
        if not args.sku:
            print("Error: SKU required for 'produce' command")
            sys.exit(1)

        result = run_elite_production(args.sku, args.view)
        print(f"\n✨ Result: {result}")

    elif args.command == "produce-batch":
        print("Batch production not yet implemented")
        sys.exit(1)


if __name__ == "__main__":
    main()
