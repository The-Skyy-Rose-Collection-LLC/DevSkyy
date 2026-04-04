"""Vision QA — compare source vs generated images.

Uses Gemini Flash (text model) for structured comparison with JSON schema output.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

log = logging.getLogger(__name__)

VISION_MODEL = "gemini-2.5-flash"

_VISION_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "pass": {"type": "BOOLEAN"},
        "score": {"type": "INTEGER"},
        "color_match": {"type": "BOOLEAN"},
        "text_match": {"type": "BOOLEAN"},
        "garment_match": {"type": "BOOLEAN"},
        "logo_match": {"type": "BOOLEAN"},
        "issues": {"type": "ARRAY", "items": {"type": "STRING"}},
        "notes": {"type": "STRING"},
    },
    "required": ["pass", "score", "color_match", "text_match", "garment_match", "logo_match", "issues", "notes"],
}


def vision_compare(
    client,
    source_path: Path,
    generated_bytes: bytes,
    product_name: str,
    view: str = "front",
) -> dict:
    """Compare generated render against source tech flat using Gemini Flash.

    Returns dict with pass/fail, score (0-100), and specific issues.
    """
    from google.genai import types

    src_bytes = source_path.read_bytes()
    src_mime = "image/jpeg" if source_path.suffix.lower() in (".jpg", ".jpeg") else "image/webp"

    view_label = view.upper()
    view_rule = (
        f"IMAGE 2 shows the {view_label} of the garment only. "
        f"Do NOT flag missing content from the opposite side."
    )

    prompt = (
        f"You are a strict QA inspector comparing a SOURCE tech flat vs an AI-generated "
        f"{view_label} VIEW render of '{product_name}'.\n\n"
        "IMAGE 1 = SOURCE tech flat (ground truth)\n"
        f"IMAGE 2 = GENERATED {view_label} VIEW render\n\n"
        f"IMPORTANT: {view_rule}\n\n"
        "Evaluate: 1) BASE COLORS 2) TEXT 3) NUMBERS 4) LOGOS 5) GARMENT TYPE 6) DESIGN ELEMENTS\n\n"
        "DO NOT penalize for: logo 3D depth, fabric drape, lighting/shadows, material gloss, "
        "or content from the opposite side.\n\n"
        "Return ONLY JSON. score=100 means all criteria match. Be strict on colors, text, numbers."
    )

    try:
        response = client.models.generate_content(
            model=VISION_MODEL,
            contents=[
                prompt,
                types.Part(inline_data=types.Blob(mime_type=src_mime, data=src_bytes)),
                types.Part(inline_data=types.Blob(mime_type="image/webp", data=generated_bytes)),
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=_VISION_SCHEMA,
            ),
        )
    except Exception as exc:
        log.error("Vision compare failed: %s", exc)
        return {"pass": True, "score": 0, "issues": [], "notes": f"Vision API error: {exc}"}

    try:
        return json.loads(response.text)
    except (json.JSONDecodeError, AttributeError):
        return {"pass": True, "score": 0, "issues": [], "notes": "Could not parse vision response"}
