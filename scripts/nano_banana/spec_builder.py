"""Build judge-ready specs from the canonical product dossier.

Why this exists: the tournament's `_dna_to_spec()` formats a flat DNA
dict (garment_type, base_color, logos, construction, fabric) into a
short prose spec for the vision judges. That format is too thin to
capture the per-element technique/color callouts ("white ribbed
neckband contrasting against the black body", "tonal embossed
black-on-black rose"), the negative list ("NO black ribbed neckband"),
and the technique distinctions (embossed vs embroidered vs printed)
that the canonical dossiers spell out.

Without this builder, judges scored against inferred DNA from
Gemini-vision-describe instead of against the canonical truth, leading
to wrong corrections (e.g., refining away the legitimate white trim on
br-001's Black Rose Crewneck because the inferred DNA didn't mention
it).

Usage:
    from nano_banana.spec_builder import build_dna_from_sku
    dna = build_dna_from_sku("br-001")  # raises if dossier missing
    result = run_tournament(clients, source, candidate, dna=dna)

The returned dna dict carries a `spec` key that `_dna_to_spec()` uses
verbatim, bypassing the lossy prose synthesis from flat fields.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from skyyrose.core.dossier_loader import (  # noqa: E402
    Dossier,
    get_product_with_dossier,
)


def build_judge_spec_from_dossier(dossier: Dossier) -> str:
    """Format a Dossier object into a multi-section spec string.

    Layout:
      GARMENT TYPE LOCK: ... (locks the type so judges reject wrong silhouettes)
      BRANDING — exactly what IS on this product: ... (per-element technique/color)
      NEGATIVE — what is NOT on this product: ... (the explicit don'ts)
      SCENE: ... (pose + setting if specified, optional)

    Each block is the dossier's verbatim text. We don't re-summarize —
    the dossier prose was authored to be read by humans and models
    alike, and lossy compression is exactly what created the bug.
    """
    parts: list[str] = []

    if dossier.name:
        parts.append(f"PRODUCT: {dossier.name} ({dossier.sku})")

    if dossier.garment_type_lock:
        parts.append(f"GARMENT TYPE LOCK:\n{dossier.garment_type_lock}")

    if dossier.branding_block:
        parts.append(f"BRANDING — exactly what IS on this product:\n{dossier.branding_block}")

    if dossier.negative_block:
        parts.append(
            f"NEGATIVE — what is NOT on this product (DO NOT render):\n{dossier.negative_block}"
        )

    if dossier.scene_pose or dossier.scene_setting:
        scene_lines = []
        if dossier.scene_pose:
            scene_lines.append(f"Pose: {dossier.scene_pose}")
        if dossier.scene_setting:
            scene_lines.append(f"Setting: {dossier.scene_setting}")
        parts.append("SCENE:\n" + "\n".join(scene_lines))

    return "\n\n".join(parts)


def build_dna_from_sku(sku: str) -> dict:
    """Return a DNA dict for `sku` keyed off the canonical dossier.

    Raises:
        KeyError: SKU not in catalog CSV.
        DossierMissingError: SKU has no dossier file (pipeline must
            hard-fail rather than fall back to inferred DNA).

    The returned dict carries:
      - `spec` (str): the comprehensive judge spec, used verbatim by
        `_dna_to_spec()` when present.
      - Catalog row fields (sku, name, collection, etc.) from the CSV.
      - `_dossier` (Dossier object): for any caller that needs the
        structured fields directly.

    Callers that pass this dict to `run_tournament(... dna=...)` will
    get judges that score against canonical truth, not inferred DNA.
    """
    bundle = get_product_with_dossier(sku)
    dossier: Dossier = bundle["_dossier"]
    spec = build_judge_spec_from_dossier(dossier)
    return {
        **{k: v for k, v in bundle.items() if k != "_dossier"},
        "spec": spec,
        "_dossier": dossier,
    }


def augment_prompt_with_dossier_negatives(prompt: str, dna: dict) -> str:
    """Append the dossier's negative block to a generation prompt (Layer 2).

    Image generators (Gemini, GPT-Image, FLUX) don't have a separate
    `negative_prompt` field on the chat-completions/messages-create
    surfaces we use; the only way to apply explicit negative
    constraints is to encode them in the prompt text. This helper
    augments a prompt-registry-built prompt with the canonical
    dossier's `negative_block` so authored "DO NOT render X" rules
    flow through to the generator, not just the judges.

    Behavior:
    - If `dna["_dossier"]` is missing or has no `negative_block`,
      return the prompt unchanged. Callers stay backward-compatible.
    - Otherwise, append the dossier's verbatim negative block under a
      DO NOT RENDER heading. The auto-generated negatives from the
      prompt registry are preserved; we only ADD authored negatives.
    """
    dossier = dna.get("_dossier")
    if not dossier:
        return prompt
    negative_block = getattr(dossier, "negative_block", "") or ""
    if not negative_block.strip():
        return prompt
    return f"{prompt}\n\nDO NOT RENDER (authored canonical negatives):\n{negative_block}"


__all__ = [
    "build_judge_spec_from_dossier",
    "build_dna_from_sku",
    "augment_prompt_with_dossier_negatives",
]
