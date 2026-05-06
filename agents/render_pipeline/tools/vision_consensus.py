"""Tool 3a (NEW): Dual-vision consensus describe — Gemini + OpenAI in parallel.

F3 root cause: vision-driven routing was stochastic because
`gemini-vision-describe` outputs varied between runs. Different keyword
sets produced different routing decisions → 58-pt swing on br-001.

Fix: run BOTH Gemini-3-flash-preview AND GPT-4o vision in parallel
against the source image, then merge their structured outputs. Routing
keys are taken from the consensus (intersection); Sonnet's Layer 0
articulator (next tool) reads both reports for richer context.

Cost: ~$0.005 (Gemini) + ~$0.005 (GPT-4o) = ~$0.01 per describe.
Cached on disk so subsequent runs of the same SKU are free.

State writes:
    vision_consensus (dict with merged fields + per-provider raw outputs)
    vision_consensus_path (cache file)
"""

from __future__ import annotations

import base64
import concurrent.futures
import json
import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING

from agents.render_pipeline.tools._paths import REPO_ROOT, ensure_repo_paths

ensure_repo_paths()

log = logging.getLogger(__name__)

if TYPE_CHECKING:
    from google.adk.tools.tool_context import ToolContext


# Structured-output schema both vision models emit. Identical schema =
# trivial merge logic. Mirrors `nano_banana.vision_describe` output shape
# so existing routing/prompt code reads consensus as drop-in replacement.
_VISION_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "garment_type": {"type": "string"},
        "garment_subtype": {"type": "string"},
        "silhouette": {"type": "string"},
        "fabric_appearance": {"type": "string"},
        "colors": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "area": {"type": "string"},
                    "color": {"type": "string"},
                    "finish": {"type": "string"},
                },
                "required": ["area", "color"],
            },
        },
        "graphics": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "type": {"type": "string"},
                    "content": {"type": "string"},
                    "location": {"type": "string"},
                    "size": {"type": "string"},
                    "style": {"type": "string"},
                },
                "required": ["type", "content", "location"],
            },
        },
        "construction": {"type": "string"},
    },
    "required": [
        "garment_type",
        "garment_subtype",
        "silhouette",
        "fabric_appearance",
        "colors",
        "graphics",
        "construction",
    ],
}


_DESCRIBE_PROMPT = """Examine this garment reference image carefully. Produce a STRUCTURED JSON
description focused on visual ground truth, not interpretation.

Required fields:
- garment_type: single-word category (hoodie, crewneck, jacket, jersey, joggers, shorts, set, tee, accessory)
- garment_subtype: more specific (e.g. "varsity bomber", "pullover hoodie", "track joggers")
- silhouette: relaxed | regular | slim | oversized
- fabric_appearance: visible fabric description (fleece, satin, mesh, knit, ribbed, etc.)
- colors: list of {area, color, finish} per visible region
- graphics: list of {type, content, location, size, style} per logo/text/patch/embroidery
- construction: panel/seam/closure observations

Be literal. Describe what you SEE, not what you think the brand intends. If a region is
ambiguous, mark it ambiguous rather than inventing detail.
"""


def _gemini_describe(source_path: Path) -> dict:
    """Gemini-3-flash-preview vision describe with structured-output."""
    from google.genai import types
    from nano_banana.client import get_genai_client

    from llm.model_ids import GEMINI_VISION_MODEL

    client = get_genai_client()
    ext = source_path.suffix.lower()
    mime = (
        "image/jpeg"
        if ext in (".jpg", ".jpeg")
        else "image/webp"
        if ext == ".webp"
        else "image/png"
    )

    response = client.models.generate_content(
        model=GEMINI_VISION_MODEL,
        contents=[
            types.Part.from_bytes(data=source_path.read_bytes(), mime_type=mime),
            _DESCRIBE_PROMPT,
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=_VISION_SCHEMA,
            max_output_tokens=4096,
            temperature=0.3,
            thinking_config=types.ThinkingConfig(thinking_budget=-1),
        ),
    )
    text_parts = []
    if response.candidates and response.candidates[0].content.parts:
        for part in response.candidates[0].content.parts:
            if hasattr(part, "text") and part.text:
                text_parts.append(part.text)
    raw = "\n".join(text_parts) if text_parts else (response.text or "")
    return json.loads(raw) if raw.strip() else {}


def _openai_describe(source_path: Path) -> dict:
    """GPT-4o vision describe via Responses API + json_schema constrained output.

    Mirrors `nano_banana.tournament._judge_call_gpt` SDK contract:
      - `client.responses.create()` (not chat.completions)
      - `text={"format": {"type": "json_schema", ...}}` for structured output
      - `input_image` part with data URL inline
      - `output_text` accessor
    """
    from nano_banana.client import get_openai_client

    from llm.model_ids import OPENAI_VISION_MODEL

    client = get_openai_client()
    if client is None:
        log.warning("OpenAI client unavailable — dual-vision degrading to Gemini-only")
        return {}

    ext = source_path.suffix.lower()
    mime = (
        "image/jpeg"
        if ext in (".jpg", ".jpeg")
        else "image/webp"
        if ext == ".webp"
        else "image/png"
    )
    b64 = base64.b64encode(source_path.read_bytes()).decode("utf-8")

    response = client.responses.create(
        model=OPENAI_VISION_MODEL,
        max_output_tokens=4096,
        text={
            "format": {
                "type": "json_schema",
                "name": "vision_describe",
                "strict": True,
                "schema": _VISION_SCHEMA,
            }
        },
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": _DESCRIBE_PROMPT},
                    {"type": "input_image", "image_url": f"data:{mime};base64,{b64}"},
                ],
            }
        ],
    )
    raw = response.output_text or ""
    return json.loads(raw) if raw.strip() else {}


def _merge_consensus(gemini: dict, openai: dict) -> dict:
    """Merge two vision reports into a consensus dict.

    Strategy:
    - Scalar fields (garment_type, fabric_appearance, etc.): prefer non-empty;
      when both are non-empty, take Gemini's (matches existing pipeline behavior).
    - List fields (colors, graphics): union by primary key (area / location).
    - Routing keywords: union — `route_product()` reads `fabric_appearance`,
      so concatenating both descriptions captures both providers' fabric reads.

    Per-provider raw payloads preserved under `_raw_gemini` / `_raw_openai`
    so Sonnet's Layer 0 articulator can read each independently when useful.
    """
    out: dict = {}
    scalar_keys = (
        "garment_type",
        "garment_subtype",
        "silhouette",
        "construction",
    )
    for k in scalar_keys:
        gem = (gemini or {}).get(k, "") or ""
        oai = (openai or {}).get(k, "") or ""
        out[k] = gem or oai  # Gemini wins ties

    # fabric_appearance: concatenate when they differ — routing keyword union
    gem_fab = (gemini or {}).get("fabric_appearance", "") or ""
    oai_fab = (openai or {}).get("fabric_appearance", "") or ""
    if gem_fab and oai_fab and gem_fab.lower() != oai_fab.lower():
        out["fabric_appearance"] = f"{gem_fab} | {oai_fab}"
    else:
        out["fabric_appearance"] = gem_fab or oai_fab

    # colors: union by `area` (case-insensitive), preserving first-seen entry
    seen_areas: set[str] = set()
    merged_colors: list[dict] = []
    for src in ((gemini or {}).get("colors", []), (openai or {}).get("colors", [])):
        for c in src or []:
            area = (c.get("area") or "").lower().strip()
            if area and area not in seen_areas:
                seen_areas.add(area)
                merged_colors.append(c)
    out["colors"] = merged_colors

    # graphics: union by (location, content) key
    seen_gfx: set[tuple] = set()
    merged_gfx: list[dict] = []
    for src in ((gemini or {}).get("graphics", []), (openai or {}).get("graphics", [])):
        for g in src or []:
            key = (
                (g.get("location") or "").lower().strip(),
                (g.get("content") or "").lower().strip(),
            )
            if key and key not in seen_gfx:
                seen_gfx.add(key)
                merged_gfx.append(g)
    out["graphics"] = merged_gfx

    out["_raw_gemini"] = gemini or {}
    out["_raw_openai"] = openai or {}
    out["_providers_succeeded"] = sum(1 for d in (gemini, openai) if d)

    return out


def vision_consensus_fn(sku: str, tool_context: "ToolContext") -> dict:
    """Run dual vision describe in parallel + merge to consensus.

    Reads state: source_path
    Writes state: vision_consensus (merged dict)

    Cache: results stored at `data/vision-consensus/{sku}.json`. Subsequent
    runs of the same SKU read from cache (free + deterministic).
    """
    source_path_str = tool_context.state.get("source_path", "")
    if not source_path_str:
        return {"error": "no source_path in state — resolve_source must run first"}
    source_path = Path(source_path_str)

    # Disk cache — F3-fix: same source = same consensus, always
    cache_dir = REPO_ROOT / "data" / "vision-consensus"
    cache_file = cache_dir / f"{sku}.json"
    if cache_file.exists() and not os.environ.get("VISION_CONSENSUS_NOCACHE"):
        try:
            cached = json.loads(cache_file.read_text())
            tool_context.state["vision_consensus"] = cached
            return {
                "sku": sku,
                "cached": True,
                "providers_succeeded": cached.get("_providers_succeeded", 0),
                "garment_type": cached.get("garment_type", ""),
                "fabric_appearance": cached.get("fabric_appearance", ""),
                "graphics_count": len(cached.get("graphics", [])),
            }
        except (json.JSONDecodeError, OSError):
            pass

    # Run both providers in parallel
    gemini_result: dict = {}
    openai_result: dict = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        f_gem = pool.submit(_gemini_describe, source_path)
        f_oai = pool.submit(_openai_describe, source_path)
        try:
            gemini_result = f_gem.result(timeout=120) or {}
        except Exception as exc:
            log.warning("vision_consensus_fn: gemini describe failed: %s", exc)
        try:
            openai_result = f_oai.result(timeout=120) or {}
        except Exception as exc:
            log.warning("vision_consensus_fn: openai describe failed: %s", exc)

    if not gemini_result and not openai_result:
        return {"error": "both vision providers failed", "sku": sku}

    consensus = _merge_consensus(gemini_result, openai_result)

    # Persist cache
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps(consensus, indent=2))

    tool_context.state["vision_consensus"] = consensus

    return {
        "sku": sku,
        "cached": False,
        "providers_succeeded": consensus["_providers_succeeded"],
        "garment_type": consensus.get("garment_type", ""),
        "fabric_appearance": consensus.get("fabric_appearance", ""),
        "graphics_count": len(consensus.get("graphics", [])),
        "colors_count": len(consensus.get("colors", [])),
    }
