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
    dna = build_dna_from_sku("br-001")  # VisionContext; raises if dossier missing
    result = run_tournament(clients, source, candidate, dna=dna)

The returned VisionContext provides dict-style read access via its
`__getitem__`/`get`/`__contains__` shim, so existing consumers like
`tournament._dna_to_spec` (which reads `dna.get("spec")`) work without
modification. The `spec` attribute carries the canonical multi-section
judge text that bypasses the lossy prose synthesis from flat fields.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from nano_banana.vision_context import VisionContext  # noqa: E402

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


def build_dna_from_sku(sku: str) -> VisionContext:
    """Return a VisionContext for `sku` keyed off the canonical dossier.

    Raises:
        KeyError: SKU not in catalog CSV.
        DossierMissingError: SKU has no dossier file (pipeline must
            hard-fail rather than fall back to inferred DNA).

    The returned VisionContext carries:
      - `spec` (str): the comprehensive judge spec, used verbatim by
        `_dna_to_spec()` when present (read via `dna.get("spec")`).
      - `dossier` (Dossier): the structured dossier object (also
        accessible via `dna.get("_dossier")` for legacy consumers).
      - `catalog` (dict): catalog row fields (sku, name, collection,
        etc.) from the CSV. Read via `dna.get("name")` etc.
      - `inferred` (dict): empty here; populated by Gemini-vision in
        `pipeline._get_or_cache_vision`.

    Callers that pass this object to `run_tournament(... dna=...)` get
    judges that score against canonical truth, not inferred DNA. The
    Mapping-style read shim means consumer code that does
    `dna.get("garment_type")` continues working — the lookup falls
    through to `catalog` (CSV) and then to `inferred` (vision).
    """
    bundle = get_product_with_dossier(sku)
    dossier: Dossier = bundle["_dossier"]
    spec = build_judge_spec_from_dossier(dossier)
    catalog_fields = {k: v for k, v in bundle.items() if k != "_dossier"}
    return VisionContext(
        inferred={},
        catalog=catalog_fields,
        spec=spec,
        dossier=dossier,
    )


def augment_prompt_with_dossier_negatives(prompt: str, dna: VisionContext | dict) -> str:
    """Append the dossier's negative block to a generation prompt (Layer 2).

    Image generators (Gemini, GPT-Image, FLUX) don't have a separate
    `negative_prompt` field on the chat-completions/messages-create
    surfaces we use; the only way to apply explicit negative
    constraints is to encode them in the prompt text. This helper
    augments a prompt-registry-built prompt with the canonical
    dossier's `negative_block` so authored "DO NOT render X" rules
    flow through to the generator, not just the judges.

    Accepts both `VisionContext` (production path) and plain `dict`
    (test fixtures and legacy callers) via the `.get("_dossier")` shim.

    Behavior:
    - If the dossier is missing or has no `negative_block`, return the
      prompt unchanged. Callers stay backward-compatible.
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
