"""Stage 3 prompts — physics-described decoration language.

Naming the technique ("embossed", "embroidered") fights the model's data
prior — internet imagery has 1000x more embroidered logos than embossed
ones, so the prior is "decoration = thread + stitching." Negative prompts
("NOT embroidery") only act between diffusion steps 5-11 (ArXiv 2406.02965)
and routinely fail.

Describing the *physical mechanism* of the technique — pressed-into-fabric
relief, raking-light shadow at edges, tonal single-color impression — gives
the model an alternative low-energy state to settle into without fighting
the prior.

H3 double-negative structure (per architecture hardening):
  1. ONLY-prefixed positive — no element exists outside the positive list.
  2. PHYSICAL TECHNIQUE physics block.
  3. TECHNIQUE_NEGATIVE_PREFIX — technique-specific hallucination ban, fires
     immediately after the physics block.
  4. _TONAL_AMPLIFIER — for embossed/debossed only, stacks a CRITICAL: block
     to give two contiguous barriers against the printed-ink prior.
  5. COLOR block.
  6. Mask-bounds constraint + photography quality.
  7. UNIVERSAL_NEGATIVE_SUFFIX — explicit rejection contract as final sentence.
"""

from __future__ import annotations

# Physical-mechanism descriptions per technique. Maps the controlled-vocabulary
# techniques from validate_dossier.py to language that describes WHAT the
# technique looks like physically, not WHAT it's called.
TECHNIQUE_PHYSICS: dict[str, str] = {
    "embossed": (
        "fabric surface impression, design pressed into cloth, same hue as "
        "surrounding fabric, zero color difference, zero contrast, no ink, no "
        "white, not screen-printed, visible ONLY under oblique raking light as "
        "micro-shadows along compression edges, invisible under flat lighting, "
        "tonal relief reads as subtle 3D texture, identical color to base fabric "
        "throughout"
    ),
    "debossed": (
        "design stamped below fabric surface level, recessed into cloth, same "
        "color as surrounding fabric, no contrast, no ink, no white, not printed, "
        "reads only in directional light as shadow pooling inside recessed channels, "
        "flat lighting makes it invisible, zero color difference between design and "
        "base fabric, tonal shadow-depth effect only, monochromatic fabric surface "
        "throughout"
    ),
    "embroidered": (
        "satin-stitch thread embroidery with visible directional thread "
        "texture, slightly raised above the fabric surface, distinct color "
        "thread against the body fabric"
    ),
    "embroidered-patch": (
        "embroidered cloth patch sewn onto the garment with visible perimeter "
        "stitching attaching the patch to the body fabric, the patch itself "
        "carries embroidered detail with thread texture"
    ),
    "printed": (
        "flat printed graphic on the fabric surface, ink-saturated colors, "
        "no texture difference between decoration and fabric, smooth surface"
    ),
    "screen-print": (
        "screen-printed graphic with slightly thick ink layer, matte finish, "
        "subtle raised feel where ink sits on top of the fabric weave"
    ),
    "sublimated": (
        "dye-sublimated graphic permanently merged into the fabric fibers, "
        "no surface texture change, the colors become part of the fabric "
        "itself, no ink layer on top"
    ),
    "stitched": (
        "construction stitching forming a structural element, visible needle "
        "perforations and thread pulled tight against the fabric"
    ),
    "patch": (
        "physically attached cloth or material patch with visible perimeter "
        "stitching securing it to the body fabric"
    ),
    "woven-label": (
        "small rectangular woven brand label sewn onto the garment, the label "
        "is a separate textile with woven thread carrying the brand name and "
        "size, attached at its perimeter"
    ),
    "puff-print": (
        "puff-print decoration that has been heat-expanded so the printed "
        "design rises above the fabric surface in a soft 3D relief"
    ),
    "heat-transfer": (
        "heat-transfer vinyl decoration with a flat smooth plastic-like "
        "surface bonded to the fabric, slightly raised at the edges"
    ),
    "laser-engraved": (
        "laser-engraved tonal design, subtle color difference where the laser "
        "modified the fabric, no thread, no surface attachment"
    ),
    "tackle-twill": (
        "tackle-twill sewn cloth letters/numbers, each character is a separate "
        "fabric piece sewn onto the body with visible perimeter stitching"
    ),
    "silicone-applique": (
        "raised silicone applique with a smooth glossy surface that sits above "
        "the fabric, full-color art preserved within the silicone layer"
    ),
}


# Per-technique negative injected immediately AFTER the physics description,
# before the color block. Bans the most likely hallucination mode per technique.
TECHNIQUE_NEGATIVE_PREFIX: dict[str, str] = {
    "embossed": (
        "ZERO printed ink, ZERO embroidery thread, ZERO applique, ZERO screen print. "
        "No letterforms, no graphic color fills — only tonal relief in the fabric."
    ),
    "debossed": (
        "ZERO printed ink, ZERO embroidery thread, ZERO applique. "
        "No letterforms, no color fills — only tonal sunken impression in the fabric."
    ),
    "embroidered": (
        "ZERO printed text overlay, ZERO flat graphic ink. "
        "Only raised thread with visible stitch directionality."
    ),
    "embroidered-patch": (
        "ZERO direct-to-fabric screen print. "
        "Only a separate cloth patch attached with perimeter stitching."
    ),
    "printed": (
        "ZERO embroidery thread, ZERO raised relief. "
        "Only flat ink-on-fabric surface with no texture variance."
    ),
    "screen-print": (
        "ZERO embroidery thread, ZERO relief. "
        "Only flat matte ink layer sitting on the fabric weave."
    ),
    "sublimated": (
        "ZERO surface ink layer, ZERO raised texture. "
        "Color is dye inside the fiber — no ink sitting on top."
    ),
    "stitched": (
        "ZERO printed text or graphic overlay. "
        "Only structural thread perforations and pulled stitching."
    ),
    "patch": (
        "ZERO direct-to-fabric print. "
        "Only a physically attached cloth piece with perimeter stitching."
    ),
    "woven-label": (
        "ZERO screen print, ZERO embroidery on the body fabric. "
        "Only a separate woven textile label attached at its edges."
    ),
    "puff-print": (
        "ZERO embroidery thread, ZERO flat print. "
        "Only heat-expanded relief sitting above the fabric surface."
    ),
    "heat-transfer": (
        "ZERO embroidery, ZERO screen-printed ink. "
        "Only flat vinyl bonded to the fabric with slightly raised edges."
    ),
    "laser-engraved": (
        "ZERO thread, ZERO ink, ZERO surface attachment. "
        "Only a tonal color shift where the laser modified the fiber."
    ),
    "tackle-twill": (
        "ZERO direct embroidery or printed text. "
        "Only separate fabric characters sewn with perimeter stitching."
    ),
    "silicone-applique": (
        "ZERO embroidery thread, ZERO flat print. "
        "Only raised glossy silicone bonded to the fabric surface."
    ),
    "_default": (
        "ZERO embroidery thread unless the technique is embroidery. "
        "ZERO printed ink unless the technique is printing. "
        "Decoration must match only the physical technique described."
    ),
}

# Tonal amplifier for embossed/debossed only — stacks with TECHNIQUE_NEGATIVE_PREFIX
# to give two contiguous barriers against the hallucinated-print failure mode.
_TONAL_AMPLIFIER: dict[str, str] = {
    "embossed": (
        "CRITICAL: this is TONAL. The decoration is the SAME COLOR as the "
        "surrounding fabric. There is NO contrasting ink, NO white text, NO "
        "dark lettering, NO color fill of any kind inside the design boundary. "
        "Visibility comes solely from surface relief catching directional light."
    ),
    "debossed": (
        "CRITICAL: this is TONAL. The decoration is the SAME COLOR as the "
        "surrounding fabric. There is NO contrasting ink, NO white text, NO "
        "dark lettering, NO color fill of any kind inside the design boundary. "
        "Visibility comes solely from the sunken depression catching shadow."
    ),
}

# Rejection contract — absolute final sentence of every Stage 3 prompt.
UNIVERSAL_NEGATIVE_SUFFIX = (
    "FINAL CONTRACT: Only the decoration described above exists in this masked region. "
    "No embroidery thread unless the technique above is embroidery. "
    "No printed or screen-printed graphics unless the technique above is printing. "
    "No contrasting letterforms, logos, or graphic fills unless explicitly listed. "
    "If any element named in this negative section appears in the output, "
    "the render is rejected and will not advance to the next pipeline stage."
)


def build_decoration_prompt(
    *,
    decoration_description: str,
    technique: str,
    region: str,
    color: str,
    lora_trigger: str | None = None,
) -> str:
    """Construct the Stage 3 (decoration inpaint) prompt.

    Implements H3 double-negative structure:
      1. ONLY-prefixed positive — model is told no element exists outside this list.
      2. PHYSICAL TECHNIQUE physics block.
      3. TECHNIQUE_NEGATIVE_PREFIX — technique-specific ban fires immediately after physics.
      4. _TONAL_AMPLIFIER — for embossed/debossed, adds a CRITICAL: tonal constraint block.
      5. COLOR block.
      6. Mask-bounds constraint + photography quality.
      7. UNIVERSAL_NEGATIVE_SUFFIX — rejection contract as the final sentence.

    Args:
        decoration_description: short description from the dossier
            ("Black Rose three-rose-cluster", "SR monogram cursive script").
        technique: controlled-vocabulary technique
            ("embossed", "embroidered", etc).
        region: dossier region name ("front-center-chest", "back-yoke").
        color: color from the dossier ("black on black", "gold thread on white").
        lora_trigger: optional trigger word if a LoRA is active
            (e.g., "SKYR_EMBOSS").

    Returns:
        Prompt string for FLUX Fill Pro / FLUX Kontext-LoRA inpainting.
    """
    physics = TECHNIQUE_PHYSICS.get(
        technique,
        f"a {technique} decoration applied to the garment fabric",
    )
    technique_negative = TECHNIQUE_NEGATIVE_PREFIX.get(
        technique,
        TECHNIQUE_NEGATIVE_PREFIX["_default"],
    )
    tonal_amplifier = _TONAL_AMPLIFIER.get(technique, "")
    trigger_prefix = f"{lora_trigger} " if lora_trigger else ""
    tonal_block = f" {tonal_amplifier}" if tonal_amplifier else ""

    # For sublimated multi-color stripes (e.g. "pink + green + lavender + yellow"),
    # FLUX defaults to 2 colors unless forced to enumerate all N explicitly.
    if technique == "sublimated" and "+" in color:
        colors = [c.strip() for c in color.split("+")]
        color_list = ", ".join(colors)
        color_block = (
            f"COLOR — EXACT PALETTE, ALL {len(colors)} COLORS REQUIRED: {color_list}. "
            f"Each of these {len(colors)} colors must appear as a distinct visible stripe. "
            f"A render showing fewer than {len(colors)} of these colors is incorrect. "
        )
    else:
        color_block = f"COLOR: {color}. "

    return (
        f"{trigger_prefix}"
        f"ONLY this decoration exists on the {region} — "
        f"no other text, graphics, logos, marks, or surface elements of any kind: "
        f"{decoration_description}. "
        f"PHYSICAL TECHNIQUE: {physics}. "
        f"{technique_negative}"
        f"{tonal_block} "
        f"{color_block}"
        f"The decoration sits exactly where the mask indicates and nowhere else. "
        f"High-fidelity professional product photography, sharp focus, "
        f"true-to-fabric appearance. "
        f"{UNIVERSAL_NEGATIVE_SUFFIX}"
    )


def build_violation_feedback(
    *, prior_violations: list[dict], retry_attempt: int, max_attempts: int
) -> str:
    """Build a retry header for the next Stage 3 prompt.

    IMPORTANT: Never name violation elements in the prompt text. Diffusion
    models have no concept of negation — "DO NOT render X" competes with
    "render X" at cross-attention and the visual token for X often wins.
    Naming the hallucinated element causes it to appear again.

    Instead: positive-only header that signals strict adherence, then the
    existing H3 prompt body follows unchanged. Guidance escalation (handled
    in decoration_inpaint.py) does the real work on retries.

    Args:
        prior_violations: list of dicts with ``element``, ``region``, ``severity``.
        retry_attempt: 1-based count of the upcoming retry.
        max_attempts: total attempts allowed.

    Returns:
        Positive-only header string, empty if no blocking violations.
    """
    blocking = [v for v in prior_violations if v.get("severity") in ("medium", "high")]
    if not blocking:
        return ""

    return (
        f"STRICT ADHERENCE MODE — pass {retry_attempt} of {max_attempts}. "
        f"Render EXACTLY and ONLY the physical technique and colors described below. "
        f"Any element not named in the specification below is absent from this product. "
        f"\n\n"
    )
