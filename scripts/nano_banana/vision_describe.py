"""Vision-to-text product describer — feeds source images to a vision model
to extract precise visual details before generation.

Instead of hardcoded prompt text, we ASK the model to LOOK at the techflat
and tell us exactly what it sees. That description then becomes the
generation prompt — grounded in reality, not guesswork.

Usage:
    from nano_banana.vision_describe import describe_product, build_render_prompt
    desc = describe_product(client, source_path, product)
    prompt = build_render_prompt(desc, product, view="front")
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

log = logging.getLogger(__name__)


# -- Vision analysis prompt ---------------------------------------------------

ANALYZE_PROMPT = """You are a luxury fashion technical analyst for SkyyRose, an Oakland-based streetwear brand.

Study this tech flat / product image with extreme precision. Extract EVERY visual detail.

Return a JSON object with these fields (be exhaustive):

{{
  "garment_type": "hoodie / crewneck / joggers / jersey / shorts / jacket / beanie / fanny pack / set",
  "garment_subtype": "football jersey / basketball jersey / hockey jersey / varsity bomber / sherpa / windbreaker / etc.",
  "silhouette": "oversized / relaxed / slim / athletic / cropped / longline",
  "construction": {{
    "panels": "description of panel layout (raglan, set-in, color-block, etc.)",
    "seams": "visible seam details (contrast stitching, flatlock, etc.)",
    "closures": "buttons, snaps, zipper type, drawstring",
    "details": "pockets, ribbing, cuffs, hem treatment, hood lining"
  }},
  "colors": [
    {{"area": "body", "color": "#hex or name", "finish": "matte / satin / glossy"}},
    {{"area": "sleeves", "color": "#hex", "finish": "..."}},
    {{"area": "trim", "color": "#hex", "finish": "..."}}
  ],
  "graphics": [
    {{
      "type": "embroidery / sublimation / screen print / silicone patch / tackle-twill / foil",
      "content": "exact text or description of graphic",
      "location": "front chest center / left thigh / full front / back / etc.",
      "size": "approximate size in inches",
      "colors": ["#hex1", "#hex2"],
      "style": "3D dimensional / flat / raised / glossy / matte"
    }}
  ],
  "branding": {{
    "primary_logo": "description of main SkyyRose logo/rose used",
    "logo_location": "where on garment",
    "logo_technique": "embroidery / silicone / sublimation / etc.",
    "secondary_marks": "any additional brand marks, tags, or labels visible"
  }},
  "fabric_appearance": "visual texture — smooth fleece, French terry, mesh, satin, sherpa pile, jersey knit",
  "unique_features": "anything distinctive about this specific product — limited edition numbering, sport patches, hidden details",
  "views_shown": "front only / front+back / front+back set (top+bottom)",
  "collection_aesthetic": "how this fits the SkyyRose brand — dark luxury, Oakland grit, emotional expression"
}}

Be extremely specific about colors (use hex codes when possible), logo placement, and construction. The generation model needs this level of detail to reproduce the garment accurately."""


def describe_product(
    client,
    source_path: Path,
    product: dict,
    *,
    model: str = "gemini-2.5-flash",
) -> dict:
    """Analyze a product source image using vision and return structured description.

    Args:
        client: google.genai.Client instance
        source_path: Path to the techflat/source image
        product: Product dict with name, sku, collection
        model: Vision model to use for analysis

    Returns:
        Parsed JSON dict with detailed product description.
    """
    from google.genai import types

    if not source_path or not source_path.exists():
        log.warning("No source image for %s — returning empty description", product.get("sku"))
        return {}

    name = product.get("name", "garment")
    sku = product.get("sku", "")
    collection = product.get("collection", "")

    context = (
        f"Product: {name}\n"
        f"SKU: {sku}\n"
        f"Collection: {collection}\n"
        f"Brand: SkyyRose — Oakland luxury streetwear"
    )

    try:
        response = client.models.generate_content(
            model=model,
            contents=[
                f"PRODUCT CONTEXT:\n{context}\n\nSOURCE IMAGE:",
                types.Part.from_bytes(
                    data=source_path.read_bytes(),
                    mime_type=_mime_type(source_path),
                ),
                ANALYZE_PROMPT,
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                max_output_tokens=4096,
                temperature=0.1,  # Low temp for factual extraction
            ),
        )

        text = ""
        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if hasattr(part, "text") and part.text:
                    text += part.text

        if not text:
            log.warning("Empty vision response for %s", sku)
            return {}

        desc = json.loads(text)
        log.info("Vision analysis for %s: %d fields extracted", sku, len(desc))
        return desc

    except Exception as exc:
        log.error("Vision describe failed for %s: %s", sku, exc)
        return {}


def _mime_type(path: Path) -> str:
    ext = path.suffix.lower()
    return {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }.get(ext, "image/jpeg")


# -- Prompt builders from vision description ----------------------------------

def build_render_prompt(desc: dict, product: dict, view: str = "front") -> str:
    """Build a generation prompt grounded in the vision model's analysis.

    This is the core innovation: instead of a generic prompt, we use
    what the vision model actually SAW to construct a precise specification.
    """
    from nano_banana.prompts import ANTI_HALLUCINATION, COLLECTION_LIGHTING, LOGO_TREATMENTS

    name = product.get("name", "garment")
    collection = product.get("collection", "black-rose")
    sku = product.get("sku", "")
    lighting = COLLECTION_LIGHTING.get(collection, COLLECTION_LIGHTING["black-rose"])

    if not desc:
        # Fallback to standard prompts if vision failed
        from nano_banana.prompts import get_prompt
        return get_prompt(product, view)

    garment = desc.get("garment_type", "garment")
    subtype = desc.get("garment_subtype", "")
    silhouette = desc.get("silhouette", "")
    fabric = desc.get("fabric_appearance", "")
    garment_label = f"{silhouette} {subtype or garment}".strip()

    # Build color spec from vision data
    color_spec = ""
    colors = desc.get("colors", [])
    if colors:
        color_lines = []
        for c in colors:
            area = c.get("area", "")
            color = c.get("color", "")
            finish = c.get("finish", "")
            if area and color:
                color_lines.append(f"  - {area}: {color} ({finish})" if finish else f"  - {area}: {color}")
        if color_lines:
            color_spec = "\n\nEXACT COLORS (from source analysis):\n" + "\n".join(color_lines)

    # Build graphics spec from vision data
    graphics_spec = ""
    graphics = desc.get("graphics", [])
    if graphics:
        gfx_lines = []
        for g in graphics:
            gtype = g.get("type", "")
            content = g.get("content", "")
            location = g.get("location", "")
            size = g.get("size", "")
            style = g.get("style", "")
            line = f"  - {location}: {content}"
            if gtype:
                line += f" ({gtype})"
            if size:
                line += f", ~{size}"
            if style:
                line += f", {style} finish"
            gfx_lines.append(line)
        if gfx_lines:
            graphics_spec = "\n\nGRAPHICS & BRANDING (from source analysis):\n" + "\n".join(gfx_lines)

    # Build construction spec
    construction_spec = ""
    construction = desc.get("construction", {})
    if construction:
        c_lines = []
        for k, v in construction.items():
            if v:
                c_lines.append(f"  - {k}: {v}")
        if c_lines:
            construction_spec = "\n\nCONSTRUCTION DETAILS:\n" + "\n".join(c_lines)

    # Add logo treatment from our metadata (enriches vision data)
    treatment = LOGO_TREATMENTS.get(sku, "")
    treatment_spec = ""
    if treatment:
        treatment_spec = f"\n\nBRANDING SPEC (verified): {treatment}"

    if view == "front":
        return (
            f"Generate a photorealistic luxury e-commerce render of this {name} — FRONT VIEW ONLY.\n\n"
            f"GARMENT: {garment_label}\n"
            f"FABRIC: {fabric}\n"
            f"{color_spec}{graphics_spec}{construction_spec}{treatment_spec}\n\n"
            f"VIEW: FRONT PANEL ONLY. Do NOT show the back.\n\n"
            f"PRESENTATION:\n"
            f"- No model, no mannequin. Garment floating on invisible form, natural 3D drape.\n"
            f"- {lighting['bg']}.\n"
            f"- {lighting['light']}.\n"
            f"- {lighting['mood']}.\n"
            f"- Photorealistic fabric texture — visible weave, thread weight, material sheen.\n\n"
            f"FIDELITY: Every color, logo, panel, stripe, and stitch must match the source EXACTLY."
            + ANTI_HALLUCINATION
        )

    elif view == "back":
        return (
            f"Generate a photorealistic luxury e-commerce render of this {name} — BACK VIEW ONLY.\n\n"
            f"GARMENT: {garment_label}\n"
            f"FABRIC: {fabric}\n"
            f"{color_spec}{graphics_spec}{construction_spec}{treatment_spec}\n\n"
            f"VIEW: BACK PANEL ONLY. Garment facing away.\n\n"
            f"PRESENTATION:\n"
            f"- No model, no mannequin. Back-facing on invisible form.\n"
            f"- {lighting['bg']}.\n"
            f"- {lighting['light']}.\n"
            f"- Photorealistic fabric texture.\n\n"
            f"FIDELITY: Match back reference exactly."
            + ANTI_HALLUCINATION
        )

    else:  # branding / editorial
        return _build_editorial_prompt(desc, product, lighting, treatment_spec)


def _build_editorial_prompt(
    desc: dict, product: dict, lighting: dict, treatment_spec: str
) -> str:
    """Build an editorial/lifestyle prompt grounded in vision analysis."""
    from nano_banana.prompts import ANTI_HALLUCINATION, BRANDING_TEMPLATES

    name = product.get("name", "garment")
    collection = product.get("collection", "black-rose")
    sku = product.get("sku", "")

    garment = desc.get("garment_type", "garment")
    subtype = desc.get("garment_subtype", "")
    fabric = desc.get("fabric_appearance", "")
    unique = desc.get("unique_features", "")
    aesthetic = desc.get("collection_aesthetic", "")

    garment_label = f"{subtype or garment}".strip()

    # Use the template but inject vision-sourced specifics
    tpl = BRANDING_TEMPLATES.get(collection, BRANDING_TEMPLATES["black-rose"])
    base = tpl.format(name=name, treatment_note=treatment_spec)

    # Enrich with vision data
    vision_enrichment = (
        f"\n\nVISION-VERIFIED DETAILS:\n"
        f"- Garment: {garment_label}\n"
        f"- Fabric: {fabric}\n"
    )
    if unique:
        vision_enrichment += f"- Unique features: {unique}\n"
    if aesthetic:
        vision_enrichment += f"- Aesthetic note: {aesthetic}\n"

    return base + vision_enrichment + ANTI_HALLUCINATION


# -- Batch describe -----------------------------------------------------------

def describe_all_products(
    client,
    products: list[dict],
    output_dir: Path | None = None,
) -> dict[str, dict]:
    """Run vision analysis on all products with source images.

    Returns dict of {sku: description}.
    Optionally saves each description to output_dir/{sku}-vision.json.
    """
    import time

    results = {}
    total = len(products)

    for i, product in enumerate(products):
        sku = product["sku"]
        source = product.get("source_image")

        if not source or not Path(source).exists():
            log.info("[%d/%d] %s — no source image, skipping", i + 1, total, sku)
            continue

        log.info("[%d/%d] Analyzing %s...", i + 1, total, sku)
        desc = describe_product(client, Path(source), product)

        if desc:
            results[sku] = desc
            if output_dir:
                output_dir.mkdir(parents=True, exist_ok=True)
                out_file = output_dir / f"{sku}-vision.json"
                out_file.write_text(json.dumps(desc, indent=2))
                log.info("  Saved → %s", out_file.name)

        # Rate limiting — 2 seconds between calls
        if i < total - 1:
            time.sleep(2)

    log.info("Vision analysis complete: %d/%d products described", len(results), total)
    return results
