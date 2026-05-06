"""Tool 4a (NEW): Sonnet 4.6 articulates Layer 0 rendering directives.

CONSTRAINED design — Sonnet ONLY writes Layer 0 (engine-specific
rendering style). It NEVER touches:
  - Layer 3 (canonical positives — garment_type_lock, branding_block)
  - Layer 2 (canonical negatives — negative_block)

Both come VERBATIM from the dossier in `build_prompt_fn`. This is the
load-bearing constraint for "identical to my products" — the canonical
text the brand author wrote goes UNTOUCHED to the generator.

What Sonnet adapts:
  - Engine-specific style (FLUX likes short, Gemini structured, GPT narrative)
  - Studio setup language (lighting, drape, fabric photorealism)
  - Vision-consensus-aware fabric/finish callouts (when consensus says
    "fleece" Sonnet says "matte fleece texture with visible loop"; when
    consensus says "satin" Sonnet says "smooth reflective satin sheen")
  - Engine output framing (front-only, ghost-mannequin, no model)

Output schema-enforced via Anthropic's tool-use JSON output. Sonnet
returns {"layer0_directives": str}. Assembler in build_prompt_fn:
  final_prompt = layer0_directives  # Sonnet
                 + "\n\n" + layer3_canonical_positives  # verbatim dossier
                 + "\n\n" + layer2_canonical_negatives  # verbatim dossier

State writes:
    layer0_directives (str — Sonnet's output)
    layer0_engine_target (str — which engine the directives are tuned for)
"""

from __future__ import annotations

import json
import logging
import os
from typing import TYPE_CHECKING

from agents.render_pipeline.tools._paths import ensure_repo_paths

ensure_repo_paths()

log = logging.getLogger(__name__)

if TYPE_CHECKING:
    from google.adk.tools.tool_context import ToolContext


_LAYER0_SCHEMA = {
    "type": "object",
    "properties": {
        "layer0_directives": {
            "type": "string",
            "description": (
                "Engine-specific rendering directives — studio setup, lighting, "
                "fabric photorealism cues, view restriction. NEVER includes the "
                "garment description, branding details, or negative rules — those "
                "are owned by the canonical dossier and assembled separately."
            ),
        }
    },
    "required": ["layer0_directives"],
}


_SONNET_INSTRUCTION = """You write engine-specific RENDERING DIRECTIVES (Layer 0) for a luxury
fashion product-render pipeline. Your output is ONE part of a 3-part prompt:

   [Layer 3 — canonical positives, verbatim from dossier]   ← NOT YOU
   [Layer 0 — your output: rendering directives]            ← YOU
   [Layer 2 — canonical negatives, verbatim from dossier]   ← NOT YOU

Your scope is STRICTLY rendering style:
  ✓ Studio setup (lighting, backdrop, drape, ghost-mannequin language)
  ✓ Fabric photorealism cues tuned to the consensus fabric description
  ✓ View restriction (front-only / back-only)
  ✓ Engine-specific framing (FLUX: terse + visual; Gemini: structured + descriptive;
    GPT: narrative + studio-photography vocabulary)

You MUST NOT:
  ✗ Describe the garment type, color, branding, logos, text, or graphics
  ✗ Negate anything (no "do not include X")
  ✗ Reference the dossier — Layers 3 + 2 handle product-identity content
  ✗ Add quality adjectives like "luxurious" or brand language

INPUT: garment hint (e.g. "BLACK Rose Crewneck — black-rose collection") + engine
hint (gemini-pro / gpt-image / flux-pro) + consensus vision data (fabric appearance,
colors, graphics — for fabric-physics styling cues only).

OUTPUT: STRUCTURED JSON {layer0_directives: "..."}.

LENGTH: Layer 0 is rendering-style only — keep it 200-450 characters. The dossier
text (Layers 3 + 2) is what carries product identity. You are setting the camera,
not the garment.

Tone: clinical, technical. Picture: Vogue editorial product shot. Not lifestyle.
"""


def _build_articulation_prompt(
    name: str,
    sku: str,
    collection: str,
    engine: str,
    consensus: dict,
) -> str:
    """Compose the user-side prompt sent to Sonnet alongside the system instruction."""
    fabric = consensus.get("fabric_appearance", "")
    silhouette = consensus.get("silhouette", "")
    construction = consensus.get("construction", "")
    colors_brief = ", ".join(
        f"{c.get('area', '')}: {c.get('color', '')}"
        for c in (consensus.get("colors", []) or [])[:5]
        if c.get("color")
    )
    return (
        f"Product hint: {name} ({sku}) — {collection} collection\n"
        f"Target engine: {engine}\n\n"
        f"Consensus vision (for fabric-physics styling only):\n"
        f"  - fabric_appearance: {fabric or '(unspecified)'}\n"
        f"  - silhouette: {silhouette or '(unspecified)'}\n"
        f"  - colors: {colors_brief or '(deferred to dossier)'}\n"
        f"  - construction: {construction or '(unspecified)'}\n\n"
        "Write Layer 0. Do not describe the garment, branding, or product details — "
        "those come from the dossier. Focus on rendering style for the target engine."
    )


def _fallback_layer0(engine: str) -> str:
    """Static fallback Layer 0 if Sonnet is unavailable.

    Engine-tuned but not vision-aware. Mirrors `prompt_registry._canonical_mode_prompt`
    rendering-style language so the pipeline degrades gracefully rather than
    failing completely. Used when ANTHROPIC_API_KEY is missing or Sonnet errors.
    """
    if engine == "flux-pro":
        return (
            "Photorealistic e-commerce product photo — front view only. "
            "Garment on invisible ghost mannequin against dark luxury backdrop. "
            "Editorial studio lighting with soft key + subtle rim. "
            "4K product-photography sharpness, visible weave + thread weight, "
            "natural drape and shadow. No model, no person, no extras."
        )
    if engine == "gpt-image":
        return (
            "Render a photorealistic editorial product photograph. No model, no "
            "person — the garment floats on an invisible ghost mannequin with "
            "natural 3D drape and shadow against a dark luxury studio backdrop. "
            "Professional fashion lighting (soft key, subtle rim) reveals authentic "
            "fabric texture — weave, sheen, thread weight appropriate to the "
            "canonical fabric. Front view only. 4K commercial product-photography "
            "sharpness."
        )
    # gemini-pro / gemini-flash (now also NB Pro) / default
    return (
        "Render task: photorealistic e-commerce product photo — front view only, "
        "no model, no mannequin. Garment floats on an invisible form with natural "
        "3D drape and shadow. Studio: dark luxury backdrop, professional editorial "
        "lighting (soft key + subtle rim). Photorealistic fabric texture: visible "
        "weave, thread weight, sheen appropriate to the canonical fabric description. "
        "4K product-photography sharpness, no motion blur, no DOF blur on the garment."
    )


def articulate_layer0_fn(sku: str, tool_context: ToolContext) -> dict:
    """Call Sonnet 4.6 to write engine-specific Layer 0 directives.

    Reads state: product_name, collection, engine, vision_consensus
    Writes state: layer0_directives, layer0_engine_target

    Returns dict with layer0_chars, engine_target, used_fallback (bool).
    The directives string itself goes to state (build_prompt_fn reads it).
    """
    from llm.model_ids import CLAUDE_SONNET_MODEL

    name = tool_context.state.get("product_name", "garment")
    collection = tool_context.state.get("collection", "")
    engine = tool_context.state.get("engine", "gemini-pro")
    consensus = tool_context.state.get("vision_consensus", {})

    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not anthropic_key:
        log.warning("articulate_layer0_fn: ANTHROPIC_API_KEY missing — using fallback Layer 0")
        directives = _fallback_layer0(engine)
        tool_context.state["layer0_directives"] = directives
        tool_context.state["layer0_engine_target"] = engine
        return {
            "engine_target": engine,
            "layer0_chars": len(directives),
            "used_fallback": True,
        }

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=anthropic_key)
        user_prompt = _build_articulation_prompt(name, sku, collection, engine, consensus)

        # Sonnet 4.6 with structured tool-use for JSON-shaped output.
        # `tool_choice={"type": "tool", "name": "..."}` forces JSON shape;
        # mirrors the pattern verified in tournament's Opus synthesis call
        # (which uses output_config + thinking but same structured-input contract).
        response = client.messages.create(
            model=CLAUDE_SONNET_MODEL,
            max_tokens=1024,
            system=_SONNET_INSTRUCTION,
            messages=[{"role": "user", "content": user_prompt}],
            tools=[
                {
                    "name": "emit_layer0",
                    "description": "Emit the Layer 0 rendering directives.",
                    "input_schema": _LAYER0_SCHEMA,
                }
            ],
            tool_choice={"type": "tool", "name": "emit_layer0"},
        )

        directives = ""
        for block in response.content:
            if getattr(block, "type", None) == "tool_use":
                payload = getattr(block, "input", {}) or {}
                directives = (payload.get("layer0_directives") or "").strip()
                break

        if not directives:
            raise ValueError("Sonnet returned empty layer0_directives")

    except Exception as exc:
        log.error("articulate_layer0_fn: Sonnet call failed (%s) — using fallback", exc)
        directives = _fallback_layer0(engine)
        tool_context.state["layer0_directives"] = directives
        tool_context.state["layer0_engine_target"] = engine
        return {
            "engine_target": engine,
            "layer0_chars": len(directives),
            "used_fallback": True,
            "error": f"{type(exc).__name__}: {exc}",
        }

    tool_context.state["layer0_directives"] = directives
    tool_context.state["layer0_engine_target"] = engine

    return {
        "engine_target": engine,
        "layer0_chars": len(directives),
        "used_fallback": False,
    }


# Allow tests/scripts to introspect the static prompt without invoking the API
__all__ = ["articulate_layer0_fn", "_LAYER0_SCHEMA", "_SONNET_INSTRUCTION", "_fallback_layer0"]


# json import preserved for fallback paths in future revisions
_ = json
