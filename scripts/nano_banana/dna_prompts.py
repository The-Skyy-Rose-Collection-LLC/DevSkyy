"""DNA-to-prompt builder — deterministic prompt generation from product DNA.

Takes the multi-model consensus DNA (from data/product-dna/{sku}.json) and
builds structured, explicit generation prompts with exact colors, text,
logo positions, and anti-hallucination guardrails.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

log = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DNA_DIR = PROJECT_ROOT / "data" / "product-dna"


def load_dna(sku: str) -> dict | None:
    """Load DNA consensus dict for a SKU. Returns None if not found."""
    dna_file = DNA_DIR / f"{sku}.json"
    if not dna_file.exists():
        return None
    data = json.loads(dna_file.read_text())
    return data.get("consensus")


def _format_text_content(text_items: list) -> str:
    """Format text content for prompt injection."""
    if not text_items:
        return ""
    lines = []
    for t in text_items:
        if not isinstance(t, dict):
            continue
        txt = t.get("text", "")
        loc = t.get("location", "")
        color = t.get("color", "")
        style = t.get("style", "")
        if txt:
            parts = [f'"{txt}"']
            if loc:
                parts.append(f"at {loc}")
            if color:
                parts.append(f"in color {color}")
            if style:
                parts.append(f"({style})")
            lines.append("  - " + " ".join(parts))
    return "\n".join(lines)


def _format_logos(logos: list) -> str:
    """Format logo specifications for prompt injection."""
    if not logos:
        return ""
    lines = []
    for lg in logos:
        if not isinstance(lg, dict):
            continue
        lg_type = lg.get("type", "logo")
        pos = lg.get("position", "")
        size = lg.get("size_inches", "")
        material = lg.get("material", "")
        parts = [lg_type]
        if pos:
            parts.append(f"at {pos}")
        if size:
            parts.append(f"({size}in)")
        if material:
            parts.append(f"— {material}")
        lines.append("  - " + " ".join(parts))
    return "\n".join(lines)


def _format_numbers(numbers: list) -> str:
    if not numbers:
        return ""
    lines = []
    for n in numbers:
        if not isinstance(n, dict):
            continue
        num = n.get("number", "")
        loc = n.get("location", "")
        if num:
            lines.append(f"  - #{num}" + (f" at {loc}" if loc else ""))
    return "\n".join(lines)


def _format_list(items: list, prefix: str = "  - ") -> str:
    if not items:
        return ""
    return "\n".join(f"{prefix}{item}" for item in items if item)


def build_prompt_from_dna(
    dna: dict,
    view: str = "front",
    collection: str = "black-rose",
) -> str:
    """Build deterministic generation prompt from DNA consensus.

    Args:
        dna: consensus dict from product-dna/{sku}.json
        view: 'front' | 'back' | 'branding'
        collection: collection slug for branding prompts

    Returns:
        Full prompt string ready for Nano Banana Pro
    """
    garment = dna.get("garment_type", "garment")
    base_color = dna.get("base_color", "")
    base_color_name = dna.get("base_color_name", "")
    secondary_colors = dna.get("secondary_colors", [])
    fabric = dna.get("fabric", "")
    text_content = dna.get("text_content", [])
    numbers = dna.get("numbers", [])
    logos = dna.get("logos", [])
    construction = dna.get("construction", [])
    patches = dna.get("patches", [])
    design_elements = dna.get("design_elements", [])
    stitching = dna.get("stitching_details", "")

    # Build the core spec block
    color_line = f"{base_color}"
    if base_color_name:
        color_line += f" ({base_color_name})"
    if secondary_colors:
        secondary = ", ".join(secondary_colors[:4])
        color_line += f", with secondary: {secondary}"

    spec_block = f"""PRODUCT SPEC (reproduce EXACTLY, pixel-accurate):
Garment type: {garment}
Base color: {color_line}
Fabric: {fabric}"""

    if text_content:
        spec_block += f"\n\nTEXT (spell exactly, same placement/font/color):\n{_format_text_content(text_content)}"

    if numbers:
        spec_block += f"\n\nNUMBERS:\n{_format_numbers(numbers)}"

    if logos:
        spec_block += f"\n\nLOGOS (exact position/size/material):\n{_format_logos(logos)}"

    if patches:
        spec_block += f"\n\nPATCHES:\n{_format_list(patches)}"

    if construction:
        spec_block += f"\n\nCONSTRUCTION:\n{_format_list(construction)}"

    if design_elements:
        spec_block += f"\n\nDESIGN ELEMENTS:\n{_format_list(design_elements)}"

    if stitching:
        spec_block += f"\n\nSTITCHING: {stitching}"

    # View directive
    view_directive = {
        "front": "FRONT VIEW ONLY — show only the front panel. Do NOT render the back.",
        "back": "BACK VIEW ONLY — show only the back panel. Do NOT render the front.",
        "branding": "LIFESTYLE/EDITORIAL shot with model wearing this EXACT garment.",
    }.get(view, "FRONT VIEW ONLY")

    # Presentation based on view
    if view == "branding":
        presentation = _branding_presentation(collection)
    else:
        presentation = """PRESENTATION: No model, no person, no mannequin.
Garment floating naturally on an invisible form with full 3D shape and drape.
Clean white/light gray studio background with subtle floor shadow.
Professional e-commerce lighting — soft key light upper-left, fill right, rim light for edge definition."""

    # Anti-hallucination constraints (non-negotiable)
    anti_halluc = """
STRICT RULES — NON-NEGOTIABLE:
- Render ONLY what is specified in the PRODUCT SPEC above.
- Do NOT add text, logos, patches, or branding not listed in the spec.
- Do NOT invent pockets, panels, zippers, or details not specified.
- Do NOT alter colors — match the hex codes EXACTLY.
- Do NOT change the garment type from what is specified.
- Do NOT add sponsor logos, team names, league marks, or athlete names.
- All text must be spelled EXACTLY as written in quotes above.
- If a detail is unclear, leave it out — NEVER guess.
This is a luxury fashion brand. Accuracy is the only standard."""

    return f"""Generate a photorealistic product render.

{view_directive}

{spec_block}

{presentation}
{anti_halluc}"""


def _branding_presentation(collection: str) -> str:
    """Get collection-specific branding/lifestyle presentation directive."""
    presentations = {
        "black-rose": (
            "PRESENTATION: Dark moody editorial setting — black marble surfaces, "
            "dramatic shadows, rose gold (#B76E79) accent lighting. Gothic luxury "
            "aesthetic. Cinematic composition, 3/4 body shot on a fashion model."
        ),
        "love-hurts": (
            "PRESENTATION: Passionate romantic editorial — red roses, velvet textures, "
            "warm dramatic lighting, luxury castle backdrop. Rich reds and deep burgundy "
            "tones. Cinematic composition, 3/4 body shot on a fashion model."
        ),
        "signature": (
            "PRESENTATION: Bay Area urban editorial — golden hour light, city skyline "
            "or Golden Gate Bridge silhouette. Warm golden tones (#D4AF37). "
            "California luxury vibes. Cinematic composition, 3/4 body shot on a fashion model."
        ),
        "kids-capsule": (
            "PRESENTATION: Child model age 8-12 wearing the garment. Playful yet premium "
            "editorial photography. Bright studio lighting, clean background. "
            "Vibrant, youthful energy with luxury quality. 3/4 body shot."
        ),
    }
    return presentations.get(collection, presentations["black-rose"])


def build_feedback_prompt(
    base_prompt: str,
    failed_metrics: dict,
) -> str:
    """Build a targeted regeneration prompt based on scoring failures.

    Args:
        base_prompt: original DNA prompt
        failed_metrics: dict of {metric_name: {current, target, fix}}

    Returns:
        Enhanced prompt with targeted corrections
    """
    fixes = []

    for metric, details in failed_metrics.items():
        if metric == "color_match":
            delta = details.get("delta_e", 0)
            fixes.append(
                f"- COLOR FIX: base color was off by ΔE={delta:.1f}. Use EXACT hex from spec."
            )
        elif metric == "text_match":
            missing = details.get("missing_text", [])
            wrong = details.get("wrong_text", [])
            if missing:
                fixes.append(f"- TEXT FIX: missing text: {missing}. Add these exactly.")
            if wrong:
                fixes.append(f"- TEXT FIX: wrong spelling/content: {wrong}. Fix to match spec.")
        elif metric == "logo_placement":
            issues = details.get("issues", [])
            for issue in issues:
                fixes.append(f"- LOGO FIX: {issue}")
        elif metric == "garment_type":
            expected = details.get("expected", "")
            got = details.get("got", "")
            fixes.append(
                f"- GARMENT FIX: rendered as '{got}', must be '{expected}'. Fix garment type."
            )
        elif metric == "hallucinations":
            extras = details.get("found", [])
            for extra in extras:
                fixes.append(f"- REMOVE: '{extra}' is NOT in spec. Remove it.")

    if not fixes:
        return base_prompt

    feedback_section = "\n\nTARGETED CORRECTIONS (previous attempt failed these):\n" + "\n".join(
        fixes
    )
    return base_prompt + feedback_section
